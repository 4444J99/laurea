# Additional statistical profile — Anthony James Padavano

Measured September 22, 2026 (America/New_York). These are additional statistical
dimensions, not alternative phrasings of the existing push-volume rank.

## New matched-cohort comparisons

All comparisons use October 1, 2025 inclusive through July 1, 2026 exclusive,
in ClickHouse's observed public GitHub event dataset. Account logins are
case-normalized; automated accounts are included.

| Dimension | Observed value | Eligible comparison population | Tie-inclusive upper-tail share, rounded upward | Context |
|---|---:|---:|---:|---|
| Persistence: distinct UTC dates with public pushes | 155 days | 17,775,327 public-push accounts | **Top 0.230%** | The 99th-percentile count was 78 days; 155 is 1.99 times that threshold. |
| Change proposals: distinct observed public PR openings | 70 | 2,267,625 accounts with public PR openings | **Top 0.800%** | The 99th-percentile count was 60; openings are not merges. |
| Repository-name reach: distinct names receiving pushes | 345 name strings | 17,775,327 public-push accounts | **Top 0.007%** | The 99th-percentile count was 19; 18.16 times that threshold. This includes forks and historical names, not 345 owned products. |

This adds persistence, proposal activity and name-based reach to the previously
saved push-volume statistic. They are related metrics; their percentiles must not
be multiplied into a combined rarity probability.

The PR count is deduplicated by repository name plus PR number. Repository
transfers/renames can affect name-based identities. The source is mutable and not
an audit of every archive hour. These are measured ranks within the observed
dataset, not current full-GitHub or human-only ranks. The 70 PRs and 155 days do
not replace the later annual contribution-calendar record.

**Reusable headline:** "Top 1% in three separately measured public GitHub activity
dimensions: push volume, push-active days, and observed PR openings." Attach the
window and metric-specific populations above. Name-based reach belongs in the
expanded evidence, not a claim about product ownership.

## Released creative output

Summing the displayed track durations on the five ETCETER4 release pages:

| Release | Artist-listed release date | Listed tracks | Sum of displayed track durations |
|---|---|---:|---:|
| [etcetera](https://etceter4.bandcamp.com/album/etcetera) | 2012-05-01 | 9 | 40:16 |
| [progres\\digres](https://etceter4.bandcamp.com/album/progres-digres) | 2013-01-01 | 11 | 54:11 |
| [OGOD](https://etceter4.bandcamp.com/album/o-g-o-d) | 2015-03-01 | 29 | 1:28:29 |
| [R M X S](https://etceter4.bandcamp.com/album/r-m-x-s) | 2016-01-01 | 8 | 33:04 |
| [PASSING//THRU](https://etceter4.bandcamp.com/album/passing-thru) | 2017-04-18 | 6 | 34:51 |
| **Observed catalog total** | **Five release pages** | **63** | **4:10:51** |

OGOD alone is a 29-part, 88-minute-29-second release with a linked visual album.
The earliest listed release predates this measurement by more than 14 years;
that is a historical starting point, not proof of uninterrupted professional
activity. The catalog includes an 8-track remix collection: do not relabel the
total as 63 original compositions or imply commissioned remixes.

**Reusable line:** "A five-release ETCETER4 catalog containing 63 listed tracks
and more than four hours of audio, including the 29-part audiovisual project OGOD."

Release dates are artist-published; durations sum displayed timestamps rather
than measuring downloaded audio. No sales or acclaim claim is derived.

## Six externally accepted contribution records

The four earlier verified projects are joined by two recovered historical merges:

- [jairus-m/dagster-sdlc#22](https://github.com/jairus-m/dagster-sdlc/pull/22),
  merged March 27, 2026, `058dc6abb4ca33e6c50c615a539d58fbeaed5132`.
- [primeinc/github-stars#39](https://github.com/primeinc/github-stars/pull/39),
  merged May 10, 2026, `573b457043c2c78dd7b5446d78e6a7edc3c056b1`.

Together with FastMCP, GuardDog, Temporal Python SDK and dbt MCP, this is
**six verified independent upstream repositories accepting work authored by
4444J99**. This expands the verified set; it is not six new merges today or proof
that the six records exhaust all contributions.

### A quantified correctness repair

The accepted one-line Dagster-project fix changes:

```python
num_rows > 1500 & num_cols == 8
# to
num_rows > 1500 and num_cols == 8
```

With exactly eight columns, the faulty predicate accepted **9 rows** where the
intended minimum was **1,501 rows**. Exhaustive evaluation for integer row counts
0 through 1,501 identified **1,492 undersized row counts** that passed the faulty
check and were rejected by the repaired check.

**Reusable line:** "Contributed an accepted data-validation fix that restored a
1,501-row minimum where an operator-precedence bug allowed nine rows to pass."

The exhaustive predicate reproduction was executed in this verification. It is
not a rerun of the upstream suite. The final accepted diff contains one line,
so the ten new tests claimed in the original PR description are not counted as
accepted tests here.

## Quantitative scale of narrative formalization

The public Narratological Algorithmic Lenses project records:

| Quantity | Recorded value | Evidence level |
|---|---:|---|
| Compendium studies | **28** | `meta.study_count` in the structured compendium, generated June 6, 2026 |
| Compendium categories | **8** | Enumerated metadata: Animation, Classical, Comics, Film, Interactive, Literature, Meta, Television |
| Formalized algorithms | **141** | Current README count; not independently enumerated or executed here |
| Protocol levels | **7** | README's P1–P7 analysis-depth description |
| Bounded legacy suite | **92 algorithms from 14 studies** | README's separately scoped legacy selection, not extra algorithms to add to 141 |

Sources: [compendium](https://github.com/organvm-ii-poiesis/narratological-algorithmic-lenses/blob/main/specs/03-structured-data/narratological-algorithms-unified.json),
blob `d082da127aa047d746941c9ada2da29aa9df2195`; [README](https://github.com/organvm-ii-poiesis/narratological-algorithmic-lenses/blob/main/README.md),
blob `631fc33599d8273add4d8fdef576a6bf27b56a65`.

**Reusable line:** "Developed a narrative-formalization corpus recorded as
28 studies across eight categories, with 141 algorithm descriptions and seven
analysis-depth levels."

These are repository-recorded corpus dimensions, not 28 peer-reviewed
publications or 141 independently validated runnable algorithms.

## What has not been converted into a public achievement

The search recovered application-level teaching and audience claims, but not the
section-level, learner-deduplicated, platform-analytics or attribution records
needed for new outcome calculations. Contact hours, essays assessed, attributable
fundraising and unique viewers remain uncomputed rather than invented.
Private implementation material was not copied into this public evidence.

## Reproduction and continuity

Raw inputs, per-track durations, source URLs, SQL, retrieval identifiers, exact
denominators, ties, and calculation boundaries:
[`evidence/2026-09-22-multi-axis-statistics.json`](evidence/2026-09-22-multi-axis-statistics.json).

Recalculate the arithmetic and exhaustively reproduce the accepted predicate:

```bash
python scripts/derive_multi_axis_statistics.py
```

This is offline arithmetic, not a fresh fetch of the comparison dataset.
The original `evidence/2026-09-22-achievements.json` remains unchanged. A later
observation must retain its own date, source, scope, and actual calculation.
