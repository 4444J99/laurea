"""Guard public summary freshness without rewriting historical evidence."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_highlights', ROOT / 'scripts/render_highlights.py')
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PublicHighlightsTests(unittest.TestCase):
    def test_readme_is_generated(self):
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertEqual(module.replace_block(text, module.render()), text)

    def test_six_accepted_projects(self):
        text = module.render()
        self.assertIn('6 accepted contributions across 6 independent upstream projects', text)
        self.assertIn('jairus-m/dagster-sdlc #22', text)
        self.assertIn('primeinc/github-stars #39', text)

    def test_three_separate_cohorts_are_labeled(self):
        text = module.render()
        for term in ['Top 1% on 3 measured axes', '0.029%', '0.230%', '0.800%',
                     '17,775,327 accounts', '2,267,625 accounts', 'automated accounts']:
            self.assertIn(term, text)

    def test_music_totals_recompute(self):
        self.assertIn('5 releases · 63 tracks · 4:10:51 of audio', module.render())

    def test_recorded_not_executed_algorithm_claim(self):
        self.assertIn('Repository-reported corpus dimensions', module.render())
        self.assertIn('not an independent enumeration or execution', module.render())

    def test_annual_contributions_are_not_renamed_commits(self):
        text = module.render()
        self.assertIn('35,896 contributions · 318 active days', text)
        self.assertNotIn('35,896 commits', text)

    def test_recruiter_history_remains_attributed(self):
        self.assertIn('top-1% Python committer', module.render())
        self.assertIn('separately attributed', module.render())

    def test_conservative_tie_rounding(self):
        self.assertEqual(str(module.upper_tail(40081, 659, 17775327)), '0.230')
        self.assertEqual(str(module.upper_tail(17761, 376, 2267625)), '0.800')

    def test_invalid_cohorts_rejected(self):
        for triple in [(0, 0, 10), (-1, 1, 10), (10, 2, 10), (0, 1, 0), (True, 1, 10)]:
            with self.subTest(triple=triple), self.assertRaises(ValueError):
                module.upper_tail(*triple)

    def test_source_pin_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'evidence').mkdir()
            name = next(iter(module.INPUTS))
            (root / 'evidence' / name).write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'pin mismatch'):
                module.load_record(root, name)

    def test_outside_block_is_preserved(self):
        before, after = '# Manual introduction\n', '\nManual ending.\n'
        old = before + module.START + '\nold\n' + module.END + after
        self.assertEqual(module.replace_block(old, 'NEW'), before + 'NEW' + after)

    def test_missing_duplicate_or_reversed_markers_rejected(self):
        for text in ['', module.START + module.START + module.END, module.END + module.START]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                module.replace_block(text, 'NEW')

    def test_deterministic(self):
        self.assertEqual(module.render(), module.render())

    def test_dated_snapshot_is_explicit(self):
        self.assertIn('September 22, 2026', module.render())
        self.assertIn('dated findings, not live counters', module.render())


if __name__ == '__main__':
    unittest.main()
