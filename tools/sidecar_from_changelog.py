#!/usr/bin/env python3
"""
sidecar_from_changelog.py — generate a machine-readable sweep sidecar JSON
from the latest CHANGELOG entry + the matching per-tool reference docs.

Reads:
    CHANGELOG.md (repo root)
    skills/market-intel/reference/tools/<slug>.md (per detected slug)

Writes:
    metrics/sweep-<version>.json (default; overridable with --out)

The output is consumed by companion-config-bridge.py to apply ADD/REPLACE
moves into the companion config. The bridge does NOT trust the
`auto_configurable_hint` flag — it is a heuristic for downstream sorting,
not a green-light per user direction ("不分类, 直接尝试").

CLI:
    python tools/sidecar_from_changelog.py --version 0.23.0 [--out PATH] [--dry-run]

Exit codes:
    0 — success (file written, or dry-run succeeded)
    1 — version not found in CHANGELOG
    2 — all detected slugs unresolved (nothing actionable to emit)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Output / encoding hygiene                                                   #
# --------------------------------------------------------------------------- #

def _reconfigure_stdout_utf8() -> None:
    """Make stdout BOM-safe on Windows so unicode summary prints cleanly."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # py3.7+
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Repo paths                                                                  #
# --------------------------------------------------------------------------- #

# Resolve repo root relative to this script: <repo>/tools/sidecar_from_changelog.py
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
TOOLS_DOC_DIR = REPO_ROOT / "skills" / "market-intel" / "reference" / "tools"
METRICS_DIR = REPO_ROOT / "metrics"


# --------------------------------------------------------------------------- #
# CHANGELOG parsing                                                           #
# --------------------------------------------------------------------------- #

# `## [0.20.0] — 2026-06-17` or `## [0.20.0] - 2026-06-17`
# We tolerate em-dash (—), en-dash (–), hyphen (-), and any amount of surrounding ws.
_HEADING_RE = re.compile(
    r"^##\s*\[(?P<ver>[^\]]+)\]\s*[—–-]\s*(?P<date>\d{4}-\d{2}-\d{2})\s*$",
    re.MULTILINE,
)


def _read_changelog() -> str:
    return CHANGELOG_PATH.read_text(encoding="utf-8-sig")


