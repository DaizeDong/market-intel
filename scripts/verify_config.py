#!/usr/bin/env python3
"""Doctor for market-intel's companion config (config-spec E3). Resolves the config dir via the
documented discovery order, validates it against the spec, and prints PASS/FAIL per check naming
exactly what is missing. Exit 0 = ready, 1 = not ready, 2 = usage error.

Authoritative deep spec: skills/market-intel/reference/companion-config-spec.md (v1.3, STABLE).
Discovery order (config-spec E2 / spec §1):
  1. $MARKET_INTEL_CONFIG   2. ~/.market-intel-config/   3. ~/.config/market-intel-config/
  ($MARKET_INTEL_CONFIG_DIR is accepted as a convenience alias for #1.)

Usage:
  python verify_config.py [--skill <name>] [--config-dir <dir>]
Stdlib only. Never echoes secret values (only presence / length).
"""
import argparse
import json
import os
import sys

PASS, FAIL = "PASS", "FAIL"


def env_var(skill):
    return skill.upper().replace("-", "_") + "_CONFIG"


def detect_skill():
    starts = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for start in starts:
        d = start
        for _ in range(6):
            pj = os.path.join(d, ".claude-plugin", "plugin.json")
            if os.path.isfile(pj):
                try:
                    with open(pj, "r", encoding="utf-8") as f:
                        return json.load(f).get("name")
                except Exception:
                    pass
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
    return None


def discover(skill, override):
    if override:
        return os.path.abspath(os.path.expanduser(override)), "explicit (--config-dir)"
    for v in (env_var(skill), env_var(skill) + "_DIR"):
        val = os.environ.get(v)
        if val:
            return os.path.abspath(os.path.expanduser(val)), "env:%s" % v
    for d in (os.path.expanduser("~/.%s-config" % skill),
              os.path.expanduser("~/.config/%s-config" % skill)):
        if os.path.isdir(d):
            return d, "default:%s" % d
    return None, None


def main():
    ap = argparse.ArgumentParser(description="Validate market-intel's companion config.")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--config-dir", default=None)
    a = ap.parse_args()

    skill = a.skill or detect_skill()
    if not skill:
        print("ERROR: could not detect skill name; pass --skill <name>.")
        return 2

    cfg, how = discover(skill, a.config_dir)
    print("Config doctor for skill '%s'" % skill)
    print("Discovery env var: %s (and %s_DIR)" % (env_var(skill), env_var(skill)))
    if not cfg:
        print("  [%s] config located -> none found." % FAIL)
        print("       Set %s=<dir> or run: python scripts/init_config.py" % env_var(skill))
        return 1
    print("  resolved via %s -> %s" % (how, cfg))
    print("-" * 60)

    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))

    check("config dir exists", os.path.isdir(cfg))

    reg = os.path.join(cfg, "registry.json")
    reg_ok = os.path.isfile(reg)
    check("registry.json present", reg_ok)
    if reg_ok:
        try:
            with open(reg, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            check("registry.json valid JSON", True)
            check("schema_version == 1", data.get("schema_version") == 1,
                  "got %r" % data.get("schema_version"))
            tools = data.get("tools", data.get("entries"))
            check("tools[]/entries[] is a list", isinstance(tools, list),
                  "type %s" % type(tools).__name__)
        except Exception as e:
            check("registry.json valid JSON", False, str(e))

    check("tools/ dir present", os.path.isdir(os.path.join(cfg, "tools")))

    sec = os.path.join(cfg, "secrets")
    check("secrets/ dir present", os.path.isdir(sec))

    gi = os.path.join(cfg, ".gitignore")
    gi_ok = os.path.isfile(gi)
    check(".gitignore present", gi_ok)
    if gi_ok:
        txt = open(gi, "r", encoding="utf-8", errors="replace").read()
        check(".gitignore blocks secrets (secrets/* + *.env)",
              "secrets/" in txt and "*.env" in txt)

    # self-contained check (E5): no absolute-path leakage in committed config files.
    leak = []
    for rel in ("registry.json", ".gitignore", os.path.join("secrets", "README.md")):
        p = os.path.join(cfg, rel)
        if os.path.isfile(p):
            t = open(p, "r", encoding="utf-8", errors="replace").read()
            if any(s in t for s in ("C:\\", "C:/", "/home/", "/Users/", "/root/")):
                leak.append(rel)
    check("self-contained (no hardcoded absolute paths)", not leak, "leaks in %s" % leak)

    # report
    n_fail = sum(1 for _, ok, _ in results if not ok)
    for nm, ok, detail in results:
        line = "  [%s] %s" % (PASS if ok else FAIL, nm)
        if detail and not ok:
            line += "  -> %s" % detail
        print(line)
    print("-" * 60)
    if n_fail:
        print("NOT READY: %d check(s) failed. Fix the above (or re-run init_config.py)." % n_fail)
        return 1
    print("READY: config at %s conforms. Add tools/<slug>/ + secrets/<slug>.env to populate it." % cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
