#!/usr/bin/env python3
"""Fail-closed gate: detect when top-level narrative docs have drifted from canonical sources.

Why this exists
---------------
`release.ps1` bumps `.claude-plugin/plugin.json` and the top of `CHANGELOG.md`, but it does
**not** touch README badges, "## The source matrix (N domains)" headings, or other
hand-written narrative. Over 8 versions (v0.16 → v0.24) the README version badge silently
said 0.16.0 while plugin.json said 0.24.0 — drift discovered manually.

This script enforces drift detection on **derived** fields (machine-checkable → fail-closed)
and **warns** on suspected stale **narrative** fields (human-judgment → exit 2).

CLI
---
  python tools/check_doc_drift.py            # fail-closed check
  python tools/check_doc_drift.py --fix      # auto-bump derived fields, then re-check
  python tools/check_doc_drift.py --json     # machine-readable for CI / release.ps1

Exit codes
----------
  0 = clean (or --fix succeeded)
  1 = any fail-level drift (release must abort)
  2 = only warn-level drift (release proceeds, but caller should print summary)

Constraints: stdlib only; BOM-safe Windows stdout.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Windows stdout: force UTF-8 so badge characters (—, ⭐, ①…) don't crash on
# cp1252 consoles. BOM-safe: we never emit a BOM ourselves.
# ---------------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")  # py3.7+
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Domain shards that are *meta* (discovery surfaces, not research targets).
# Excluded from the domain count badge — the badge counts "research-target
# domains" (15) not all .md files (16).
META_DOMAINS: set[str] = {"mcp-ecosystem"}

# Files glob-excluded from the per-tool how-to count.
TOOL_EXCLUDES: set[str] = {"index.md", "registry.json"}

# Months after which narrative fields turn warn-level stale.
STALE_TRIGGERED_WORK_MONTHS = 12
STALE_PHILOSOPHY_AMENDMENT_MONTHS = 12
STALE_README_NARRATIVE_MONTHS = 6
STALE_README_RELEASES_SINCE_TOUCH = 3

# Bytes-from-section-start to hash for README narrative-stale detection.
README_NARRATIVE_HASH_BYTES = 500

# ---------------------------------------------------------------------------
# Canonical-value readers
# ---------------------------------------------------------------------------

def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def get_canonical_version() -> str:
    """Authoritative version: `.claude-plugin/plugin.json` `version` field."""
    raw = _read_text(os.path.join(ROOT, ".claude-plugin", "plugin.json"))
    data = json.loads(raw)
    return data["version"]


def count_domains() -> int:
    """Number of *research-target* domain shards.

    Excludes META_DOMAINS (e.g. mcp-ecosystem, which is a discovery meta-domain
    that surfaces sources for the other domains and is never the answer to a
    user query). The README badge phrasing — "Source Matrix-N domains" — refers
    to research targets, not meta-domains.
    """
    pattern = os.path.join(ROOT, "skills", "market-intel", "reference", "domains", "*.md")
    files = glob.glob(pattern)
    out = []
    for f in files:
        slug = os.path.splitext(os.path.basename(f))[0]
        if slug in META_DOMAINS:
            continue
        if slug.lower() in {"index", "readme"}:
            continue
        out.append(slug)
    return len(out)


def count_tools() -> int:
    """Number of per-tool how-to docs.

    Excludes `*.auto.md` (machine-generated sidecars), `index.md`, and
    `registry.json`. Matches the convention used by other tools in this repo.
    """
    pattern = os.path.join(ROOT, "skills", "market-intel", "reference", "tools", "*.md")
    files = glob.glob(pattern)
    out = []
    for f in files:
        name = os.path.basename(f)
        if name in TOOL_EXCLUDES:
            continue
        if name.endswith(".auto.md"):
            continue
        out.append(name)
    return len(out)


def get_top_changelog_version() -> tuple[str | None, int | None]:
    """Parse top `## [<version>]` entry from CHANGELOG.md, return (version, 1-based line_no)."""
    path = os.path.join(ROOT, "CHANGELOG.md")
    if not os.path.exists(path):
        return None, None
    pat = re.compile(r"^##\s*\[([^\]]+)\]")
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            m = pat.match(line)
            if m:
                return m.group(1).strip(), i
    return None, None


# ---------------------------------------------------------------------------
# Derived-field readers (with line numbers for actionable diagnostics)
# ---------------------------------------------------------------------------

def _find_line(path: str, regex: re.Pattern[str]) -> tuple[str | None, int | None, str | None]:
    """Find first regex match in file; return (group1, 1-based line_no, full_line)."""
    if not os.path.exists(path):
        return None, None, None
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            m = regex.search(line)
            if m:
                return m.group(1), i, line.rstrip("\n")
    return None, None, None


def get_readme_version_badge(readme_path: str) -> tuple[str | None, int | None]:
    """Extract version from shields.io Version badge.

    Matches the URL fragment: `version-<x.y.z>-purple` (the dash-separated label
    syntax shields.io uses). Tolerates the surrounding markdown.
    """
    pat = re.compile(r"img\.shields\.io/badge/version-([0-9][^-\s)]*)-")
    v, ln, _ = _find_line(readme_path, pat)
    return v, ln


def get_readme_domain_badge(readme_path: str) -> tuple[int | None, int | None]:
    """Extract N from the `Source Matrix-N domains` shield URL."""
    # shields.io uses `--` to escape literal dashes in labels, but the label
    # here is just "Source Matrix" → "Source%20Matrix-N%20domains". Match
    # the dash that separates label from value.
    pat = re.compile(r"badge/Source%20Matrix-(\d+)%20domains")
    v, ln, _ = _find_line(readme_path, pat)
    if v is None:
        return None, None
    return int(v), ln


def get_readme_section_domain_count(readme_path: str) -> tuple[int | None, int | None]:
    """Extract N from `## The source matrix (N domains)` (EN) or `## 源矩阵（N 个方向）` (CN)."""
    if not os.path.exists(readme_path):
        return None, None
    # EN: "## The source matrix (15 domains)"
    en = re.compile(r"^##\s+The source matrix\s*\((\d+)\s+domains?\)", re.IGNORECASE)
    # CN: "## 源矩阵（15 个方向）" — full-width parens
    cn = re.compile(r"^##\s+源矩阵[（(](\d+)\s*个方向[)）]")
    with open(readme_path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            m = en.match(line) or cn.match(line)
            if m:
                return int(m.group(1)), i
    return None, None


# ---------------------------------------------------------------------------
# Drift checks
# ---------------------------------------------------------------------------

def _drift(
    severity: str,
    field: str,
    expected: Any,
    found: Any,
    location: str,
    auto_fixable: bool = False,
    hint: str | None = None,
) -> dict[str, Any]:
    d = {
        "severity": severity,
        "field": field,
        "expected": expected,
        "found": found,
        "location": location,
        "auto_fixable": auto_fixable,
    }
    if hint:
        d["hint"] = hint
    return d


def check_derived() -> list[dict[str, Any]]:
    """Fail-level drift on machine-checkable derived fields."""
    drifts: list[dict[str, Any]] = []
    canonical_version = get_canonical_version()
    n_domains = count_domains()

    # ---- CHANGELOG top entry must match plugin.json version
    cl_version, cl_line = get_top_changelog_version()
    if cl_version is None:
        drifts.append(_drift("fail", "CHANGELOG top entry", canonical_version, "<missing>",
                             "CHANGELOG.md", auto_fixable=False,
                             hint="Add `## [<version>] - YYYY-MM-DD` entry at the top."))
    elif cl_version != canonical_version:
        drifts.append(_drift("fail", "CHANGELOG top entry version", canonical_version, cl_version,
                             f"CHANGELOG.md:{cl_line}", auto_fixable=False,
                             hint="Edit the changelog entry manually — auto-fix would clobber the date/body."))

    # ---- READMEs: version badge + domain badge + section heading
    for readme_name in ("README.md", "README_CN.md"):
        readme_path = os.path.join(ROOT, readme_name)
        if not os.path.exists(readme_path):
            drifts.append(_drift("fail", f"{readme_name} present", "exists", "<missing>",
                                 readme_name, auto_fixable=False))
            continue

        v, vln = get_readme_version_badge(readme_path)
        if v is None:
            drifts.append(_drift("fail", f"{readme_name} version badge", canonical_version, "<not found>",
                                 readme_name, auto_fixable=False,
                                 hint="Expected a shields.io badge URL containing `version-<x.y.z>-purple`."))
        elif v != canonical_version:
            drifts.append(_drift("fail", f"{readme_name} version badge", canonical_version, v,
                                 f"{readme_name}:{vln}", auto_fixable=True))

        n, nln = get_readme_domain_badge(readme_path)
        if n is None:
            drifts.append(_drift("fail", f"{readme_name} domain count badge", n_domains, "<not found>",
                                 readme_name, auto_fixable=False,
                                 hint="Expected a shields.io badge URL containing `Source%20Matrix-<N>%20domains`."))
        elif n != n_domains:
            drifts.append(_drift("fail", f"{readme_name} domain count badge", n_domains, n,
                                 f"{readme_name}:{nln}", auto_fixable=True))

        sn, snln = get_readme_section_domain_count(readme_path)
        if sn is None:
            # Section heading is not strictly required, but if it's present in
            # one README it should be present in the other. We only fail-flag
            # this as `warn` (next pass) if it's missing entirely.
            pass
        elif sn != n_domains:
            drifts.append(_drift("fail", f"{readme_name} section heading domain count", n_domains, sn,
                                 f"{readme_name}:{snln}", auto_fixable=True))

    return drifts


def _months_between(then: date, now: date) -> int:
    return (now.year - then.year) * 12 + (now.month - then.month)


def check_warnings() -> list[dict[str, Any]]:
    """Warn-level drift on narrative fields (human-judgment-required)."""
    drifts: list[dict[str, Any]] = []
    today = date.today()

    # ---- ROADMAP: triggered-work staleness
    roadmap_path = os.path.join(ROOT, "ROADMAP.md")
    if os.path.exists(roadmap_path):
        text = _read_text(roadmap_path)
        # Find the "## Triggered work" section and count unchecked items inside it.
        m = re.search(r"^##\s+Triggered work.*?$", text, flags=re.MULTILINE)
        if m:
            sec_start = m.end()
            next_h = re.search(r"^##\s+", text[sec_start:], flags=re.MULTILINE)
            sec_end = sec_start + next_h.start() if next_h else len(text)
            section = text[sec_start:sec_end]
            unchecked = len(re.findall(r"^\s*-\s*\[\s\]", section, flags=re.MULTILINE))
            # If everything is checked, the section is functionally drained — flag for review.
            if unchecked == 0:
                drifts.append(_drift(
                    "warn", "ROADMAP triggered work", "at least 1 unchecked OR section refresh",
                    "all items checked", "ROADMAP.md",
                    hint="No triggered items pending — consider whether new conditions should be added or section archived.",
                ))

    # ---- PHILOSOPHY: latest amendment date staleness
    phil_path = os.path.join(ROOT, "PHILOSOPHY.md")
    if os.path.exists(phil_path):
        text = _read_text(phil_path)
        # Match patterns like "(2026-06-17 added against drift)" or "added 2026-06-17"
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})\s*added", text)
        dates += re.findall(r"added\s*(\d{4}-\d{2}-\d{2})", text)
        if dates:
            latest = max(datetime.strptime(d, "%Y-%m-%d").date() for d in dates)
            months = _months_between(latest, today)
            if months > STALE_PHILOSOPHY_AMENDMENT_MONTHS:
                drifts.append(_drift(
                    "warn", "PHILOSOPHY amendment freshness",
                    f"<={STALE_PHILOSOPHY_AMENDMENT_MONTHS} months old",
                    f"{months} months ({latest.isoformat()})",
                    "PHILOSOPHY.md",
                    hint="Latest amendment is stale — consider whether the philosophy still reflects practice.",
                ))

    # ---- README narrative-stale: hash unchanged but ≥3 releases since
    readme_path = os.path.join(ROOT, "README.md")
    changelog_path = os.path.join(ROOT, "CHANGELOG.md")
    if os.path.exists(readme_path) and os.path.exists(changelog_path):
        narrative = _extract_narrative_hash(readme_path)
        if narrative is not None:
            cache_path = os.path.join(ROOT, "metrics", "doc-drift-cache.json")
            cache = _load_cache(cache_path)
            entry = cache.get("readme_narrative", {})
            release_count = _count_changelog_entries(changelog_path)
            now_iso = today.isoformat()
            if entry.get("hash") != narrative:
                # Hash changed → reset tracker.
                cache["readme_narrative"] = {
                    "hash": narrative,
                    "first_seen": now_iso,
                    "release_count_at_first_seen": release_count,
                }
                _save_cache(cache_path, cache)
            else:
                first_seen = datetime.strptime(entry["first_seen"], "%Y-%m-%d").date()
                months = _months_between(first_seen, today)
                releases_since = release_count - entry.get("release_count_at_first_seen", release_count)
                if months > STALE_README_NARRATIVE_MONTHS and releases_since >= STALE_README_RELEASES_SINCE_TOUCH:
                    drifts.append(_drift(
                        "warn", "README narrative freshness",
                        "touched in last 6 months OR <3 releases since",
                        f"{months} months, {releases_since} releases since last touch",
                        "README.md",
                        hint="README narrative may be stale — multiple releases since last touch.",
                    ))

    # ---- README_CN structural parity with README
    readme_path = os.path.join(ROOT, "README.md")
    readme_cn_path = os.path.join(ROOT, "README_CN.md")
    if os.path.exists(readme_path) and os.path.exists(readme_cn_path):
        en_h = _count_h2(readme_path)
        cn_h = _count_h2(readme_cn_path)
        if en_h != cn_h:
            drifts.append(_drift(
                "warn", "README/README_CN structural parity",
                f"{en_h} ## headings in EN", f"{cn_h} ## headings in CN",
                "README_CN.md",
                hint="CN may be missing or have extra sections relative to EN.",
            ))

    return drifts


def _extract_narrative_hash(readme_path: str) -> str | None:
    """Hash the first ~500 chars after the first relevant intro section heading.

    We look for either `## What it is` / `## What is this` / `## What it does`
    (the project's framing varies). Falls back to first 500 chars of body.
    """
    text = _read_text(readme_path)
    # Skip past the H1 title.
    body = re.sub(r"^#\s+.*?\n", "", text, count=1)
    m = re.search(r"^##\s+What\s+(it\s+is|is\s+this|it\s+does).*?$", body, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        start = m.end()
    else:
        start = 0
    chunk = body[start:start + README_NARRATIVE_HASH_BYTES]
    if not chunk.strip():
        return None
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()


def _count_changelog_entries(changelog_path: str) -> int:
    text = _read_text(changelog_path)
    return len(re.findall(r"^##\s*\[", text, flags=re.MULTILINE))


def _count_h2(path: str) -> int:
    text = _read_text(path)
    return len(re.findall(r"^##\s+", text, flags=re.MULTILINE))


def _load_cache(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def check_drift() -> list[dict[str, Any]]:
    return check_derived() + check_warnings()


# ---------------------------------------------------------------------------
# --fix support
# ---------------------------------------------------------------------------

def fix_drift(drifts: list[dict[str, Any]]) -> list[str]:
    """Apply regex-replace fixes for auto_fixable=True derived drifts.

    Returns a list of human-readable fix-log lines (one per applied fix).
    Only touches READMEs; never the canonical sources, never narrative.
    """
    applied: list[str] = []
    canonical_version = get_canonical_version()
    n_domains = count_domains()

    for d in drifts:
        if not d.get("auto_fixable"):
            continue
        if d["severity"] != "fail":
            continue
        loc = d["location"].split(":")[0]
        if loc not in ("README.md", "README_CN.md"):
            continue
        path = os.path.join(ROOT, loc)
        text = _read_text(path)
        new_text = text

        field = d["field"]
        if field.endswith("version badge"):
            new_text = re.sub(
                r"(img\.shields\.io/badge/version-)([0-9][^-\s)]*)(-)",
                lambda m: m.group(1) + canonical_version + m.group(3),
                new_text,
                count=1,
            )
        elif field.endswith("domain count badge"):
            new_text = re.sub(
                r"(badge/Source%20Matrix-)(\d+)(%20domains)",
                lambda m: m.group(1) + str(n_domains) + m.group(3),
                new_text,
                count=1,
            )
        elif field.endswith("section heading domain count"):
            # EN section heading
            new_text = re.sub(
                r"(^##\s+The source matrix\s*\()(\d+)(\s+domains?\))",
                lambda m: m.group(1) + str(n_domains) + m.group(3),
                new_text,
                count=1,
                flags=re.MULTILINE | re.IGNORECASE,
            )
            # CN section heading
            new_text = re.sub(
                r"(^##\s+源矩阵[（(])(\d+)(\s*个方向[)）])",
                lambda m: m.group(1) + str(n_domains) + m.group(3),
                new_text,
                count=1,
                flags=re.MULTILINE,
            )

        if new_text != text:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            applied.append(f"fixed: {d['location']} {field} {d['found']}->{d['expected']}")

    return applied


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _exit_code(drifts: list[dict[str, Any]]) -> int:
    if any(d["severity"] == "fail" for d in drifts):
        return 1
    if any(d["severity"] == "warn" for d in drifts):
        return 2
    return 0


def _print_human(drifts: list[dict[str, Any]]) -> None:
    if not drifts:
        print("doc-drift: clean")
        return
    fails = [d for d in drifts if d["severity"] == "fail"]
    warns = [d for d in drifts if d["severity"] == "warn"]
    if fails:
        print(f"doc-drift: {len(fails)} FAIL ({len(warns)} warn)")
        for d in fails:
            print(f"  FAIL  {d['location']:32s}  {d['field']}: expected={d['expected']!r} found={d['found']!r}"
                  + (f"  -- {d['hint']}" if d.get("hint") else ""))
    else:
        print(f"doc-drift: clean (fail) / {len(warns)} warn")
    for d in warns:
        print(f"  WARN  {d['location']:32s}  {d['field']}: expected={d['expected']!r} found={d['found']!r}"
              + (f"  -- {d['hint']}" if d.get("hint") else ""))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--fix", action="store_true", help="auto-bump derived fields where possible, then re-check")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON to stdout")
    args = p.parse_args(argv)

    drifts = check_drift()

    if args.fix:
        applied = fix_drift(drifts)
        for line in applied:
            print(line)
        # Re-check after fix.
        drifts = check_drift()

    if args.json:
        out = {
            "canonical": {
                "version": get_canonical_version(),
                "domain_count": count_domains(),
                "tool_count": count_tools(),
            },
            "drifts": drifts,
            "exit_code": _exit_code(drifts),
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        _print_human(drifts)

    return _exit_code(drifts)


if __name__ == "__main__":
    sys.exit(main())