def _find_entry(text: str, version: str) -> Optional[tuple[str, str, Optional[str]]]:
    """
    Return (body, date, previous_version) for the requested version, or None.

    body is the slice between the matching `## [ver]` heading and the NEXT
    `## [` heading (or EOF).
    """
    matches = list(_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group("ver").strip() == version:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            prev_ver = matches[i + 1].group("ver").strip() if i + 1 < len(matches) else None
            return body, m.group("date"), prev_ver
    return None


# --------------------------------------------------------------------------- #
# Slug extraction from CHANGELOG body                                         #
# --------------------------------------------------------------------------- #

# Backtick-quoted slugs — the dominant form in v0.20+ entries
_BACKTICK_RE = re.compile(r"`([^`]+)`")

# Stale-marker suffix that appears next to old slugs in REPLACE lines,
# e.g. ``funding-rates-mcp` (D-STALE)``.
_STALE_SUFFIX_RE = re.compile(r"\s*\(D-[A-Z]+\)\s*$")

# Heading detectors for the "Adds" and "Replaces" sub-blocks. The format
# drifts across releases — we look for multiple shapes.
_ADDS_HEADERS = (
    re.compile(r"^\*\*Adds(?:\s*\(\d+\))?:\*\*", re.MULTILINE),
    re.compile(r"^Adds(?:\s*\(\d+\))?:", re.MULTILINE),
    re.compile(r"^###\s+Adds", re.MULTILINE),
)
_REPLACES_HEADERS = (
    re.compile(r"^\*\*Replaces?(?:\s*\(\d+\))?:\*\*", re.MULTILINE),
    re.compile(r"^Replaces?(?:\s*\(\d+\))?:", re.MULTILINE),
    re.compile(r"^###\s+Replaces?", re.MULTILINE),
)


def _slice_after(body: str, headers: tuple[re.Pattern, ...]) -> Optional[str]:
    """
    Return the text starting AT the first matched header through the end of
    the body. We don't try to find the next sibling header — splitting by
    paragraph break later handles where this sub-block ends.
    """
    for pat in headers:
        m = pat.search(body)
        if m:
            return body[m.end():]
    return None


def _isolate_block(text: str) -> str:
    """
    Heuristic block-isolation: stop at the next markdown subheading (`###` or
    `##`) **or** the next bold-bullet sibling header line like `**Replaces (N):**`
    / `**HOLD (N):**`. Without the sibling-bold cutoff, the Adds prose flows
    straight into the Replaces prose in v0.20.0-style entries.
    """
    cut = len(text)
    for marker in ("\n## ", "\n### "):
        idx = text.find(marker)
        if idx != -1 and idx < cut:
            cut = idx

    # Stop at the next `**<Word>` bold-bullet sibling heading. We search by
    # regex so we tolerate `**Replaces (4):**`, `**HOLD (1):**`, etc. The
    # caller already sliced AFTER our own opening bullet, so any match here
    # is a sibling — cut at the first one.
    sibling_re = re.compile(r"(?m)^\*\*[A-Z][A-Za-z ]+(?:\s*\(\d+\))?:\*\*")
    m = sibling_re.search(text)
    if m and m.start() < cut:
        cut = m.start()

    return text[:cut]


def _extract_adds_slugs(body: str) -> list[str]:
    sub = _slice_after(body, _ADDS_HEADERS)
    if sub is None:
        return []
    block = _isolate_block(sub)
    return [s.strip() for s in _BACKTICK_RE.findall(block)]


def _extract_replaces(body: str) -> list[tuple[str, str]]:
    """
    Return list of (old_slug, new_slug). Format is `old → new`
    (em-arrow), `old -> new`, or `old to new`. We treat each
    backticked-pair separated by an arrow within the block as one mapping.
    """
    sub = _slice_after(body, _REPLACES_HEADERS)
    if sub is None:
        return []
    block = _isolate_block(sub)

    pairs: list[tuple[str, str]] = []

    # Pattern: `<old>` [optional decorator like ` (D-STALE)`] <arrow> `<new>`.
    # Arrow can be →, ->, =>, "to". We allow up to ~40 chars of any non-
    # backtick text between the closing backtick of `old` and the arrow to
    # tolerate bracketed D-code annotations (e.g. ``funding-rates-mcp` (D-STALE) →``).
    # The non-greedy quantifier + lookahead-style arrow alternation prevents
    # cross-pair spans.
    pair_re = re.compile(
        r"`([^`]+)`[^`]{0,40}?(?:→|->|=>|\s+to\s+)\s*`([^`]+)`",
    )
    for m in pair_re.finditer(block):
        old = _STALE_SUFFIX_RE.sub("", m.group(1).strip())
        new = _STALE_SUFFIX_RE.sub("", m.group(2).strip())
        pairs.append((old, new))

    return pairs


# --------------------------------------------------------------------------- #
# Slug → file resolution                                                      #
# --------------------------------------------------------------------------- #

def _slugify_candidates(raw: str) -> list[str]:
    """
    Given a slug as it appears in CHANGELOG, produce ordered candidate
    filename stems to look up in TOOLS_DOC_DIR. Tried in order; first hit wins.

    Strategy:
      1. lowercased verbatim with underscores → hyphens
      2. drop GitHub-owner prefix (`Owner/Repo` → `Repo`)
      3. owner-prefixed kebab form (`SaseQ/discord-mcp` → `saseq-discord-mcp`)
      4. strip common decorative suffixes like ` MCP`, `.ai`, parens
      5. collapse any run of non-alnum to single hyphen
    """
    candidates: list[str] = []
    raw = raw.strip()

    def _norm(s: str) -> str:
        s = s.lower()
        # turn underscores into hyphens; collapse anything not [a-z0-9-]
        # into hyphens; strip leading/trailing hyphens; collapse runs.
        s = re.sub(r"[_\s]+", "-", s)
        s = re.sub(r"[^a-z0-9./-]+", "", s)
        s = s.replace(".", "-")  # `instantly.ai` → `instantly-ai`
        s = re.sub(r"-+", "-", s).strip("-")
        return s

    # 1. owner-prefix handling FIRST (highest signal): a slug with `/` is
    # almost always GitHub owner/repo and the canonical doc is owner-prefixed
    # only when needed for disambiguation (per refresh-protocol D1 rule).
    # We try owner-prefixed first, then the bare repo as fallback.
    if "/" in raw:
        owner, _, repo = raw.partition("/")
        candidates.append(_norm(f"{owner}-{repo}"))
        candidates.append(_norm(f"{owner}-{repo.replace('_', '-')}"))
        candidates.append(_norm(repo))
        candidates.append(_norm(repo.replace("_", "-")))

    # 2. lowercase + underscore→hyphen verbatim
    candidates.append(_norm(raw))

    # 3. decorative suffix strip (`OpenBB MCP` → `openbb`)
    stripped = re.sub(
        r"\s*(MCP server|MCP|server|directory|registry)\s*$",
        "",
        raw,
        flags=re.IGNORECASE,
    )
    if stripped and stripped != raw:
        candidates.append(_norm(stripped))
        # Plus the stripped form with `-mcp` appended back (`OpenBB MCP` →
        # `openbb-mcp` matches `openbb-mcp.md`).
        candidates.append(_norm(stripped) + "-mcp")

    # 4. brand-tail dropping anywhere in the slug, not just trailing.
    # `Instantly.ai MCP` → norm `instantly-ai-mcp` → drop `-ai-` → `instantly-mcp`.
    base = _norm(raw)
    for brand in ("ai", "com", "io", "app"):
        # internal
        cleaned = re.sub(rf"-{brand}-", "-", base)
        if cleaned != base:
            candidates.append(cleaned)
        # trailing
        cleaned = re.sub(rf"-{brand}$", "", base)
        if cleaned != base:
            candidates.append(cleaned)

    # Dedup preserving order
    seen = set()
    out: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _resolve_slug(raw: str) -> tuple[Optional[str], Optional[Path]]:
    """
    Resolve a CHANGELOG slug to (canonical_filename_stem, full_path).
    canonical_filename_stem is the file basename without `.md`.
    """
    if not TOOLS_DOC_DIR.is_dir():
        return None, None

    # Build a quick stem index. We accept both `name.md` and `name.auto.md`
    # → prefer the non-auto core doc.
    stems: dict[str, Path] = {}
    for p in TOOLS_DOC_DIR.glob("*.md"):
        stem = p.stem
        if stem.endswith(".auto"):
            stem = stem[: -len(".auto")]
            # don't overwrite a non-auto entry already present
            stems.setdefault(stem, p)
        else:
            stems[stem] = p

    for cand in _slugify_candidates(raw):
        if cand in stems:
            return cand, stems[cand]

    # Last-resort fuzzy. We require the stem to CONTAIN a candidate (not the
    # reverse — `polygon` ⊂ `polygon-io-mcp-polygon` would otherwise match
    # `polygon.md` to a slashed slug that explicitly named a different repo).
    # Also require the candidate length ≥ 6 chars so we don't false-match on
    # tiny tokens like `mcp`, `ai`.
    raw_norms = _slugify_candidates(raw)
    best: Optional[tuple[str, Path, int]] = None  # (stem, path, score)
    for stem, path in stems.items():
        for cand in raw_norms:
            if not cand or len(cand) < 6:
                continue
            if cand in stem:
                # prefer the closest-length match
                score = abs(len(stem) - len(cand))
                if best is None or score < best[2]:
                    best = (stem, path, score)
    if best is not None:
        return best[0], best[1]

    return None, None


# --------------------------------------------------------------------------- #
# Tool doc field extraction                                                   #
# --------------------------------------------------------------------------- #

# Bullet label form is `**Label:**` — colon goes BEFORE the closing `**`.
# We absorb the bold close marker after the colon so the captured value
# starts with the human-meaningful text, not stray asterisks.
_DOMAIN_RE = re.compile(
    r"^\s*[-*]?\s*\**\s*Domain\(s\)\s*\**:\s*\**\s*(?P<val>[^\n]+)",
    re.IGNORECASE | re.MULTILINE,
)
# Value side stops at the next inline separator: `·`, `|`, or ` - ` (space-
# hyphen-space, the alternate separator some docs use), or newline. The
# ` - ` separator must NOT eat a hyphen mid-word like `bot-token`, so we
# require the surrounding spaces in the negation class via a non-bracket
# stop set.
_ROUTE_RE = re.compile(
    r"\**\s*Barrier route\s*\**:\s*\**\s*(?P<val>.+?)(?=\s+[-·|]\s+\**|\n|$)",
    re.IGNORECASE,
)
_TIER_RE = re.compile(
    r"\**\s*Source tier\s*\**:\s*\**\s*(?P<val>.+?)(?=\s+[-·|]\s+\**|\n|$)",
    re.IGNORECASE,
)
_COST_RE = re.compile(
    r"\**\s*Cost:?\s*\**:?\s*\**\s*(?P<val>[^\n]+)",
    re.IGNORECASE,
)

# GitHub repo URL — first occurrence
_GH_URL_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_./-]+")

