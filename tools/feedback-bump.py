#!/usr/bin/env python3
"""
feedback-bump.py — Step -1 of refresh-protocol + cleanup auto-bump executor.

This script implements two pieces of the refresh-protocol (skills/market-intel/
reference/refresh-protocol.md):

    1. Step -1 (Procedure full sweep): consume metrics/live-runs.jsonl since the
       last refresh, bucket entries by `outcome`, and emit the structured
       report that drives the rest of the sweep:
         - hot_domains (Discovery budget x2)
         - forced_recheck_slugs
         - auto_bump_slugs
         - top_priority (user_correction != null — highest weight)
         - by_outcome counts
         - price_pressure per domain (for P2 D-PRICE wave detection)

    2. Cleanup pass §8 "Auto-advance ## Last verified": for every slug that
       appears with outcome=verified, advance its
       reference/tools/<slug>.md `## Last verified: YYYY-MM` line to the month
       of the most recent verified run. Truthful "I just used it and it worked"
       is stronger evidence than a scheduled re-check.

When to run:
    Step -1 of EVERY refresh sweep, before Horizon scan.
    Default window: 30 days. For first run / catch-up, pass --since with a
    90-day window per the protocol.

Usage:
    # report-only (default), 30-day window
    python tools/feedback-bump.py

    # 90-day catch-up window, dump JSON
    python tools/feedback-bump.py --since 2026-03-16 --out feedback-report.json

    # actually mutate tool docs (cleanup pass auto-bump)
    python tools/feedback-bump.py --mode bump --since 2026-03-16

Exit codes:
    0 — clean sweep (no hot domains, no P2 trigger)
    1 — hot_domains non-empty (this sweep needs extra attention)
    2 — P2 trigger fires (>=3 distinct D-PRICE domains in window)
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


# --- paths -----------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_RUNS = REPO_ROOT / "skills" / "market-intel" / "metrics" / "live-runs.jsonl"
TOOLS_DIR = REPO_ROOT / "skills" / "market-intel" / "reference" / "tools"

LAST_VERIFIED_RE = re.compile(r"^(## Last verified:\s*)(\d{4}-\d{2})\s*$", re.MULTILINE)


def reconfigure_stdout_utf8() -> None:
    """Make stdout UTF-8 on Windows so unicode in detail fields doesn't blow up."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # py3.7+
    except Exception:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )


# --- jsonl loader ----------------------------------------------------------

def load_live_runs(path: Path, since: str) -> list[dict]:
    """Read live-runs.jsonl, tolerate UTF-8 BOM, and filter by ts >= since.

    Each non-empty line is a JSON object. Malformed lines are skipped with a
    warning to stderr — we never want a bad line to block a sweep.
    """
    if not path.exists():
        print(f"WARN: live-runs.jsonl not found at {path}", file=sys.stderr)
        return []

    entries: list[dict] = []
    # utf-8-sig swallows a BOM if present; plain utf-8 lines pass through unchanged.
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"WARN: skipping malformed line {lineno}: {e}", file=sys.stderr)
                continue
            ts = obj.get("ts", "")
            if ts >= since:
                entries.append(obj)
    return entries


# --- slug extraction -------------------------------------------------------

# Listing the tools dir is the source of truth for valid slugs; cache it.
_TOOL_SLUGS_CACHE: list[str] | None = None


def _known_tool_slugs() -> list[str]:
    """Return all valid tool-doc basenames (without .md) under reference/tools/.

    Includes .core.md variants stripped to bare slug.
    """
    global _TOOL_SLUGS_CACHE
    if _TOOL_SLUGS_CACHE is not None:
        return _TOOL_SLUGS_CACHE
    slugs: list[str] = []
    if TOOLS_DIR.exists():
        for p in TOOLS_DIR.glob("*.md"):
            name = p.stem
            if name.endswith(".core"):
                name = name[: -len(".core")]
            slugs.append(name)
    _TOOL_SLUGS_CACHE = sorted(set(slugs))
    return _TOOL_SLUGS_CACHE


