"""Incident DATA and model boundaries; all records come from synthetic fixtures."""
import json
from unittest.mock import patch

import pytest
import incident_helper
import model_adapter
import private_inventory
from make_fixtures import fixture
from test_private_writers import companion


def test_missing_model_adapter_reports_setup_without_provider_details(monkeypatch, capsys):
    def missing(_name):
        raise ImportError("synthetic credential")
    monkeypatch.setattr(model_adapter.importlib, "import_module", missing)
    with pytest.raises(model_adapter.ModelUnavailable, match="CONFIG.md#model-adapter") as exc:
        model_adapter.call("synthetic prompt")
    assert "synthetic credential" not in str(exc.value)
    assert model_adapter.main(["--check"]) == 3
    assert "UNINITIALIZED" in capsys.readouterr().err


def test_model_adapter_forwards_only_the_callers_options(monkeypatch):
    from types import SimpleNamespace
    calls = []
    reply = object()
    def configured(prompt, **options):
        calls.append((prompt, options))
        return reply
    monkeypatch.setattr(model_adapter.importlib, "import_module",
                        lambda _name: SimpleNamespace(call=configured))
    assert model_adapter.call("synthetic prompt", schema={"type": "object"}) is reply
    assert calls == [("synthetic prompt", {"schema": {"type": "object"}})]


def test_noncallable_model_interface_is_uninitialized(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(model_adapter.importlib, "import_module",
                        lambda _name: SimpleNamespace(call=None))
    with pytest.raises(model_adapter.ModelUnavailable):
        model_adapter.require_call()


def test_missing_adapter_stops_changelog_before_source_reads(monkeypatch, capsys):
    import changelog_draft
    def missing():
        raise model_adapter.ModelUnavailable()
    monkeypatch.setattr(changelog_draft, "require_call", missing)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: pytest.fail("must not read the changelog"))
    assert changelog_draft.main(["--since", "HEAD~1"]) == 3
    assert "UNINITIALIZED" in capsys.readouterr().err


def test_missing_adapter_never_becomes_an_incident_fallback(monkeypatch):
    def missing(*args, **kwargs):
        raise model_adapter.ModelUnavailable()
    monkeypatch.setattr(incident_helper, "_llmcall", missing)
    with pytest.raises(model_adapter.ModelUnavailable):
        incident_helper.suggest_commit_message("synthetic-tool", "none", "finance-markets", "Synthetic incident.")


def test_changelog_refuses_unproven_output_before_reading_input(monkeypatch, tmp_path, capsys):
    import changelog_draft
    monkeypatch.setattr(changelog_draft, "require_call", lambda: None)
    def refuse(*args, **kwargs):
        raise private_inventory.InventoryError("synthetic unproven destination")
    monkeypatch.setattr(private_inventory, "resolve_destination", refuse)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: pytest.fail("must validate output before reading the changelog"))
    target = tmp_path / "draft.md"
    assert changelog_draft.main(["--since", "HEAD~1", "--out", str(target)]) == 2
    assert not target.exists()
    assert "destination" in capsys.readouterr().err


@pytest.mark.parametrize("write_fails", [False, True])
def test_changelog_uses_verified_atomic_output(companion, monkeypatch, write_fails):
    import changelog_draft
    repository, _, _, _ = companion
    sample = fixture()["maintenance"]
    text = sample["discovery"]["one_line_pitch"]
    target = repository / "data/deliverables/reports" / "draft.md"
    target.parent.mkdir(parents=True)
    target.write_text(text, encoding="utf-8")
    monkeypatch.setattr(changelog_draft, "require_call", lambda: None)
    monkeypatch.setattr(changelog_draft, "parse_latest_changelog_version",
                        lambda: sample["release"]["version"])
    monkeypatch.setattr(changelog_draft, "parse_plugin_version",
                        lambda: sample["release"]["version"])
    monkeypatch.setattr(changelog_draft, "extract_top_entry_text", lambda: text)
    monkeypatch.setattr(changelog_draft, "collect_git_data",
                        lambda _since: {"log": sample["release"]["commit"], "stat": "", "name_status": ""})
    monkeypatch.setattr(changelog_draft, "run_claude", lambda _prompt: (0, text, ""))
    if write_fails:
        def refuse(*args):
            raise PermissionError("synthetic write denial")
        monkeypatch.setattr(private_inventory.os, "replace", refuse)
    assert changelog_draft.main(["--since", "HEAD~1", "--out", str(target)]) == (2 if write_fails else 0)
    expected = text if write_fails else text + "\n" + changelog_draft.FOOTER
    assert target.read_text(encoding="utf-8") == expected
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == (1 if write_fails else 0)
    if pending:
        assert pending[0].read_text(encoding="utf-8") == text + "\n" + changelog_draft.FOOTER
    assert set(target.parent.iterdir()) == {target}


