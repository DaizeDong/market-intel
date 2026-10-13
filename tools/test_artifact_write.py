"""Exercise the production lock-path seam with generated artifact names."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generated():
    spec = importlib.util.spec_from_file_location("artifact_fixture_builder", ROOT / "tools/make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.artifact_write_scenario()


def test_lock_key_respects_platform_path_identity(tmp_path):
    import private_inventory as storage
    relative = generated()["allowed"]
    first = storage.Destination(tmp_path / relative, tmp_path)
    second = storage.Destination(tmp_path / relative.upper(), tmp_path)
    assert (storage._update_lock_path(first) == storage._update_lock_path(second)) == (os.name == "nt")