# Other plausible repo URL (gitlab, codeberg etc.) — fallback
_GENERIC_REPO_RE = re.compile(r"https?://(?:gitlab|codeberg|bitbucket|sourcehut)\.[^\s)\]]+")

# Signup / dashboard URL hints inside the Auth section
_DASHBOARD_HINT_RE = re.compile(
    r"https?://[^\s)\]>]+(?:dashboard|signup|sign-up|developers?|console|portal|app|account)[^\s)\]>]*",
    re.IGNORECASE,
)


def _section(text: str, heading_words: tuple[str, ...]) -> Optional[str]:
    """
    Extract a `## <heading>` section body from a tool doc. Stops at the next
    `## ` heading or EOF. Case-insensitive header match.
    """
    pattern = re.compile(
        r"^##\s+(?P<h>[^\n]+)$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        h = m.group("h").lower()
        if any(w.lower() in h for w in heading_words):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end]
    return None


def _strip_md(s: Optional[str]) -> Optional[str]:
    """Strip stray markdown bold/code markers and trailing separators from a
    captured-bullet value."""
    if s is None:
        return None
    out = s.strip()
    # leading/trailing `**`
    out = re.sub(r"^\*+|\*+$", "", out).strip()
    # trailing `·` or `|` separator chunks that survived the inline split
    out = out.rstrip("·|").strip()
    # leading `:` if any (from a malformed match)
    out = out.lstrip(":").strip()
    return out or None


