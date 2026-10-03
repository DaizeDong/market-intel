"""Checked historical reads and diffs against one verified commit and a copied index."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


class BaselineError(RuntimeError):
    """The historical comparison was not examined successfully."""


class Baseline:
    def __init__(self, repository, reference):
        self.repository = Path(repository).resolve()
        self.environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.environment["GIT_OPTIONAL_LOCKS"] = "0"
        self._scratch = None
        self._index = None
        self.commit = self._run("rev-parse", "--verify", "--end-of-options", reference + "^{commit}").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", self.commit):
            raise BaselineError("NOT_EXAMINED: baseline did not resolve to a commit")

    def _run(self, *args, copied_index=False):
        environment = dict(self.environment)
        if copied_index:
            environment["GIT_INDEX_FILE"] = str(self._copied_index())
        try:
            result = subprocess.run(["git", "-c", "core.fsmonitor=false", "--literal-pathspecs", *args],
                                    cwd=self.repository, env=environment, capture_output=True,
                                    text=True, encoding="utf-8", errors="strict", timeout=30)
        except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
            raise BaselineError("NOT_EXAMINED: Git comparison could not execute") from exc
        if result.returncode != 0:
            raise BaselineError("NOT_EXAMINED: Git rejected the baseline or historical comparison")
        return result.stdout

    def _copied_index(self):
        if self._index is None:
            path = Path(self._run("rev-parse", "--git-path", "index").strip())
            original = path if path.is_absolute() else self.repository / path
            if not original.is_file():
                raise BaselineError("NOT_EXAMINED: source index is unavailable")
            try:
                self._scratch = tempfile.TemporaryDirectory(prefix="market-intel-comparison-")
                self._index = Path(self._scratch.name) / "index.copy"
                shutil.copyfile(original, self._index)
            except OSError as exc:
                raise BaselineError("NOT_EXAMINED: source index could not be copied") from exc
        return self._index

    def files(self, relative_directory):
        """List the verified baseline, including files absent from the working tree."""
        return [name for name in self._run(
            "ls-tree", "-r", "--name-only", "-z", self.commit, "--", relative_directory
        ).split("\0") if name]

    def show(self, relative_path):
        names = self._run("ls-tree", "--name-only", "-z", self.commit, "--", relative_path).split("\0")
        if relative_path not in names:
            return None  # The commit exists; this particular historical path does not.
        return self._run("show", self.commit + ":" + relative_path)

    def diff(self, relative_path):
        return self._run("diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                         self.commit, "--", relative_path, copied_index=True)

    def close(self):
        if self._scratch is not None:
            self._scratch.cleanup()
