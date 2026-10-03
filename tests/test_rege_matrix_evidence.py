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


if __name__ == "__main__":
    unittest.main()