def _route_canonicalize(raw: str) -> Optional[str]:
    """
    Convert a route blob like '③ self-host scrape' into the canonical short
    symbol/digit. We keep a string (since the doctrine uses both digits and
    circled numerals).
    """
    raw = raw.strip().strip("·|")
    if not raw:
        return None
    # Look for first ①②③④⑤ or digit 1-9
    m = re.search(r"[①-⑨0-9]", raw)
    if m:
        ch = m.group(0)
        mapping = {"①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
                   "⑥": "6", "⑦": "7", "⑧": "8", "⑨": "9"}
        return mapping.get(ch, ch)
    # else surface a trimmed short form
    return raw.split()[0]


def _infer_transport(install_text: Optional[str], full_text: str) -> Optional[str]:
    """
    Heuristic transport classification based on install/full doc language.
    Returns one of: 'uvx', 'npx', 'pip', 'docker', 'http', 'stdio',
    'self-host', 'browser', or None.
    """
    blob = (install_text or "") + "\n" + full_text
    blob_l = blob.lower()

    # Order matters: more specific wins.
    if re.search(r"\buvx\b", blob_l):
        return "uvx"
    if re.search(r"\bnpx\b", blob_l):
        return "npx"
    if re.search(r"\bdocker\b", blob_l):
        return "docker"
    if re.search(r"\bpip install\b", blob_l):
        return "pip"
    if "mcp.instantly.ai" in blob_l or "hosted http" in blob_l \
       or re.search(r"\bhosted mcp\b", blob_l) or "mcp.apify.com" in blob_l \
       or "http://localhost" in blob_l or "https://mcp." in blob_l:
        return "http"
    if re.search(r"\bstdio\b", blob_l):
        return "stdio"
    if "self-host" in blob_l or "self host" in blob_l:
        return "self-host"
    if "browser only" in blob_l or "browse the readme" in blob_l \
       or "directory page" in blob_l or "no install" in blob_l:
        return "browser"
    if "rest" in blob_l and "http" in blob_l:
        return "http"
    return None


