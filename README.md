# LAVREA — distinctions, with receipts

## Anthony James Padavano · @4444J99

**AI systems builder and multimedia artist connecting language, executable structure, and human experience.**

**[Explore the Distinction Atlas](DISTINCTIONS.md)** — nine documented areas spanning systems engineering, instruction design, computational representation, literary infrastructure and released music; four problem-fit pathways for applied AI, creative technology, learning and research.

The atlas connects what the work demonstrates to where it can help. Its [source registry](evidence/2026-09-22-distinction-atlas.json) and [method](docs/distinction-method.md) preserve the evidence behind each connection. The achievement ledger below remains the canonical record of the measured activity distinction and accepted upstream work.

| Distinction | Evidence |
|---|---|
| **Top 0.029% by observed public GitHub push-event volume** | Rank **5,045 of 17,775,327 active accounts**, October 2025–June 2026; a measured comparison, not an estimated distribution. |
| **35,896 GitHub contribution events · 318 active days** | Trailing-year profile manifest generated **September 22, 2026**. |
| **Four confirmed upstream merges** | **FastMCP, Datadog GuardDog, Temporal Python SDK, and dbt MCP** accepted distinct contributions. |
| **Python-centered, cross-stack systems corpus** | **88 Python-primary repositories** among **168 classified original ecosystem repositories**, spanning **13 primary-language labels**, in the September 22 manifest. |

**[Read the achievement ledger](ACHIEVEMENTS.md)** · **[Inspect the frozen evidence and replayable SQL](evidence/2026-09-22-achievements.json)** · **[Understand the measurement](METHODOLOGY.md)**

The public-event ranking includes automated accounts and is specific to push frequency in the observed dataset. It is not an authored-commit, Python-only, private-activity, or engineering-quality ranking. The separately recruiter-originated **top-1% Python committer** distinction is retained with its provenance in the ledger.

## Beyond activity: accepted work

| Project | Contribution |
|---|---|
| [FastMCP #3662](https://github.com/PrefectHQ/fastmcp/pull/3662) | Corrected OpenAPI object query serialization, with regression tests. |
| [GuardDog #703](https://github.com/DataDog/guarddog/pull/703) | Normalized equivalent git URLs to prevent security-scanner false positives. |
| [Temporal Python SDK #1385](https://github.com/temporalio/sdk-python/pull/1385) | Documented OpenTelemetry and Prometheus configuration behavior. |
| [dbt MCP #669](https://github.com/dbt-labs/dbt-mcp/pull/669) | Clarified the OAuth authentication experience for developers using team-configured tooling. |

The distinction is the combination: measurable activity at scale, a Python-centered systems corpus, and accepted work that improves both machine behavior and the human understanding of that behavior.

## What LAVREA does

LAVREA discovers, measures, and presents the strongest evidence-backed distinctions in this body of work. The achievement comes first; its scope is visible beside it; the detailed proof is one click away.

Facts live in dated evidence records. Derived rankings retain the actual cohort, SQL, dates, counts, and rounding rule. Historical third-party findings retain their attribution. A failed later reconstruction does not erase an earlier finding, and missing context is not disproof.

### Build audience-specific distinction reports

```bash
python scripts/build_distinction_atlas.py --check
python scripts/build_distinction_atlas.py --audience applied-ai
python scripts/build_distinction_atlas.py --audience creative-technology
python scripts/build_distinction_atlas.py --audience learning-design
python scripts/build_distinction_atlas.py --audience research
python -m unittest discover -s tests -p 'test_distinction_atlas.py' -v
```

These reports are generated offline from reviewed public evidence. They are not autonomous research runs. Each pathway connects several documented capabilities to a proposed use, a demonstration and an outcome measure.

### Verify the achievement record

These commands are offline and require only Python's standard library. They validate the saved arithmetic and evidence structure; they do not pretend to refetch the external dataset.

```bash
python scripts/verify_achievements.py
python -m unittest discover -s tests -p test_achievement_evidence.py -v
```

The evidence file includes the two SQL queries and HTTP replay URLs for independent remeasurement. Refreshes create new dated records rather than silently rewriting historical results. Automated regression checks also run on relevant pull requests and pushes.

<details>
<summary>Earlier generated API profile and cards — dated snapshot, separate measurement scope</summary>

The [generated profile](assets/PROFILE.md) and [metrics](assets/metrics.json) retain the earlier API snapshot. Their dates and visible-repository scope differ from the September 22 ecosystem manifest above; do not mix their counts.

<p align="center"><img src="assets/cards/hero.svg" alt="Earlier dated GitHub API activity snapshot" width="800"/></p>
<p align="center"><img src="assets/cards/contributions_year.svg" alt="Earlier contribution activity" width="420"/><img src="assets/cards/repos_visible.svg" alt="Earlier visible non-fork corpus" width="420"/></p>
<p align="center"><img src="assets/cards/language_breadth.svg" alt="Earlier primary-language breadth" width="420"/><img src="assets/cards/language_layer_coverage.svg" alt="Earlier mapped language-layer coverage" width="420"/></p>

</details>

## The arena

An issue titled `arena: your-login` asks CI to compute the same bounded API fields for another public account and update [LEADERBOARD.md](LEADERBOARD.md). Ordering that table by activity is not a quality ranking or the population comparison reported above.

## Run it on yourself

Use this repository as a template or fork it, then enable Actions. A personal copy defaults to its repository owner; an organization-owned copy should set `LAUREA_LOGIN`. The legacy canonical `organvm/laurea` workflow target remains `4444J99`. Optionally add a `LAUREA_TOKEN` secret for restricted contribution counts and private organization visibility.

```bash
pip install -e '.[test]'
laurea run --login YOUR_LOGIN
laurea axes
python -m pytest tests -q
```

LAVREA has zero runtime dependencies. The frozen Anthony-specific achievement record remains explicitly identified; running API cards for a different account does not transfer these distinctions to that account.

## License

MIT.
