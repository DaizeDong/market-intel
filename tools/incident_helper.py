#!/usr/bin/env python3
"""Semi-automatic draft helper for the 6-step `runbooks/fix-broken-tool.md` incident flow.

User describes an incident in 1-2 sentences. Helper:
  - Parses it via `claude -p` into a structured {slug, outcome, detail, domain, d_code}.
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
      --detail "gh api 404 since 2025-04" [--domain crypto-defi] [--d-code D-404]

Exit codes:
  0  drafts generated cleanly
  1  parse error (bad LLM JSON, bad CLI args)
  2  claude -p invocation error
  3  claude CLI not on PATH
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from typing import Optional

# ─── stdout UTF-8 safety (Windows) ───────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ─── paths ───────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datadir import resolve_data_dir, DataDirNotInitialized  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = "market-intel"


def live_runs_path() -> str:
    """Where a real-run observation gets appended: the PRIVATE store, or nowhere at all.

    This is the WRITER, and unlike the reader in feedback-bump.py it must never degrade quietly.
    A writer that shrugs when the destination is missing has exactly two options, and both are the
    bug: drop the operator's observation on the floor, or "helpfully" fall back to a path inside
    the repo -- which is precisely how live-runs.jsonl came to sit in a public repo, one real
    research run at a time, recording what the operator was investigating. So: raise, with
    instructions, and let the human decide where their data lives.
    """
    d = resolve_data_dir(SKILL)
    if d is None:
        raise DataDirNotInitialized(
            "market-intel has no private data directory, so there is nowhere to record this\n"
            "observation. A live-run entry describes what YOU were actually researching -- it is\n"
            "data, not tool knowledge, and it never goes back into the public repo.\n"
            "    mkdir -p ~/.market-intel-config/data/metrics\n"
            "    (or set MARKET_INTEL_DATA_DIR)\n"
            "The shape is in skills/market-intel/metrics/live-runs.jsonl.example."
        )
    return os.path.join(str(d), "metrics", "live-runs.jsonl")


DOMAINS_DIR = os.path.join(ROOT, "skills", "market-intel", "reference", "domains")
SOURCES_INDEX = os.path.join(ROOT, "skills", "market-intel", "reference", "sources-index.md")

VALID_OUTCOMES = {
    "dead", "barrier_found", "coverage_gap",
    "price_mismatch", "verified", "user_correction",
}
VALID_D_CODES = {"D-404", "D-PRICE", "D-STALE", "D-TOS", "D-SUPERSEDED", "none"}
VALID_DOMAINS = {
    "x-twitter", "reddit-community", "web-scraping", "ecommerce-arbitrage",
    "finance-markets", "crypto-defi", "seo-keywords", "social-publishing",
    "content-cms", "leadgen-crm", "trends-discovery", "frontier-research",
    "ready-skills", "browser-automation", "consumer-price-compare", "mcp-ecosystem",
}

D_CODE_EXPLANATIONS = {
    "D-404": "repo / endpoint gone (HTTP 404, dead URL, NXDOMAIN)",
    "D-PRICE": "priced out of usefulness (free tier killed / paywall added / price jumped)",
    "D-STALE": "abandoned but technically reachable (last commit >12mo, no releases)",
    "D-TOS": "TOS / legal hostility (active scraping bans, captcha walls, account bans)",
    "D-SUPERSEDED": "replaced by a clearly better thing — REQUIRES a named successor",
    "none": "not deprecated — this is barrier_found / verified / coverage_gap / etc.",
}


# ─── LLM bridge ──────────────────────────────────────────────────────────────
def _run_claude(prompt: str, stdin_payload: Optional[str] = None, timeout: int = 180) -> str:
    """Invoke `claude -p <prompt>`; optionally pipe extra context via stdin.

    Returns stdout text on success, raises RuntimeError on non-zero exit.
    Uses argument-form for the prompt (clearer) and stdin only for bulk context
    (e.g. a shard file's contents) so the prompt stays auditable in process lists.
    """
    if not shutil.which("claude"):
        print("ERROR: `claude` CLI not on PATH — install it or fix PATH", file=sys.stderr)
        sys.exit(3)
    cmd = ["claude", "-p", prompt]
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_payload if stdin_payload is not None else "",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"claude -p timed out after {timeout}s")
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p exited {proc.returncode}: {proc.stderr.strip()[:400]}"
        )
    return proc.stdout.strip()


def _extract_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in ```json ... ``` fences or add prose. Strip and parse."""
    s = text.strip()
    # Strip code fences if present.
    if s.startswith("```"):
        # Drop first fence line.
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()
    # Find first { ... } block.
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object found in LLM reply: {text[:300]}")
    return json.loads(s[start:end + 1])


# ─── step 2: parse the incident into structure ───────────────────────────────
def parse_incident(user_text: str) -> dict:
    """Ask claude -p to extract {slug, outcome, detail, domain, d_code} from free text."""
    prompt = (
        "You are parsing a market-intel incident report. Extract these fields:\n"
        "- slug: tool slug (e.g. \"funding-rates-mcp\" or \"kukapay/funding-rates-mcp\" or \"barker\")\n"
        "- outcome: one of [dead, barrier_found, coverage_gap, price_mismatch, verified, user_correction]\n"
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
        raw = _run_claude(prompt)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        data = _extract_json(raw)
    except Exception as e:
        print(f"ERROR: failed to parse LLM JSON: {e}", file=sys.stderr)
        print(f"--- raw reply ---\n{raw}", file=sys.stderr)
        sys.exit(1)
    # Light validation — coerce instead of erroring, surface warnings.
    warnings = []
    if data.get("outcome") not in VALID_OUTCOMES:
        warnings.append(f"outcome={data.get('outcome')!r} not in canonical 6 — review manually")
    if data.get("domain") not in VALID_DOMAINS:
        warnings.append(f"domain={data.get('domain')!r} unknown — shard edit will be skipped")
    if data.get("d_code") not in VALID_D_CODES:
        warnings.append(f"d_code={data.get('d_code')!r} not in canonical set — review manually")
    data["_warnings"] = warnings
    return data


# ─── step 3: shard edit suggestion ───────────────────────────────────────────
def suggest_shard_edit(slug: str, d_code: str, domain: str, detail: str) -> Optional[str]:
    """Read the relevant shard, ask claude -p for the exact FROM/TO line edit.

    Returns suggestion text or None if shard doesn't exist / d_code is 'none'.
    """
    if d_code == "none":
        return "(d_code is 'none' — no tombstone needed; skipping shard edit suggestion)"
    shard_path = os.path.join(DOMAINS_DIR, f"{domain}.md")
    if not os.path.exists(shard_path):
        return f"(shard not found at {shard_path} — manual review required)"
    with open(shard_path, "r", encoding="utf-8-sig") as f:
        shard_text = f.read()
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
    except RuntimeError as e:
        return f"(claude -p failed for shard edit: {e})"


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
    except RuntimeError as e:
        return f"(claude -p failed for sources-index check: {e})"


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
    except RuntimeError as e:
        return f"(claude -p failed for commit message: {e})\nFallback skeleton:\n" + (
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
    """Append a single line to live-runs.jsonl — UTF-8, no BOM, LF terminated."""
    live_runs = live_runs_path()          # raises if uninitialized — never falls back into the repo
    os.makedirs(os.path.dirname(live_runs), exist_ok=True)
    # Read existing content as utf-8-sig (BOM-safe), write back as utf-8.
    existing = ""
    if os.path.exists(live_runs):
        with open(live_runs, "r", encoding="utf-8-sig") as f:
            existing = f.read()
    if existing and not existing.endswith("\n"):
        existing += "\n"
    new_content = existing + entry_line + "\n"
    with open(live_runs, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print(f"  ✓ appended to {live_runs}")


def apply_shard_edit(domain: str, from_line: str, to_block: str) -> None:
    """Replace `from_line` in the shard with `to_block`. Strict — fails if not found
    or multiple matches. BOM-safe read, BOM-less write."""
    shard_path = os.path.join(DOMAINS_DIR, f"{domain}.md")
    if not os.path.exists(shard_path):
        print(f"  ✗ shard not found: {shard_path}")
        return
    with open(shard_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    if from_line not in content:
        print(f"  ✗ FROM line not found verbatim in shard — apply manually")
        return
    if content.count(from_line) > 1:
        print(f"  ✗ FROM line appears {content.count(from_line)}x — ambiguous, apply manually")
        return
    new_content = content.replace(from_line, to_block, 1)
    with open(shard_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
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
    print(f"\n[Step 5] Config-side check (skip if no companion repo):")
    print(f"  python C:\\Users\\<username>\\CodesSelf\\market-intel-config\\scripts\\sync-check.py")
    print(f"  Expect: slug `{slug}` surfaces in bucket C; follow §C action per d_code.")

    # Step 6.
    print(f"\n[Step 6] Commit message draft:")
    commit_msg = suggest_commit_message(slug, d_code, domain, detail)
    for ln in commit_msg.splitlines():
        print(f"  {ln}")

    # Apply path — strictly opt-in, per-step y/N.
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
                   help="Domain shard name (skips LLM parse for this field).")
    p.add_argument("--d-code", dest="d_code", choices=sorted(VALID_D_CODES),
                   help="D-code (skips LLM parse for this field).")
    args = p.parse_args()

    # Build the struct: prefer explicit flags, fall back to LLM parse.
    have_structured = any([args.slug, args.outcome, args.detail])
    if not have_structured and not args.description:
        p.error("provide either a natural-language description or --slug/--outcome/--detail flags")

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
        struct.setdefault("d_code", "none")
        if not struct.get("slug") or not struct.get("outcome") or not struct.get("detail"):
            print("ERROR: --slug, --outcome, --detail all required when not using LLM parse",
                  file=sys.stderr)
            return 1
    else:
        struct = parse_incident(args.description)

    return run(struct, apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())
