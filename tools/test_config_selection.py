"""Blank setup and conflicting companion selection cannot report readiness."""
import json
import sys

import pytest

from test_first_use_contract import config_script
from test_private_writers import load_writer
import private_inventory


def test_empty_template_is_not_ready(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["init_config.py", "--out", str(tmp_path)])
    assert config_script("init_config.py").main() == 0
    monkeypatch.setattr(sys, "argv", ["verify_config.py", "--config-dir", str(tmp_path)])
    assert config_script("verify_config.py").main() == 1
    assert "NOT READY" in capsys.readouterr().out


def test_runtime_requires_data_child(tmp_path, monkeypatch):
    monkeypatch.delenv("MARKET_INTEL_DATA_DIR", raising=False)
    monkeypatch.setenv("MARKET_INTEL_CONFIG", str(tmp_path))
    with pytest.raises(private_inventory.InventoryError, match="data"):
        private_inventory._data_directory()


def test_doctor_discovery_refuses_mixed_companions(tmp_path, monkeypatch):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    (second / "data").mkdir(parents=True)
    monkeypatch.setenv("MARKET_INTEL_CONFIG", str(first))
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(second / "data"))
    with pytest.raises((ValueError, RuntimeError), match="same companion|conflict"):
        config_script("verify_config.py").discover("market-intel", None)


@pytest.mark.parametrize("selection", ["alias", "missing-data", "conflict"])
def test_feedback_reader_shares_config_and_data_layout(tmp_path, monkeypatch, selection):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    for key in ("MARKET_INTEL_CONFIG", "MARKET_INTEL_CONFIG_DIR", "MARKET_INTEL_DATA_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MARKET_INTEL_CONFIG_DIR", str(first))
    if selection != "missing-data":
        (first / "data").mkdir()
    if selection == "conflict":
        (second / "data").mkdir(parents=True)
        monkeypatch.setenv("MARKET_INTEL_DATA_DIR", str(second / "data"))
    feedback = load_writer("feedback-bump")
    if selection == "conflict":
        with pytest.raises(ValueError, match="conflict"):
            feedback.live_runs_path()
    else:
        expected = None if selection == "missing-data" else first / "data/metrics/live-runs.jsonl"
        assert feedback.live_runs_path() == expected
