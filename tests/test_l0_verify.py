"""Synthetic HTTP responses test verdict semantics without asserting a site's uptime."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('l0_test_target', ROOT / 'tools/l0_verify.py')
l0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l0)


class L0VerdictTests(unittest.TestCase):
    def web(self, status, body=b'Example service documentation', *, registry=False, body_error=False):
        response = SimpleNamespace(status_code=status, headers={}, url='https://example.com/docs',
            raw=SimpleNamespace(read=lambda *args, **kwargs: body), close=lambda: None)
        with patch.object(l0, '_cached_or', side_effect=lambda path, key, fn: l0._result(fn())), \
             patch.object(l0, '_dns_resolves', return_value=True), \
             patch.object(l0, '_cert_check', return_value={'ok':True,'expires':None}), \
             patch.object(l0.requests, 'head', return_value=response), \
             patch.object(l0.requests, 'get', side_effect=l0.requests.exceptions.Timeout() if body_error else None, return_value=response):
            return l0.verify('https://example.com/docs', 'web-registry' if registry else 'web')['verdict']

    def test_success_missing_and_maintenance(self):
        self.assertEqual('PASS', self.web(200))
        self.assertEqual('BLOCK', self.web(404))
        self.assertEqual('UNCERTAIN', self.web(503))
        self.assertEqual('UNCERTAIN', self.web(200, b'this domain is for sale'))

    def test_antibot_requires_the_correct_scope(self):
        self.assertEqual('UNCERTAIN', self.web(403))
        self.assertEqual('PASS', self.web(403, registry=True))

    def test_failed_body_inspection_is_not_a_clean_success(self):
        self.assertEqual('UNCERTAIN', self.web(200, body_error=True))

    def test_unrecognized_candidate_is_uncertain(self):
        self.assertEqual('UNCERTAIN', l0.verify('https://example.com', 'unsupported')['verdict'])


if __name__ == '__main__':
    unittest.main()
