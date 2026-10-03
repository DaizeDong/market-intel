#!/usr/bin/env bash
# Deploy only clean, published main after verification. The installed skill leaf is managed:
# replace it completely, retaining the whole previous tree (including custom files) beside it.
set -euo pipefail
REPO="${MARKET_INTEL_REPO:-$HOME/CodesClaude/market-intel}"
LIVE="${MARKET_INTEL_LIVE:-$HOME/.claude/skills/market-intel}"
for selector in "$REPO" "$LIVE"; do
  normalized=${selector//\\//}
  case "/$normalized/" in
    */../*) printf '%s\n' "Deployment paths must not contain '..'." >&2; exit 1 ;;
  esac
  case "$normalized" in
    /*|[A-Za-z]:/*) ;;
    *) printf '%s\n' "Deployment paths must be absolute." >&2; exit 1 ;;
  esac
done
if command -v cygpath >/dev/null 2>&1; then
  REPO=$(cygpath -aw "$REPO")
  LIVE=$(cygpath -aw "$LIVE")
fi

python -B - "$REPO" "$LIVE" <<'PY'
import hashlib
import ctypes
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile

MANIFEST = ".market-intel-deployment.json"


def checked_path(value):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts or path == Path(path.anchor):
        raise RuntimeError(f"Select an absolute, non-root path without '..': {path}")
    for part in [*reversed(path.parents), path]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise RuntimeError(f"Filesystem alias refused: {part}")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise RuntimeError(f"Hardlinked file refused: {part}")
        if not stat.S_ISREG(info.st_mode) and not stat.S_ISDIR(info.st_mode):
            raise RuntimeError(f"Nonordinary path refused: {part}")
    return path.resolve()


def directory_identity(path):
    path = checked_path(path)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"Expected a directory: {path}")
    return info.st_dev, info.st_ino


def require_identity(path, expected):
    if directory_identity(path) != expected:
        raise RuntimeError(f"Directory identity changed; refusing to move or write it: {path}")


def move_to_empty(source, destination):
    """Rename a tree without replacing any concurrently created destination."""
    source, destination = checked_path(source), checked_path(destination)
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    if os.name == "nt":
        os.rename(source, destination)
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    elif sys.platform == "darwin" and hasattr(library, "renamex_np"):
        rename = library.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(os.fsencode(source), os.fsencode(destination), 4)
    else:
        raise RuntimeError("This platform has no supported exclusive directory rename.")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def tree_state(root):
    root = checked_path(root)
    if not root.exists():
        return None
    if not root.is_dir():
        raise RuntimeError(f"Expected a directory: {root}")
    files = {}
    for directory, folders, names in os.walk(root, followlinks=False):
        for name in folders:
            checked_path(Path(directory) / name)
        for name in names:
            path = checked_path(Path(directory) / name)
            info = path.stat()
            files[path.relative_to(root).as_posix()] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mode": "100755" if info.st_mode & stat.S_IXUSR else "100644",
            }
    return files


def deploy(repo, live):
    repo, live = checked_path(repo), checked_path(live)
    if repo == live or repo in live.parents or live in repo.parents:
        raise RuntimeError("The source repository and installed skill must not contain each other.")
    if not live.parent.is_dir():
        raise RuntimeError(f"Create the selected installation parent first: {live.parent}")
    parent_identity = directory_identity(live.parent)
    repo_identity = directory_identity(repo)
    previous = tree_state(live)
    previous_identity = directory_identity(live) if previous is not None else None

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE).stdout

    def clean_source(expected=None):
        require_identity(repo, repo_identity)
        if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != repo:
            raise RuntimeError("Selected source is not the repository root.")
        if git("status", "--porcelain=v1", "--untracked-files=all"):
            raise RuntimeError("Source repository must be clean before deployment.")
        if expected is not None:
            if git("branch", "--show-current").decode().strip() != "main":
                raise RuntimeError("Deployment source is no longer main.")
            if git("rev-parse", "HEAD").decode().strip() != expected:
                raise RuntimeError("Deployment source commit changed.")
            if git("rev-parse", "refs/remotes/origin/main").decode().strip() != expected:
                raise RuntimeError("Deployment source is not the published origin/main commit.")

    clean_source()
    git("checkout", "main", "--quiet")
    git("pull", "--quiet", "--ff-only", "origin", "main")
    commit = git("rev-parse", "HEAD").decode().strip()
    clean_source(commit)
    source = checked_path(repo / "skills" / "market-intel")
    tree_state(source)
    subprocess.run([sys.executable, "tools/verify_matrix.py", "--no-net", "--no-cache"], cwd=repo, check=True)
    clean_source(commit)

    require_identity(live.parent, parent_identity)
    stage = Path(tempfile.mkdtemp(prefix=f".{live.name}.stage-", dir=live.parent))
    stage_identity = directory_identity(stage)
    snapshot_location = stage
    backup = None
    published = False

    def absent_sibling(kind):
        require_identity(live.parent, parent_identity)
        path = Path(tempfile.mkdtemp(prefix=f".{live.name}.{kind}-", dir=live.parent))
        path.rmdir()
        return path

    try:
        manifest = {}
        folded = set()
        prefix = "skills/market-intel/"
        entries = git("ls-tree", "-rz", "--full-tree", commit, "--", prefix).split(b"\0")
        for entry in filter(None, entries):
            metadata, raw_name = entry.split(b"\t", 1)
            mode, kind, blob = metadata.decode().split()
            name = raw_name.decode("utf-8")
            if not name.startswith(prefix) or kind != "blob" or mode not in {"100644", "100755"}:
                raise RuntimeError("The committed skill contains an unsupported entry.")
            relative = name[len(prefix):]
            parts = PurePosixPath(relative).parts
            if not parts or any(part in {".", ".."} for part in parts) or ":" in relative or "\\" in relative:
                raise RuntimeError("The committed skill contains an unsafe path.")
            if relative == MANIFEST or relative.casefold() in folded:
                raise RuntimeError("The committed skill has a reserved or colliding path.")
            folded.add(relative.casefold())
            checked_path(source / relative)
            payload = git("cat-file", "blob", blob)
            require_identity(live.parent, parent_identity)
            require_identity(stage, stage_identity)
            target = checked_path(stage / relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(0o755 if mode == "100755" else 0o644)
            manifest[relative] = {"sha256": hashlib.sha256(payload).hexdigest(), "mode": mode}
        if "SKILL.md" not in manifest:
            raise RuntimeError("The selected commit has no managed SKILL.md.")
        receipt = json.dumps({"schema_version": 1, "commit": commit, "files": manifest}, indent=2) + "\n"
        require_identity(stage, stage_identity)
        manifest_path = checked_path(stage / MANIFEST)
        with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(receipt)

        def verify_snapshot(path):
            state = tree_state(path)
            if state is None:
                raise RuntimeError(f"Deployment snapshot disappeared: {path}")
            actual_receipt = state.pop(MANIFEST, None)
            if actual_receipt is None or (path / MANIFEST).read_text(encoding="utf-8") != receipt:
                raise RuntimeError("Deployment manifest verification failed.")
            # Windows does not retain POSIX executable bits; content and path equality still apply.
            if set(state) != set(manifest) or any(state[name]["sha256"] != row["sha256"] for name, row in manifest.items()):
                raise RuntimeError("Installed files do not match the selected commit.")
            if os.name != "nt" and state != manifest:
                raise RuntimeError("Installed executable modes do not match the selected commit.")

        verify_snapshot(stage)
        clean_source(commit)
        if tree_state(live) != previous:
            raise RuntimeError("Installed tree changed during preparation.")
        if previous_identity is not None:
            require_identity(live, previous_identity)
        require_identity(live.parent, parent_identity)
        require_identity(stage, stage_identity)
        if previous is not None:
            candidate = absent_sibling("backup")
            require_identity(live, previous_identity)
            move_to_empty(live, candidate)
            backup = candidate
        require_identity(live.parent, parent_identity)
        require_identity(stage, stage_identity)
        move_to_empty(stage, live)
        snapshot_location = live
        published = True
        verify_snapshot(live)
        require_identity(live, stage_identity)
        clean_source(commit)
    except Exception:
        try:
            require_identity(live.parent, parent_identity)
            checked_path(live)
            if published:
                require_identity(live, stage_identity)
                failed = absent_sibling("failed")
                require_identity(live, stage_identity)
                move_to_empty(live, failed)
                snapshot_location = failed
            if backup is not None:
                require_identity(backup, previous_identity)
                if tree_state(backup) != previous or live.exists():
                    raise RuntimeError("Rollback target changed; retained backup requires manual recovery.")
                restore = absent_sibling("restore")
                require_identity(live.parent, parent_identity)
                require_identity(backup, previous_identity)
                checked_path(restore)
                shutil.copytree(backup, restore)
                restore_identity = directory_identity(restore)
                if tree_state(restore) != previous:
                    raise RuntimeError("Rollback copy did not match the preserved tree.")
                require_identity(live.parent, parent_identity)
                require_identity(restore, restore_identity)
                move_to_empty(restore, live)
                print(f"Previous installation restored; complete backup retained at {backup}", file=sys.stderr)
        except Exception as rollback_error:
            print(f"Rollback incomplete: {rollback_error}. Preserved backup: {backup}", file=sys.stderr)
        print(f"Deployment failed; last known prepared snapshot location: {snapshot_location}", file=sys.stderr)
        raise
    print(f"Deployed market-intel commit {commit} to {live}")
    if backup is not None:
        print(f"Complete previous installation, including custom files, retained at {backup}")


try:
    deploy(Path(sys.argv[1]), Path(sys.argv[2]))
except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
    print(f"Deployment refused or failed: {error}", file=sys.stderr)
    sys.exit(1)
PY
