import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "2026-10-02-rege-matrix-execution.json"
SCRIPT = ROOT / "scripts" / "verify_rege_matrix_evidence.py"

spec = importlib.util.spec_from_file_location("verify_rege_matrix_evidence", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class RegeMatrixEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_saved_evidence_verifies(self):
        result = module.verify(self.data)
        self.assertEqual(result["collected"], 1998)
        self.assertFalse(result["cross_version_full_suite_green"])

    def test_matrix_does_not_double_count_suite(self):
        rows = self.data["environments"]
        self.assertEqual({row["collected"] for row in rows}, {1998})
        self.assertEqual(self.data["derived"]["defined_and_collected_tests"], 1998)

    def test_python_312_step_is_success_not_job_success(self):
        row = next(r for r in self.data["environments"] if r["python"] == "3.12.14")
        self.assertEqual(row["test_step_conclusion"], "success")
        self.assertEqual(row["job_conclusion"], "cancelled")
        self.assertEqual(row["passed"], 1998)

    def test_python_311_failure_is_preserved(self):
        row = next(r for r in self.data["environments"] if r["python"] == "3.11.16")
        self.assertEqual((row["passed"], row["failed"]), (1997, 1))
        self.assertEqual(row["failure"]["exception"], "TypeError")

    def test_cross_version_green_cannot_be_flipped(self):
        changed = copy.deepcopy(self.data)
        changed["derived"]["cross_version_full_suite_green"] = True
        with self.assertRaises(ValueError):
            module.verify(changed)

    def test_source_pins_are_enforced(self):
        changed = copy.deepcopy(self.data)
        changed["workflow"]["blob_sha"] = "0" * 40
        with self.assertRaises(ValueError):
            module.verify(changed)


# New dated evidence validator; earlier frozen October 2 tests remain unchanged.
PATCH_SCRIPT = ROOT / "scripts" / "verify_patch_and_ci.py"
PATCH_DATA = ROOT / "evidence" / "2026-10-16-accepted-patch-and-ci.json"
patch_spec = importlib.util.spec_from_file_location("verify_patch_and_ci", PATCH_SCRIPT)
patch_module = importlib.util.module_from_spec(patch_spec)
assert patch_spec.loader is not None
patch_spec.loader.exec_module(patch_module)


class PatchAndCiRecheckTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(PATCH_DATA.read_text())

    def test_source_record_reconciles(self):
        result = patch_module.verify(self.data)
        self.assertEqual(result["accepted_patch_counts"]["changed_file_entries"], 13)
        self.assertEqual(result["green_jobs_with_zero_package_tests"], 2)

    def test_false_green_cannot_be_recast_as_suite_success(self):
        copy_data = copy.deepcopy(self.data)
        copy_data["rege_ci_recheck"]["jobs"][0]["executed_package_test_cases"] = 1998
        with self.assertRaises(ValueError): patch_module.verify(copy_data)

    def test_source_head_change_needs_new_evidence(self):
        copy_data = copy.deepcopy(self.data)
        copy_data["rege_ci_recheck"]["head_sha"] = "0" * 40
        with self.assertRaises(ValueError): patch_module.verify(copy_data)

    def test_duplicate_acceptance_fails(self):
        copy_data = copy.deepcopy(self.data)
        copy_data["accepted_patch_census"]["records"][1] = copy_data["accepted_patch_census"]["records"][0]
        with self.assertRaises(ValueError): patch_module.verify(copy_data)

    def test_dagster_test_claim_not_in_accepted_patch(self):
        dagster = next(x for x in self.data["accepted_patch_census"]["records"] if x["repo"] == "jairus-m/dagster-sdlc")
        self.assertEqual(dagster["files"], ["dagster_proj/assets/ml_analytics/energy_prediction.py"])

    def test_test_file_total_excludes_pr_body_promises(self):
        copy_data = copy.deepcopy(self.data)
        copy_data["accepted_patch_census"]["reported_counts"]["prs_with_changed_test_files"] = 3
        with self.assertRaises(ValueError): patch_module.verify(copy_data)

    def test_new_namespace_entry_not_new_acceptance(self):
        copy_data = copy.deepcopy(self.data)
        copy_data["namespace_followup"]["derived"]["merged"] += 1
        with self.assertRaises(ValueError): patch_module.verify(copy_data)

    def test_both_green_jobs_are_zero_suite(self):
        jobs = self.data["rege_ci_recheck"]["jobs"]
        self.assertEqual([(x["python"], x["job_conclusion"], x["executed_package_test_cases"]) for x in jobs],
                         [("3.11", "success", 0), ("3.12", "success", 0)])



if __name__ == "__main__":
    unittest.main()
