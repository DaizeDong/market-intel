#!/usr/bin/env python3
"""Initialize a spec-conformant companion config repo for market-intel (config-spec E3/E4).

Deterministic + template-driven. Derives the discovery env var from the skill name and stamps an
empty, conformant config skeleton (Mode B: secrets gitignored). Re-running with the same skill +
out dir produces byte-identical output — no interactive divergence (E4).

Authoritative deep spec: skills/market-intel/reference/companion-config-spec.md (v1.3, STABLE).
Discovery order this skill uses (also in CONFIG.md, E2), the config dir resolves from, in order:
  1. $MARKET_INTEL_CONFIG          (UPPER_SNAKE of skill name + _CONFIG)
  2. ~/.market-intel-config/       (dotfile fallback)
  3. ~/.config/market-intel-config/ (XDG fallback)
  ($MARKET_INTEL_CONFIG_DIR is accepted by the tooling as a convenience alias for #1.)

Usage:
  python init_config.py [--skill <name>] [--out <dir>] [--mode B] [--force]

--skill   skill name; if omitted, auto-detected from the nearest .claude-plugin/plugin.json.
--out     target dir; if omitted, the default discovery path ~/.<skill>-config/.
Stdlib only. Cross-platform. Never writes secrets; never echoes anything secret.
"""
import argparse
import json
import os
import sys

GITIGNORE = """\
# Secrets gate (config-spec E6 / Mode B) — real values never enter git.
secrets/*
!secrets/README.md
!secrets/.gitkeep
*.env
!*.env.template
!env.template
claude.json
.claude.json
*credentials*.json
*.key
*.pem
!*.key.template
!*.pem.template
"""

SECRETS_README = """\
# secrets/ — Mode B (gitignored)

Real secret values live here and are **gitignored** (see ../.gitignore). They never enter git.
Back them up out-of-band (cloud sync / encrypted drive). Restore on a new machine by copying the
`*.env` files back into this directory, then re-running the skill's verify script.

Active storage mode: **B** (gitignored + out-of-band backup).
Per tool, create `secrets/<slug>.env` with the KEY=VALUE pairs its `tools/<slug>/env.template` lists.
Files MUST be UTF-8 without BOM.
"""


def env_var(skill):
    return skill.upper().replace("-", "_") + "_CONFIG"


def default_dir(skill):
    return os.path.expanduser("~/.%s-config" % skill)


def detect_skill():
    """Find the skill name from the nearest .claude-plugin/plugin.json (search cwd + script parents)."""
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


def write(path, content, force):
    if os.path.exists(path) and not force:
        print("  SKIP (exists): %s" % path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  wrote: %s" % path)


def main():
    ap = argparse.ArgumentParser(description="Stamp a spec-conformant companion config repo.")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--mode", default="B", choices=["A", "B"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    skill = a.skill or detect_skill()
    if not skill:
        print("ERROR: could not detect skill name; pass --skill <name>.")
        return 2
    out = a.out or default_dir(skill)
    out = os.path.abspath(os.path.expanduser(out))

    print("Init config for skill '%s' (mode %s) at %s" % (skill, a.mode, out))
    print("Discovery env var: %s  (fallback %s)" % (env_var(skill), default_dir(skill)))

    # registry.json, deterministic; no machine-specific content (E4/E5).
    # Top-level shape per companion-config-spec.md §3 (schema_version + tools[]).
    registry = {"schema_version": 1, "tools": []}
    write(os.path.join(out, "registry.json"),
          json.dumps(registry, indent=2, ensure_ascii=False) + "\n", a.force)
    write(os.path.join(out, ".gitignore"), GITIGNORE, a.force)
    write(os.path.join(out, "tools", ".gitkeep"), "", a.force)
    write(os.path.join(out, "secrets", "README.md"), SECRETS_README, a.force)
    write(os.path.join(out, "secrets", ".gitkeep"), "", a.force)

    print("\nNext:")
    print("  1) For each tool: create tools/<slug>/{claude.json.template,env.template} and")
    print("     secrets/<slug>.env with real values (gitignored).")
    print("  2) export %s=%s   (or use the default path)" % (env_var(skill), out))
    print("  3) python scripts/verify_config.py   # doctor: confirms the config is ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
