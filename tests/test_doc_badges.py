import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('doc_badges', ROOT / 'tools/check_doc_drift.py')
drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drift)


class BadgeTests(unittest.TestCase):
    def test_both_languages_round_trip_count_fix(self):
        for filename, label, unit in [('README.md', 'Source Matrix', 'domains'),
                                      ('README_CN.md', '源矩阵', '个方向')]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / filename
                badge = 'https://img.shields.io/badge/' + quote(label) + '-2%20' + quote(unit) + '-green'
                path.write_text(badge, encoding='utf-8')
                self.assertEqual(2, drift.get_readme_domain_badge(str(path))[0])
                record = {'severity':'fail', 'field':filename+' domain count badge', 'location':filename,
                          'auto_fixable':True, 'found':2, 'expected':3}
                with patch.object(drift, 'ROOT', root), patch.object(drift, 'get_canonical_version', return_value='1.0.0'), \
                     patch.object(drift, 'count_domains', return_value=3):
                    self.assertEqual(1, len(drift.fix_drift([record])))
                self.assertEqual(3, drift.get_readme_domain_badge(str(path))[0])


if __name__ == '__main__':
    unittest.main()
