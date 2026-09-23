#!/usr/bin/env python3
"""Generate synthetic feedback fixtures; --check verifies reproducibility."""
import argparse
import json
from pathlib import Path


def feedback_cases():
    base = {'ts': '2020-01-01', 'domain': 'web-scraping', 'source': 'shard/example-source',
            'detail': 'Generated synthetic observation', 'user_correction': None}
    return {
        'legacy_gaps': [dict(base, outcome=o) for o in ('unverifiable', 'fallback_used')],
        'unknown': [dict(base, outcome='synthetic_unknown_event')],
        'unscoped_verified': [dict(base, outcome='verified')],
        'documentation_verified': [dict(base, outcome='verified', verification_scope='tool_documentation',
                                        evidence_ref='https://example.com/documentation-check')],
        'documentation_without_evidence': [dict(base, outcome='verified', verification_scope='tool_documentation')],
        'correction_event': [dict(base, outcome='user_correction')],
        'typed_failures': [dict(base, outcome=o) for o in ('transport_error', 'auth_failed', 'quota_exceeded', 'content_invalid')],
        'invalid_records': [None, 7, dict(base, ts='not-a-date', outcome='verified'),
                            dict(base, outcome=['not-a-string'])],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--out', type=Path, help='alternate root used by the data-boundary verifier')
    args = parser.parse_args()
    target = (args.out / 'live-runs.json' if args.out is not None else
              Path(__file__).resolve().parents[1] / 'tests/fixtures/live-runs.json')
    expected = json.dumps(feedback_cases(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        matches = target.is_file() and target.read_text(encoding='utf-8') == expected
        print('fixtures: reproducible' if matches else 'fixtures: missing or differs from generator')
        return 0 if matches else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(expected, encoding='utf-8')
    print('generated synthetic feedback fixtures')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
