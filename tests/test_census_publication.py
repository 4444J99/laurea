import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('census_publication',ROOT/'scripts/render_source_census.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CensusPublicationTests(unittest.TestCase):
    def setUp(self): self.d=m.load(ROOT)
    def reject(self):
        with self.assertRaises(ValueError): m.validate(self.d)
    def test_valid_record(self): self.assertEqual(m.validate(self.d)['subject'],'4444J99')
    def test_skills_total(self):
        self.d['projects']['skills']['skills']['canonical_files']+=1;self.reject()
    def test_duplicates_not_promoted(self):
        self.d['projects']['skills']['skills']['duplicate_declared_ids']={'x':2};self.reject()
    def test_validator_failure(self):
        self.d['projects']['skills']['skills']['validator']['exit_code']=1;self.reject()
    def test_missing_contract_field(self):
        self.d['projects']['narrative']['narrative']['algorithm_field_presence']['inputs']=140;self.reject()
    def test_study_identity(self):
        self.d['projects']['narrative']['narrative']['enumerated_studies']=29;self.reject()
    def test_source_pin(self):
        self.d['projects']['titan']['commit']='main';self.reject()
    def test_definition_execution_separation(self):
        self.assertEqual(self.d['projects']['titan']['python']['test_function_definitions'],1530)
        self.assertEqual(self.d['checks']['titan']['counts']['passed'],48)
    def test_failure_not_hidden(self):
        self.d['checks']['rege']['exit_code']=0;self.reject()
    def test_execution_sum(self):
        self.d['checks']['narrative']['counts']['passed']=326;self.reject()
    def test_scope_required(self):
        self.d['checks']['titan']['selection']='';self.reject()
    def test_report_and_roles_regenerated(self):
        for path,text in m.outputs(self.d,ROOT).items():
            with self.subTest(path=path.name): self.assertEqual(path.read_text(),text)
    def test_readme_block_regenerated(self):
        text=(ROOT/'README.md').read_text();self.assertEqual(m.replace_block(text,m.block(self.d)),text)
    def test_bad_evidence_pin(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'evidence').mkdir();(root/m.RECORD).write_text('{}')
            with self.assertRaisesRegex(ValueError,'pin mismatch'):m.load(root)
    def test_outside_text_preserved(self):
        self.assertEqual(m.replace_block('a'+m.START+'old'+m.END+'z','new'),'anewz')
    def test_invalid_marker_sets(self):
        for text in ['',m.START+m.START+m.END,m.END+m.START]:
            with self.subTest(text=text),self.assertRaises(ValueError):m.replace_block(text,'new')
    def test_only_known_audiences(self):
        with self.assertRaises(ValueError):m.stat_block(self.d,'one-in-a-million')
    def test_report_preserves_nonpassing_results(self):
        text=m.report(self.d)
        self.assertIn('1770 | 0 | 2 | 0',text);self.assertIn('not certified green',text)
    def test_no_mutation(self):
        before=copy.deepcopy(self.d);m.report(self.d);m.block(self.d);self.assertEqual(self.d,before)

if __name__=='__main__':unittest.main()
