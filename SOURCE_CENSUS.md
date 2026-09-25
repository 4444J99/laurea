# Source census — Anthony James Padavano

Local evidence edition: 2026-09-24 (America/New_York). Collection timestamp: 2026-09-25T02:14:21.401120+00:00.

## AI instruction library

**184 unique canonical skills; 184/184 passed native structural validation.**

169 subject-category skills across 12 categories, four document skills and 11 plugin skills. Canonical roots are skills/, document-skills/ and plugins/. The 692 outside-root paths are not counted as additional canonical skills.

| Category | Canonical files |
|---|---:|
| document-skills | 4 |
| plugins | 11 |
| creative | 17 |
| data | 10 |
| development | 49 |
| documentation | 7 |
| education | 4 |
| integrations | 14 |
| knowledge | 10 |
| professional | 13 |
| project-management | 9 |
| security | 7 |
| specialized | 6 |
| tools | 23 |

The validator ran with --unique, without --check-links. Metadata validity is not a measurement of task success, licensing originality or sole authorship. This is a maintained and extended corpus.

## Narrative formalization — independently counted

| Source dimension | Enumerated result |
|---|---:|
| Studies / categories | 28 / 8 |
| Algorithm records / unique study-scoped identities | 141 / 141 |
| Axioms | 135 |
| Diagnostic questions | 246 |
| Complete name/purpose/pseudocode/inputs/outputs records | 141 / 141 |
| Cross-reference sequences | 7 |

The core_algorithms field was enumerated directly; these are not 141 independently validated executable algorithms or 28 peer-reviewed publications. Seven cross-reference sequences are a separate count from the earlier seven protocol levels.

## Executed verification — no combined passing-test score

| Project and selection | Passed | Skipped | Failed | Errors |
|---|---:|---:|---:|---:|
| narrative | 324 | 2 | 0 | 0 |
| titan | 48 | 0 | 0 | 0 |
| rege | 1770 | 0 | 2 | 0 |

### narrative

All tests collected in core, CLI and API test directories, with repository import mode; not web/MCP integration or remote model efficacy.

Command: `PYTHONPATH=.:packages/core/src:packages/cli/src:packages/api/src:packages/mcp/src python -m pytest packages/core/tests packages/cli/tests packages/api/tests --import-mode=importlib -q -o addopts= --disable-warnings`

[Execution log](evidence/source-census-2026-09-24/narrative-retry.log)

- skipped: `packages.cli.tests.test_llm_config.TestGetProvider.test_get_provider_anthropic_with_key` — anthropic package not installed
- skipped: `packages.cli.tests.test_llm_config.TestGetProvider.test_get_provider_openai_with_key` — openai package not installed

### titan

Decision/consensus, cross-model replay and migration tests only; not full Titan suite.

Command: `PYTHONPATH=. TEST_USE_REAL_LLM=false python -m pytest tests/test_decision.py tests/test_replay.py tests/test_migration.py -q -o addopts= --disable-warnings`

[Execution log](evidence/source-census-2026-09-24/titan-selected.log)


### rege

Explicit 52-file non-CLI selection, in recorded selection order, executed unprivileged; selected file list is in the verification package.

Command: `python -m pytest <explicit non-CLI file selection> -q -o addopts= --disable-warnings`

[Execution log](evidence/source-census-2026-09-24/rege-non-cli.log)

- failure: `rege.tests.test_formatting.TestColors.test_colors_defined` — AssertionError: assert False
- failure: `rege.tests.test_bloom_misc_final_coverage.TestFormattingNoColor.test_no_color_env_triggers_disable` — AssertionError: assert '' != ''

Full suite did not finish: REPL EOF/interrupt test timed out. Initial root-only permission failure was environment-dependent; unprivileged retry avoided that failure. The two completed-selection failures involve persistent Colors state. Reproduce under supported dependencies before attributing a product defect.

The local environment used Python 3.13 and preinstalled packages, without installing the projects’ locked environments or calling paid models. The two narrative skips were for missing optional Anthropic and OpenAI packages. RE:GE is not certified green: its bounded completed selection has two failures, and the full-suite REPL path timed out. Titan’s 48 passes cover the named three-file selection, not its entire suite.

## Definition counts — not execution claims

| Corpus | Source Python files | Test Python files | Test function definitions |
|---|---:|---:|---:|
| narrative | 60 | 22 | 263 |
| titan | 233 | 106 | 1530 |
| rege | 61 | 59 | 1998 |

These AST counts retain repeated definitions across files, include parameterized function definitions only once each, and are not test-coverage measurements. Generated copies in the larger skills repository are not used as a source-code-volume headline.

## Immutable source identities

**skills:** repository ID `1089036944`, [`6b53d3ec9525`](https://github.com/organvm-iv-taxis/a-i--skills/tree/6b53d3ec952527cc82bb38b272e425a81ee3dd25).

**narrative:** repository ID `1144699044`, [`8ce8b2d03ff0`](https://github.com/organvm-ii-poiesis/narratological-algorithmic-lenses/tree/8ce8b2d03ff0f5483b7120420f11ccefd1236c86).

**titan:** repository ID `1137629933`, [`63444d87f4e8`](https://github.com/organvm-iii-ergon/agentic-titan/tree/63444d87f4e81bea1437c17822893a547ca181f9).

**rege:** repository ID `1140011103`, [`4e8a94450ce1`](https://github.com/4444J99/recursive-engine--generative-entity/tree/4e8a94450ce1ce12d0fb0acbb16215600f854db8).

The [successful census run](https://github.com/4444J99/laurea/actions/runs/36085382938) executed the collector and native skill validator. Its original downloadable artifact expires on 2026-10-25T02:14:34Z; this permanent record retains the hashes, source identities and reproducible collector. The initial wrong-field collector run is explicitly superseded, not promoted as a zero-algorithm result.

Canonical evidence: [evidence/2026-09-24-source-census.json](evidence/2026-09-24-source-census.json).

## Reuse

Audience-specific, source-scoped stat blocks: [engineering](docs/stat-blocks/engineering.md), [research](docs/stat-blocks/research.md), [creative practice](docs/stat-blocks/creative.md), and [learning design](docs/stat-blocks/learning.md).

Private teaching and client source records are stored separately. No private correspondence, student records, client asset contents or font files are included in this public package.
