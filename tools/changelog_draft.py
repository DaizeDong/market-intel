#!/usr/bin/env python3
"""
changelog_draft.py — draft a CHANGELOG entry via `claude -p` (headless Claude
Code), so the human author reviews + edits + commits.

Why this exists:
    Every release the human author hand-crafts a CHANGELOG entry. The pattern
    is structured (NEW / Modified / Files touched / Net) and the source data
    (git log, git diff --stat) is mechanical. An LLM can give a high-quality
    draft; the human edits; ~10 min saved per release.

This is a DRAFT helper, NOT a gate.
    Output goes to stdout (and optionally a file). The user reads, edits, and
    manually pastes into CHANGELOG.md. This script NEVER auto-writes to
    CHANGELOG.md. Per PHILOSOPHY P4, every commit-time fact must be verified
    by a human, not an LLM.

CLI:
    python tools/changelog_draft.py --since v0.24.0
    python tools/changelog_draft.py --since HEAD~5
    python tools/changelog_draft.py --since v0.24.0 --out tmp/changelog-draft.md

Default --since:
    Parses the most recent `## [<version>]` header from CHANGELOG.md and
    prefixes 'v'. (If the repo has no matching tag, pass --since HEAD~N
    instead.)

Default --out:
    stdout. With --out PATH, also write to file.

Exit codes:
    0 — success
    1 — git log empty (no commits in range, nothing to draft)
    2 — claude -p errored
    3 — `claude` CLI not available
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Output / encoding hygiene                                                   #
# --------------------------------------------------------------------------- #

def _reconfigure_stdout_utf8() -> None:
    """Make stdout BOM-safe on Windows so unicode prints cleanly."""
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

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
PLUGIN_JSON_PATH = REPO_ROOT / ".claude-plugin" / "plugin.json"


# --------------------------------------------------------------------------- #
# Read previous CHANGELOG entry + plugin.json                                 #
# --------------------------------------------------------------------------- #

_HEADER_RE = re.compile(r"^##\s+\[(?P<ver>\d+\.\d+\.\d+)\]\s*[—\-]")


def parse_latest_changelog_version() -> Optional[str]:
    """Return the most recent `## [X.Y.Z]` version string in CHANGELOG.md."""
    if not CHANGELOG_PATH.exists():
        return None
    for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines():
        m = _HEADER_RE.match(line)
        if m:
            return m.group("ver")
    return None


def extract_top_entry_text() -> str:
    """Return the text of the most recent CHANGELOG entry (top `## [X.Y.Z]`
    block), to feed the LLM as a house-style reference."""
    if not CHANGELOG_PATH.exists():
        return ""
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Find first `## [` header
    start = None
    for i, line in enumerate(lines):
        if _HEADER_RE.match(line):
            start = i
            break
    if start is None:
        return ""
    # Find next `## [` header (the one after) or EOF
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _HEADER_RE.match(lines[j]):
            end = j
            break
    return "\n".join(lines[start:end]).rstrip() + "\n"


def parse_plugin_version() -> Optional[str]:
    """Return the `version` field from .claude-plugin/plugin.json."""
    if not PLUGIN_JSON_PATH.exists():
        return None
    import json
    try:
        data = json.loads(PLUGIN_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    v = data.get("version")
    return str(v) if v else None


# --------------------------------------------------------------------------- #
# Git helpers                                                                 #
# --------------------------------------------------------------------------- #

def _git(args: list[str]) -> tuple[int, str, str]:
    """Run a git command in the repo root. Returns (rc, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def collect_git_data(since: str) -> Optional[dict]:
    """Collect git log + diff stats since `since`. Returns None if git fails."""
    rc, log_out, log_err = _git(["log", f"{since}..HEAD", "--oneline"])
    if rc != 0:
        print(f"[error] git log {since}..HEAD failed:", file=sys.stderr)
        print(log_err.strip(), file=sys.stderr)
        print(
            f"[hint] this repo may not have a `{since}` tag. Try a commit ref like "
            f"`--since HEAD~5` instead.",
            file=sys.stderr,
        )
        return None

    log_text = log_out.strip()
    if not log_text:
        return {"log": "", "stat": "", "name_status": ""}

    _, stat_out, _ = _git(["diff", f"{since}..HEAD", "--stat"])
    stat_lines = stat_out.strip().splitlines()
    if len(stat_lines) > 30:
        stat_lines = stat_lines[:30] + [f"... ({len(stat_lines) - 30} more)"]
    stat_text = "\n".join(stat_lines)

    _, ns_out, _ = _git(["diff", f"{since}..HEAD", "--name-status"])
    ns_lines = ns_out.strip().splitlines()
    if len(ns_lines) > 50:
        ns_lines = ns_lines[:50] + [f"... ({len(ns_lines) - 50} more)"]
    ns_text = "\n".join(ns_lines)

    return {"log": log_text, "stat": stat_text, "name_status": ns_text}


# --------------------------------------------------------------------------- #
# Prompt construction                                                         #
# --------------------------------------------------------------------------- #

PROMPT_TEMPLATE = """You are drafting a CHANGELOG entry for the market-intel skill. The user will
review and edit before committing.

Current version being released: {new_version}
Previous version: {previous_version}

Recent CHANGELOG entry (for style reference):
===
{previous_entry_text}
===

Commits since {previous_version}:
{git_log_oneline}

File changes:
{git_diff_stat}

File rename/move/add/delete:
{git_name_status}

Draft a CHANGELOG entry matching the house style above. Sections to consider:
- One-paragraph framing (what this release fixes/improves and why it matters)
- NEW machinery (list of new scripts/files)
- Modified mechanisms (changes to existing scripts/protocols)
- Doctrine/philosophy additions (if any)
- Files touched (categorized list)
- Net (one-line summary)

Be concrete and specific - reference the actual commits and files. Don't invent.
If a section has no content, omit it.

Output ONLY the CHANGELOG entry markdown, starting with `## [{new_version}] - {today}`.
"""


def build_prompt(
    *,
    new_version: str,
    previous_version: str,
    previous_entry_text: str,
    git_log_oneline: str,
    git_diff_stat: str,
    git_name_status: str,
    today: str,
) -> str:
    return PROMPT_TEMPLATE.format(
        new_version=new_version,
        previous_version=previous_version,
        previous_entry_text=previous_entry_text.strip() or "(no previous entry)",
        git_log_oneline=git_log_oneline.strip() or "(no commits)",
        git_diff_stat=git_diff_stat.strip() or "(no diff stats)",
        git_name_status=git_name_status.strip() or "(no name-status)",
        today=today,
    )


# --------------------------------------------------------------------------- #
# Claude invocation                                                           #
# --------------------------------------------------------------------------- #

from llmcall import call as _llmcall  # noqa: E402


def find_claude_cli() -> Optional[str]:
    """Preflight: is ANY llmcall provider (codex/cc/claude) reachable? Returns the first found, else
    None (the draft now runs through the codex -> cc -> claude chain, not claude alone)."""
    for name in ("codex", "cc", "claude"):
        p = shutil.which(name)
        if p:
            return p
    return None


def run_claude(prompt: str) -> tuple[int, str, str]:
    """Draft the entry via the shared llmcall chain (codex -> cc -> claude; read-only, one-shot). The
    (rc, stdout, stderr) shape is preserved so main() is unchanged: rc 0 + text on success, nonzero +
    error on total failure. The prompt (several KB) goes on stdin inside llmcall, dodging arg limits."""
    r = _llmcall(prompt)
    return (0, r.text, "") if r else (2, "", r.error or "llmcall chain failed")


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #

FOOTER = """\

---
Draft generated by changelog_draft.py - REVIEW + EDIT before pasting into CHANGELOG.md.
This is a DRAFT helper, not a gate. Per PHILOSOPHY P4: every commit-time fact must be
verified by a human, not an LLM.
"""


def main(argv: Optional[list[str]] = None) -> int:
    _reconfigure_stdout_utf8()

    parser = argparse.ArgumentParser(
        description="Draft a CHANGELOG entry via claude -p (headless Claude Code).",
    )
    parser.add_argument(
        "--since",
        default=None,
        help=(
            "Git ref to compare against (e.g. v0.24.0 or HEAD~5). "
            "Default: latest version in CHANGELOG.md prefixed with 'v'."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Also write draft to this path (default: stdout only).",
    )
    args = parser.parse_args(argv)

    # Locate `claude` CLI early
    if find_claude_cli() is None:
        print(
            "[error] `claude` CLI not found on PATH. Install Claude Code "
            "(https://claude.ai/code) and ensure `claude` is on PATH.",
            file=sys.stderr,
        )
        return 3

    # Resolve --since default
    previous_version = parse_latest_changelog_version()
    since = args.since
    if since is None:
        if previous_version is None:
            print(
                "[error] could not parse a previous version from CHANGELOG.md; "
                "pass --since explicitly (e.g. --since HEAD~5).",
                file=sys.stderr,
            )
            return 1
        since = f"v{previous_version}"

    # If --since matches the parsed version, use that as previous_version. Otherwise
    # strip a leading 'v' from --since for display.
    if previous_version is None:
        previous_version = since.lstrip("v")

    new_version = parse_plugin_version() or "X.Y.Z"
    today = _dt.date.today().isoformat()

    # Collect git data
    git_data = collect_git_data(since)
    if git_data is None:
        return 1
    if not git_data["log"]:
        print(
            f"[error] no commits found in range {since}..HEAD; nothing to draft.",
            file=sys.stderr,
        )
        return 1

    # Build prompt
    previous_entry_text = extract_top_entry_text()
    prompt = build_prompt(
        new_version=new_version,
        previous_version=previous_version,
        previous_entry_text=previous_entry_text,
        git_log_oneline=git_data["log"],
        git_diff_stat=git_data["stat"],
        git_name_status=git_data["name_status"],
        today=today,
    )

    print(
        f"[info] drafting CHANGELOG entry for v{new_version} "
        f"(since {since}, prev v{previous_version})...",
        file=sys.stderr,
    )
    print(
        f"[info] prompt size: {len(prompt):,} chars, "
        f"{len(git_data['log'].splitlines())} commits",
        file=sys.stderr,
    )

    rc, stdout, stderr = run_claude(prompt)
    if rc != 0:
        print(f"[error] `claude -p` exited with code {rc}:", file=sys.stderr)
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)
        return 2

    draft = stdout.rstrip() + "\n" + FOOTER

    # Emit to stdout
    sys.stdout.write(draft)
    sys.stdout.flush()

    # Also write to file if requested
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(draft, encoding="utf-8")
        print(f"\n[info] draft also written to {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