def test_incident_requires_private_destination_before_any_write(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(tmp_path))
    with patch.object(private_inventory, "_shared_boundary", side_effect=private_inventory.InventoryError("synthetic unversioned directory")):
        with pytest.raises(private_inventory.InventoryError):
            incident_helper.apply_live_runs_append(json.dumps(fixture()["inventory"]))
    assert not (tmp_path / "metrics").exists()


def test_incident_uses_canonical_destination_and_atomic_write(companion, monkeypatch):
    repository = companion[0]
    target = repository / "data/metrics/live-runs.jsonl"
    target.parent.mkdir(parents=True)
    old = json.dumps(fixture()["inventory"]) + "\n"
    target.write_text(old, encoding="utf-8")
    with patch.object(private_inventory.os, "replace", side_effect=PermissionError("synthetic credential must never appear")):
        with pytest.raises(private_inventory.InventoryError, match="persistence failed"):
            incident_helper.apply_live_runs_append(json.dumps(fixture()["evidence"]))
    assert target.read_text(encoding="utf-8") == old
    pending = list((repository / ".staging").glob("inventory-*.tmp"))
    assert len(pending) == 1
    assert pending[0].read_text(encoding="utf-8") == old + json.dumps(fixture()["evidence"]) + "\n"
    assert set(target.parent.iterdir()) == {target}


def test_incident_model_bridge_inherits_defaults_and_hides_provider_errors(capsys):
    class Reply:
        error = "synthetic credential must never appear"
        text = "synthetic private reply must never appear"
        def __bool__(self):
            return False
    with patch.object(incident_helper, "_llmcall", return_value=Reply()) as model:
        with pytest.raises(RuntimeError):
            incident_helper._run_claude("synthetic prompt")
        assert model.call_args.kwargs == {}
        with pytest.raises(SystemExit):
            incident_helper.parse_incident("synthetic prompt")
        assert "timeout" not in model.call_args.kwargs
    output = capsys.readouterr()
    assert "synthetic credential" not in output.err
    assert "synthetic private reply" not in output.err


def test_model_exception_is_reported_without_provider_credentials(capsys):
    with patch.object(incident_helper, "_llmcall", side_effect=RuntimeError("synthetic credential")):
        with pytest.raises(RuntimeError, match="inspect private provider diagnostics") as exc:
            incident_helper._run_claude("synthetic prompt")
        assert "synthetic credential" not in str(exc.value)
        with pytest.raises(SystemExit):
            incident_helper.parse_incident("synthetic prompt")
    assert "synthetic credential" not in capsys.readouterr().err


def test_draft_model_call_has_no_provider_preflight_or_default_overrides():
    import changelog_draft
    class Reply:
        text = "Synthetic draft"
        def __bool__(self):
            return True
    with patch.object(changelog_draft, "_llmcall", return_value=Reply()) as model:
        assert changelog_draft.run_claude("synthetic prompt") == (0, "Synthetic draft", "")
        model.assert_called_once_with("synthetic prompt")
    with patch.object(changelog_draft, "_llmcall", side_effect=RuntimeError("synthetic credential")):
        code, text, error = changelog_draft.run_claude("synthetic prompt")
    assert code != 0 and text == ""
    assert "synthetic credential" not in error


