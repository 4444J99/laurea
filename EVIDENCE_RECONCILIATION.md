# Evidence reconciliation — September 25, 2026

## External contribution breadth

**23 tracked authored external pull requests across 23 independent upstream repositories:** **6 merged**, **11 open**, **6 closed unmerged**.

This is a bounded reconciliation of the public contribution ledger plus the two accepted PRs previously recovered by LAVREA, not a lifetime-submission claim. Every PR was re-read with `4444J99` as author; only actually merged records retain merge SHAs. Open/closed state is not a quality score or an acceptance prediction.

The six merged records remain FastMCP, Datadog GuardDog, dbt MCP, primeinc/github-stars, jairus-m/dagster-sdlc and Temporal Python SDK. No seventh **independent-upstream** merge was established in this tracked corpus.

## RE:GE verification correction

PR #35 installed the declared `click 8.5.0` / `pytest 9.1.1` environment on Python 3.11 and 3.12, but both required test jobs **skipped the package suite** because the workflow only discovers root-level test directories while the suite lives in `rege/tests`. The evidence-only head is an empty commit with zero changed files. The green statuses therefore do **not** establish the PR body's 1,998-pass claim. Issue #34 remains the owner until the full suite actually executes under the declared environment.

## October 2 broader namespace census

A later measurement uses a different selection rule: GitHub's public query `author:4444J99 is:pr -user:4444J99`. It returns **32 authored PRs across 30 current base-repository identities outside the `4444J99` namespace: 7 merged, 13 open, 12 closed unmerged**.

That result does not overwrite the September 25 tracked corpus. Current owner namespace is not the same as independence; the seventh merged namespace record is `unnamedplay-r/etceter4#1`, and the independently verified upstream-acceptance set remains six projects.

[Read the October 2 census](EXTERNAL_PR_CENSUS.md).

## Publication boundary

The reusable September 25 claim remains: **23 tracked authored external PRs across 23 independent upstream repositories in the reconciled corpus: 6 merged, 11 open, 6 closed unmerged.** The October 2 claim must retain its different current-owner namespace definition. Do not relabel either as a lifetime submission total or compute a career acceptance rate from these bounded sets. Do not claim RE:GE has 1,998 hosted passing tests from the current green statuses.

Canonical September 25 machine-readable note: [`evidence/2026-09-25-reconciliation-note.json`](evidence/2026-09-25-reconciliation-note.json). October 2 machine-readable census: [`evidence/2026-10-02-external-owner-pr-census.json`](evidence/2026-10-02-external-owner-pr-census.json).
