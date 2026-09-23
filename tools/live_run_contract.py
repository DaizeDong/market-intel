"""Refresh-side consumer of the published live-run event contract."""
import json
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[1] / 'skills/market-intel/reference/live-run-contract.json'
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
SCHEMA_VERSION = CONTRACT['schema_version']
VALID_OUTCOMES = frozenset(CONTRACT['outcomes'])
REVIEW_OUTCOMES = frozenset(CONTRACT['review_outcomes'])


def documentation_verified(entry):
    evidence = entry.get('evidence_ref')
    return (entry.get('outcome') == 'verified'
            and entry.get('verification_scope') == CONTRACT['documentation_verification_scope']
            and isinstance(evidence, str) and bool(evidence.strip()))
