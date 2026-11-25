# MEASURED PROFILE

*Generated 2026-11-25T09:23:16.455139Z for [@4444J99](https://github.com/4444J99). Counts come from the GitHub API; derived observations name their transformation. No percentile ranking is published because this repository does not carry a validated population distribution.*

*Source implementation: `4444J99/laurea` at `9edbf2d281f725e7f8c5ca13bbe0db5ba741e75e`.*

## Source coverage

Collection: **complete**. Health: **unmeasured**.

Observed repositories: 84; private repositories excluded: 0; failed sources: 0.

Token-visible membership scope is not an administered-estate census. Default SHA identifies a source generation; it does not prove executed verification, security coverage or PR readiness.

## CI health across the active corpus — **measured**

**Observed:** 0.9 fraction

35 of 41 active repositories have a green latest completed default-branch run; 2 have no CI at all.

**Definition:** REST check-runs and commit status on the default-branch head.

**Boundary:** A green latest run is not evidence of correctness, only of a passing gate at that head.

## GitHub contribution activity (12 months) — **measured**

**Observed:** 54,553 contribution events

GitHub reports 54,553 contribution-calendar events in the last 12 months. Associated API fields report 5,290 commits, 1,806 pull requests, 58 reviews, and 1,894 issues; these fields are not an additive breakdown.

**Definition:** GitHub GraphQL contributionsCollection and contributionCalendar.

**Boundary:** This is an activity count, not a count of shipped units. GitHub events vary in scope and do not establish review, merge, quality, or impact.

## Documentation density across the active corpus — **measured**

**Observed:** 1 fraction

41 of 41 active repositories have a README of at least 1024 bytes; 34 have a docs/ directory.

**Definition:** REST git-trees probe of the default branch; substantive means at least 1024 bytes.

**Boundary:** A long README is not evidence the docs are accurate or current.

## Visible organization memberships — **measured**

**Observed:** 10 organizations

GitHub returned 10 organization memberships for this account.

**Definition:** GitHub GraphQL user.organizations (paginated, visible to the token).

**Boundary:** Membership does not by itself establish ownership, administrative authority, or individual responsibility for every repository in an organization.

## Pull requests opened (12 months) — **measured**

**Observed:** 1,806 pull requests

GitHub reports 1,806 pull requests opened in the trailing 12-month collection.

**Definition:** GitHub GraphQL contributionsCollection.totalPullRequestContributions.

**Boundary:** Opened pull requests are activity events; this field does not say whether they were reviewed, mergeable, merged, distinct in scope, or created without automation.

## Visible non-fork repository corpus — **measured**

**Observed:** 60 repositories

60 non-fork repositories were visible across the personal account and 10 organization memberships returned by the API.

**Definition:** GitHub GraphQL repositories connections with isFork=false.

**Boundary:** Organization repositories can include work by other contributors. Visibility does not establish individual authorship, maintenance, or operation.

## Test-suite presence across the active corpus — **measured**

**Observed:** 1.0 fraction

39 of 41 active repositories show a test signal: a tests/ or test/ directory, a *_test.py or *.test.* file, pyproject [tool.pytest], or a CI test step.

**Definition:** REST git-trees probe of the default branch plus workflow-file read.

**Boundary:** Presence of a test suite is not evidence tests pass or cover anything.

## Primary-language breadth of the visible corpus — **derived**

**Observed:** 4 primary-language labels

GitHub assigns 4 distinct primary-language labels across the visible non-fork corpus — led by Python (35), TypeScript (10), HTML (8), JavaScript (3).

**Definition:** Distinct repository.primaryLanguage.name values in the visible corpus.

**Boundary:** A repository has one GitHub-assigned primary language. This describes the corpus and does not establish individual proficiency or authorship.

## Mapped language-layer coverage — **derived**

**Observed:** 2 mapped layers

The static language map places the visible corpus in 2 layers: backend, frontend.

**Definition:** Deterministic primary-language-to-layer mapping in src/laurea/detectors.py.

**Boundary:** This is a corpus classification, not evidence that one person authored, shipped, or is proficient in every mapped layer.

## Account age — **derived**

**Observed:** 9.9 years

The GitHub account was created in 2016 (9.9 years ago).

**Definition:** GitHub GraphQL user.createdAt.

**Boundary:** Account age is not equivalent to continuous professional experience or activity.

## What these numbers do not establish

LAVREA reports an API-visible activity and repository corpus. It does not establish:

- individual authorship or responsibility for organization repositories
- code quality, correctness, maintainability, or security
- whether pull requests were reviewed, mergeable, or merged
- system reliability in production
- product adoption, user satisfaction, or business impact
- professional experience or engineering judgment
- reliability or engineering judgment — likely not GitHub-measurable; kept here rather than proxied

GitHub activity does not establish authorship, quality, reliability, adoption, or impact.