def _extract_env_vars(auth_text: Optional[str]) -> list[str]:
    """
    Pull SCREAMING_SNAKE env var names from the Auth section. We only accept
    names that look like API keys / tokens (uppercase + underscore, ≥2 segments
    or ≥6 chars, contain TOKEN/KEY/SECRET/PASS).
    """
    if not auth_text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"\b([A-Z][A-Z0-9_]{4,})\b", auth_text):
        name = m.group(1)
        if name in seen:
            continue
        if any(k in name for k in ("TOKEN", "KEY", "SECRET", "PASS", "API")):
            seen.add(name)
            found.append(name)
    return found


def _extract_install_cmd(install_text: Optional[str], repo_url: Optional[str]) -> str:
    """
    Best-effort first concrete install command. We look for:
      - first fenced code block content
      - else first inline-backtick command line
      - else fall back to '(see <repo>)'
    """
    if install_text:
        # First fenced code block.
        code = re.search(r"```(?:\w+)?\n(.+?)\n```", install_text, re.DOTALL)
        if code:
            first_line = code.group(1).strip().splitlines()[0].strip()
            if first_line and not first_line.startswith("#"):
                return first_line
            # else if first line is comment, look for second
            for line in code.group(1).splitlines()[1:]:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line

        # First inline backtick command (loosely: any backticked string with
        # a command-looking head).
        for m in re.finditer(r"`([^`]+)`", install_text):
            cand = m.group(1).strip()
            if re.match(r"^(uvx|npx|pip|git|docker|claude|gh|cargo|brew|go|/)", cand):
                return cand

    if repo_url:
        return f"(see {repo_url})"
    return "(see tool doc)"


def _extract_signup_url(auth_text: Optional[str]) -> Optional[str]:
    if not auth_text:
        return None
    m = _DASHBOARD_HINT_RE.search(auth_text)
    if m:
        # trim trailing punctuation
        return m.group(0).rstrip(".,);")
    return None


def _has_friction_signal(auth_text: Optional[str], full_text: str) -> bool:
    """
    Heuristic — returns True if doc mentions captcha, oauth, manual approval,
    phone/sms verify, or other 'human-in-loop' onboarding friction. Used to
    flip auto_configurable_hint OFF.

    We word-boundary-anchor the triggers and explicitly veto negated phrases
    like "no oauth", "no key", "without oauth" so a doc that says "no OAuth
    needed" doesn't get flagged.
    """
    blob = (auth_text or "") + "\n" + full_text
    blob_l = blob.lower()
    triggers = [
        r"\bcaptcha\b",
        r"\boauth\b",
        r"\bphone verification\b",
        r"\bsms verification\b",
        r"\bmanual approval\b",
        r"\bkyc\b",
        r"\bcredit card\b",
        r"\bcard required\b",
        r"\bbilling required\b",
        r"\bcard on file\b",
        r"\btwo-factor\b",
        r"\b2fa\b",
        r"\btos\s*/\s*ban risk\b",
        r"\bban risk\b",
        r"\bself-bot\b",
        r"\buser session\b",
    ]
    # Negation veto — phrases that explicitly say a friction layer is absent.
    neg_re = re.compile(
        r"\b(?:no|without|zero|don'?t need(?:s)?|not required)\s+(?:\w+\s+)?"
        r"(?:oauth|captcha|key|account|login|signup|sign-up|card)\b",
        re.IGNORECASE,
    )
    for trig in triggers:
        if re.search(trig, blob_l):
            # If this is the negated form, ignore. We do a quick window scan:
            # take ±60 chars around the trigger hit and check for negation.
            m = re.search(trig, blob_l)
            start = max(0, m.start() - 60)
            end = min(len(blob_l), m.end() + 60)
            window = blob_l[start:end]
            if neg_re.search(window):
                continue
            return True
    return False


