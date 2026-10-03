"""Deterministic, operation-scoped evidence from the current-session adapter."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

TTL_SECONDS = 900
FUTURE_SKEW_SECONDS = 60
OBSERVATION_METHOD = "current-session-adapter"


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def load_environment():
    """Read explicitly supplied evidence without discovering or probing tools."""
    context = {"host": os.environ.get("MARKET_INTEL_HOST", ""),
               "session_id": os.environ.get("MARKET_INTEL_SESSION_ID", "")}
    path = os.environ.get("MARKET_INTEL_CAPABILITIES")
    if not path:
        return {**context, "error": "supply current-session evidence with MARKET_INTEL_CAPABILITIES"}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {**context, "error": "capability evidence file is unreadable or malformed; supply a valid schema-v1 file"}
    return {**context, "payload": payload}


def _timestamp(value):
    if not _text(value):
        raise ValueError("observed_at is missing")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("observed_at requires a timezone")
    return stamp


def classify(context, source, capability="read", now=None, authentication_required=None):
    """Bind v1 proof to exact operation IDs; latest proof wins, failure wins ties."""
    def result(state, reason, **extra):
        # Selection identity is known even when no observation can be attributed.
        return {"status": state, "reason": reason, "access": "unproven",
                "operation": "unproven", **extra,
                "source_id": source, "capability_id": capability}

    if not _text(source) or not _text(capability):
        return result("setup", "declare source_id and capability_id for the selected catalog operation")
    if not isinstance(context, dict):
        return result("setup", "supply current-session capability evidence")
    if context.get("error"):
        return result("setup", context["error"])
    host, session = context.get("host"), context.get("session_id")
    if host not in ("codex", "claude") or not _text(session):
        return result("setup", "set MARKET_INTEL_HOST to codex or claude and set MARKET_INTEL_SESSION_ID")
    payload = context.get("payload")
    if (not isinstance(payload, dict) or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != 1):
        return result("setup", "supply capability evidence with schema_version 1")
    if payload.get("host") != host or payload.get("session_id") != session:
        return result("setup", "evidence belongs to another host or session; request a current adapter observation")
    provenance = payload.get("provenance")
    if (not isinstance(provenance, dict) or provenance.get("host") != host
            or provenance.get("session_id") != session
            or provenance.get("observation_method") != OBSERVATION_METHOD):
        return result("setup", "supply attributed provenance from the current-session-adapter")
    now = now or datetime.now(timezone.utc)
    try:
        age = (now - _timestamp(provenance.get("observed_at"))).total_seconds()
        if age > TTL_SECONDS or age < -FUTURE_SKEW_SECONDS:
            raise ValueError("outside evidence freshness window")
    except (ValueError, TypeError, OverflowError):
        return result("setup", "provenance timestamp is invalid, stale or outside future skew; refresh adapter evidence")
    rows = payload.get("capabilities")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return result("setup", "supply a valid capabilities array")
    matches = [row for row in rows if row.get("source_id") == source and row.get("capability_id") == capability]
    if not matches:
        return result("setup", "no evidence for the selected source_id and capability_id; verify that operation")
    observations = []
    for row in matches:
        if row.get("host") != host or row.get("session_id") != session:
            return result("setup", "selected evidence has missing or foreign attribution; refresh adapter evidence")
        try:
            # Parse historical observations before selecting the latest one, so
            # later successful verification can establish recovery after failure.
            stamp = _timestamp(row.get("observed_at"))
            if (now - stamp).total_seconds() < -FUTURE_SKEW_SECONDS:
                raise ValueError("future timestamp")
        except (ValueError, TypeError, OverflowError):
            return result("setup", "selected timestamp is invalid or outside future skew; refresh adapter evidence")
        observations.append((stamp, row))
    latest_time = max(stamp for stamp, _ in observations)
    decisions = []
    for stamp, row in observations:
        if stamp != latest_time:
            continue
        if (now - stamp).total_seconds() > TTL_SECONDS:
            return result("setup", "selected evidence is stale; verify the operation again")
        binding = {"host": host, "session_id": session, "observed_at": row["observed_at"],
                   "observation_method": OBSERVATION_METHOD,
                   "access": "exposed" if row.get("exposed") is True else "unproven"}
        if (any(type(row.get(field)) is not bool for field in ("exposed", "supported", "response_valid"))
                or not _text(row.get("execution")) or not _text(row.get("authentication"))):
            reason = "selected evidence has malformed readiness fields; supply typed schema-v1 observations"
        elif row["supported"] is False:
            decisions.append(result("hard-gap", "current adapter evidence explicitly marks the selected operation unsupported",
                                    **binding))
            continue
        elif row["authentication"] in ("failed", "expired", "denied"):
            reason = "latest selected operation authentication failed; reconnect and verify again"
        elif row["exposed"] is not True:
            reason = "selected capability is not exposed; enable it in the active host session"
        elif row["execution"] != "success":
            reason = "selected operation has no successful execution proof; run and verify it"
        elif (row["authentication"] not in ("authenticated", "success", "not-required")
              or (authentication_required is True and row["authentication"] == "not-required")):
            reason = "selected operation authentication is unproven; verify required authentication"
        elif row["response_valid"] is not True:
            reason = "selected operation has no usable response validation; validate returned content"
        else:
            decisions.append(result("available-now", "fresh selected operation and usable content verified",
                                    **binding, operation="ready"))
            continue
        decisions.append(result("setup", reason, **binding))
    return min(decisions, key=lambda d: {"setup": 0, "hard-gap": 1, "available-now": 2}[d["status"]])
