# Evidence reconciliation — September 25, 2026

## External contribution breadth

**23 tracked authored external pull requests across 23 independent upstream repositories:** **6 merged**, **11 open**, **6 closed unmerged**.

This is a bounded reconciliation of the public contribution ledger plus the two accepted PRs previously recovered by LAVREA, not a lifetime-submission claim. Every PR was re-read with `4444J99` as author; only actually merged records retain merge SHAs. Open/closed state is not a quality score or an acceptance prediction.

The six merged records remain FastMCP, Datadog GuardDog, dbt MCP, primeinc/github-stars, jairus-m/dagster-sdlc and Temporal Python SDK. No seventh merge was found in this tracked corpus.

## RE:GE verification correction

PR #35 installed the declared `click 8.5.0` / `pytest 9.1.1` environment on Python 3.11 and 3.12, but both required test jobs **skipped the package suite** because the workflow only discovers root-level test directories while the suite lives in `rege/tests`. The evidence-only head is an empty commit with zero changed files. The green statuses therefore do **not** establish the PR body's 1,998-pass claim. Issue #34 remains the owner until the full suite actually executes under the declared environment.

## Publication boundary

The reusable public claim from this edition is: **23 tracked authored external PRs across 23 independent upstream repositories in the reconciled corpus: 6 merged, 11 open, 6 closed unmerged.** Do not relabel this as a lifetime submission total or compute a career acceptance rate from the bounded corpus. Do not claim RE:GE has 1,998 hosted passing tests from the current green statuses.

Canonical machine-readable evidence: [`evidence/2026-09-25-evidence-reconciliation.json`](evidence/2026-09-25-evidence-reconciliation.json).
