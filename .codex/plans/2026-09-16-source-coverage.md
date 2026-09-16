# Explicit source coverage

Owner: Codex. Implements the Laurea coverage tranche of Limen's gap-filling plan.

The collector previously omitted failed organizations and stopped membership
scope at 20. Paginate both connections with finite limits, stable totals and
advancing cursors. Preserve failed sources as unmeasured. Record immutable public
repository IDs and current default SHAs; exclude private repository identities
while retaining counts. Collection completeness is distinct from health evidence.

Verification, security and PR readiness remain explicitly unmeasured. Follow-up
must collect exact-generation executed checks, security obligations and current
PR acceptance; token-visible memberships cannot replace the 326-repository
administered estate denominator. No deployment or estate-health acceptance is
claimed by this source-coverage implementation.

Verification: `PYTHONPATH=src python3 -m pytest -q`.
Pagination reference: https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api
