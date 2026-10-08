#!/usr/bin/env python3
"""Validate the selected companion configuration for market-intel.

Selection and required fields are defined in CONFIG.md and config.contract.json.
Explicit CLI paths isolate environment selection. Runtime uses the same pinned Guards
companion discovery; invalid selectors never fall through to another companion.
"""
import argparse
import json
import os
import re
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
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from config_paths import companion_root
    selected = companion_root(override)
    return (str(selected), "shared companion selection") if selected is not None else (None, None)


def storage_mode(config):
    """Read the declared policy, retaining Mode B for older undeclared configs."""
    readme = os.path.join(config, "secrets", "README.md")
    if not os.path.isfile(readme):
        return "B"
    with open(readme, "r", encoding="utf-8-sig") as stream:
        text = stream.read()
    declarations = re.findall(r"^\s*Active storage mode:\s*(.*)$", text, re.I | re.M)
    if not declarations:
        first_line = next((line for line in text.splitlines() if line.strip()), "")
        declarations = re.findall(r"\bMode\s+([A-Z])\b", first_line, re.I)
    if not declarations:
        return "B"
    modes = set()
    for declaration in declarations:
        match = re.match(r"(?:Mode\s+)?([AB])\b", declaration.strip(" *`"), re.I)
        if not match:
            raise ValueError("declare Active storage mode: A or B in secrets/README.md")
        modes.add(match.group(1).upper())
    if len(modes) != 1:
        raise ValueError("conflicting storage modes in secrets/README.md")
    return modes.pop()


def validate_tools(entries, config):
    """Validate selected capabilities without invoking a provider or revealing credentials."""
    if not isinstance(entries, list):
        return ["tools must be an array"]
    errors, selected, seen = [], 0, set()
    for index, entry in enumerate(entries):
        label = "tools[%d]" % index
        if not isinstance(entry, dict):
            errors.append(label + " must be an object")
            continue
        slug = entry.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            errors.append(label + ".slug must be a kebab-case identifier")
            continue
        if slug in seen:
            errors.append(label + ".slug must be unique")
        seen.add(slug)
        if not isinstance(entry.get("installed"), bool):
            errors.append(label + ".installed must be boolean")
            continue
        if not entry["installed"]:
            continue
        selected += 1
        directory = os.path.join(config, "tools", slug)
        for filename in ("claude.json.template", "env.template"):
            if not os.path.isfile(os.path.join(directory, filename)):
                errors.append(label + " needs tools/<slug>/" + filename)
        template = os.path.join(directory, "claude.json.template")
        if os.path.isfile(template):
            try:
                with open(template, encoding="utf-8-sig") as stream:
                    payload = json.load(stream)
                if not isinstance(payload, dict) or not isinstance(payload.get("mcpServers"), dict):
                    errors.append(label + " claude.json.template needs an mcpServers object")
            except (OSError, ValueError):
                errors.append(label + " claude.json.template must be readable JSON")
    if not selected:
        errors.append("TEMPLATE_VALID is not READY: configure at least one tool with installed=true")
    return errors


def main():
    ap = argparse.ArgumentParser(description="Validate market-intel's companion config.")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--config-dir", default=None)
    a = ap.parse_args()

    skill = a.skill or detect_skill()
    if not skill:
        print("ERROR: could not detect skill name; pass --skill <name>.")
        return 2

    try:
        cfg, how = discover(skill, a.config_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        print("NOT READY: " + str(exc))
        return 1
    print("Config doctor for skill '%s'" % skill)
    print("Discovery env var: %s (and %s_DIR)" % (env_var(skill), env_var(skill)))
    if not cfg:
        print("  [%s] config located -> none found." % FAIL)
        print("       Set %s=<dir> or run: python scripts/init_config.py" % env_var(skill))
        return 1
    print("  resolved via %s -> %s" % (how, cfg))
    print("RESOLVED: " + cfg)
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
            errors = validate_tools(tools, cfg)
            check("selected capability fields and templates", not errors, "; ".join(errors))
        except Exception as e:
            check("registry.json valid JSON", False, str(e))

    check("tools/ dir present", os.path.isdir(os.path.join(cfg, "tools")))

    sec = os.path.join(cfg, "secrets")
    check("secrets/ dir present", os.path.isdir(sec))

    mode = None
    try:
        mode = storage_mode(cfg)
        check("credential storage mode: %s" % mode, True)
    except (OSError, UnicodeError, ValueError):
        check("credential storage mode is valid", False,
              "declare one readable Active storage mode: A or B in secrets/README.md")

    gi = os.path.join(cfg, ".gitignore")
    gi_ok = os.path.isfile(gi)
    if mode == "B":
        check(".gitignore present", gi_ok)
        if gi_ok:
            with open(gi, "r", encoding="utf-8", errors="replace") as stream:
                txt = stream.read()
            check("Mode B .gitignore blocks secrets (secrets/* + *.env)",
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
        print("NOT READY: %d check(s) failed. Fix the above for the selected storage mode." % n_fail)
        return 1
    print("READY: config at %s has configured capability templates; provider connectivity is not probed." % cfg)
    if mode == "A":
        print("Mode A uses PRIVATE Git for credential backup; verify remote visibility and backup durability separately.")
    else:
        print("Mode B requires a separate credential backup; verify its recovery separately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