def test_private_proof_module_must_exist_before_any_metadata_commands(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(private_inventory, "ROOT", tmp_path / "consumer")
    private_inventory._shared_boundary.cache_clear()
    try:
        with patch.object(subprocess, "run", side_effect=AssertionError("no metadata command before module validation")):
            with pytest.raises(private_inventory.InventoryError, match="initialize the guards"):
                private_inventory._shared_boundary()
    finally:
        private_inventory._shared_boundary.cache_clear()


def incident_draft_output(monkeypatch, tmp_path, capsys, d_code="D-STALE", selection=None):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for name in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    for name, value in (selection or {}).items():
        monkeypatch.setenv(name, str(value))
    monkeypatch.setattr(incident_helper, "suggest_shard_edit", lambda *args: "Synthetic shard draft")
    monkeypatch.setattr(incident_helper, "sources_index_advisory", lambda *args: "Synthetic index draft")
    monkeypatch.setattr(incident_helper, "suggest_commit_message", lambda *args: "Synthetic commit draft")
    code = incident_helper.run({"slug": "synthetic-source", "outcome": "dead",
        "detail": "Synthetic evidence awaiting review", "domain": "finance-markets", "d_code": d_code}, False)
    assert code == 0
    return capsys.readouterr().out


@pytest.mark.parametrize("d_code,required", [
    ("D-404", ("api 404", "archived")),
    ("D-PRICE", ("official", "url", "date")),
    ("D-STALE", ("18 months", "and", "verified replacement")),
    ("D-TOS", ("official policy", "route")),
    ("D-SUPERSEDED", ("named", "verified")),
])
def test_incident_draft_uses_canonical_death_evidence(monkeypatch, tmp_path, capsys, d_code, required):
    text = incident_draft_output(monkeypatch, tmp_path, capsys, d_code)
    rationale = text.split("rationale:", 1)[1].splitlines()[0].lower()
    assert all(term in rationale for term in required)
    assert not any(term in rationale for term in (">12mo", "nxdomain", "captcha", "account bans"))


@pytest.mark.parametrize("choice", ["explicit", "alias", "home", "xdg", "priority"])
def test_incident_draft_uses_selected_companion_checker(monkeypatch, tmp_path, capsys, choice):
    selected = tmp_path / {"home": ".market-intel-config", "xdg": ".config/market-intel-config"}.get(choice, "selected config")
    checker = selected / "scripts/sync-check.py"
    checker.parent.mkdir(parents=True)
    checker.write_text("# Generated synthetic checker; never executed.\n", encoding="utf8")
    selection = {}
    if choice in {"explicit", "priority"}:
        selection["MARKET_INTEL_CONFIG"] = selected
    elif choice == "alias":
        selection["MARKET_INTEL_CONFIG_DIR"] = selected
    if choice == "priority":
        selection["MARKET_INTEL_CONFIG_DIR"] = tmp_path / "missing lower priority"
    text = incident_draft_output(monkeypatch, tmp_path, capsys, selection=selection)
    if choice == "xdg":
        assert str(checker.resolve()) not in text
        return
    assert str(checker.resolve()) in text
    assert "python " in text and "<username>" not in text
    assert "Expect: slug" not in text
    assert "GAP:" not in text and "SKIP:" not in text


@pytest.mark.parametrize("case", ["absent", "explicit-missing", "explicit-file", "missing-checker"])
def test_incident_draft_reports_config_gaps_without_fallback(monkeypatch, tmp_path, capsys, case):
    selection = {}
    if case != "absent":
        selected = tmp_path / "selected config"
        selection["MARKET_INTEL_CONFIG"] = selected
        if case == "explicit-file":
            selected.write_text("Synthetic invalid companion path\n", encoding="utf8")
        elif case == "missing-checker":
            selected.mkdir()
        fallback = tmp_path / ".market-intel-config/scripts"
        fallback.mkdir(parents=True)
        (fallback / "sync-check.py").write_text("# Synthetic fallback must not win\n", encoding="utf8")
    text = incident_draft_output(monkeypatch, tmp_path, capsys, selection=selection)
    assert ("SKIP:" if case == "absent" else "GAP:") in text
    assert "  python " not in text and "<username>" not in text
