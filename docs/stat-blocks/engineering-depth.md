# Engineering depth — dated evidence

## RE:GE full package-suite execution — October 2, 2026

After correcting the required CI path so it executes `rege/tests`, the exact draft-PR head collected **1,998 tests in both supported matrix environments**. The Python 3.12 test step passed **1,998 / 1,998**. Python 3.11 passed **1,997 / 1,998** and exposed one version-specific validator failure: an invalid depth string reaches Enum containment semantics that raise `TypeError` on Python 3.11 rather than becoming a validation error.

This is stronger evidence than the earlier static 1,998-test-definition count because the entire package suite actually executed in hosted CI. It is **not** a cross-version green claim: Python 3.11 still has one failing test, and the Python 3.12 matrix job was later cancelled after its successful test step when the sibling matrix job failed.

Evidence: [`evidence/2026-10-02-rege-matrix-execution.json`](../../evidence/2026-10-02-rege-matrix-execution.json).
