"""Evidence-structure and publication regression checks, without network access."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atlas', ROOT / 'scripts/build_distinction_atlas.py')
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)

class DistinctionAtlasTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'evidence/2026-09-22-distinction-atlas.json').read_text())

    def reject(self):
        with self.assertRaises((ValueError, KeyError)):
            atlas.validate(self.data)

    def test_nine_documented_claim_families(self):
        self.assertEqual(len(atlas.validate(self.data)), 9)

    def test_generated_report_matches(self):
        self.assertEqual(atlas.render(self.data), (ROOT / 'DISTINCTIONS.md').read_text())

    def test_evidence_tampering_rejected(self):
        self.data['canonical_evidence']['sha256'] = '0' * 64
        self.reject()

    def test_path_traversal_rejected(self):
        self.data['canonical_evidence']['path'] = '../outside.json'
        self.reject()

    def test_changed_subject_rejected(self):
        self.data['subject'] = 'someone-else'
        self.reject()

    def test_duplicate_claim_rejected(self):
        self.data['claims'].append(copy.deepcopy(self.data['claims'][0]))
        self.reject()

    def test_missing_evidence_rejected(self):
        self.data['claims'][0]['evidence'] = ['missing']
        self.reject()

    def test_changed_comparison_scope_rejected(self):
        self.data['claims'][0]['statement'] = 'Top 0.029% of human Python programmers'
        self.reject()

    def test_self_description_cannot_be_acceptance(self):
        self.data['claims'][1]['evidence'] = ['symbolic-parser']
        self.reject()

    def test_changed_merge_sha_rejected(self):
        self.data['sources'][-1]['merge_sha'] = '0' * 40
        self.reject()

    def test_restricted_source_cannot_be_published(self):
        self.data['sources'][1]['visibility'] = 'restricted'
        self.reject()

    def test_private_claim_and_dependent_pathway_are_omitted(self):
        item = self.data['claims'][8]
        item['visibility'] = 'restricted'
        item['statement'] = 'PRIVATE SENTINEL'
        text = atlas.render(self.data)
        self.assertNotIn('PRIVATE SENTINEL', text)
        self.assertNotIn('### Creative practice that can also build its instruments', text)

    def test_unverified_lead_not_promoted(self):
        self.data['claims'][8]['kind'] = 'lead'
        self.data['claims'][8]['statement'] = 'UNVERIFIED SENTINEL'
        self.assertNotIn('UNVERIFIED SENTINEL', atlas.render(self.data))

    def test_audience_filter(self):
        text = atlas.render(self.data, 'creative-technology')
        self.assertIn('An artistic record', text)
        self.assertNotIn('### Security tooling with fewer false positives', text)
        self.assertNotIn('### Human intent into inspectable systems', text)

    def test_unknown_audience_rejected(self):
        with self.assertRaises(ValueError): atlas.render(self.data, 'genius')

    def test_no_composite_genius_score(self):
        self.data['claims'][0]['genius_score'] = 100
        self.reject()

    def test_invalid_source_pin_rejected(self):
        self.data['sources'][5]['blob_sha'] = 'unknown'
        self.reject()

    def test_pathway_needs_multiple_claims(self):
        self.data['pathways'][0]['claims'] = ['protocol', 'protocol']
        self.reject()

    def test_network_scheme_rejected(self):
        self.data['sources'][0]['url'] = 'javascript:alert(1)'
        self.reject()

    def test_mutation_free(self):
        before = copy.deepcopy(self.data)
        atlas.render(self.data)
        self.assertEqual(self.data, before)

if __name__ == '__main__': unittest.main()
