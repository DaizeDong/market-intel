"""Generated synthetic destination and concurrent-writer regressions; no live calls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import private_inventory as storage
from make_fixtures import (
    fixture, make_runtime_fixture, make_runtime_repository,
    runtime_transport_cases, runtime_visibility_cases,
)

SAMPLE = fixture()["maintenance"]


@dataclass(frozen=True)
class SyntheticProof:
    root: str
    repositories: tuple
    signature: str


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


@pytest.mark.parametrize("label,remote,configuration,environment,accepted", runtime_transport_cases())
def test_native_private_proof_rejects_unsafe_transport(
        native_companion, monkeypatch, label, remote, configuration, environment, accepted):
    repository = native_companion["repository"]
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin", remote], check=True)
    for key, value in configuration.items():
        subprocess.run(["git", "-C", str(repository), "config", key, value], check=True)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    original_run = subprocess.run
    forbidden = []

    def local_only(command, *args, **kwargs):
        if command[0] == "git":
            return original_run(command, *args, **kwargs)
        forbidden.append(command[0])
        if command[0] == "gh":
            return subprocess.CompletedProcess(command, 0, json.dumps(
                {"nameWithOwner": SAMPLE["companion_identity"], "visibility": "PRIVATE"}), "")
        if command[0] == "ssh":
            return subprocess.CompletedProcess(command, 0, "hostname github.com\n", "")
        pytest.fail("a transport command was executed")

    monkeypatch.setattr(subprocess, "run", local_only)
    if accepted:
        destination = storage.resolve_destination()
        assert destination.repository == repository
    else:
        with pytest.raises(storage.InventoryError):
            storage.resolve_destination()
    assert forbidden == [], "fresh synthetic receipts require only local Git metadata reads"
    assert not (repository / "data/inventory").exists()


@pytest.mark.parametrize("identity,accepted", [
    (SAMPLE["other_identity"], True), (SAMPLE["public_identity"], False),
    ("example/unknown", False),
])
def test_native_nested_repository_is_authoritative(native_companion, identity, accepted):
    repository = native_companion["repository"]
    assert storage.resolve_directory(path=repository).repository == repository
    nested = make_runtime_repository(repository / "runtime", native_companion["environment"], identity)
    if accepted:
        selected = storage.resolve_directory(path=nested)
        assert selected.repository == nested and selected.identity == identity
    else:
        with pytest.raises(storage.InventoryError):
            storage.resolve_directory(path=nested)
    assert not (nested / "inventory").exists()


@pytest.mark.parametrize("failure", ["ignored", "unversioned"])
def test_native_storage_requirements_are_preserved(native_companion, failure):
    repository = native_companion["repository"]
    target = repository / "ignored-output/record.json" if failure == "ignored" else repository / "data/deliverables/report.json"
    if failure == "unversioned":
        subprocess.run(["git", "-C", str(repository), "update-ref", "-d", "HEAD"], check=True)
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination(path=target)
    assert not target.exists()


@pytest.mark.parametrize("change", ["stable", "public", "other-private", "same-identity-url", "lexical-target"])
def test_native_publication_rechecked_before_replace(native_companion, monkeypatch, change):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/synthetic.json"
    target.parent.mkdir(parents=True)
    before, after = "Synthetic retained bytes\n", "Synthetic replacement bytes\n"
    target.write_text(before, encoding="utf-8")
    lexical = repository / "data/deliverables/reports/selected.json"
    selected_path = [target]
    if change == "lexical-target":
        original_resolve = Path.resolve
        monkeypatch.setattr(Path, "resolve", lambda path, *a, **k:
                            selected_path[0] if path == lexical else original_resolve(path, *a, **k))
    selected = storage.resolve_destination(path=lexical if change == "lexical-target" else target)
    real_fsync = os.fsync
    def change_after_flush(descriptor):
        real_fsync(descriptor)
        identity = {"public": SAMPLE["public_identity"], "other-private": SAMPLE["other_identity"],
                    "same-identity-url": SAMPLE["companion_identity"]}.get(change)
        if identity:
            suffix = "" if change == "same-identity-url" else ".git"
            subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin",
                            "https://github.com/" + identity + suffix], check=True)
        elif change == "lexical-target":
            selected_path[0] = repository / "data/deliverables/reports/other.json"
    monkeypatch.setattr(os, "fsync", change_after_flush)
    if change == "stable":
        storage.write_text(after, "reports/synthetic.json", selected)
        assert target.read_text(encoding="utf-8") == after
    else:
        with pytest.raises(storage.InventoryError):
            storage.write_text(after, "reports/synthetic.json", selected)
        assert target.read_text(encoding="utf-8") == before
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == (0 if change == "stable" else 1)
    if pending:
        assert pending[0].read_text(encoding="utf-8") == after
    assert not (target.parent / "other.json").exists()


def test_native_same_identity_route_change_is_revalidated(native_companion):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/result.json"
    selected = storage.resolve_destination(path=target)
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin",
                    "https://github.com/" + SAMPLE["companion_identity"]], check=True)
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_text("{}\n", "reports/result.json", selected)
    assert not target.parent.exists()


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


def test_native_effective_git_rewrite_cannot_hide_physical_public_route(native_companion, monkeypatch):
    repository = native_companion["repository"]
    public = "https://github.com/" + SAMPLE["public_identity"] + ".git"
    private = "https://github.com/" + SAMPLE["companion_identity"] + ".git"
    subprocess.run(["git", "-C", str(repository), "remote", "set-url", "origin", public], check=True)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url." + private + ".insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", public)
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()
    assert not (repository / "data/inventory").exists()


@pytest.mark.parametrize("label,payload", runtime_visibility_cases())
def test_native_invalid_visibility_receipt_refuses_before_writes(native_companion, label, payload):
    native_companion["receipt"].write_text(payload, encoding="utf-8")
    with pytest.raises(storage.InventoryError, match="visibility"):
        storage.resolve_destination()
    assert not (native_companion["repository"] / "inventory").exists()


@pytest.fixture
def companion(tmp_path, monkeypatch):
    repository = tmp_path / "companion"
    (repository / ".git").mkdir(parents=True)
    (repository / "data").mkdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(repository / "data"))
    routes = {"origin": {"fetch": [SAMPLE["companion_identity"]],
                          "push": [SAMPLE["companion_identity"]]}}
    visibility = {SAMPLE["companion_identity"]: "PRIVATE", SAMPLE["other_identity"]: "PRIVATE",
                  SAMPLE["public_identity"]: "PUBLIC"}
    configuration = []

    class ProofError(RuntimeError):
        pass

    def prove(directory):
        if not Path(directory).is_relative_to(repository):
            raise ProofError("synthetic unmanaged directory")
        if any(line.split(None, 1)[1] not in routes for line in configuration):
            raise ProofError("synthetic missing publication remote")
        identities = sorted({identity for route in routes.values()
                             for values in route.values() for identity in values})
        if any(visibility.get(identity) != "PRIVATE" for identity in identities):
            raise ProofError("synthetic PUBLIC or UNKNOWN visibility")
        return SyntheticProof(str(repository), tuple(identities), json.dumps([routes, configuration], sort_keys=True))

    def read(proof, *arguments):
        if arguments == ("rev-parse", "--verify", "HEAD"):
            return subprocess.CompletedProcess(arguments, 0, "1" * 40, "")
        if arguments[:4] == ("check-ignore", "--no-index", "-q", "--"):
            return subprocess.CompletedProcess(arguments, 1, "", "")
        raise AssertionError(arguments)

    boundary = SimpleNamespace(prove_private_companion=prove, read_private_companion_git=read, GitError=ProofError)
    monkeypatch.setattr(storage, "_shared_boundary", lambda: boundary)
    contract_boundary = SimpleNamespace(prove_private_companion=lambda directory, *_: prove(directory),
                                        read_private_companion_git=read, GitError=ProofError)
    monkeypatch.setattr(storage._storage_contract(), "load_boundary", lambda: contract_boundary)
    return repository, routes, visibility, configuration


@pytest.mark.parametrize("visibility", ["PUBLIC", "UNKNOWN"])
def test_every_effective_push_destination_must_be_private(companion, visibility):
    repository, routes, states, _ = companion
    routes["origin"]["push"].append(SAMPLE["public_identity"])
    states[SAMPLE["public_identity"]] = visibility
    with pytest.raises(storage.InventoryError, match="visibility"):
        storage.resolve_destination()
    assert set(repository.iterdir()) == {repository / ".git", repository / "data"}


def test_all_remotes_and_configured_push_remotes_are_verified(companion):
    _, routes, _, configuration = companion
    routes["publish"] = {"fetch": [SAMPLE["other_identity"]], "push": [SAMPLE["public_identity"]]}
    configuration.append("remote.pushdefault publish")
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()
    routes["publish"]["push"] = [SAMPLE["other_identity"]]
    destination = storage.resolve_destination()
    assert set(destination.identity.split(", ")) == {SAMPLE["companion_identity"], SAMPLE["other_identity"]}
    configuration[:] = ["branch.main.pushremote absent-remote"]
    with pytest.raises(storage.InventoryError):
        storage.resolve_destination()


def test_publication_route_change_is_rechecked_before_write(companion):
    repository, routes, _, _ = companion
    selected = storage.resolve_destination()
    routes["origin"]["push"] = [SAMPLE["other_identity"]]
    with pytest.raises(storage.InventoryError, match="changed"):
        storage.write_snapshot(fixture()["inventory"], selected)
    assert not (repository / "data/inventory").exists()


def test_explicit_destinations_use_final_private_repository(companion, tmp_path):
    repository, _, _, _ = companion
    selected = storage.resolve_destination("reports/feedback.json", path=repository / "data/deliverables/reports/result.json")
    storage.write_text("synthetic\n", "reports/feedback.json", selected)
    assert selected.path.read_text() == "synthetic\n"
    for target in (storage.ROOT / "inventory/research.json", tmp_path / "unmanaged/result.json"):
        with pytest.raises(storage.InventoryError):
            storage.resolve_destination("reports/feedback.json", path=target)


def test_serialized_updates_preserve_both_generated_rows(companion):
    repository, _, _, _ = companion
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
def test_writers_persist_only_to_verified_private_override(name, companion, monkeypatch):
    repository, _, _, _ = companion
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
    repository, _, _, _ = companion
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


def test_temporary_cleanup_refuses_replaced_directory_junction(native_companion, monkeypatch, capsys):
    repository = native_companion["repository"]
    reports = repository / ".staging"
    reports.mkdir(parents=True)
    target = repository / "data/deliverables/result.json"
    target.parent.mkdir(parents=True)
    before = json.dumps(fixture()["inventory"], sort_keys=True).encode()
    target.write_bytes(before)
    other = make_runtime_repository(repository.parent / "other", native_companion["environment"], SAMPLE["other_identity"])
    selected = storage.resolve_destination(path=target)
    original = storage._revalidate
    calls, observed = [], {}
    def changed(relative, destination):
        calls.append(relative)
        if len(calls) == 2:
            pending, = (repository / ".staging").glob("inventory-*.tmp")
            held = repository / "held-reports"
            assert reports.resolve().is_relative_to(repository.parent.resolve())
            assert held.absolute().is_relative_to(repository.parent.resolve())
            reports.rename(held)
            sentinel = other / pending.name
            sentinel.write_bytes(before)
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(str(other), str(reports))
            else:
                reports.symlink_to(other, target_is_directory=True)
            observed.update(sentinel=sentinel, held=held, temporary=pending.name)
        return original(relative, destination)
    monkeypatch.setattr(storage, "_revalidate", changed)
    with pytest.raises(storage.InventoryError):
        storage.write_text("Synthetic replacement\n", "reports/result.json", selected)
    assert observed["sentinel"].read_bytes() == before
    assert target.read_bytes() == before
    assert (observed["held"] / observed["temporary"]).is_file()
    assert "cleanup refused" in capsys.readouterr().err


def test_temporary_cleanup_refuses_replaced_file(native_companion, monkeypatch, capsys):
    repository = native_companion["repository"]
    target = repository / "data/deliverables/reports/result.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"Synthetic original target\n")
    selected = storage.resolve_destination(path=target)
    original = storage._revalidate
    calls, observed = [], {}
    def changed(relative, destination):
        calls.append(relative)
        if len(calls) == 2:
            pending, = (repository / ".staging").glob("inventory-*.tmp")
            held = target.parent / "held-temporary"
            pending.rename(held)
            pending.write_bytes(b"Synthetic unrelated replacement\n")
            observed.update(pending=pending, held=held)
            # Publication must detect the substituted ordinary file itself.
        return original(relative, destination)
    monkeypatch.setattr(storage, "_revalidate", changed)
    with pytest.raises(storage.InventoryError, match="temporary file changed identity"):
        storage.write_text("Synthetic replacement\n", "reports/result.json", selected)
    assert observed["pending"].read_bytes() == b"Synthetic unrelated replacement\n"
    assert observed["held"].read_text() == "Synthetic replacement\n"
    assert target.read_bytes() == b"Synthetic original target\n"
    assert "cleanup refused" in capsys.readouterr().err



@pytest.mark.parametrize("failed", [False, True])
def test_native_lock_cleanup_preserves_substituted_parent(tmp_path, monkeypatch, failed, companion):
    tmp_path = companion[0]
    parent, held, other = (tmp_path / name for name in (".staging", "held", "other"))
    parent.mkdir()
    other.mkdir()
    target = parent / "ledger.jsonl"
    selected = storage.Destination(target, tmp_path, "example/companion")
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
def test_native_lock_close_failure_tracks_current_transaction(tmp_path, monkeypatch, capsys, case, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
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


def test_native_lock_repeated_acquisition_and_failure_recovery(tmp_path, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
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
def test_native_lock_cleanup_anchors_parent_during_transaction(tmp_path, failed, companion):
    tmp_path = companion[0]
    parent, held = (tmp_path / name for name in (".staging", "held"))
    parent.mkdir()
    selected = storage.Destination(parent / "ledger.jsonl", tmp_path, "example/companion")
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
def test_native_lock_cleanup_refuses_replaced_entry(tmp_path, capsys, failed, companion):
    tmp_path = companion[0]
    selected = storage.Destination(tmp_path / "ledger.jsonl", tmp_path, "example/companion")
    lock, held = storage._update_lock_path(selected), tmp_path / "held-lock"
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
