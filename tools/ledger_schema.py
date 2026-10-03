"""Canonical vocabulary for private live-run ledgers and generated public examples."""

from live_run_contract import CONTRACT

OUTCOMES = tuple(CONTRACT["outcomes"])


def schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Market-intel private live-run ledger row",
        "type": "object",
        "required": ["ts", "domain", "source", "route", "outcome", "detail", "user_correction"],
        "properties": {
            "ts": {"type": "string"}, "domain": {"type": "string"},
            "source": {"type": "string"}, "route": {"enum": ["①", "②", "③", "④"]},
            "outcome": {"enum": list(OUTCOMES)}, "detail": {"type": "string"},
            "user_correction": {"type": ["string", "null"]},
        },
    }


def synthetic_rows():
    return [
        {"ts": "2031-01-02", "domain": "example-domain", "source": "example-source",
         "route": "①", "outcome": outcome, "detail": "Generated synthetic ledger example.",
         "user_correction": None}
        for outcome in OUTCOMES
    ]
