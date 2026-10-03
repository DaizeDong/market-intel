"""Actual shipped catalog journeys using generator-derived operation evidence."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import console
from make_fixtures import fixture


def test_catalog_declares_one_identity_per_real_tool():
    registry = console.load_registry()
    rows = registry["tools"]
    assert registry["count"] == len(rows)
    assert len({row["source_id"] for row in rows}) == len(rows)
    for row in rows:
        assert row["source_id"] and row["capability_id"]
        assert row["authentication_required"] in (True, False, None)
        assert not row["slug"].endswith((".auto", ".core"))
    assert registry["aliases"]["apify.auto"] == "apify"
    assert registry["aliases"]["polygon.auto"] == "polygon"


def test_real_github_catalog_accepts_matching_synthetic_search(tmp_path, monkeypatch, capsys):
    payload = deepcopy(fixture()["evidence"])
    instant = datetime.now(timezone.utc).isoformat()
    payload["provenance"]["observed_at"] = instant
    payload["capabilities"][0]["observed_at"] = instant
    path = tmp_path / "synthetic-evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("MARKET_INTEL_HOST", payload["host"])
    monkeypatch.setenv("MARKET_INTEL_SESSION_ID", payload["session_id"])
    monkeypatch.setenv("MARKET_INTEL_CAPABILITIES", str(path))
    assert console.main(["tool", "github-mcp", "--capability", "search"]) == 0
    output = capsys.readouterr().out
    assert "status: available-now" in output
    assert "source_id: github-mcp" in output
    assert "capability_id: search" in output
    assert "operation: ready" in output


def test_mechanical_document_aliases_resolve_without_extra_sources(monkeypatch, capsys):
    monkeypatch.delenv("MARKET_INTEL_CAPABILITIES", raising=False)
    for alias, canonical in (("apify.auto", "apify"), ("polygon.auto", "polygon")):
        assert console.main(["tool", alias]) == 0
        output = capsys.readouterr().out
        assert f"TOOL · {canonical} " in output
        assert f"source_id: {canonical}\n" in output
        assert "status: setup" in output
