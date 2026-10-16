"""Bind shared companion discovery to this skill's supported runtime layout."""
from contextlib import contextmanager
from functools import lru_cache
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = "market-intel"
PREFIX = "MARKET_INTEL"
DATA_CHILD = "data"


@lru_cache(maxsize=1)
def resolver():
    try:
        from fleet_guards.runtime import companion_resolver
    except ImportError as exc:
        raise RuntimeError(
            'fleet_guards is not installed; install it: pip install -e "$(git config --get fleet.guards)"'
        ) from exc
    return companion_resolver(source_root=ROOT)


def _directory(value, label):
    if not value or not str(value).strip():
        raise ValueError(label + " is empty")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(label + " is not an existing config directory")
    resolver().assert_outside_own_repo(path, SKILL)
    return path


def companion_root(override=None):
    """An explicit CLI path, else the shared resolver's companion root (or None)."""
    if override is not None:
        return _directory(override, "explicit companion")
    root = resolver().resolve_companion_root(SKILL)
    if root is None:
        return None
    root = Path(root).resolve()
    return root.parent if DATA_CHILD and root.name == DATA_CHILD else root


def data_directory(override=None):
    root = companion_root(override)
    if root is None:
        return None
    if DATA_CHILD:
        return root / DATA_CHILD
    if override is None:
        return Path(resolver().resolve_data_dir(SKILL)).resolve()
    return root / "data" if (root / "data").is_dir() else root


@contextmanager
def selected_environment(root):
    """Run a doctor against exactly its CLI selection and restore the caller environment."""
    keys = (PREFIX + "_CONFIG", PREFIX + "_DATA_DIR")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        os.environ[keys[0]] = str(root)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
