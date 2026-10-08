"""Exercise real source-contract ownership at production atomic write seams."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def generated():
    spec = importlib.util.spec_from_file_location("artifact_fixture_builder", ROOT / "tools/make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.artifact_write_scenario()


@pytest.mark.parametrize("state", ["declared", "undeclared", "ignored"])
def test_atomic_writer_enforces_source_contract(tmp_path, monkeypatch, state):
    sample = generated()
    target = tmp_path / (sample["undeclared"] if state == "undeclared" else sample["allowed"])
    proof = SimpleNamespace(root=str(tmp_path), repositories=("example/synthetic-config",), signature="synthetic-proof")
    def read(snapshot, *args):
        ignored = state == "ignored" and args[0] == "check-ignore" and args[-1] == sample["allowed"]
        return SimpleNamespace(returncode=(0 if ignored else 1) if args[0] == "check-ignore" else 0, stdout="synthetic-head")
    boundary = SimpleNamespace(prove_private_companion=lambda *a: proof,
                               read_private_companion_git=read, GitError=RuntimeError)
    import private_inventory as storage
    monkeypatch.setattr(storage, "_shared_boundary", lambda: boundary)
    destination = storage.Destination(target, tmp_path, "example/synthetic-config", target,
                                      (("example/synthetic-config",), "synthetic-proof"))
    monkeypatch.setattr(storage._storage_contract(), "load_boundary", lambda: boundary)
    before = set(tmp_path.rglob("*"))
    if state == "declared":
        storage.write_text(json.dumps(sample["content"]), sample["allowed"], destination)
        assert target.is_file()
        assert json.loads(target.read_text(encoding="utf-8")) == sample["content"]
    else:
        with pytest.raises((RuntimeError, ValueError)):
            storage.write_text(json.dumps(sample["content"]), sample["allowed"], destination)
        assert not target.exists()
        assert set(tmp_path.rglob("*")) == before


def test_lock_key_respects_platform_path_identity(tmp_path):
    import private_inventory as storage
    relative = generated()["allowed"]
    first = storage.Destination(tmp_path / relative, tmp_path, "example/synthetic-config")
    second = storage.Destination(tmp_path / relative.upper(), tmp_path, "example/synthetic-config")
    assert (storage._update_lock_path(first) == storage._update_lock_path(second)) == (os.name == "nt")