def _extract_tier(text: str) -> Optional[str]:
    # Source tier line first
    m = _TIER_RE.search(text)
    if m:
        return m.group("val").strip().strip("·|*").strip()
    # Else first explicit Cost: bullet
    m = _COST_RE.search(text)
    if m:
        return m.group("val").strip().strip("·|*").strip()
    return None


def _summarize_tool_doc(path: Path) -> dict:
    """
    Read a tool doc and pull the sidecar-relevant fields. Missing fields
    return None / [] — we never raise on a malformed doc.
    """
    text = path.read_text(encoding="utf-8-sig")

    # Top-of-file bullet block — most fields live in the first ~10 bullets.
    head = text[:2000]  # bullets are always near the top

    domain = None
    m = _DOMAIN_RE.search(head)
    if m:
        domain = _strip_md(m.group("val"))

    route_raw = None
    m = _ROUTE_RE.search(head)
    if m:
        route_raw = m.group("val")
    route = _route_canonicalize(_strip_md(route_raw) or "") if route_raw else None

    tier = _strip_md(_extract_tier(head))

    install_section = _section(text, ("Install",))
    auth_section = _section(text, ("Auth",))

    transport = _infer_transport(install_section, text)

    # repo_url: prefer github first, else generic, else None
    repo_url = None
    m = _GH_URL_RE.search(text)
    if m:
        repo_url = m.group(0).rstrip(".,);")
    else:
        m = _GENERIC_REPO_RE.search(text)
        if m:
            repo_url = m.group(0).rstrip(".,);")

    signup_url = _extract_signup_url(auth_section)
    env_vars = _extract_env_vars(auth_section)
    install_cmd = _extract_install_cmd(install_section, repo_url)
    friction = _has_friction_signal(auth_section, text)

    auto_configurable = (not env_vars) and (signup_url is None) and (not friction)

    return {
        "domain": domain,
        "route": route,
        "tier": tier,
        "transport_hint": transport,
        "repo_url": repo_url,
        "signup_url": signup_url,
        "env_vars": env_vars,
        "install_cmd": install_cmd,
        "auto_configurable_hint": auto_configurable,
    }


def _build_entry(raw_slug: str) -> tuple[dict, Optional[str]]:
    """
    Build a sidecar entry for one slug. Returns (entry, unresolved_raw_slug).
    `unresolved_raw_slug` is None on success, or the raw slug when no doc match.

    On resolution failure, the entry still carries the raw slug + nulls so
    the bridge can decide what to do.
    """
    stem, path = _resolve_slug(raw_slug)
    if path is None:
        return (
            {
                "slug": raw_slug,
                "domain": None,
                "route": None,
                "tier": None,
                "transport_hint": None,
                "repo_url": None,
                "signup_url": None,
                "env_vars": [],
                "install_cmd": None,
                "auto_configurable_hint": False,
                "doc_path": None,
            },
            raw_slug,
        )

    summary = _summarize_tool_doc(path)
    entry = {"slug": stem}
    entry.update(summary)
    # Record relative doc path for traceability (POSIX-style separators).
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = str(path)
    entry["doc_path"] = rel
    return entry, None


