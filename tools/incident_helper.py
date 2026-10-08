#!/usr/bin/env python3
"""Semi-automatic draft helper for the 6-step `runbooks/fix-broken-tool.md` incident flow.

User describes an incident in 1-2 sentences. Helper:
  - Parses it via installed llmcall into a structured {slug, outcome, detail, domain, d_code}.
  - Drafts the 6 step artifacts (live-runs.jsonl entry, D-code rationale, shard edit
    suggestion, sources-index advisory, config-side reminder, commit message).
  - Prints everything to stdout for human review.
  - With `--apply`, prompts y/N for steps 1 and 3 only — never auto-commits, never
    writes to git, never bypasses the human reviewer.

This is a DRAFT helper, not a gate. Per CONSTITUTION P4 (Mechanisms not intentions):
the mechanism here is "force human review before any artifact lands." Apply ≠ commit.

Usage:
  python tools/incident_helper.py "<natural language incident description>"
  python tools/incident_helper.py --apply "<...>"
  python tools/incident_helper.py --slug funding-rates-mcp --outcome dead \\
      --detail "gh api 404 since 2025-04" --domain crypto-defi [--d-code D-404]

Exit codes:
  0  drafts generated cleanly
  1  invalid incident fields or an unsafe shard path
  2  private destination or persistence failure
  3  optional model interface is uninitialized
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Optional

from model_adapter import ModelUnavailable, call as _llmcall, require_call

# ─── stdout UTF-8 safety (Windows) ───────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ─── paths ───────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import private_inventory  # noqa: E402
from ledger_schema import OUTCOMES
from document_io import read_document, replace_document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = "market-intel"
LIVE_RUNS_RELATIVE = "metrics/live-runs.jsonl"


def live_runs_path() -> str:
    """Resolve a canonical, versionable PRIVATE destination without creating it."""
    return str(private_inventory.resolve_destination(LIVE_RUNS_RELATIVE).path)


DOMAINS_DIR = os.path.join(ROOT, "skills", "market-intel", "reference", "domains")
SOURCES_INDEX = os.path.join(ROOT, "skills", "market-intel", "reference", "sources-index.md")

VALID_OUTCOMES = set(OUTCOMES)
VALID_D_CODES = {"D-404", "D-PRICE", "D-STALE", "D-TOS", "D-SUPERSEDED", "none"}
VALID_DOMAINS = {
    "x-twitter", "reddit-community", "web-scraping", "ecommerce-arbitrage",
    "finance-markets", "crypto-defi", "seo-keywords", "social-publishing",
    "content-cms", "leadgen-crm", "trends-discovery", "frontier-research",
    "ready-skills", "browser-automation", "consumer-price-compare", "mcp-ecosystem",
}

D_CODE_EXPLANATIONS = {
    "D-404": "confirmed API 404 or archived repository",
    "D-PRICE": "official price page proves the route is now paywalled, with URL and date",
    "D-STALE": "more than 18 months without a push AND a verified replacement added",
    "D-TOS": "official policy proves the route is no longer permitted",
    "D-SUPERSEDED": "a named verified better source replaces it, with supporting evidence",
    "none": "not deprecated — this is barrier_found / verified / coverage_gap / etc.",
}


def config_check_advisory() -> str:
    """Locate the optional companion checker without reading config or running it."""
    try:
        from config_paths import companion_root
        selected = companion_root()
        if selected is None:
            return "SKIP: no companion is configured under the documented discovery convention."
        if not selected.is_dir():
            return f"GAP: selected companion is not an existing directory: {selected}"
        checker = selected.resolve() / "scripts" / "sync-check.py"
        if not checker.is_file():
            return f"GAP: selected companion checker is missing: {checker}"
    except (OSError, RuntimeError, ValueError):
        return "GAP: selected companion path could not be resolved; check the configuration."
    argument = "'" + str(checker).replace("'", "''") + "'" if os.name == "nt" else shlex.quote(str(checker))
    return (f"python {argument}\n"
            "Inspect the actual sync report. If it reports a bucket C tombstone, follow the selected "
            "companion's runbooks/sync-with-skill.md section C.")


# ─── LLM bridge ──────────────────────────────────────────────────────────────
def _run_claude(prompt: str, stdin_payload: Optional[str] = None) -> str:
    """Parse via the installed llmcall routing and defaults. Extra bulk
    context is folded into the prompt (llmcall takes a single prompt on stdin). Returns text on
    success, raises RuntimeError if the whole chain failed."""
    full = f"{prompt}\n\n{stdin_payload}" if stdin_payload else prompt
    try:
        r = _llmcall(full)
    except ModelUnavailable:
        raise
    except Exception:
        raise RuntimeError("llmcall could not complete the draft; inspect private provider diagnostics") from None
    if not r:
        raise RuntimeError("llmcall could not complete the draft; inspect private provider diagnostics")
    return r.text.strip()


_INCIDENT_FIELDS = ("slug", "outcome", "detail", "domain", "d_code")
_INCIDENT_SCHEMA = {
    "type": "object",
    "required": list(_INCIDENT_FIELDS),
    "properties": {
        "slug": {"type": "string", "minLength": 1},
        "outcome": {"type": "string", "enum": sorted(VALID_OUTCOMES)},
        "detail": {"type": "string", "minLength": 1},
        "domain": {"type": "string", "enum": sorted(VALID_DOMAINS)},
        "d_code": {"type": "string", "enum": sorted(VALID_D_CODES)},
    },
}


def _validate_incident(data):
    """Reject untrusted fields before drafting can read files or call a model."""
    if not isinstance(data, dict):
        raise ValueError("incident must be an object")
    for field in _INCIDENT_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"{field} must be a nonempty string")
    for field, allowed in (("outcome", VALID_OUTCOMES), ("domain", VALID_DOMAINS),
                           ("d_code", VALID_D_CODES)):
        if data[field] not in allowed:
            raise ValueError(f"{field} must be a supported value")


def _shard_path(domain):
    """Validate the domain again and keep resolved shard paths inside the directory."""
    if not isinstance(domain, str) or domain not in VALID_DOMAINS:
        raise ValueError("domain must be a supported value")
    directory = os.path.realpath(DOMAINS_DIR)
    shard = os.path.join(DOMAINS_DIR, f"{domain}.md")
    if os.path.dirname(os.path.realpath(shard)) != directory:
        raise ValueError("domain shard resolves outside the domains directory")
    return shard


# ─── step 2: parse the incident into structure ───────────────────────────────
def parse_incident(user_text: str) -> dict:
    """Ask installed llmcall to extract {slug, outcome, detail, domain, d_code} from free text."""
    prompt = (
        "You are parsing a market-intel incident report. Extract these fields:\n"
        "- slug: tool slug (e.g. \"funding-rates-mcp\" or \"kukapay/funding-rates-mcp\" or \"barker\")\n"
        f"- outcome: one of [{', '.join(OUTCOMES)}]\n"
        "- detail: 1-line specific observation (<=200 chars, include evidence like dates/URLs)\n"
        "- domain: one of [x-twitter, reddit-community, web-scraping, ecommerce-arbitrage, "
        "finance-markets, crypto-defi, seo-keywords, social-publishing, content-cms, leadgen-crm, "
        "trends-discovery, frontier-research, ready-skills, browser-automation, "
        "consumer-price-compare, mcp-ecosystem]\n"
        "- d_code: one of [D-404, D-PRICE, D-STALE, D-TOS, D-SUPERSEDED, none] "
        "(use \"none\" if outcome is not 'dead' or the tool isn't deprecated)\n\n"
        "Reply ONLY with a JSON object on a single line, no prose, no code fences. "
        "Example: {\"slug\":\"funding-rates-mcp\",\"outcome\":\"dead\","
        "\"detail\":\"gh api 404 since 2025-04\",\"domain\":\"crypto-defi\","
        "\"d_code\":\"D-404\"}\n\n"
        f"Incident description: {user_text}"
    )
    try:
        r = _llmcall(prompt, schema=_INCIDENT_SCHEMA)
    except ModelUnavailable as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(3) from None
    except Exception:
        print("ERROR: incident model call failed; inspect private provider diagnostics", file=sys.stderr)
        raise SystemExit(1) from None
    if not r:
        # covers both a dead chain and a reply that never validated (llmcall already retried once)
        print("ERROR: incident model or schema validation failed; inspect private provider diagnostics", file=sys.stderr)
        sys.exit(1)
    data = r.data
    try:
        _validate_incident(data)
    except ValueError as exc:
        print(f"ERROR: invalid incident: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    return {**{field: data[field] for field in _INCIDENT_FIELDS}, "_warnings": []}


# ─── step 3: shard edit suggestion ───────────────────────────────────────────
def suggest_shard_edit(slug: str, d_code: str, domain: str, detail: str) -> Optional[str]:
    """Read the relevant shard, ask installed llmcall for the exact FROM/TO line edit.

    Returns suggestion text or None if shard doesn't exist / d_code is 'none'.
    """
    shard_path = _shard_path(domain)
    if d_code == "none":
        return "(d_code is 'none' — no tombstone needed; skipping shard edit suggestion)"
    if not os.path.exists(shard_path):
        return f"(shard not found at {shard_path} — manual review required)"
    shard_text, _ = read_document(shard_path, DOMAINS_DIR)
    prompt = (
        "You are suggesting a tombstone edit for a market-intel domain shard. "
        "Given the shard markdown below (piped via stdin), find the table row that "
        f"corresponds to the slug `{slug}`. "
        f"Suggest the EXACT line edit per runbooks/fix-broken-tool.md Step 3 — "
        "tombstone the row with strikethrough and a `⚠ Avoid (dead, "
        f"{d_code})` note. Do NOT delete the row. If a successor is already in the "
        "shard, keep it as-is.\n\n"
        f"Evidence: {detail}\n\n"
        "Output format — exactly three sections, no prose outside them:\n"
        "FROM:\n<the exact existing line to replace>\n"
        "TO:\n<the replacement line(s)>\n"
        "NOTES:\n<1-3 lines: which row you matched, any caveats, whether default-pick "
        "needs updating>\n\n"
        "If you cannot find a matching row, output:\n"
        f"FROM:\n(no matching row for `{slug}` — manual lookup needed)\n"
        "TO:\n(n/a)\n"
        "NOTES:\n<grep the shard for the closest match>"
    )
    try:
        return _run_claude(prompt, stdin_payload=shard_text)
    except ModelUnavailable:
        raise
    except RuntimeError as e:
        return f"(llmcall failed for shard edit: {e})"


# ─── step 4: sources-index advisory ──────────────────────────────────────────
def sources_index_advisory(slug: str, d_code: str, domain: str) -> str:
    """For D-SUPERSEDED, ask if sources-index.md top-pick mention needs updating."""
    if d_code != "D-SUPERSEDED":
        return ("(d_code is not D-SUPERSEDED — sources-index.md edit is unlikely needed; "
                "skip unless the shard's `Default pick:` line moved)")
    if not os.path.exists(SOURCES_INDEX):
        return f"(sources-index.md not found at {SOURCES_INDEX} — manual review)"
    with open(SOURCES_INDEX, "r", encoding="utf-8-sig") as f:
        idx_text = f.read()
    prompt = (
        f"Check if `sources-index.md` (piped via stdin) mentions slug `{slug}` as the "
        f"top pick for domain `{domain}`. If yes, the index needs updating once the shard "
        "default-pick line moves to the successor. If no, no edit needed.\n\n"
        "Reply in 2-3 lines:\n"
        "MENTION: yes|no — <quote the line if yes>\n"
        "ACTION: <skip | edit-after-shard-default-changes | other>"
    )
    try:
        return _run_claude(prompt, stdin_payload=idx_text)
    except ModelUnavailable:
        raise
    except RuntimeError as e:
        return f"(llmcall failed for sources-index check: {e})"


# ─── step 6: commit message ──────────────────────────────────────────────────
def suggest_commit_message(slug: str, d_code: str, domain: str, detail: str) -> str:
    """Draft the `incident: <slug> D-<code>` commit message."""
    if d_code == "none":
        d_code_for_msg = "<pick code or use generic>"
    else:
        d_code_for_msg = d_code
    prompt = (
        "Draft a git commit message for a market-intel incident fix. Format strictly:\n\n"
        "Line 1 (subject, <=72 chars): `incident: <slug> <D-code> — <short reason>`\n"
        "Blank line\n"
        "Body: 2-4 lines covering: what broke, evidence (URL/date), successor if any, "
        "downstream config touched yes/no.\n"
        "Footer line: `Per runbooks/fix-broken-tool.md.`\n\n"
        f"Inputs:\n  slug: {slug}\n  d_code: {d_code_for_msg}\n  domain: {domain}\n"
        f"  detail: {detail}\n\n"
        "Output ONLY the commit message text, no markdown fences, no preamble."
    )
    try:
        return _run_claude(prompt)
    except ModelUnavailable:
        raise
    except RuntimeError as e:
        return f"(llmcall failed for commit message: {e})\nFallback skeleton:\n" + (
            f"incident: {slug} {d_code_for_msg}\n\n"
            f"{detail}\n\n"
            "Per runbooks/fix-broken-tool.md."
        )


# ─── step 1 artifact: live-runs.jsonl line ───────────────────────────────────
def build_live_runs_entry(struct: dict) -> str:
    """Build the JSON line for metrics/live-runs.jsonl. Date-only ts is fine —
    the existing entries (sample read at write time) use YYYY-MM-DD."""
    today = dt.date.today().isoformat()
    entry = {
        "ts": today,
        "domain": struct.get("domain", "<unknown>"),
        "source": f"shard/{struct.get('slug', '<unknown>')}",
        "route": "①",  # best-guess default; user can edit
        "outcome": struct.get("outcome", "<unknown>"),
        "detail": struct.get("detail", ""),
        "user_correction": None,
    }
    return json.dumps(entry, ensure_ascii=False)


# ─── apply helpers ───────────────────────────────────────────────────────────
def _prompt_yn(question: str) -> bool:
    try:
        ans = input(f"{question} (y/N): ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def apply_live_runs_append(entry_line: str) -> None:
    """Append through a reverified PRIVATE target and preserve it on write failure."""
    def append(existing):
        separator = "\n" if existing and not existing.endswith("\n") else ""
        return existing + separator + entry_line + "\n"
    saved = private_inventory.update_text(append, LIVE_RUNS_RELATIVE)
    print(f"  ✓ appended incident ledger; PRIVATE companion {saved.identity}")


def apply_shard_edit(domain: str, from_line: str, to_block: str) -> None:
    """Replace `from_line` in the shard with `to_block`. Strict — fails if not found
    or multiple matches. BOM-safe read, BOM-less write."""
    shard_path = _shard_path(domain)
    if not os.path.exists(shard_path):
        print(f"  ✗ shard not found: {shard_path}")
        return
    content, expected = read_document(shard_path, DOMAINS_DIR)
    if from_line not in content:
        print(f"  ✗ FROM line not found verbatim in shard — apply manually")
        return
    if content.count(from_line) > 1:
        print(f"  ✗ FROM line appears {content.count(from_line)}x — ambiguous, apply manually")
        return
    new_content = content.replace(from_line, to_block, 1)
    replace_document(shard_path, DOMAINS_DIR, new_content, expected)
    print(f"  ✓ edited {shard_path}")


def _parse_from_to(shard_suggestion: str) -> Optional[tuple]:
    """Pull FROM:/TO: blocks from the suggestion text. Returns (from_line, to_block) or None."""
    if "FROM:" not in shard_suggestion or "TO:" not in shard_suggestion:
        return None
    try:
        after_from = shard_suggestion.split("FROM:", 1)[1]
        from_part, rest = after_from.split("TO:", 1)
        to_part = rest.split("NOTES:", 1)[0] if "NOTES:" in rest else rest
        from_line = from_part.strip().splitlines()
        to_lines = to_part.strip().splitlines()
        if not from_line or not to_lines:
            return None
        # Use just first non-empty line for FROM (table row); preserve all TO lines.
        from_line_str = next((ln for ln in from_line if ln.strip()), "").rstrip()
        to_block_str = "\n".join(to_lines).rstrip()
        if not from_line_str or from_line_str.startswith("("):
            return None
        return (from_line_str, to_block_str)
    except Exception:
        return None


# ─── orchestrator ────────────────────────────────────────────────────────────
HONEST_BOUNDARY = """
---
Generated by incident_helper.py. Per PHILOSOPHY P4: this is a DRAFT.
- Every artifact above must be reviewed before applying.
- Re-run with --apply only after you've sanity-checked the slug, outcome, and shard edit.
- The commit itself is YOUR responsibility — the helper doesn't push.
"""


def run(struct: dict, apply: bool) -> int:
    try:
        _validate_incident(struct)
    except ValueError as exc:
        print(f"ERROR: invalid incident: {exc}", file=sys.stderr)
        return 1
    # Surface any parse warnings up-front.
    for w in struct.get("_warnings", []):
        print(f"WARN: {w}", file=sys.stderr)

    slug = struct.get("slug", "<unknown>")
    outcome = struct.get("outcome", "<unknown>")
    detail = struct.get("detail", "")
    domain = struct.get("domain", "<unknown>")
    d_code = struct.get("d_code", "none")

    print("=" * 72)
    print(f"INCIDENT DRAFT  —  slug={slug}  outcome={outcome}  domain={domain}  d_code={d_code}")
    print("=" * 72)

    # Step 1.
    entry_line = build_live_runs_entry(struct)
    print("\n[Step 1] live-runs.jsonl entry  (review the `route` field — defaulted to ①):")
    print(f"  {entry_line}")

    # Step 2.
    print(f"\n[Step 2] D-code: {d_code}")
    print(f"  rationale: {D_CODE_EXPLANATIONS.get(d_code, 'unknown code — manual review')}")

    # Step 3.
    print(f"\n[Step 3] Shard edit suggestion ({domain}.md):")
    shard_suggestion = suggest_shard_edit(slug, d_code, domain, detail)
    if shard_suggestion:
        for ln in shard_suggestion.splitlines():
            print(f"  {ln}")

    # Step 4.
    print(f"\n[Step 4] sources-index.md advisory:")
    idx_advisory = sources_index_advisory(slug, d_code, domain)
    for ln in idx_advisory.splitlines():
        print(f"  {ln}")

    # Step 5.
    print("\n[Step 5] Config-side check (review before running):")
    for line in config_check_advisory().splitlines():
        print(f"  {line}")

    # Step 6.
    print(f"\n[Step 6] Commit message draft:")
    commit_msg = suggest_commit_message(slug, d_code, domain, detail)
    for ln in commit_msg.splitlines():
        print(f"  {ln}")

    # Apply path, strictly opt-in, per-step y/N.
    if apply:
        print("\n" + "=" * 72)
        print("APPLY MODE — each step is opt-in. Review the draft above before answering.")
        print("=" * 72)
        if _prompt_yn("\nApply step 1 (append entry to live-runs.jsonl)?"):
            apply_live_runs_append(entry_line)
        else:
            print("  - skipped")

        parsed = _parse_from_to(shard_suggestion or "")
        if parsed and d_code != "none":
            from_line, to_block = parsed
            print(f"\nProposed shard edit:")
            print(f"  FROM: {from_line}")
            print(f"  TO:   {to_block.splitlines()[0]}{' ...' if len(to_block.splitlines()) > 1 else ''}")
            if _prompt_yn("Apply step 3 (edit shard)?"):
                apply_shard_edit(domain, from_line, to_block)
            else:
                print("  - skipped")
        else:
            print("\nStep 3 not auto-applicable (no clean FROM/TO parse or d_code=none).")
            print("  Apply manually after reviewing the suggestion above.")

        print("\nReminder: review `git diff`, then commit with the suggested message.")
        print("         Helper does NOT auto-commit and does NOT push.")

    print(HONEST_BOUNDARY)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Semi-automatic draft helper for runbooks/fix-broken-tool.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("description", nargs="?",
                   help="Natural-language incident description (1-2 sentences).")
    p.add_argument("--apply", action="store_true",
                   help="After printing drafts, prompt y/N for step 1 and step 3 apply. "
                        "Default OFF — drafts only.")
    p.add_argument("--slug", help="Skip LLM parse — provide slug directly.")
    p.add_argument("--outcome", choices=sorted(VALID_OUTCOMES),
                   help="Skip LLM parse — provide outcome directly.")
    p.add_argument("--detail", help="Skip LLM parse — provide detail directly.")
    p.add_argument("--domain", choices=sorted(VALID_DOMAINS),
                   help="Supported domain shard; required without a parsed incident description.")
    p.add_argument("--d-code", dest="d_code", choices=sorted(VALID_D_CODES),
                   help="D-code (skips LLM parse for this field).")
    args = p.parse_args()

    # Build the struct: prefer explicit flags, fall back to LLM parse.
    have_structured = any([args.slug, args.outcome, args.detail])
    if not have_structured and not args.description:
        p.error("provide either a natural-language description or --slug/--outcome/--detail flags")

    try:
        require_call()
    except ModelUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 3

    if have_structured:
        # Use flags; if any required field is missing, ask LLM to fill the rest using description.
        struct = {
            "slug": args.slug,
            "outcome": args.outcome,
            "detail": args.detail,
            "domain": args.domain,
            "d_code": args.d_code,
            "_warnings": [],
        }
        # If description also given, let the LLM fill missing fields.
        if args.description and (not args.domain or not args.d_code or not args.outcome):
            llm_struct = parse_incident(args.description)
            for k in ("slug", "outcome", "detail", "domain", "d_code"):
                if not struct.get(k):
                    struct[k] = llm_struct.get(k)
            struct["_warnings"].extend(llm_struct.get("_warnings", []))
        # Defaults if still missing.
        struct.setdefault("domain", "<unknown>")
        struct["d_code"] = struct.get("d_code") or "none"
        if not struct.get("slug") or not struct.get("outcome") or not struct.get("detail"):
            print("ERROR: --slug, --outcome, --detail all required when not using LLM parse",
                  file=sys.stderr)
            return 1
    else:
        struct = parse_incident(args.description)

    try:
        return run(struct, apply=args.apply)
    except ModelUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except private_inventory.InventoryError as exc:
        print(f"ERROR: incident persistence failed: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERROR: invalid incident shard: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
