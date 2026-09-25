import importlib.util
import io
import json
import tarfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('source_census',Path(__file__).resolve().parents[1]/'scripts/source_census.py')
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

class CensusTests(unittest.TestCase):
    def test_empty_blob_pin(self):
        self.assertEqual(c.blob_sha(b''),'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
    def test_frontmatter_requires_delimiters(self):
        with self.assertRaises(ValueError): c.frontmatter(b'name: x')
    def test_frontmatter_duplicate_rejected(self):
        with self.assertRaises(ValueError): c.frontmatter(b'---\nname: x\nname: y\n---')
    def test_distribution_copies_excluded(self):
        raw=b'---\nname: x\nlicense: MIT\n---'
        d=c.skills_census({'skills/one/x/SKILL.md':raw,'distributions/codex/x/SKILL.md':raw})
        self.assertEqual(d['unique_declared_ids'],1); self.assertEqual(d['outside_canonical_roots'],1)
    def test_duplicates_are_visible(self):
        raw=b'---\nname: x\n---'
        d=c.skills_census({'skills/one/x/SKILL.md':raw,'plugins/x/SKILL.md':raw})
        self.assertEqual(d['duplicate_declared_ids'],{'x':2})
    def test_malformed_skill_not_silently_counted(self):
        d=c.skills_census({'skills/x/SKILL.md':b'bad'})
        self.assertEqual(len(d['parse_errors']),1); self.assertEqual(d['canonical_files'],0)
    def test_algorithm_scope_is_per_study(self):
        d={'meta':{'study_count':2},'studies':{k:{'id':k,'category':'Film','algorithms':[{'id':'a','pseudocode':'x'}],'axioms':[{'id':'x'}]} for k in ['a','b']}}
        r=c.narrative_census(json.dumps(d).encode())
        self.assertEqual(r['unique_study_algorithm_ids'],2); self.assertEqual(r['axiom_records'],2)
    def test_duplicate_algorithm_flagged(self):
        d={'studies':{'a':{'algorithms':[{'id':'x'},{'id':'x'}]}}}
        self.assertEqual(c.narrative_census(json.dumps(d).encode())['duplicate_study_algorithm_ids'],['a:x'])
    def test_real_core_algorithms_schema(self):
        d={'studies':{'x':{'core_algorithms':[{'name':'a','purpose':'p','pseudocode':'p','inputs':['a'],'outputs':['b']}],'diagnostic_questions':['why']}}}
        r=c.narrative_census(json.dumps(d).encode())
        self.assertEqual(r['algorithm_records'],1); self.assertEqual(r['complete_algorithm_contracts'],1); self.assertEqual(r['diagnostic_questions'],1)
    def test_unknown_algorithm_schema_rejected(self):
        with self.assertRaises(ValueError): c.narrative_census(json.dumps({'studies':{'x':{}}}).encode())
    def test_metadata_not_used_as_measured_count(self):
        d={'meta':{'study_count':999},'studies':{}}
        self.assertEqual(c.narrative_census(json.dumps(d).encode())['enumerated_studies'],0)
    def test_python_definitions_are_not_execution(self):
        r=c.python_inventory({'tests/test_one.py':b'def test_x():\n assert False\n','a.py':b'def a(): pass\n'})
        self.assertEqual(r['test_function_definitions'],1); self.assertNotIn('passed',r)
    def test_parse_failure_retained(self):
        r=c.python_inventory({'bad.py':b'def :'})
        self.assertEqual(len(r['parse_errors']),1)
    def test_unsafe_archive_rejected(self):
        b=io.BytesIO()
        with tarfile.open(fileobj=b,mode='w:gz') as t:
            info=tarfile.TarInfo('repo/../escape'); info.size=1; t.addfile(info,io.BytesIO(b'x'))
        with self.assertRaises(ValueError): c.unpack(b.getvalue())

if __name__=='__main__': unittest.main()