# --------------------------------------------------------------------------- #
# Top-level orchestration                                                     #
# --------------------------------------------------------------------------- #

def _build_sidecar(version: str) -> tuple[dict, list[str]]:
    """
    Parse CHANGELOG entry for `version`, resolve each slug, and assemble
    the sidecar payload. Returns (payload, unresolved_raw_slugs).
    Raises FileNotFoundError if CHANGELOG missing; ValueError if version
    not found.
    """
    if not CHANGELOG_PATH.exists():
        raise FileNotFoundError(f"CHANGELOG not found at {CHANGELOG_PATH}")

    text = _read_changelog()
    found = _find_entry(text, version)
    if found is None:
        raise ValueError(f"Version {version!r} not found in CHANGELOG.md")
    body, sweep_date, prev_version = found

    adds_raw = _extract_adds_slugs(body)
    replaces_raw = _extract_replaces(body)

    unresolved: list[str] = []

    adds: list[dict] = []
    for raw in adds_raw:
        entry, miss = _build_entry(raw)
        adds.append(entry)
        if miss is not None:
            unresolved.append(miss)

    replaces: list[dict] = []
    for old_raw, new_raw in replaces_raw:
        old_entry, miss_old = _build_entry(old_raw)
        new_entry, miss_new = _build_entry(new_raw)
        replaces.append({"old": old_entry, "new": new_entry})
        if miss_old is not None:
            unresolved.append(miss_old)
        if miss_new is not None:
            unresolved.append(miss_new)

    payload = {
        "skill_version": version,
        "sweep_date": sweep_date,
        "previous_version": prev_version,
        "adds": adds,
        "replaces": replaces,
        "unresolved": unresolved,
    }
    return payload, unresolved


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def _default_out(version: str) -> Path:
    return METRICS_DIR / f"sweep-{version}.json"


def main(argv: Optional[list[str]] = None) -> int:
    _reconfigure_stdout_utf8()

    parser = argparse.ArgumentParser(
        description=(
            "Generate metrics/sweep-<version>.json from the matching CHANGELOG "
            "entry + per-tool reference docs."
        )
    )
    parser.add_argument(
        "--version", required=True,
        help="Skill version to parse (e.g. 0.20.0). Must exist in CHANGELOG.md.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output path (default: metrics/sweep-<version>.json).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse + print summary but do not write the JSON file.",
    )
    args = parser.parse_args(argv)

    try:
        payload, unresolved = _build_sidecar(args.version)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    n_adds = len(payload["adds"])
    n_replaces = len(payload["replaces"])
    n_unresolved = len(unresolved)

    # Exit 2 only when there's something to emit but NOTHING resolved. If the
    # CHANGELOG entry simply has no Adds/Replaces (e.g. a pure refactor
    # release), that's not a failure — just an empty sidecar.
    total_slug_attempts = n_adds + 2 * n_replaces
    if total_slug_attempts > 0 and n_unresolved == total_slug_attempts:
        print(
            f"ERROR: all {n_unresolved} detected slug(s) unresolved for "
            f"version {args.version}; refusing to emit sidecar.",
            file=sys.stderr,
        )
        return 2

    out_path = Path(args.out) if args.out else _default_out(args.version)

    if args.dry_run:
        # Print the payload (truncated for readability) to stdout for inspection.
        preview = json.dumps(payload, indent=2, ensure_ascii=False)
        # Cap preview size so we don't flood the terminal on big sidecars.
        if len(preview) > 8000:
            preview = preview[:8000] + "\n  ... [truncated]"
        print(preview)
        print(
            f"\n[dry-run] Would write {n_adds} adds + {n_replaces} replaces -> "
            f"{out_path.as_posix()}. Unresolved: {n_unresolved}"
        )
        return 0

    # Real write — ensure metrics/ exists, then atomic write.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out_path.write_text(serialized, encoding="utf-8")
    print(
        f"Wrote {n_adds} adds + {n_replaces} replaces -> {out_path.as_posix()}. "
        f"Unresolved: {n_unresolved}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
