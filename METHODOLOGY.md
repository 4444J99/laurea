# METHODOLOGY — field definitions and publication boundary

## Two measurement layers

LAVREA combines an API snapshot renderer with a provenance-bearing achievement ledger. The API renderer reports bounded GitHub fields and deterministic descriptions of the corpus visible to a run. The achievement layer records independently checked acceptances, attributed historical findings, and reproducible comparisons against explicitly observed cohorts.

Activity alone does not establish engineering quality, employability, authorship of every line, reliability, adoption, or revenue. A measured activity rank is nevertheless a real distinction when its metric, population, dates, and limitations are stated accurately.

## Measured public-event ranking — September 22, 2026

The [frozen evidence record](evidence/2026-09-22-achievements.json) contains the actual target and cohort SQL, returned aggregates, source endpoint, retrieval identifiers, comparison dates, and conservative rounding rule. [ACHIEVEMENTS.md](ACHIEVEMENTS.md) supplies the public interpretation.

- Metric: rows with `event_type = 'PushEvent'` in ClickHouse's public `github_events` table.
- Population: nonempty, case-normalized actor logins with at least one such row in the same window. Bots and other automated accounts are included; these are not verified unique people.
- Window: October 1, 2025 inclusive through July 1, 2026 exclusive, using GitHub event timestamps. The dataset did not cover the full requested trailing year, so the reported window is not silently extended.
- Result: 4,905 observed events for `4444j99`; 17,775,327 active accounts; 5,044 strictly above and one at the target count. Rank is 5,045. The tie-inclusive upper-tail share is `100 * (above + tied) / population`, rounded upward to 0.001 percentage points: **top 0.029%**.
- Boundary: this is observed public push frequency, not unique authored commits, Python-only commits, private activity, or software quality. `push_size` is unusable for much of this window. Do not substitute the pull-request `commits` field.

The aggregate observation is frozen in Git, but the remote source is mutable. This is not an immutable copy of all underlying event rows. The queried schema lacks an event ID, and an independent event-level deduplication or every-hour coverage audit has not been performed. Replays may yield changed results; preserve both dated observations rather than silently overwriting the first.

## Historical percentile model and recruiter finding

The previous heuristic percentile model was withdrawn because it lacked a validated per-user population distribution. Large values, generic platform totals, national leaderboards, or informal medians do not establish a population percentile. That withdrawal remains correct and is not reversed by the new, separately scoped observed-cohort calculation.

The recruiter-originated top-1% Python-committer finding is also separate. Anthony attests to its recruiter origin and prior verification. The original artifact and Python-specific denominator were not recovered in this audit. Preserve attribution: neither the withdrawn heuristic nor this public-push result proves or disproves that earlier Python-only calculation.

## Direct API measurements

- `contributions_year` uses `contributionsCollection.contributionCalendar.totalContributions`. Associated API commit, pull-request, review, and issue fields are neither disjoint nor an additive breakdown of the calendar total. Contribution events are not authored commits or standardized units of shipped work.
- `pull_requests_year` uses `contributionsCollection.totalPullRequestContributions`. It counts opened PRs, not accepted work. Upstream acceptance is checked separately using PR author, `merged`, merge time, and merge SHA.
- `repos_visible` counts `isFork=false` entries in personal and visible organization repository connections. An organization repository is not thereby wholly attributed to the account.
- `organization_memberships` reports the first 20 memberships returned by the current query. Membership is not operation or ownership.
- `tenure` derives elapsed time from `user.createdAt`; account age does not establish continuous professional experience.

The September 22 profile manifest and August 21 LAVREA snapshot have different observation dates and repository scopes. Preserve both source labels. In particular, 35,896 is the newer manifest's contribution-calendar count; 15,671 is the older snapshot's commit-contribution count, not a current commit measurement.

## Deterministic corpus descriptions

- `language_breadth` counts distinct `primaryLanguage.name` values. GitHub assigns one primary language per repository; this does not establish personal proficiency or authorship. Labels can include markup and other non-general-purpose languages.
- `language_layer_coverage` maps those labels through `src/laurea/detectors.py`. It describes the corpus rather than ranking full-stack engineers.

## Token and provenance boundary

Visibility depends on the token. A user token can expose restricted contribution counts and organization repositories unavailable to the default Actions token. Every report records subject, generation time, source repository, and source SHA. Unavailable provenance is recorded as `unknown`, not invented.

The legacy central scheduled target is `4444J99`. Personal copies default to `github.repository_owner`; organization-owned copies must set `LAUREA_LOGIN` to the authorized subject. Non-user subjects, malformed repository entries, and incomplete contribution fields fail clearly instead of silently publishing partial aggregates. Frozen achievement records remain subject-specific and are not automatically transferred to another user of this template.

## Evidence checks and future comparisons

`python scripts/verify_achievements.py` validates the frozen record's arithmetic and scope. Fourteen standard-library regression tests guard its metric naming, cohort, dates, source pins, retained history, and acceptance evidence. These are offline checks, not claims that the source queries were rerun.

A new comparison must retain its observed population, metric, time window, collection method, actual results, source coverage, and reproducible calculation. Version the evidence and implementation; explicitly state whether the underlying dataset itself is immutable. Publish the strongest claim those sources support, not a broader or narrower one invented from missing context. Legitimate corrections append an explicit supersession record rather than deleting historical observations.
