"""Generated first-use and input-boundary regressions using synthetic records."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import check_all
import console
import incident_helper as incident
import test_check_all as registration
from test_private_writers import companion

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULES = sorted(path.name for directory in ("tools", "tests")
                      for path in (ROOT / directory).glob("test_*.py"))
INCIDENT = {"slug": "synthetic-tool", "outcome": "dead", "detail": "Synthetic endpoint is gone.",
            "domain": "finance-markets", "d_code": "D-404"}
INVALID_DOMAINS = ["../synthetic-private-note", "/synthetic-private-note",
                   r"C:\synthetic-private-note", "nested/synthetic-note",
                   r"nested\synthetic-note", "unknown-domain", "", None, 0, [], {}]


def config_script(name):
    import importlib.util
    source = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("synthetic_config_" + source.stem, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def populate_config(directory):
    from make_fixtures import configured_doctor_files
    for relative, content in configured_doctor_files().items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


@pytest.mark.parametrize("relative", ["registry.json", ".gitignore", "tools/.gitkeep",
                                       "secrets/README.md", "secrets/.gitkeep"])
@pytest.mark.parametrize("force,linked", [(False, True), (True, True), (True, False)])
def test_initializer_preflights_every_output_before_mutation(tmp_path, monkeypatch, relative, force, linked):
    import sys
    outside = tmp_path / "synthetic-outside"
    retained = b"Synthetic retained bytes\n"
    outside.write_bytes(retained)
    directory = tmp_path / "configuration"
    target = directory / relative
    target.parent.mkdir(parents=True)
    if linked:
        os.link(outside, target)
    else:
        target.write_bytes(retained)
    before = {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
              for path in directory.rglob("*")}
    args = ["init_config.py", "--skill", "synthetic-skill", "--out", str(directory)]
    monkeypatch.setattr(sys, "argv", args + (["--force"] if force else []))
    result = config_script("init_config.py").main()
    assert outside.read_bytes() == retained
    if linked:
        assert result != 0
        after = {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
                 for path in directory.rglob("*")}
        assert after == before, "all output paths must be checked before any output is changed"
    else:
        assert result == 0 and target.read_bytes() != retained
        assert json.loads((directory / "registry.json").read_text()) == {"schema_version": 1, "tools": []}


@pytest.mark.parametrize("mode", ["A", "B"])
def test_config_doctor_honors_declared_storage_mode(tmp_path, monkeypatch, mode):
    import sys
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill", "--out", str(tmp_path)])
    assert config_script("init_config.py").main() == 0
    populate_config(tmp_path)
    if mode == "A":
        (tmp_path / ".gitignore").write_text("# Mode A: private credential backup\n", encoding="utf-8")
        (tmp_path / "secrets/README.md").write_text("Active storage mode: A. Synthetic private fixture.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_config.py", "--skill", "synthetic-skill", "--config-dir", str(tmp_path)])
    assert config_script("verify_config.py").main() == 0


@pytest.mark.parametrize("declaration,ignored,accepted", [
    ("Active storage mode: **A**", False, True),
    ("Active storage mode: C", True, False),
    ("Active storage mode: A\nActive storage mode: B", True, False),
    ("Active storage mode: B", False, False),
    ("Synthetic legacy configuration", True, True),
    ("Synthetic legacy configuration", False, False),
])
def test_config_doctor_applies_explicit_and_legacy_policy(
        tmp_path, monkeypatch, declaration, ignored, accepted):
    import sys
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill", "--out", str(tmp_path)])
    assert config_script("init_config.py").main() == 0
    populate_config(tmp_path)
    (tmp_path / "secrets/README.md").write_text(declaration + "\n", encoding="utf-8")
    if not ignored:
        (tmp_path / ".gitignore").write_text("# Synthetic unexcluded configuration\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["verify_config.py", "--skill", "synthetic-skill", "--config-dir", str(tmp_path)])
    assert (config_script("verify_config.py").main() == 0) is accepted


def document_writer(writer, directory, monkeypatch):
    from test_private_writers import load_writer
    if writer == "incident":
        monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
        return "web-scraping", lambda: incident.apply_shard_edit(
            "web-scraping", "Synthetic old row", "Synthetic new row")
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", directory)
    return "example-source", lambda: feedback.bump_last_verified({"example-source": "2020-01-01"})


def native_junction(target, alias):
    try:
        import _winapi
        create = _winapi.CreateJunction
    except (ImportError, AttributeError):
        pytest.skip("native Windows directory junctions unavailable")
    try:
        create(str(target), str(alias))
    except OSError as exc:
        pytest.skip(f"native Windows directory junctions unavailable: {exc}")


@pytest.mark.parametrize("writer", ["incident", "feedback"])
def test_document_writers_reject_native_junction_before_read(tmp_path, monkeypatch, writer):
    directory = tmp_path / "docs"
    outside = tmp_path / "outside"
    outside.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = outside / (slug + ".md")
    before = b"## Last verified: 2019-01\nSynthetic old row\n"
    target.write_bytes(before)
    native_junction(outside, directory)
    with patch.object(Path, "open", side_effect=AssertionError("aliased document was opened")), \
            patch("builtins.open", side_effect=AssertionError("aliased document was opened")):
        with pytest.raises(ValueError):
            write()
    assert target.read_bytes() == before
    assert sorted(path.name for path in outside.iterdir()) == [target.name]


@pytest.mark.parametrize("position", ["root", "parent"])
def test_initializer_rejects_native_junction_before_mutation(tmp_path, monkeypatch, position):
    import sys
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "synthetic-retained.txt"
    sentinel.write_bytes(b"Synthetic retained bytes\n")
    directory = tmp_path / "configuration"
    alias = directory
    if position == "parent":
        directory.mkdir()
        alias = directory / "secrets"
    native_junction(outside, alias)
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill",
                                     "--out", str(directory), "--force"])
    assert config_script("init_config.py").main() != 0
    assert sorted(path.name for path in outside.iterdir()) == [sentinel.name]
    assert sentinel.read_bytes() == b"Synthetic retained bytes\n"
    if position == "parent":
        assert list(directory.iterdir()) == [alias]


def test_initializer_atomic_replace_failure_preserves_prior_file(tmp_path, monkeypatch):
    import sys
    before = b"Synthetic retained registry\n"
    target = tmp_path / "registry.json"
    target.write_bytes(before)
    def fail_replace(*_args):
        raise OSError("Synthetic replace failure")
    monkeypatch.setattr(os, "replace", fail_replace)
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--skill", "synthetic-skill",
                                     "--out", str(tmp_path), "--force"])
    assert config_script("init_config.py").main() != 0
    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("writer", ["incident", "feedback"])
@pytest.mark.parametrize("alias", ["regular", "hardlink", "symlink"])
def test_document_writers_reject_aliases_before_reading(tmp_path, monkeypatch, writer, alias):
    before = b"# Synthetic tool\n\n## Last verified: 2019-01\n\nSynthetic old row\n"
    outside = tmp_path / "outside.md"
    outside.write_bytes(before)
    directory = tmp_path / "docs"
    directory.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = directory / (slug + ".md")
    if alias == "hardlink":
        os.link(outside, target)
    elif alias == "symlink":
        try:
            target.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"native symlinks unavailable: {exc}")
    else:
        target.write_bytes(before)
    if alias == "regular":
        write()
        assert target.read_bytes() != before
    else:
        with patch.object(Path, "open", side_effect=AssertionError("aliased document was opened")), \
                patch("builtins.open", side_effect=AssertionError("aliased document was opened")):
            with pytest.raises(ValueError):
                write()
        assert target.read_bytes() == before
    assert outside.read_bytes() == before
    assert sorted(path.name for path in directory.iterdir()) == [target.name]


@pytest.mark.parametrize("writer", ["incident", "feedback"])
@pytest.mark.parametrize("change", ["hardlink", "content", "replacement", "replace-failure"])
def test_document_writers_recheck_before_atomic_replace(tmp_path, monkeypatch, writer, change):
    directory = tmp_path / "docs"
    directory.mkdir()
    slug, write = document_writer(writer, directory, monkeypatch)
    target = directory / (slug + ".md")
    before = b"## Last verified: 2019-01\nSynthetic old row\n"
    replacement = before if change == "replacement" else b"Synthetic concurrent edit\n"
    target.write_bytes(before)
    outside = tmp_path / "outside.md"
    outside.write_bytes(replacement)
    original_fsync = os.fsync
    reached = []
    def change_after_flush(descriptor):
        original_fsync(descriptor)
        reached.append(True)
        if change == "hardlink":
            target.unlink()
            os.link(outside, target)
        elif change == "replacement":
            candidate = tmp_path / "replacement.md"
            candidate.write_bytes(replacement)
            os.replace(candidate, target)
        elif change == "content":
            target.write_bytes(replacement)
    monkeypatch.setattr(os, "fsync", change_after_flush)
    if change == "replace-failure":
        def fail_replace(*_args):
            raise OSError("Synthetic replacement failure")
        monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises((ValueError, OSError)):
        write()
    assert reached == [True]
    assert outside.read_bytes() == replacement
    assert target.read_bytes() == (before if change == "replace-failure" else replacement)
    assert sorted(path.name for path in directory.iterdir()) == [target.name]


@pytest.mark.parametrize("timestamp", ["2020-01-01", "2099-01-01"])
def test_future_feedback_is_visible_without_bumping(tmp_path, monkeypatch, capsys, timestamp):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    doc = tmp_path / "example-source.md"
    before = "## Last verified: 2019-01\n"
    doc.write_text(before, encoding="utf-8")
    row = dict(feedback_cases()["documentation_verified"][0], ts=timestamp, domain="")
    ledger = tmp_path / "synthetic.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    entries = feedback.load_live_runs(ledger, "2019-01-01")
    assert entries == [row], "future observations must remain visible, not be discarded"
    buckets = feedback.bucket_entries(entries)
    monkeypatch.setattr(feedback, "live_runs_path", lambda: ledger)
    status = feedback.main(["--mode", "bump", "--since", "2019-01-01"])
    if timestamp.startswith("2099"):
        assert buckets["auto_bump_slugs"] == {}
        assert buckets["timestamp_issues"][0]["reason"] == "future_timestamp"
        assert status == 1 and "timestamp" in capsys.readouterr().out.lower()
        assert doc.read_text(encoding="utf-8") == before
        results = feedback.bump_last_verified({"example-source": timestamp})
        assert results[0]["status"] == "review_required"
        assert doc.read_text(encoding="utf-8") == before
    else:
        assert status == 0
        assert "## Last verified: 2020-01" in doc.read_text(encoding="utf-8")


def test_feedback_orders_timestamps_as_instants_and_uses_utc_month(tmp_path, monkeypatch):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    earlier = "2020-03-01T00:30:00+02:00"
    later = "2020-02-29T23:00:00Z"
    row = feedback_cases()["documentation_verified"][0]
    for order in ([earlier, later], [later, earlier]):
        buckets = feedback.bucket_entries([dict(row, ts=stamp) for stamp in order])
        assert buckets["auto_bump_slugs"] == {"example-source": later}
    doc = tmp_path / "example-source.md"
    doc.write_text("## Last verified: 2019-01\n", encoding="utf-8")
    result = feedback.bump_last_verified({"example-source": earlier})
    assert result[0]["new"] == "2020-02"
    assert "## Last verified: 2020-02" in doc.read_text(encoding="utf-8")


@pytest.mark.parametrize("timestamp", ["0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"])
def test_feedback_out_of_range_utc_instants_require_review(tmp_path, monkeypatch, timestamp):
    from make_fixtures import feedback_cases
    from test_private_writers import load_writer
    feedback = load_writer("feedback-bump")
    monkeypatch.setattr(feedback, "TOOLS_DIR", tmp_path)
    monkeypatch.setattr(feedback, "_TOOL_SLUGS_CACHE", ["example-source"])
    row = dict(feedback_cases()["documentation_verified"][0], ts=timestamp)
    ledger = tmp_path / "synthetic.jsonl"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    entries = feedback.load_live_runs(ledger, "2019-01-01")
    assert len(entries) == 1 and entries[0]["outcome"] == "invalid_record"
    buckets = feedback.bucket_entries([row])
    assert buckets["timestamp_issues"][0]["reason"] == "invalid_timestamp"
    assert buckets["auto_bump_slugs"] == {}
    result = feedback.bump_last_verified({"example-source": timestamp})
    assert result[0]["status"] == "review_required"


def test_requests_is_a_direct_runtime_dependency():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert any(re.match(r"requests(?:[<=>!~;\[\s]|$)", line.strip(), re.I)
               for line in requirements if not line.lstrip().startswith("#"))
    development = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert re.search(r"(?m)^\s*-r\s+requirements\.txt\s*$", development)


@pytest.mark.parametrize("selection", ["MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR",
                                       "MARKET_INTEL_DATA_DIR"])
@pytest.mark.parametrize("with_registry", [False, True])
@pytest.mark.parametrize("nested_data", [False, True])
def test_refresh_reads_only_its_selected_companion(
        selection, with_registry, nested_data, companion, tmp_path, monkeypatch):
    selected, _, _, _ = companion
    other = tmp_path / ".market-intel-config"
    other.mkdir()
    other_registry = other / "registry.json"
    other_bytes = b'{"tools":[{"slug":"synthetic-other","installed":true}]}\n'
    other_registry.write_bytes(other_bytes)
    if with_registry:
        (selected / "registry.json").write_text(
            '{"tools":[{"slug":"synthetic-selected","installed":true}]}\n', encoding="utf-8")
    data = selected / "data" if nested_data else selected
    if nested_data:
        data.mkdir(exist_ok=True)
    else:
        (selected / "data").rmdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR", "MARKET_INTEL_DATA_DIR"):
        monkeypatch.delenv(key, raising=False)
    if selection == "MARKET_INTEL_DATA_DIR":
        monkeypatch.setenv("MARKET_INTEL_CONFIG", str(other))
        monkeypatch.setenv(selection, str(data))
    else:
        monkeypatch.setenv(selection, str(selected))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    original_expanduser = os.path.expanduser
    monkeypatch.setattr(os.path, "expanduser",
                        lambda value: str(tmp_path) if value == "~" else original_expanduser(value))
    for probe in ("probe_mcp", "probe_clis", "probe_python_modules"):
        monkeypatch.setattr(console, probe, lambda: {})
    reads = []
    original_read = console.read_json
    def read(path, default=None):
        reads.append(Path(path))
        assert Path(path) == selected / "registry.json"
        return original_read(path, default=default)
    monkeypatch.setattr(console, "read_json", read)
    if not nested_data or selection == "MARKET_INTEL_DATA_DIR":
        # A missing canonical data/ or conflicting config override must fail before collection.
        with pytest.raises(console.private_inventory.InventoryError):
            console.load_snapshot(refresh=True)
        assert reads == []
        assert other_registry.read_bytes() == other_bytes
        return
    snapshot, status = console.load_snapshot(refresh=True)
    collected = snapshot["companion"]
    assert collected["path"] == str(selected)
    assert collected["present"] is with_registry
    assert set(collected["tools"]) == ({"synthetic-selected"} if with_registry else set())
    assert reads == ([selected / "registry.json"] if with_registry else [])
    assert json.loads((data / "inventory/availability-cache.json").read_text(encoding="utf-8")) == snapshot
    assert "PRIVATE companion" in status
    assert other_registry.read_bytes() == other_bytes
    assert not (other / "inventory").exists()


@pytest.mark.parametrize("removed", TEST_MODULES)
def test_registration_detects_each_missing_test_module(removed, monkeypatch, capsys):
    altered = dict(check_all.MANIFEST)
    assert removed in altered
    del altered[removed]
    candidate = SimpleNamespace(MANIFEST=altered, EXCLUDED=dict(check_all.EXCLUDED),
                                checker_path=check_all.checker_path)
    monkeypatch.setattr(registration, "load", lambda: candidate)
    registration.failures.clear()
    try:
        if removed == "test_console.py":
            with pytest.raises(KeyError, match="test_console.py"):
                registration.main()
        else:
            assert registration.main() == 1
        assert "every checker in tools/ is registered in MANIFEST or EXCLUDED" in registration.failures
        assert removed in capsys.readouterr().out
    finally:
        registration.failures.clear()


def test_unified_runner_executes_all_required_test_modules(monkeypatch):
    executed = []
    monkeypatch.setattr(check_all.sys, "argv", ["check_all.py"])
    monkeypatch.setattr(check_all, "run", lambda name, args: executed.append(name) or 0)
    assert check_all.main() == 0
    assert set(TEST_MODULES) <= set(executed)
    assert "test_verification_contract.py" in executed
    assert all(check_all.MANIFEST[name][2] for name in TEST_MODULES)


@pytest.mark.parametrize("domain", INVALID_DOMAINS)
def test_incident_rejects_invalid_model_domain_before_followups(domain, monkeypatch, capsys):
    data = dict(INCIDENT, domain=domain)
    model = SimpleNamespace(data=data)
    with patch.object(incident, "_llmcall", return_value=model) as parse, \
            patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected follow-up")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file read")):
        with pytest.raises(SystemExit) as exc:
            incident.parse_incident("Synthetic incident.")
        assert exc.value.code == 1 and parse.call_count == 1
        assert incident.run(data, apply=True) == 1
        assert parse.call_count == 1
    assert "invalid incident" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["slug", "outcome", "detail", "domain", "d_code"])
@pytest.mark.parametrize("value", [None, 1, [], {}])
def test_incident_rejects_wrong_field_types_before_drafting(field, value, monkeypatch):
    data = dict(INCIDENT)
    data[field] = value
    with patch.object(incident, "_llmcall", side_effect=AssertionError("unexpected model")), \
            patch.object(incident, "_prompt_yn", side_effect=AssertionError("unexpected prompt")), \
            patch.object(incident, "apply_live_runs_append", side_effect=AssertionError("unexpected append")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        assert incident.run(data, apply=True) == 1


@pytest.mark.parametrize("domain", INVALID_DOMAINS)
def test_both_shard_helpers_reject_invalid_domain_before_any_io(domain):
    with patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected model")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        with pytest.raises(ValueError, match="domain"):
            incident.suggest_shard_edit("synthetic-tool", "D-404", domain, "Synthetic evidence.")
        with pytest.raises(ValueError, match="domain"):
            incident.suggest_shard_edit("synthetic-tool", "none", domain, "Synthetic evidence.")
        with pytest.raises(ValueError, match="domain"):
            incident.apply_shard_edit(domain, "Synthetic before", "Synthetic after")


@pytest.mark.parametrize("operation", ["suggest", "apply"])
def test_shard_helpers_reject_canonical_escape(operation, tmp_path, monkeypatch):
    directory = tmp_path / "domains"
    directory.mkdir()
    shard = directory / "finance-markets.md"
    shard.write_text("Synthetic original\n", encoding="utf-8")
    outside = tmp_path / "synthetic-private-note.md"
    original = b"Synthetic outside content\n"
    outside.write_bytes(original)
    monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
    realpath = os.path.realpath
    def canonical(path):
        return str(outside) if os.fspath(path) == str(shard) else realpath(path)
    monkeypatch.setattr(os.path, "realpath", canonical)
    with patch.object(incident, "_run_claude", side_effect=AssertionError("unexpected model")), \
            patch("builtins.open", side_effect=AssertionError("unexpected file access")):
        with pytest.raises(ValueError, match="outside"):
            if operation == "suggest":
                incident.suggest_shard_edit("synthetic-tool", "D-404", "finance-markets", "Synthetic.")
            else:
                incident.apply_shard_edit("finance-markets", "Synthetic", "Changed")
    assert outside.read_bytes() == original
    assert shard.read_text(encoding="utf-8") == "Synthetic original\n"


def test_valid_incident_preserves_draft_and_explicit_apply(tmp_path, monkeypatch):
    directory = tmp_path / "domains"
    directory.mkdir()
    shard = directory / "finance-markets.md"
    before, after = "| synthetic-tool | usable |", "| synthetic-tool | retired |"
    shard.write_text(before + "\n", encoding="utf-8")
    index = tmp_path / "sources-index.md"
    index.write_text("Synthetic index\n", encoding="utf-8")
    monkeypatch.setattr(incident, "DOMAINS_DIR", str(directory))
    monkeypatch.setattr(incident, "SOURCES_INDEX", str(index))
    model_inputs = []
    def draft(prompt, stdin_payload=None):
        model_inputs.append((prompt, stdin_payload))
        return f"FROM:\n{before}\nTO:\n{after}\nNOTES:\nSynthetic review." if stdin_payload else "Synthetic commit draft"
    monkeypatch.setattr(incident, "_run_claude", draft)
    appended = []
    monkeypatch.setattr(incident, "apply_live_runs_append", appended.append)
    monkeypatch.setattr(incident, "_prompt_yn", lambda prompt: True)
    assert incident.run(deepcopy(INCIDENT), apply=False) == 0
    assert shard.read_text(encoding="utf-8") == before + "\n"
    assert appended == []
    assert incident.run(deepcopy(INCIDENT), apply=True) == 0
    assert shard.read_text(encoding="utf-8") == after + "\n"
    assert len(appended) == 1 and json.loads(appended[0])["source"] == "shard/" + INCIDENT["slug"]
    assert [body for _, body in model_inputs if body is not None] == [before + "\n", before + "\n"]
