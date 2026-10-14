# Explicit security priorities and repository scope

Owner: Codex; Laurea PR #10, full gap-filling health evidence model.

Add counts-only vulnerability severity observations and a separate credential-alert count. Validate unique positive alert identities and open state; malformed input stays unmeasured. Missing severity cannot be inferred from an advisory or code-quality error. Full pages preserve lower-bound observed counts and incomplete coverage. No secret, location, package name, alert URL or account metadata leaves the summarizer.

The one requested repository now has an explicit public-observed/private-excluded/unmeasured denominator. Archived public repositories remain included. A current default generation remains separate from required verification, enabled scanner coverage, and PR acceptance.

## Historical evidence and correction (2026-09-20)

The original note claimed: "All 92 tests pass with PYTHONPATH=src python3 -m pytest -q." No exact tested source SHA or retained test-output artifact is bound to that statement here. The 92-test claim is therefore unverified historical reporting, not a current or exact-head acceptance result. Do not combine it with differently scoped 72-, 75-, or 90-test observations to infer a total. The later [172-test receipt for 15fdde32845c70d365d4d37d40b15e9626e0d5b4](https://github.com/organvm/laurea/pull/10#issuecomment-5742349918) is a separate run, not retrospective proof of 92 tests.

The live API read recorded at 2026-09-16T04:55:13Z confirms then-current default faf6c5f67130925518233f5f99a76182b544fb85, 21 listed runs with 10 inspected and no executed steps among those ten, eleven runs unmeasured, empty Dependabot/code-scanning alert lists with coverage still unmeasured, and unavailable secret-scanning evidence. No provider run was launched. The redacted API receipt is docs/receipts/security-scope-observation-20260916.json; it is not a pytest log.

The original plan proposed one integration submission after push. That intention is not evidence of a completed submission. Current source, test, review and integration outcomes remain on PR #10. Hosted admission, deployment, required policy, and the full administered-estate denominator are distinct acceptance obligations.
