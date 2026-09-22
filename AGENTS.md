# LAVREA achievement continuity

Before editing career positioning, achievement claims, or rankings, read `ACHIEVEMENTS.md` and `evidence/2026-09-22-achievements.json`. LAVREA's purpose is to find and prominently communicate real distinctions, not merely render counters or accumulate disclaimers.

## Existing evidence must survive context loss

- The frozen comparison establishes top 0.029% by observed public PushEvent count among 17,775,327 active accounts, October 2025–June 2026. Preserve the metric, observed-public scope, population, bot inclusion, and dates.
- The September 22 profile manifest records 35,896 contribution events and 318 active days. Contributions are not authored commits. The older August commit count is not a current measurement.
- The recruiter-originated top-1% Python-committer finding is a distinct historical claim attested by Anthony. Missing original artifacts, a later failed model, or chat context loss is not disproof. Preserve attribution; do not claim the push ranking reproduced the Python-only calculation.
- Four upstream merges have saved author, merge-state, timestamp, and SHA evidence. Do not downgrade accepted work to merely submitted work because the next session lacks context.

Use the dated JSON as the canonical evidence record, the ledger as the explanatory surface, and the README as the showcase. Lead with achievements and let readers open detailed evidence. Distinguish measured facts, derived comparisons, attributed findings, and editorial synthesis.

Refresh by adding a new dated evidence record with source, scope, queries, and observation time. Correct mistakes when contradictory evidence exists, but preserve the old observation and explicitly explain supersession. Never silently replace a denominator, metric, or time window. Never infer code quality, unique humans, Python-only rank, deployed products, or revenue from activity counts.

## Verification

Run `python scripts/verify_achievements.py` and `python -m unittest discover -s tests -p test_achievement_evidence.py -v`. These are offline structural/arithmetic checks, not proof that a network query was rerun. The saved SQL/replay URLs support external remeasurement. Do not alter frozen values merely to make tests pass; a justified update gets a new record and matching tests.

Preserve the existing API renderer, arena, historical snapshots, and one-intention-per-PR workflow. Do not delete history or create a competing achievement repository.
