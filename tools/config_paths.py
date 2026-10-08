"""Bind shared companion discovery to this skill's supported runtime layout."""
from contextlib import contextmanager
from functools import lru_cache
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = "market-intel"
PREFIX = "MARKET_INTEL"
DATA_CHILD = "data"


@lru_cache(maxsize=1)
def resolver():
    source = ROOT / "guards/tools/datadir.py"
    spec = importlib.util.spec_from_file_location(PREFIX.lower() + "_config_datadir", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except (OSError, ImportError) as exc:
        raise RuntimeError("initialize the pinned guards submodule before selecting configuration") from exc
    return module


def _directory(value, label):
    if not value or not str(value).strip():
        raise ValueError(label + " is empty")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(label + " is not an existing config directory")
    resolver().assert_outside_own_repo(path, SKILL, source_root=ROOT)
    return path


def companion_root(override=None):
    """Explicit CLI selection is isolated; conflicting ambient config and DATA fail."""
    if override is not None:
        return _directory(override, "explicit companion")
    selected = None
    for name in (PREFIX + "_CONFIG", PREFIX + "_CONFIG_DIR"):
        if name in os.environ:
            selected = _directory(os.environ[name], name)
            break
    data_name = PREFIX + "_DATA_DIR"
    data_root = None
    if data_name in os.environ:
        data = _directory(os.environ[data_name], data_name)
        if DATA_CHILD and data.name != DATA_CHILD:
            raise ValueError(data_name + " must select the companion's " + DATA_CHILD + "/ directory")
        data_root = data.parent if data.name == (DATA_CHILD or "data") else data
        if selected is not None and selected != data_root:
            raise ValueError("CONFIG and DATA_DIR conflict: settings and DATA must belong to the same companion")
    discovered = resolver().resolve_companion_root(SKILL, source_root=ROOT)
    # The shared resolver recognizes data/. Demand deliberately stores runtime state in pool/.
    if data_root is not None:
        return selected or data_root
    return selected or (Path(discovered).resolve() if discovered is not None else None)


def data_directory(override=None):
    root = companion_root(override)
    if root is None:
        return None
    if override is None and PREFIX + "_DATA_DIR" in os.environ:
        return _directory(os.environ[PREFIX + "_DATA_DIR"], PREFIX + "_DATA_DIR")
    if DATA_CHILD:
        return root / DATA_CHILD
    return root / "data" if (root / "data").is_dir() else root


@contextmanager
def selected_environment(root):
    """Run a doctor against exactly its CLI selection and restore the caller environment."""
    keys = (PREFIX + "_CONFIG", PREFIX + "_CONFIG_DIR", PREFIX + "_DATA_DIR")
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
