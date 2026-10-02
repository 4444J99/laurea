# External-owner pull-request census — October 2, 2026

## Measured snapshot

**32 public pull requests authored by `4444J99` across 30 current repository identities outside the `4444J99` namespace: 7 merged, 13 open, 12 closed unmerged.**

The selection rule is the GitHub query `author:4444J99 is:pr -user:4444J99`, followed by an exact per-PR read that rechecks the author, current state, base repository stable ID, head SHA and base SHA. Identity is `(base_repository_id, pull_request_number)`, so two PRs in the same repository do not inflate the repository count.

This is a **dated current-owner namespace census**, not a lifetime-submission total and not a statement that all 30 repositories are independent of Anthony. Repository transfers, affiliations, visibility and GitHub search indexing can affect the returned set.

## Relationship to the verified upstream-acceptance set

The independently verified upstream-acceptance record remains **six projects**: FastMCP, Datadog GuardDog, Temporal Python SDK, dbt MCP, `jairus-m/dagster-sdlc`, and `primeinc/github-stars`.

This namespace census contains **seven merged PRs** because it additionally returns [`unnamedplay-r/etceter4#1`](https://github.com/unnamedplay-r/etceter4/pull/1). That historical creative-project merge is deliberately retained in the namespace census but **not promoted into the independent upstream set**.

## Current states

| Repository PR | State | Stable repository ID |
|---|---|---:|
| [a2aproject/a2a-python #915](https://github.com/a2aproject/a2a-python/pull/915) | closed unmerged | `980428225` |
| [aden-hive/hive #6707](https://github.com/aden-hive/hive/pull/6707) | closed unmerged | `1132431999` |
| [anthropics/anthropic-sdk-python #1306](https://github.com/anthropics/anthropic-sdk-python/pull/1306) | open | `590187800` |
| [anthropics/skills #723](https://github.com/anthropics/skills/pull/723) | open | `1061953414` |
| [camel-ai/camel #3974](https://github.com/camel-ai/camel/pull/3974) | open | `615510678` |
| [coinbase/agentkit #1054](https://github.com/coinbase/agentkit/pull/1054) | open | `881569514` |
| [dapr/dapr #9719](https://github.com/dapr/dapr/pull/9719) | open | `192632000` |
| [databricks/dbt-databricks #1376](https://github.com/databricks/dbt-databricks/pull/1376) | closed unmerged | `419004753` |
| [DataDog/guarddog #703](https://github.com/DataDog/guarddog/pull/703) | merged | `503403377` |
| [dbt-labs/dbt-mcp #669](https://github.com/dbt-labs/dbt-mcp/pull/669) | merged | `947516890` |
| [grafana/k6 #5770](https://github.com/grafana/k6/pull/5770) | closed unmerged | `54400687` |
| [indeedeng/iwf #601](https://github.com/indeedeng/iwf/pull/601) | open | `518169634` |
| [ipqwery/ipapi-py #8](https://github.com/ipqwery/ipapi-py/pull/8) | open | `886694502` |
| [jairus-m/dagster-sdlc #22](https://github.com/jairus-m/dagster-sdlc/pull/22) | merged | `882969720` |
| [jupyter/jupyter #802](https://github.com/jupyter/jupyter/pull/802) | closed unmerged | `36895421` |
| [langchain-ai/langgraph #7237](https://github.com/langchain-ai/langgraph/pull/7237) | open | `676672661` |
| [m13v/summarize_recent_commit #1](https://github.com/m13v/summarize_recent_commit/pull/1) | open | `829266807` |
| [m13v/summarize_recent_commit #2](https://github.com/m13v/summarize_recent_commit/pull/2) | open | `829266807` |
| [makenotion/notion-mcp-server #242](https://github.com/makenotion/notion-mcp-server/pull/242) | open | `946169991` |
| [modelcontextprotocol/python-sdk #2361](https://github.com/modelcontextprotocol/python-sdk/pull/2361) | closed unmerged | `862584018` |
| [modelcontextprotocol/typescript-sdk #1799](https://github.com/modelcontextprotocol/typescript-sdk/pull/1799) | closed unmerged | `862578138` |
| [openai/openai-agents-python #2802](https://github.com/openai/openai-agents-python/pull/2802) | closed unmerged | `946380199` |
| [pionxzh/chatgpt-exporter #316](https://github.com/pionxzh/chatgpt-exporter/pull/316) | closed unmerged | `574411233` |
| [PrefectHQ/fastmcp #3662](https://github.com/PrefectHQ/fastmcp/pull/3662) | merged | `896296825` |
| [primeinc/github-stars #39](https://github.com/primeinc/github-stars/pull/39) | merged | `1019799780` |
| [pydantic/pydantic-ai #4912](https://github.com/pydantic/pydantic-ai/pull/4912) | closed unmerged | `818331198` |
| [rclone/rclone #8969](https://github.com/rclone/rclone/pull/8969) | closed unmerged | `17803236` |
| [tadata-org/fastapi_mcp #274](https://github.com/tadata-org/fastapi_mcp/pull/274) | open | `944976593` |
| [temporalio/sdk-python #1385](https://github.com/temporalio/sdk-python/pull/1385) | merged | `451613653` |
| [TheGuardDawg/print2a #1](https://github.com/TheGuardDawg/print2a/pull/1) | closed unmerged | `250886099` |
| [TheGuardDawg/print2a #2](https://github.com/TheGuardDawg/print2a/pull/2) | open | `250886099` |
| [unnamedplay-r/etceter4 #1](https://github.com/unnamedplay-r/etceter4/pull/1) | merged | `73011784` |

## Reproduction boundary

Machine-readable evidence: [`evidence/2026-10-02-external-owner-pr-census.json`](evidence/2026-10-02-external-owner-pr-census.json).

Offline verification:

```bash
python scripts/render_external_pr_census.py --check
python -m unittest discover -s tests -p 'test_external_owner_pr_census.py' -v
```

The verifier recomputes the PR and repository counts, enforces stable identity and author/current-owner boundaries, validates merge identities, and prevents the seven namespace merges from silently replacing the six independently verified upstream acceptances.
