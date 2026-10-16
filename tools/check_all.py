#!/usr/bin/env python3
"""Run every check this repo has, so that picking the wrong one stops being possible.

WHY THIS EXISTS
---------------
This repo runs eight checkers. Three of them run in the commit hooks (from the local fleet-guards
and fleet-style checkouts), verify_matrix runs in CI, and the rest are wired to nothing else. On 2026-08-29 a change
landed that violated the three-way registry rule, and the check that catches it exists and works;
it just was not the one that got run, because the person running it had to know which of eight
names applied. A checker nobody can reliably select is not much better than a checker nobody wrote.

So this is not a new check. It is the single entry point in front of the ones already here, and it
is deliberately dumb: it holds a manifest, it runs what the manifest says, and it prints one line
per checker with what actually happened.

WHAT IT DOES NOT DO
-------------------
It does not decide policy. A checker's own exit code is its verdict and this passes it through. It
does not aggregate a "score" or downgrade anything to a warning, because a runner that softens its
children's verdicts is how a red becomes a habit. Exit is 1 if any REQUIRED checker failed, 0
otherwise, and every checker's own output is printed in full.

  python tools/check_all.py              # everything except the network-bound ones
  python tools/check_all.py --with-net   # including them (verify_matrix hits the GitHub API)
  python tools/check_all.py --list       # show the manifest and exit
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# name -> (argv after the script, network_bound, required, one-line description)
# `required` False means a failure is reported and does not set the exit code. Use it only for a
# checker whose red is known to be pre-existing and owned elsewhere, and say so in the description,
# because a permanently-not-required checker is an orphan wearing a badge.
MANIFEST = {
    "pii_guard.py":       (["--tree"], False, True,  "no real private data in tracked files"),
    "dash_guard.py":      (["--tree"], False, True,  "no en/em dashes in prose"),
    "data_boundary.py":   ([],         False, True,  "no real-run output can land inside the repo"),
    "check_doc_drift.py": ([],         False, False, "README badges vs plugin.json; 3 pre-existing "
                                                     "badge failures owned by a separate change"),
    "check_drift.py":     ([],         False, True,  "shard and doc cross-references"),
    "check_p5_drift.py":  ([],         False, True,  "SKILL.md must not import refresh-side scripts"),
    "l0_verify.py":       (["--live-selftest"], True, True, "L0 install-guide mechanics with live source probes"),
    "verify_matrix.py":   ([],         True,  True,  "registry, index and docs three-way, plus live "
                                                     "star claims (GitHub API)"),
}

def _kit_tool(key, name):
    """A checker in the local kit checkout named by `git config <key>`; unset reads as MISSING."""
    kit = subprocess.run(["git", "config", "--get", key], cwd=REPO, capture_output=True,
                         text=True).stdout.strip()
    return os.path.join(kit, "tools", name) if kit else "<git config %s is unset>" % key


CHECKER_PATHS = {
    "pii_guard.py": _kit_tool("fleet.guards", "pii_guard.py"),
    "data_boundary.py": _kit_tool("fleet.guards", "data_boundary.py"),
    "dash_guard.py": _kit_tool("fleet.style", "dash_guard.py"),
}


def checker_path(name):
    return CHECKER_PATHS.get(name, os.path.join(HERE, name))

# name -> reason. A checker here is deliberately not run by this entry point.
EXCLUDED = {
    "load_budget.py": "measures context cost and prints a number; it has no pass/fail to add here",
}


def run(name, argv):
    path = checker_path(name)
    if not os.path.isfile(path):
        # A manifest entry whose file is gone is a broken manifest, not a pass. Never infer
        # "nothing to run" from a missing file.
        print("check_all: MISSING %s (listed in MANIFEST but not on disk)" % name, file=sys.stderr)
        return 2
    print("\n" + "=" * 78)
    print("== %s %s" % (name, " ".join(argv)))
    print("=" * 78)
    command = [sys.executable, "-X", "utf8", "-B"]
    p = subprocess.run(command + [path] + argv, cwd=REPO,
                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    return p.returncode


def main():
    ap = argparse.ArgumentParser(description="run every check this repo has")
    ap.add_argument("--with-net", action="store_true",
                    help="also run the checkers that call out to the network")
    ap.add_argument("--list", action="store_true", help="print the manifest and exit")
    a = ap.parse_args()

    if a.list:
        print("%-22s %-4s %-9s %s" % ("checker", "net", "required", "what it checks"))
        for n, (argv, net, req, desc) in sorted(MANIFEST.items()):
            print("%-22s %-4s %-9s %s" % (n, "yes" if net else "", "yes" if req else "no", desc))
        for n, why in sorted(EXCLUDED.items()):
            print("%-22s %-4s %-9s EXCLUDED: %s" % (n, "", "", why))
        return 0

    results, skipped = [], []
    for name, (argv, net, req, _desc) in sorted(MANIFEST.items()):
        if net and not a.with_net:
            skipped.append(name)
            continue
        results.append((name, run(name, argv), req))

    print("\n" + "=" * 78)
    failed_required = [n for n, rc, req in results if rc != 0 and req]
    failed_other = [n for n, rc, req in results if rc != 0 and not req]
    for n, rc, req in results:
        print("  %-22s rc=%-3d %s" % (n, rc, "" if rc == 0 else ("FAIL" if req else "fail (not required)")))
    if skipped:
        # Say what was not run. A summary that silently omits the network checks reads exactly like
        # one where they passed.
        print("  NOT RUN (needs --with-net): %s" % ", ".join(skipped))
    print("check_all: %d run, %d failed (%d of them required)"
          % (len(results), len(failed_required) + len(failed_other), len(failed_required)))
    return 1 if failed_required else 0


if __name__ == "__main__":
    sys.exit(main())
