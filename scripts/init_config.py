#!/usr/bin/env python3
"""Initialize synthetic configuration templates for market-intel.

Selection and required fields are defined in CONFIG.md and config.contract.json.
Explicit CLI paths isolate environment selection. Runtime uses the same pinned Guards
companion discovery; invalid selectors never fall through to another companion.
"""
import argparse
import json
import os
import stat
import sys
import tempfile

GITIGNORE = """\
# Secrets gate (config-spec E6 / Mode B) — Mode B excludes credential values from this backup.
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

Real secret values live here and are **gitignored** (see ../.gitignore). Mode B ignores these values; a separately selected Mode A may use verified PRIVATE versioning.
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


def preflight(path):
    """Reject aliased outputs and ancestors without creating or opening files."""
    selected = os.path.abspath(path)
    current = selected
    existing = None
    while True:
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            pass
        else:
            reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if stat.S_ISLNK(info.st_mode) or reparse:
                raise ValueError("output path contains a filesystem alias: %s" % current)
            if current == selected:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError("output must be an ordinary file with no hardlinks: %s" % current)
                existing = info
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError("output parent is not a directory: %s" % current)
        parent = os.path.dirname(current)
        if parent == current:
            return existing
        current = parent


def write(path, content, force):
    if preflight(path) is not None and not force:
        print("  SKIP (exists): %s" % path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    preflight(path)
    temporary = None
    created = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=os.path.dirname(path), prefix=".init-config-", delete=False) as f:
            temporary = f.name
            created = os.fstat(f.fileno())
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        if preflight(path) is not None and not force:
            print("  SKIP (exists): %s" % path)
            return
        pending = preflight(temporary)
        if pending is None or not os.path.samestat(created, pending):
            raise ValueError("initializer temporary file changed before replacement")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            pending = preflight(temporary)
            if pending is not None:
                if created is None or not os.path.samestat(created, pending):
                    raise ValueError("initializer temporary file changed; cleanup refused")
                os.unlink(temporary)
    print("  wrote: %s" % path)


def main():
    ap = argparse.ArgumentParser(description="Stamp a spec-conformant companion config repo.")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--mode", default="B", choices=["A", "B"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.mode == "A":
        ap.error("Mode A is not implemented; no output was created. Use --mode B.")

    skill = a.skill or detect_skill()
    if not skill:
        print("ERROR: could not detect skill name; pass --skill <name>.")
        return 2
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from config_paths import companion_root
    out = a.out or companion_root() or default_dir(skill)
    out = os.path.abspath(os.path.expanduser(out))

    print("Init config for skill '%s' (mode %s) at %s" % (skill, a.mode, out))
    print("Discovery env var: %s  (fallback %s)" % (env_var(skill), default_dir(skill)))

    # registry.json, deterministic; no machine-specific content (E4/E5).
    # Top-level shape per companion-config-spec.md §3 (schema_version + tools[]).
    registry = {"schema_version": 1, "tools": []}
    outputs = [
        (os.path.join(out, "registry.json"), json.dumps(registry, indent=2, ensure_ascii=False) + "\n"),
        (os.path.join(out, ".gitignore"), GITIGNORE),
        (os.path.join(out, "tools", ".gitkeep"), ""),
        (os.path.join(out, "secrets", "README.md"), SECRETS_README),
        (os.path.join(out, "secrets", ".gitkeep"), ""),
    ]
    try:
        for path, _ in outputs:
            preflight(path)
        for path, content in outputs:
            write(path, content, a.force)
    except (OSError, ValueError) as exc:
        print("ERROR: config initialization failed: %s" % exc)
        return 2

    print("\nNext:")
    print("  1) For each tool: create tools/<slug>/{claude.json.template,env.template} and")
    print("     secrets/<slug>.env with real values (gitignored).")
    print("  2) export %s=%s   (or use the default path)" % (env_var(skill), out))
    print("  3) python scripts/verify_config.py   # doctor: confirms the config is ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
