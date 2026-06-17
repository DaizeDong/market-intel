#!/usr/bin/env python3
"""P5 hard-limit drift check — enforce the seam boundary at PHILOSOPHY.md §P5.

The P5 hard limit (added 2026-06-17 against drift) says: any script under tools/ or
scripts/ may only run during REFRESH (monthly/weekly/manual sweep) — it MUST NOT be
imported/loaded/called from SKILL.md, which is the user-query path. The grep one-liner
spelled out in PHILOSOPHY.md is the canonical check:

    grep -E "(import|load|from|require).*(discover|feedback-bump|l0_verify|
            verify_matrix|workflow_helpers|check_drift|emit_metrics)" SKILL.md

Any hit = P5 violation. This script wraps that grep so the cleanup pass can run it
mechanically. Advisory (never blocks): exit 0 = clean OR SKILL.md not found; exit 1 =
violation. See PHILOSOPHY.md §"P5 hard limit · 接缝硬边界" rule 5: never quietly violated.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_MD = os.path.join(ROOT, "skills", "market-intel", "SKILL.md")

# Match: a context keyword (import/load/from/require) followed by any of the refresh-side
# script basenames. Mirrors the one-liner in PHILOSOPHY.md §P5; case-insensitive belt-and-
# suspenders, though SKILL.md is lowercase by convention.
PATTERN = re.compile(
    r"(import|load|from|require)\b.*?"
    r"(discover|feedback-bump|l0_verify|verify_matrix|workflow_helpers|check_drift|emit_metrics)",
    re.IGNORECASE,
)


def check() -> int:
    if not os.path.exists(SKILL_MD):
        print(f"check_p5_drift: SKILL.md not found at {SKILL_MD} — advisory check skipped")
        return 0
    hits = []
    with open(SKILL_MD, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if PATTERN.search(line):
                hits.append((lineno, line.rstrip()))
    if not hits:
        return 0
    print("P5 VIOLATION: SKILL.md imports/loads a refresh-side script (PHILOSOPHY.md §P5 rule 1):")
    for lineno, line in hits:
        print(f"  SKILL.md:{lineno}: {line}")
    print("Action: revert the import, or explicitly revise PHILOSOPHY.md P5 per its own 'never quietly violated' rule.")
    return 1


if __name__ == "__main__":
    sys.exit(check())
