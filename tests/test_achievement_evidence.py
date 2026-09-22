"""Regression tests for the frozen record, runnable without third-party packages."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('achievement_validator', ROOT / 'scripts/verify_achievements.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class AchievementEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'evidence/2026-09-22-achievements.json').read_text(encoding='utf-8'))

    def test_reproduces_rank(self):
        result = validator.validate(self.record)
        self.assertEqual(result['rank'], 5045)
        self.assertEqual(result['top_percent_conservative'], '0.029')
        self.assertEqual(result['verified_upstream_merges'], 4)

    def test_commits_cannot_replace_pushes(self):
        self.record['ranking']['metric'] = 'authored_commits'
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_wrong_denominator_rejected(self):
        self.record['ranking']['cohort_result']['active_accounts'] = 180000000
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_wrong_window_rejected(self):
        self.record['ranking']['window']['end_exclusive'] = '2026-09-22 00:00:00'
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_zero_population_rejected(self):
        self.record['ranking']['cohort_result']['active_accounts'] = 0
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_wrong_query_threshold_rejected(self):
        self.record['ranking']['target_result']['push_events'] = 35000
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_ties_use_conservative_upper_tail(self):
        self.record['ranking']['cohort_result']['accounts_tied'] = 200
        self.record['ranking']['derived']['top_percent_conservative'] = '0.030'
        self.assertEqual(validator.validate(self.record)['top_percent_conservative'], '0.030')

    def test_contributions_are_not_commits(self):
        self.record['profile']['current_commit_only_total'] = 35896
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_historical_claim_cannot_disappear(self):
        del self.record['historical_python_distinction']
        with self.assertRaises(KeyError): validator.validate(self.record)

    def test_historical_claim_cannot_be_relabelled_disproved(self):
        self.record['historical_python_distinction']['status'] = 'disproved'
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_missing_source_pin_rejected(self):
        self.record['profile']['source_blob_sha'] = ''
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_unmerged_upstream_is_not_acceptance(self):
        self.record['upstream_merges'][0]['merged'] = False
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_duplicate_merge_rejected(self):
        self.record['upstream_merges'].append(copy.deepcopy(self.record['upstream_merges'][0]))
        with self.assertRaises(ValueError): validator.validate(self.record)

    def test_language_scope_mismatch_rejected(self):
        self.record['profile']['python_primary_repositories'] = 109
        with self.assertRaises(ValueError): validator.validate(self.record)


if __name__ == '__main__':
    unittest.main()
