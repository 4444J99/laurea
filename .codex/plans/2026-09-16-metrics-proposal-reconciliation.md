# Metrics proposal reconciliation

Owner: organvm/laurea PR #10; review 4023513106.

The daily metrics workflow now opts into bounded pending-proposal refresh and fetches ancestry. Publisher ownership discovery covers both metrics and arena-table branches, retaining multiple proposals as explicit pending owners. Metrics requires the current default generation. A single assets-only predecessor can advance through a normal fast-forward push with both predecessor/default parents; unrelated changes and generated symlinks fail closed. Existing ambiguity handling remains one write attempt and one readback.

## Historical verification stages (clarified 2026-09-20)

This note originally recorded an isolated-Git metrics integration case passing in 1.43 seconds, a preceding publication suite of 30 tests in 18.04 seconds, workflow/diff checks, and "Full final-source suite: 156 passed in 19.24 seconds." The integration case covers current metrics/default files, both parents, default preservation, and no duplicate PR or force push. These numbers describe the intermediate stage of this note; they are not a final count for every later PR revision. No immutable tested head was recorded beside the 156-test assertion, so it must not be used as exact-head acceptance evidence.

The PR's later evidence history explicitly binds **158 passed in 19.29 seconds** to aacd88367ebb5b4784793d08a6970169b6c33236. Its [subsequent 172-test receipt](https://github.com/organvm/laurea/pull/10#issuecomment-5742349918) binds a different run to 15fdde32845c70d365d4d37d40b15e9626e0d5b4. These are separate source generations, not conflicting totals for one execution. Current verification is the exact-head receipt on PR #10, not a rolling test count in this historical note.

These are source and local Git records. Hosted admission, server-side enforcement, generated-PR checks, merge, and deployed behavior are not established by them. Arena issue settlement remains separate. The original instruction to keep the PR draft was an intermediate review posture; current draft/open/merged state must be read from GitHub rather than inferred from this note.
