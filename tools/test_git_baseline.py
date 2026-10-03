"""Synthetic Git replies verify failures and source-index preservation without real Git."""
from pathlib import Path
import subprocess

import pytest
from git_baseline import Baseline, BaselineError


def test_missing_commit_and_git_execution_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 128, "", "synthetic error"))
    with pytest.raises(BaselineError, match="NOT_EXAMINED"):
        Baseline(tmp_path, "absent-commit")
    def fail(*args, **kwargs):
        raise FileNotFoundError("synthetic Git unavailable")
    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(BaselineError, match="NOT_EXAMINED"):
        Baseline(tmp_path, "main")


def test_absent_path_is_distinct_from_failed_historical_read(tmp_path, monkeypatch):
    fail_show = False
    def git(argv, **kwargs):
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, "1" * 40, "")
        if "ls-tree" in argv:
            return subprocess.CompletedProcess(argv, 0, "known.md\0" if argv[-1] == "known.md" else "", "")
        if "show" in argv:
            return subprocess.CompletedProcess(argv, 128 if fail_show else 0, "historical\n", "")
        raise AssertionError(argv)
    monkeypatch.setattr(subprocess, "run", git)
    baseline = Baseline(tmp_path, "main")
    assert baseline.show("new.md") is None
    assert baseline.show("known.md") == "historical\n"
    fail_show = True
    with pytest.raises(BaselineError, match="NOT_EXAMINED"):
        baseline.show("known.md")


def test_every_diff_uses_a_private_index_and_propagates_failure(tmp_path, monkeypatch):
    original = tmp_path / "source-index"
    original.write_bytes(b"synthetic original index")
    failed = False
    seen = []
    def git(argv, **kwargs):
        assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
        if "--git-path" in argv:
            return subprocess.CompletedProcess(argv, 0, str(original), "")
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, "1" * 40, "")
        assert "diff" in argv
        copied = Path(kwargs["env"]["GIT_INDEX_FILE"])
        assert copied != original and copied.read_bytes() == original.read_bytes()
        assert all(flag in argv for flag in ("--no-ext-diff", "--no-textconv", "--no-renames"))
        seen.append(copied)
        return subprocess.CompletedProcess(argv, 128 if failed else 0, "synthetic diff\n", "")
    monkeypatch.setattr(subprocess, "run", git)
    baseline = Baseline(tmp_path, "main")
    try:
        assert baseline.diff("document.md") == "synthetic diff\n"
        failed = True
        with pytest.raises(BaselineError, match="NOT_EXAMINED"):
            baseline.diff("document.md")
        assert original.read_bytes() == b"synthetic original index"
    finally:
        baseline.close()
    assert len(seen) == 2 and all(not path.exists() for path in seen)
