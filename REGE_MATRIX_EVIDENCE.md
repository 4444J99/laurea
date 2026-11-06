# RE:GE matrix execution evidence — October 2, 2026

The September source census found 1,998 RE:GE test-function definitions but explicitly did **not** call them 1,998 passing tests. The first follow-up draft PR also produced false-green required jobs because the workflow only looked for root-level `tests`, `test`, or `test_*.py` paths while the project declares `rege/tests`.

The draft branch now fails closed on its pyproject development dependencies and directly executes the package suite with a five-minute external bound. On exact head `a00d55f9c3bbbb4486ec0fc7e589bb35d5da905e`, hosted GitHub Actions collected all **1,998** tests in both matrix environments with the same resolved core test dependencies: Click 8.5.0, pytest 9.1.1, pytest-cov 7.1.0, and coverage 7.16.2.

| Environment | Test-step result | Test disposition | Boundary |
|---|---|---:|---|
| Python 3.12.14 | success | **1,998 passed** | Overall matrix job was later cancelled after the sibling 3.11 failure; the successful test step is preserved without relabeling the job green. |
| Python 3.11.16 | failure | **1,997 passed · 1 failed** | `TestValidatorInvalidDepth.test_invalid_depth_adds_error` raises `TypeError` because invalid string depth is tested with Enum containment semantics. |

The new evidence therefore upgrades the engineering record in two ways: the complete suite is now known to execute quickly under the declared dependency family, and a real cross-version compatibility defect has been isolated. It does **not** establish a cross-version passing suite, production deployment, or application efficacy.

The exact source identity, workflow blob, run/job IDs, dependencies, failure identity, source blobs, and calculation boundaries are recorded in [`evidence/2026-10-02-rege-matrix-execution.json`](evidence/2026-10-02-rege-matrix-execution.json). Recalculate and validate the saved record with:

```bash
python scripts/verify_rege_matrix_evidence.py
python -m unittest discover -s tests -p test_rege_matrix_evidence.py -v
```
