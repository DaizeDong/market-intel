#!/usr/bin/env python3
"""The one property check_all.py has to keep: no checker is missing from it.

check_all.py only removes the "I ran the wrong one" failure if it actually covers everything. The
moment a ninth checker lands and nobody adds it to MANIFEST, this repo is back to having an orphan,
and the entry point is worse than nothing because it looks like coverage. So the coverage claim is
asserted against the directory listing rather than trusted.

  python tools/test_check_all.py
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Same shape the fleet inventory uses. Kept here rather than imported so a change to check_all.py
# cannot quietly change what this test considers a checker.
CHECKER = re.compile(r"(check|verify|guard|gate|budget|boundary)[a-z_0-9]*\.py$", re.I)
SELF = {"check_all.py", "test_check_all.py"}

failures = []


def check(label, cond, detail=""):
    if cond:
        print("  ok    " + label)
    else:
        print("  FAIL  " + label + ("  <- " + detail if detail else ""))
        failures.append(label)


def load():
    spec = importlib.util.spec_from_file_location("check_all", os.path.join(HERE, "check_all.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ca = load()
    on_disk = {f for f in os.listdir(HERE)
               if f.endswith(".py") and CHECKER.search(f)
               and not f.startswith("test_") and f not in SELF}
    registered = set(ca.MANIFEST) | set(ca.EXCLUDED)

    # 1. THE DEFECT THIS FILE EXISTS FOR.
    missing = sorted(on_disk - registered)
    check("every checker in tools/ is registered in MANIFEST or EXCLUDED",
          not missing, "unregistered: " + ", ".join(missing))

    # 2. The mirror: a manifest entry with no file is a broken manifest, and check_all returns 2 for
    #    it at runtime. Catch it here instead, where the message is cheaper to read.
    ghosts = sorted(n for n in ca.MANIFEST if not os.path.isfile(os.path.join(HERE, n)))
    check("every MANIFEST entry exists on disk", not ghosts, "missing files: " + ", ".join(ghosts))

    # 3. An exclusion without a reason is an orphan with extra steps.
    unreasoned = sorted(n for n, why in ca.EXCLUDED.items() if not (why or "").strip())
    check("every EXCLUDED entry carries a written reason", not unreasoned,
          "no reason: " + ", ".join(unreasoned))

    # 4. `required` is the only thing that can turn a red into a pass, so it must be a deliberate,
    #    explained minority rather than the way entries get added.
    not_required = [n for n, (_a, _n, req, _d) in ca.MANIFEST.items() if not req]
    check("at most one checker is marked not-required", len(not_required) <= 1,
          "not required: " + ", ".join(sorted(not_required)))
    for n in not_required:
        desc = ca.MANIFEST[n][3]
        check("not-required %s explains why in its description" % n,
              len(desc) > 40 and ("pre-existing" in desc or "owned" in desc), desc)

    # 5. NEGATIVE CONTROL. A test that cannot fail proves nothing, so prove this one can: pretend a
    #    new checker appeared and confirm the coverage assertion goes red for it.
    fake = "verify_nothing_at_all.py"
    would_fail = fake not in registered and bool(CHECKER.search(fake))
    check("the coverage assertion would reject an unregistered newcomer", would_fail,
          "a new checker named %r would NOT have been caught" % fake)

    print("")
    if failures:
        print("test_check_all: %d FAILED" % len(failures))
        return 1
    print("test_check_all: all cases passed (%d checker(s) on disk, %d registered)"
          % (len(on_disk), len(registered)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
