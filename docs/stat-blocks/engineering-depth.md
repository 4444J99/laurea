# Engineering depth — dated evidence

## Accepted upstream patch composition — October 16, 2026

Across **six independently verified accepted upstream PRs**, the **final patches modify 13 file entries**. **Three** PRs correct runtime/data behavior, **one** improves authentication-interface wording, **one** supplies runtime configuration documentation, and **one** adds security-scanning and repository-policy material. **Two PRs include actual regression-test-file changes** (FastMCP and GuardDog). The Dagster PR's test-description claim is not treated as tests in its accepted patch.

These are directly inspected patch-file and contribution-type counts, not executed upstream test totals. [Full evidence](../../ACCEPTED_PATCH_COMPOSITION.md) · [Frozen input](../../evidence/2026-10-16-accepted-patch-and-ci.json).

## RE:GE matrix status — October 16 recheck

The exact **current repaired-validator draft head** `18287492` has two successful Python matrix jobs that executed **zero** package test cases because CI skipped `rege/tests`. It is **not** cross-version verified. Issue #34 remains open, and no previously safety-blocked workflow edit was retried. The real package-suite results below apply **only** to their earlier October 2 head `a00d55f`.

## RE:GE full package-suite execution — October 2, 2026 (historical head)

After correcting the required CI path so it executes `rege/tests`, the earlier exact draft-PR head collected **1,998 tests in both supported matrix environments**. The Python 3.12 test step passed **1,998 / 1,998**. Python 3.11 passed **1,997 / 1,998** and exposed one version-specific validator failure: an invalid depth string reaches Enum containment semantics that raise `TypeError` on Python 3.11 rather than becoming a validation error.

This is stronger evidence than the earlier static 1,998-test-definition count because the entire package suite actually executed in hosted CI. It is **not** a cross-version green claim: Python 3.11 still has one failing test, and the Python 3.12 matrix job was later cancelled after its successful test step when the sibling matrix job failed.

Evidence: [`evidence/2026-10-02-rege-matrix-execution.json`](../../evidence/2026-10-02-rege-matrix-execution.json).
