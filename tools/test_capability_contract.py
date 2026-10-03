"""Public contract regressions using only the reproducible fixture generator."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch

import console
import host_capabilities
from make_fixtures import fixture


def context():
    payload = fixture()["evidence"]
    return {"host": payload["host"], "session_id": payload["session_id"], "payload": payload}


def classify(ctx=None):
    ctx = context() if ctx is None else ctx
    return host_capabilities.classify(ctx, "github-mcp", "search",
                                     now=datetime(2031, 1, 2, 3, 4, 5, tzinfo=timezone.utc))


def test_canonical_proof_is_available_with_all_named_bindings():
    result = classify()
    assert result["status"] == "available-now"
    for field in ("host", "session_id", "source_id", "capability_id", "observed_at", "observation_method"):
        assert result[field]
    assert result["access"] == "exposed"
    assert result["operation"] == "ready"


def test_provenance_is_required_attributed_fresh_and_current_session():
    for replacement in (None, {}, {"host": "other"}):
        ctx = context()
        ctx["payload"]["provenance"] = replacement
        assert classify(ctx)["status"] == "setup"
    for field, value in (("host", "claude"), ("session_id", "another-session"),
                         ("observation_method", "subprocess-host-list"),
                         ("observed_at", "2031-01-02T03:04:05"),
                         ("observed_at", "2030-01-01T00:00:00Z")):
        ctx = context()
        ctx["payload"]["provenance"][field] = value
        assert classify(ctx)["status"] == "setup"


def test_exact_catalog_operation_identity_beats_display_collision():
    ctx = context()
    snap = {"_host_evidence": ctx}
    tool = fixture()["tool"]
    with patch.object(host_capabilities, "datetime") as clock:
        clock.now.return_value = datetime(2031, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        clock.fromisoformat.side_effect = datetime.fromisoformat
        assert console.compute_states(tool, snap, {})["available_now"] == console.YES
        tool["capability_id"] = "different-operation"
        assert console.compute_states(tool, snap, {})["available_now"] == console.NO
        tool["capability_id"] = "search"
        ctx["payload"]["capabilities"][0]["authentication"] = "not-required"
        assert console.compute_states(tool, snap, {})["available_now"] == console.NO
        legacy = {"slug": "github-mcp", "name": tool["name"]}
        assert console.compute_states(legacy, snap, {})["available_now"] == console.NO


def test_unsupported_requires_explicit_current_attributed_false():
    ctx = context()
    ctx["payload"]["capabilities"][0]["supported"] = False
    assert classify(ctx)["status"] == "hard-gap"
    for invalid in (None, "false", 0):
        ctx["payload"]["capabilities"][0]["supported"] = invalid
        assert classify(ctx)["status"] == "setup"


def test_auth_failure_is_scoped_and_newest_observation_wins():
    ctx = context()
    rows = ctx["payload"]["capabilities"]
    failure = deepcopy(rows[0])
    failure.update(authentication="failed", observed_at="2031-01-02T03:04:06+00:00")
    rows.append(failure)
    assert classify(ctx)["status"] == "setup"
    failure["capability_id"] = "different-operation"
    assert classify(ctx)["status"] == "available-now"


def test_each_timestamp_boundary_is_inclusive_and_flags_are_strict():
    instant = datetime(2031, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    for target in ("provenance", "operation"):
        for seconds, expected in ((900, "available-now"), (900.001, "setup"),
                                  (-60, "available-now"), (-60.001, "setup")):
            ctx = context()
            row = ctx["payload"]["provenance"] if target == "provenance" else ctx["payload"]["capabilities"][0]
            row["observed_at"] = (instant - timedelta(seconds=seconds)).isoformat()
            assert classify(ctx)["status"] == expected
    for field, value in (("host", None), ("session_id", None), ("exposed", "true"),
                         ("supported", 1), ("response_valid", "true"), ("authentication", "failed")):
        ctx = context()
        ctx["payload"]["capabilities"][0][field] = value
        assert classify(ctx)["status"] == "setup"


def test_tool_cli_emits_canonical_named_lines(tmp_path, monkeypatch):
    payload = fixture()["evidence"]
    instant = datetime.now(timezone.utc).isoformat()
    payload["provenance"]["observed_at"] = instant
    payload["capabilities"][0]["observed_at"] = instant
    path = tmp_path / "synthetic-capabilities.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("MARKET_INTEL_HOST", "codex")
    monkeypatch.setenv("MARKET_INTEL_SESSION_ID", "fixture-session")
    monkeypatch.setenv("MARKET_INTEL_CAPABILITIES", str(path))
    monkeypatch.setattr(console, "load_registry", lambda: {"tools": [fixture()["tool"]]})
    output = io.StringIO()
    with redirect_stdout(output):
        assert console.main(["tool", "synthetic-display"]) == 0
    lines = {line.strip().split(": ", 1)[0]: line.strip().split(": ", 1)[1]
             for line in output.getvalue().splitlines() if ": " in line}
    assert lines["status"] == "available-now"
    for field in ("reason", "host", "session_id", "source_id", "capability_id", "observed_at", "observation_method"):
        assert lines[field].strip()