def extract_slug(source: str) -> str | None:
    """Pull a tool slug out of a `source` field.

    `source` is free-form, but writers typically use one of:
        - `shard/<slug>`
        - `d60/<slug>`
        - `tools/<slug>`
        - `<slug>` (bare; matches tools/<slug>.md or tools/<slug>-mcp.md etc.)
        - `<slug>-<qualifier>` (e.g. `buffer-turnstile`, `apollo-onboarding`,
          `ebay-developer-approval`)

    Returns None when no plausible slug could be recovered. Caller should
    surface this list for writer-side correction.
    """
    if not source:
        return None

    s = source.strip()
    # strip recognised path-like prefixes
    for prefix in ("shard/", "d60/", "tools/", "reference/tools/"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break

    # take only the first path segment if any slashes remain
    s = s.split("/")[0].strip()

    if not s:
        return None

    # normalise: lowercase, replace spaces with hyphens
    norm = s.lower().replace(" ", "-")

    known = _known_tool_slugs()
    if not known:
        # No tools dir to match against — return the normalised form best-effort.
        return norm

    # 1) exact match
    if norm in known:
        return norm

    # 2) prefix match — try peeling trailing `-qualifier` segments one at a time
    #    e.g. `apollo-onboarding` -> `apollo`, `buffer-turnstile` -> `buffer`,
    #    `ebay-developer-approval` -> `ebay-developer` -> `ebay`.
    parts = norm.split("-")
    for cut in range(len(parts) - 1, 0, -1):
        candidate = "-".join(parts[:cut])
        if candidate in known:
            return candidate

    # 3) suffix tolerance — `attio` matches `attio-mcp`, `hubspot` -> `hubspot-mcp`,
    #    `ebay` -> `ebay-api`.
    for slug in known:
        if slug.startswith(norm + "-") or slug.startswith(norm + "."):
            return slug

    # 4) substring fallback — unique match wins, ambiguous drops to None
    hits = [slug for slug in known if norm in slug]
    if len(hits) == 1:
        return hits[0]

    return None


# --- bucketing -------------------------------------------------------------

def bucket_entries(entries: list[dict]) -> dict:
    """Bucket entries by outcome and derive the Step -1 sets per protocol table.

    Returns a dict containing all fields the report will emit, plus an
    `unresolved_sources` list (sources we couldn't extract a slug from — useful
    for fixing the writer side).
    """
    by_outcome: Counter[str] = Counter()
    hot_domains: set[str] = set()
    forced_recheck: set[str] = set()
    # auto_bump_slugs is a {slug: latest_ts} dict so we can pick the most
    # recent verified date as the bump target (defensible later).
    auto_bump_slugs: dict[str, str] = {}
    top_priority: list[dict] = []
    open_questions: list[dict] = []
    price_pressure: Counter[str] = Counter()
    unresolved_sources: list[dict] = []

    for e in entries:
        outcome = e.get("outcome") or ""
        domain = e.get("domain") or ""
        source = e.get("source") or ""
        ts = e.get("ts") or ""
        user_correction = e.get("user_correction")

        by_outcome[outcome] += 1

        # user_correction always wins (highest priority signal)
        if user_correction is not None:
            top_priority.append(
                {
                    "ts": ts,
                    "domain": domain,
                    "source": source,
                    "user_correction": user_correction,
                }
            )

        slug = extract_slug(source)
        if slug is None and source and outcome in {"dead", "verified", "price_mismatch"}:
            # only flag unresolved when slug extraction actually matters for this outcome
            unresolved_sources.append({"ts": ts, "source": source, "outcome": outcome})

        if outcome == "dead":
            if domain:
                hot_domains.add(domain)
            if slug:
                forced_recheck.add(slug)
        elif outcome == "barrier_found":
            if domain:
                hot_domains.add(domain)
                price_pressure[domain] += 1
        elif outcome == "coverage_gap":
            if domain:
                hot_domains.add(domain)
            open_questions.append(
                {
                    "ts": ts,
                    "domain": domain,
                    "source": source,
                    "detail": e.get("detail", ""),
                }
            )
        elif outcome == "price_mismatch":
            if slug:
                forced_recheck.add(slug)
        elif outcome == "verified":
            if slug:
                # keep the latest ts for this slug
                prev = auto_bump_slugs.get(slug)
                if prev is None or ts > prev:
                    auto_bump_slugs[slug] = ts

    return {
        "by_outcome": dict(by_outcome),
        "hot_domains": sorted(hot_domains),
        "forced_recheck_slugs": sorted(forced_recheck),
        "auto_bump_slugs": auto_bump_slugs,  # dict {slug: ts}
        "top_priority": top_priority,
        "open_questions": open_questions,
        "price_pressure": dict(price_pressure),
        "unresolved_sources": unresolved_sources,
    }


# --- report ----------------------------------------------------------------

def build_report(buckets: dict, since: str, total: int) -> dict:
    """Assemble the JSON-shaped Step -1 report."""
    return {
        "since": since,
        "total_entries": total,
        "hot_domains": buckets["hot_domains"],
        "forced_recheck_slugs": buckets["forced_recheck_slugs"],
        "auto_bump_slugs": sorted(buckets["auto_bump_slugs"].keys()),
        "auto_bump_detail": buckets["auto_bump_slugs"],  # {slug: ts}
        "top_priority": buckets["top_priority"],
        "open_questions": buckets["open_questions"],
        "by_outcome": buckets["by_outcome"],
        "price_pressure": buckets["price_pressure"],
        "unresolved_sources": buckets["unresolved_sources"],
    }


def print_report(report: dict) -> None:
    """Pretty-print the report to stdout."""
    print("=" * 72)
    print("Step -1 — live-runs feedback report")
    print(f"  Window: since {report['since']}")
    print(f"  Total entries: {report['total_entries']}")
    print("=" * 72)

    print("\nBy outcome:")
    if not report["by_outcome"]:
        print("  (no entries)")
    for k, v in sorted(report["by_outcome"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:20s} {v}")

    print(f"\nHot domains (Discovery budget x2): {len(report['hot_domains'])}")
    for d in report["hot_domains"]:
        print(f"  - {d}")

    print(f"\nForced recheck slugs: {len(report['forced_recheck_slugs'])}")
    for s in report["forced_recheck_slugs"]:
        print(f"  - {s}")

    print(f"\nAuto-bump candidates (verified outcomes): {len(report['auto_bump_slugs'])}")
    for s in report["auto_bump_slugs"]:
        ts = report["auto_bump_detail"].get(s, "?")
        print(f"  - {s} (latest verified ts: {ts})")

    print(f"\nTop priority (user_correction != null): {len(report['top_priority'])}")
    for tp in report["top_priority"]:
        print(f"  - {tp['ts']} {tp['domain']}/{tp['source']} -> {tp['user_correction']!r}")

    print(f"\nPrice pressure per domain (D-PRICE-like barriers): "
          f"{len(report['price_pressure'])}")
    for d, n in sorted(report["price_pressure"].items(), key=lambda kv: -kv[1]):
        print(f"  - {d}: {n}")

    if report["unresolved_sources"]:
        print(f"\nUnresolved source fields (writer-side fix needed): "
              f"{len(report['unresolved_sources'])}")
        for u in report["unresolved_sources"]:
            print(f"  - {u['ts']} [{u['outcome']}] {u['source']!r}")


# --- p2 trigger ------------------------------------------------------------

def check_p2_trigger(price_pressure: dict, since: str) -> bool:
    """Return True if >=3 distinct domains show D-PRICE-like barriers.

    Per refresh-protocol Step -1 table: the 3rd D-PRICE wave in the window is
    the trigger to consider `transport: brokerage` per P2 ROADMAP.
    """
    if sum(1 for n in price_pressure.values() if n >= 1) >= 3:
        print("")
        print(
            "WARNING: P2 trigger active: 3rd D-PRICE wave detected in window "
            f"since {since} — consider transport: brokerage per ROADMAP.md"
        )
        return True
    return False


# --- bump mode -------------------------------------------------------------

def _resolve_doc_path(slug: str) -> Path | None:
    """Find tools/<slug>.md or tools/<slug>.core.md (in that order)."""
    bare = TOOLS_DIR / f"{slug}.md"
    if bare.exists():
        return bare
    core = TOOLS_DIR / f"{slug}.core.md"
    if core.exists():
        return core
    return None


def bump_last_verified(auto_bump: dict[str, str]) -> list[dict]:
    """Advance `## Last verified: YYYY-MM` for each slug to its latest verified ts month.

    Skips a doc when the existing date is already >= the target month (time is
    monotone — never roll backwards). Reads BOM-tolerantly, writes plain UTF-8.

    Returns a list of {slug, path, old, new, status} records.
    """
    results: list[dict] = []
    for slug, ts in sorted(auto_bump.items()):
        target_month = ts[:7]  # YYYY-MM
        doc = _resolve_doc_path(slug)
        if doc is None:
            results.append(
                {"slug": slug, "path": None, "old": None, "new": target_month,
                 "status": "not_found"}
            )
            continue

        text = doc.read_text(encoding="utf-8-sig", errors="replace")
        m = LAST_VERIFIED_RE.search(text)
        if not m:
            results.append(
                {"slug": slug, "path": str(doc), "old": None, "new": target_month,
                 "status": "no_marker"}
            )
            continue

        old_month = m.group(2)
        if old_month >= target_month:
            results.append(
                {"slug": slug, "path": str(doc), "old": old_month, "new": old_month,
                 "status": "already_current"}
            )
            continue

        new_text = LAST_VERIFIED_RE.sub(
            lambda mm, nm=target_month: f"{mm.group(1)}{nm}", text, count=1
        )
        doc.write_text(new_text, encoding="utf-8", newline="")
        results.append(
            {"slug": slug, "path": str(doc), "old": old_month, "new": target_month,
             "status": "bumped"}
        )

    return results


def print_bump_results(results: list[dict]) -> None:
    """Pretty-print the bump table."""
    print("\n" + "=" * 72)
    print("Auto-bump results")
    print("=" * 72)
    if not results:
        print("  (no auto-bump candidates)")
        return
    width = max((len(r["slug"]) for r in results), default=10)
    for r in results:
        old = r["old"] or "----"
        new = r["new"] or "----"
        print(f"  {r['slug']:{width}s}  {old} -> {new}  [{r['status']}]")
    n_bumped = sum(1 for r in results if r["status"] == "bumped")
    print(f"\n  Bumped: {n_bumped}/{len(results)}")


# --- main ------------------------------------------------------------------

def default_since() -> str:
    """30 days ago in YYYY-MM-DD."""
    return (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI definition."""
    p = argparse.ArgumentParser(
        description="Step -1 + cleanup auto-bump for the market-intel refresh sweep.",
    )
    p.add_argument(
        "--since",
        default=default_since(),
        help="YYYY-MM-DD lower bound (inclusive) on ts. Default: 30 days ago.",
    )
    p.add_argument(
        "--mode",
        choices=("report", "bump"),
        default="report",
        help="report (default) just prints; bump modifies tools/<slug>.md.",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Optional path: write the structured report as JSON.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code."""
    reconfigure_stdout_utf8()
    args = parse_args(argv)

    # validate --since format early so a typo doesn't silently match nothing
    try:
        datetime.strptime(args.since, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: --since must be YYYY-MM-DD, got {args.since!r}", file=sys.stderr)
        return 64

    entries = load_live_runs(LIVE_RUNS, args.since)
    buckets = bucket_entries(entries)
    report = build_report(buckets, args.since, len(entries))

    print_report(report)
    p2 = check_p2_trigger(buckets["price_pressure"], args.since)

    if args.mode == "bump":
        results = bump_last_verified(buckets["auto_bump_slugs"])
        print_bump_results(results)
        report["bump_results"] = results

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        print(f"\nReport written: {out_path}")

    # exit-code policy:
    #   2 if P2 trigger fires (highest priority signal)
    #   1 if hot_domains non-empty
    #   0 otherwise
    if p2:
        return 2
    if report["hot_domains"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
