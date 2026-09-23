import importlib.util
import json
from pathlib import Path
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feedback_bump', ROOT / 'tools/feedback-bump.py')
feedback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feedback)
CASES = json.loads((ROOT / 'tests/fixtures/live-runs.json').read_text(encoding='utf-8'))


class FeedbackContractTests(unittest.TestCase):
    def setUp(self):
        self.old_cache = feedback._TOOL_SLUGS_CACHE
        feedback._TOOL_SLUGS_CACHE = ['example-source']

    def tearDown(self):
        feedback._TOOL_SLUGS_CACHE = self.old_cache

    def test_legacy_gap_events_trigger_distinct_review(self):
        result = feedback.bucket_entries(CASES['legacy_gaps'])
        self.assertEqual(['web-scraping'], result['hot_domains'])
        self.assertEqual({'unverifiable', 'fallback_used'}, {x['outcome'] for x in result['open_questions']})

    def test_unknown_event_remains_visible(self):
        result = feedback.bucket_entries(CASES['unknown'])
        self.assertEqual(1, len(result.get('unknown_outcomes', [])))

    def test_unscoped_verification_cannot_refresh_whole_document(self):
        result = feedback.bucket_entries(CASES['unscoped_verified'])
        self.assertEqual({}, result['auto_bump_slugs'])

    def test_documentation_verification_requires_evidence(self):
        self.assertEqual({}, feedback.bucket_entries(CASES['documentation_without_evidence'])['auto_bump_slugs'])
        self.assertEqual({'example-source': '2020-01-01'},
                         feedback.bucket_entries(CASES['documentation_verified'])['auto_bump_slugs'])

    def test_explicit_user_correction_is_priority(self):
        self.assertEqual(1, len(feedback.bucket_entries(CASES['correction_event'])['top_priority']))

    def test_typed_failures_do_not_imply_price_pressure(self):
        result = feedback.bucket_entries(CASES['typed_failures'])
        self.assertEqual(['web-scraping'], result['hot_domains'])
        self.assertEqual({}, result['price_pressure'])

    def test_invalid_records_cannot_disappear_as_clean_feedback(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'synthetic.jsonl'
            path.write_text('\n'.join(json.dumps(row) for row in CASES['invalid_records']), encoding='utf-8')
            rows = feedback.load_live_runs(path, '2020-01-01')
        self.assertEqual(len(CASES['invalid_records']), len(rows))
        self.assertEqual(len(rows), len(feedback.bucket_entries(rows)['unknown_outcomes']))


if __name__ == '__main__':
    unittest.main()
