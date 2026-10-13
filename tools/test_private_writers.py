"""Generated synthetic destination and concurrent-writer regressions; no live calls."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

import pytest
import private_inventory as storage
from make_fixtures import fixture, make_runtime_fixture, make_runtime_repository

SAMPLE = fixture()["maintenance"]


@pytest.fixture
def native_companion(tmp_path, monkeypatch):
    generated = make_runtime_fixture(tmp_path)
    for key in list(os.environ):
        if key not in generated["environment"]:
            monkeypatch.delenv(key)
    for key, value in generated["environment"].items():
        monkeypatch.setenv(key, value)
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(generated["repository"] / "data"))
    (generated["repository"] / "data").mkdir(exist_ok=True)
    return generated


def test_native_nested_repository_is_authoritative(native_companion):
    repository = native_companion["repository"]
    assert storage.resolve_directory(path=repository).repository == repository
    nested = make_runtime_repository(repository / "runtime", native_companion["environment"], SAMPLE["other_identity"])
    selected = storage.resolve_directory(path=nested)
    assert selected.repository == nested
    assert not (nested / "inventory").exists()


def test_native_path_checks_start_no_process(native_companion, monkeypatch):
    repository = native_companion["repository"]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("runtime path check started a process"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("runtime path check started a process"))
    target = repository / "data/deliverables/report.json"
    selected = storage.resolve_destination(path=target)
    storage.write_text("{}\n", "reports/report.json", selected)
    assert target.read_text(encoding="utf-8") == "{}\n"


def test_native_publication_replaces_target(native_companion):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/synthetic.json"
    target.parent.mkdir(parents=True)
    target.write_text("Synthetic retained bytes\n", encoding="utf-8")
    selected = storage.resolve_destination(path=target)
    storage.write_text("Synthetic replacement bytes\n", "reports/synthetic.json", selected)
    assert target.read_text(encoding="utf-8") == "Synthetic replacement bytes\n"
    assert not list((repository / ".staging").glob("inventory-*.tmp"))


def test_native_explicit_target_retains_lexical_selection(native_companion, monkeypatch):
    repository = native_companion["repository"]
    lexical = repository / "data/deliverables/selected.json"
    selected_target = [repository / "data/deliverables/first.json"]
    original_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        return selected_target[0] if path == lexical else original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    selected = storage.resolve_destination(path=lexical)
    assert selected.requested_path == lexical and selected.path == selected_target[0]
    selected_target[0] = repository / "data/deliverables/second.json"
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_text("{}\n", "reports/result.json", selected)
    assert not (repository / "data/deliverables/first.json").exists()
    assert not (repository / "data/deliverables/second.json").exists()


@pytest.fixture
def companion(tmp_path, monkeypatch):
    """A synthetic companion worktree: path checks only need the Git marker."""
    repository = tmp_path / "companion"
    (repository / ".git").mkdir(parents=True)
    (repository / "data").mkdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(repository / "data"))
    return repository


def test_explicit_destinations_use_final_private_repository(companion, tmp_path):
    repository = companion
    selected = storage.resolve_destination("reports/feedback.json", path=repository / "data/deliverables/reports/result.json")
    storage.write_text("synthetic\n", "reports/feedback.json", selected)
    assert selected.path.read_text() == "synthetic\n"
    for target in (storage.ROOT / "inventory/research.json", tmp_path / "unmanaged/result.json"):
        with pytest.raises(storage.InventoryError):
            storage.resolve_destination("reports/feedback.json", path=target)


def test_serialized_updates_preserve_both_generated_rows(companion):
    repository = companion
    selected = storage.resolve_destination("metrics/live-runs.jsonl")
    start = threading.Barrier(2)
    rows = SAMPLE["ledger"][:2]
    def append(row):
        start.wait(timeout=5)
        storage.update_text(lambda body: body + json.dumps(row) + "\n",
                            "metrics/live-runs.jsonl", selected)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(append, rows))
    observed = [json.loads(line) for line in selected.path.read_text().splitlines()]
    assert sorted(row["outcome"] for row in observed) == sorted(row["outcome"] for row in rows)
    assert list(selected.path.parent.iterdir()) == [selected.path]
    before = selected.path.read_bytes()
    with patch.object(storage.os, "replace", side_effect=PermissionError("synthetic denial")):
        with pytest.raises(storage.InventoryError):
            storage.update_text(lambda body: body + json.dumps(SAMPLE["ledger"][2]) + "\n",
                                "metrics/live-runs.jsonl", selected)
    assert selected.path.read_bytes() == before
    pending, = (repository / ".staging").glob("inventory-*.tmp")
    assert pending.read_text() == before.decode() + json.dumps(SAMPLE["ledger"][2]) + "\n"
    assert set(selected.path.parent.iterdir()) == {selected.path}


def load_writer(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke(writer, args):
    with patch.object(sys, "argv", [writer.__file__, *args]):
        return writer.main()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces", "feedback-bump"])
def test_writers_refuse_unproven_output_before_observation(name, tmp_path, monkeypatch):
    writer = load_writer(name)
    target = tmp_path / "unmanaged/result.json"
    def unproven(*args, **kwargs):
        raise storage.InventoryError("synthetic unproven destination")
    monkeypatch.setattr(storage, "resolve_destination", unproven)
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: pytest.fail("observation preceded validation")})
        args = ["--out", str(target)]
    elif name == "poll_surfaces":
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: pytest.fail("observation preceded validation")})
        args = ["--inbox", str(target)]
    else:
        monkeypatch.setattr(writer, "live_runs_path", lambda: pytest.fail("ledger read preceded output validation"))
        args = ["--out", str(target)]
    assert invoke(writer, args) == 2
    assert not target.parent.exists()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces", "feedback-bump"])
def test_writers_persist_only_to_checked_companion_override(name, companion, monkeypatch):
    repository = companion
    writer = load_writer(name)
    target = repository / "data/deliverables/reports/result.json"
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: [deepcopy(SAMPLE["discovery"])]})
        args = ["--out", str(target)]
    elif name == "poll_surfaces":
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: [deepcopy(SAMPLE["surface"])]})
        args = ["--inbox", str(target)]
    else:
        ledger = repository / "data/metrics/live-runs.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(json.dumps(SAMPLE["ledger"][0]) + "\n", encoding="utf-8")
        monkeypatch.setattr(writer, "live_runs_path", lambda: ledger)
        args = ["--out", str(target), "--since", "2030-01-01"]
    assert invoke(writer, args) in (0, 1)
    assert target.is_file()
    assert target.read_text(encoding="utf-8").strip()


@pytest.mark.parametrize("name", ["discover", "poll_surfaces"])
def test_polling_dry_run_does_not_create_output_directories(name, companion, monkeypatch):
    repository = companion
    writer = load_writer(name)
    target = repository / "data/deliverables/uncreated/result.json"
    if name == "discover":
        monkeypatch.setattr(writer, "CHANNELS", {"e1": lambda *_: [deepcopy(SAMPLE["discovery"])]})
        args = ["--out", str(target), "--dry-run"]
    else:
        monkeypatch.setattr(writer, "SURFACES", {"E1": lambda *_: [deepcopy(SAMPLE["surface"])]})
        args = ["--inbox", str(target), "--dry-run"]
    assert invoke(writer, args) == 0
    assert not target.parent.exists()


def test_feedback_preserves_all_generated_outcomes():
    module = load_writer("feedback-bump")
    rows = fixture()["maintenance"]["ledger"]
    result = module.bucket_entries(rows)
    assert set(result["by_outcome"]) == {row["outcome"] for row in rows}
    assert {row["outcome"] for row in result["open_questions"] if "outcome" in row} == {
        "coverage_gap", "fallback_used", "unverifiable", "transport_error",
        "auth_failed", "quota_exceeded", "content_invalid"}


def test_writer_reader_and_generated_schema_share_the_published_vocabulary():
    import incident_helper
    import ledger_schema
    from live_run_contract import VALID_OUTCOMES
    assert set(ledger_schema.OUTCOMES) == VALID_OUTCOMES
    assert set(ledger_schema.schema()["properties"]["outcome"]["enum"]) == VALID_OUTCOMES
    for row in fixture()["maintenance"]["ledger"]:
        incident_helper._validate_incident({"slug": "synthetic-tool", "outcome": row["outcome"],
                                           "detail": row["detail"], "domain": "finance-markets",
                                           "d_code": "none"})



@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_preserves_substituted_parent(monkeypatch, failed, companion):
    parent, held, other = (companion / name for name in (".staging", "held", "other"))
    parent.mkdir()
    other.mkdir()
    target = parent / "ledger.jsonl"
    selected = storage.Destination(target, companion)
    lock = storage._update_lock_path(selected)
    sentinel = other / lock.name
    sentinel.write_bytes(b"Synthetic unrelated lock\n")
    real_open, real_close = storage.os.open, storage.os.close
    observed = {}
    def open_lock(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == lock.name:
            observed["descriptor"] = descriptor
        return descriptor
    def close_lock(descriptor):
        real_close(descriptor)
        if descriptor == observed.get("descriptor"):
            parent.rename(held)
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(other), str(parent))
            else:
                parent.symlink_to(other, target_is_directory=True)
            observed["substituted"] = True
    monkeypatch.setattr(storage.os, "open", open_lock)
    if real_open in os.supports_dir_fd:
        monkeypatch.setattr(storage.os, "supports_dir_fd", os.supports_dir_fd | {open_lock})
    monkeypatch.setattr(storage.os, "close", close_lock)
    if failed:
        with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
            with storage._exclusive_update(selected):
                raise storage.InventoryError("Synthetic transaction failure")
    else:
        with storage._exclusive_update(selected):
            pass
    assert observed.get("substituted") is True
    assert sentinel.read_bytes() == b"Synthetic unrelated lock\n"
    assert not (held / lock.name).exists()


@pytest.mark.parametrize("case", ["ordinary", "handled-outer", "failed-current"])
def test_native_lock_close_failure_tracks_current_transaction(monkeypatch, capsys, case, companion):
    selected = storage.Destination(companion / "ledger.jsonl", companion)
    lock = storage._update_lock_path(selected)
    real_open, real_close = storage.os.open, storage.os.close
    observed = {}
    def open_lock(path, flags, *args, **kwargs):
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == lock.name:
            observed["descriptor"] = descriptor
        return descriptor
    def fail_close(descriptor):
        if descriptor == observed.get("descriptor"):
            raise OSError("Synthetic owned descriptor close failure")
        real_close(descriptor)
    monkeypatch.setattr(storage.os, "open", open_lock)
    if real_open in os.supports_dir_fd:
        monkeypatch.setattr(storage.os, "supports_dir_fd", os.supports_dir_fd | {open_lock})
    monkeypatch.setattr(storage.os, "close", fail_close)
    def transaction():
        with storage._exclusive_update(selected):
            if case == "failed-current":
                raise storage.InventoryError("Synthetic primary transaction failure")
    try:
        if case == "handled-outer":
            try:
                raise ValueError("Synthetic already handled outer error")
            except ValueError:
                with pytest.raises(storage.InventoryError, match="cleanup refused"):
                    transaction()
        else:
            expected = "primary transaction failure" if case == "failed-current" else "cleanup refused"
            with pytest.raises(storage.InventoryError, match=expected):
                transaction()
        if case == "failed-current":
            assert "cleanup refused" in capsys.readouterr().err
    finally:
        if "descriptor" in observed:
            real_close(observed["descriptor"])
    assert not lock.exists()


def test_native_lock_repeated_acquisition_and_failure_recovery(companion):
    selected = storage.Destination(companion / "ledger.jsonl", companion)
    lock = storage._update_lock_path(selected)
    for unused in range(2):
        with storage._exclusive_update(selected):
            with pytest.raises(storage.InventoryError, match="lock is busy"):
                with storage._exclusive_update(selected, timeout=0):
                    pytest.fail("A concurrent acquisition must not enter")
        assert not lock.exists()
    with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
        with storage._exclusive_update(selected):
            raise storage.InventoryError("Synthetic transaction failure")
    assert not lock.exists()
    with storage._exclusive_update(selected):
        pass
    assert not lock.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor contract")
@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_anchors_parent_during_transaction(failed, companion):
    parent, held = (companion / name for name in (".staging", "held"))
    parent.mkdir()
    selected = storage.Destination(parent / "ledger.jsonl", companion)
    lock = storage._update_lock_path(selected)
    def transaction():
        with storage._exclusive_update(selected):
            parent.rename(held)
            parent.mkdir()
            lock.write_bytes(b"Synthetic unrelated lock\n")
            if failed:
                raise storage.InventoryError("Synthetic transaction failure")
    if failed:
        with pytest.raises(storage.InventoryError, match="Synthetic transaction failure"):
            transaction()
    else:
        transaction()
    assert lock.read_bytes() == b"Synthetic unrelated lock\n"
    assert not (held / lock.name).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory descriptor contract")
@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_refuses_replaced_entry(capsys, failed, companion):
    selected = storage.Destination(companion / "ledger.jsonl", companion)
    lock, held = storage._update_lock_path(selected), companion / "held-lock"
    message = "Synthetic transaction failure" if failed else "cleanup refused"
    with pytest.raises(storage.InventoryError, match=message):
        with storage._exclusive_update(selected):
            lock.rename(held)
            lock.write_bytes(b"Synthetic unrelated lock\n")
            if failed:
                raise storage.InventoryError("Synthetic transaction failure")
    assert lock.read_bytes() == b"Synthetic unrelated lock\n"
    assert held.is_file()
    if failed:
        assert "cleanup refused" in capsys.readouterr().err
