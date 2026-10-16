"""Bind shared companion discovery to this skill's supported runtime layout."""
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = "market-intel"


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
    return None if root is None else Path(root).resolve()


def data_directory():
    """Real-run output lives at <companion>/data."""
    root = companion_root()
    return None if root is None else root / "data"
