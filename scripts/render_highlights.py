"""Render the current README highlights from pinned, dated evidence; offline only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- LAVREA:HIGHLIGHTS:START -->'
END = '<!-- LAVREA:HIGHLIGHTS:END -->'
# Refresh by adding a reviewed, dated record and updating its pin; never alter history.
INPUTS = {
    '2026-09-22-achievements.json': '1b1bee9c8b82a88e64030325a68fb35422491a88',
    '2026-09-22-multi-axis-statistics.json': '16bf7c3aa02f79f44b722fce984f2226975704dd',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_record(root: Path, name: str) -> dict[str, Any]:
    raw = (root / 'evidence' / name).read_bytes()
    oid = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    require(oid == INPUTS[name], f'Evidence pin mismatch: {name}')
    data = json.loads(raw)
    require(isinstance(data, dict), 'Evidence must be an object')
    return data


def upper_tail(above: int, tied: int, population: int) -> Decimal:
    require(all(type(v) is int for v in (above, tied, population)), 'Integer counts required')
    require(above >= 0 and tied > 0 and above + tied <= population, 'Invalid cohort')
    return (Decimal(above + tied) * 100 / Decimal(population)).quantize(
        Decimal('0.001'), rounding=ROUND_CEILING)


def render(root: Path = ROOT) -> str:
    base = load_record(root, '2026-09-22-achievements.json')
    more = load_record(root, '2026-09-22-multi-axis-statistics.json')
    require(base['subject']['login'] == more['subject'] == '4444J99', 'Subject mismatch')
    r, a = base['ranking'], more['archive']
    require(r['window']['start_inclusive'] == a['window_start_inclusive']
            and r['window']['end_exclusive'] == a['window_end_exclusive'], 'Window mismatch')
    c, pc, qc = r['cohort_result'], a['push_cohorts'], a['pr_cohort']
    require(c['active_accounts'] == pc['active_accounts'], 'Push cohort mismatch')
    ranks = [upper_tail(c['accounts_strictly_above'], c['accounts_tied'], c['active_accounts']),
             upper_tail(pc['days_above'], pc['days_tied'], pc['active_accounts']),
             upper_tail(qc['above'], qc['tied'], qc['pr_openers'])]
    require(all(v < 1 for v in ranks), 'Top-1% headline is not supported')
    merges = base['upstream_merges'] + more['upstream_acceptance']['newly_recovered_historical_merges']
    unique = {}
    for m in merges:
        require(m['author'] == '4444J99' and m['merged'] is True, 'Unaccepted or misattributed work')
        require(re.fullmatch('[0-9a-f]{40}', m['merge_sha']) is not None, 'Missing merge identity')
        key = (m['repository'].casefold(), m['number'])
        require(key not in unique, 'Duplicate merge evidence')
        unique[key] = m
    projects = {key[0] for key in unique}
    albums = more['creative_catalog']['albums']
    tracks = seconds = 0
    for album in albums:
        total = 0
        for text in album['track_durations_display']:
            minute, second = map(int, text.split(':'))
            require(minute >= 0 and 0 <= second < 60, 'Invalid track duration')
            total += minute * 60 + second
        require(total == album['duration_seconds'] and len(album['track_durations_display']) == album['tracks'],
                'Album inputs do not match totals')
        tracks += album['tracks']
        seconds += total
    h, rem = divmod(seconds, 3600)
    minute, second = divmod(rem, 60)
    duration = f'{h}:{minute:02}:{second:02}'
    p, n = base['profile'], more['narrative_corpus']
    repair = more['upstream_acceptance']['predicate_reproduction']
    lines = [START, '## Statistical highlights', '',
        'Evidence edition: **September 22, 2026**. These are dated findings, not live counters.', '',
        '| Dimension | Result | Evidence and scope |', '|---|---|---|',
        f"| Comparative activity | **Top 1% on {len(ranks)} measured axes** | Push volume **{ranks[0]}%**, push-active days **{ranks[1]}%**, PR openings **{ranks[2]}%**; upper-tail positions in the observed public dataset, October 2025–June 2026. |",
        f"| Annual participation | **{p['contribution_calendar_events']:,} contributions · {p['active_days']} active days** | Trailing-year contribution-calendar snapshot, September 22, 2026. |",
        f"| External acceptance | **{len(unique)} accepted contributions across {len(projects)} independent upstream projects** | Authored PRs with recorded merge identifiers; the expanded six-project record supersedes the earlier four-project selection. |",
        f"| Released music | **{len(albums)} releases · {tracks} tracks · {duration} of audio** | ETCETER4 catalog; sum of displayed durations, including a remix collection. |",
        f"| Narrative corpus | **{n['recorded_studies']} studies · {len(n['categories'])} categories · {n['recorded_algorithms']} algorithm descriptions** | Repository-reported corpus dimensions; not an independent enumeration or execution of all algorithms. |",
        f"| Correctness repair | **{repair['correct_min_accepted_rows']:,}-row minimum restored where {repair['faulty_min_accepted_rows']} rows passed** | Accepted Dagster-project predicate fix, with {repair['undersized_row_counts_wrongly_accepted']:,} undersized row-count cases reproduced locally. |",
        f"| Technical concentration | **{p['python_primary_repositories']} Python-primary repositories** | {p['classified_original_repositories']} classified non-fork ecosystem repositories; {p['primary_language_labels']} primary-language labels in the dated manifest. |", '',
        f"The push-volume and active-day comparison populations each contain **{pc['active_accounts']:,} accounts**; the PR-opening population contains **{qc['pr_openers']:,} accounts**. These include automated accounts and observed public events only. The three metrics are related, not independent probabilities; they are not multiplied into a composite rank.", '',
        '**[Full statistical evidence](STATISTICS.md)** · **[Original achievement ledger](ACHIEVEMENTS.md)** · **[Whole-practice atlas](DISTINCTIONS.md)**', '',
        '### Accepted work outside the owner ecosystem', '',
        '| Upstream contribution | Merged |', '|---|---|']
    for m in sorted(merges, key=lambda x: x['repository'].casefold()):
        # Repository names and numbers are from the reviewed pinned records, not arbitrary URLs.
        url = f"https://github.com/{m['repository']}/pull/{m['number']}"
        lines.append(f"| [{m['repository']} #{m['number']}]({url}) | {m['merged_at'][:10]} |")
    lines += ['', 'The recruiter-originated **top-1% Python committer** finding remains separately attributed in the achievement ledger. None of these newer comparisons erases or relabels that history.', END]
    return '\n'.join(lines)


def replace_block(text: str, block: str) -> str:
    require(text.count(START) == 1 and text.count(END) == 1, 'Exactly one highlight marker pair required')
    before, rest = text.split(START)
    _, after = rest.split(END)
    require(text.index(START) < text.index(END), 'Reversed markers')
    return before + block + after


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        path = ROOT / 'README.md'
        old = path.read_text(encoding='utf-8')
        new = replace_block(old, render())
        if args.check:
            require(old == new, 'README statistics drift; run python scripts/render_highlights.py')
            print('README highlights match the pinned evidence and recomputed arithmetic.')
        else:
            path.write_text(new, encoding='utf-8')
            print('README highlights regenerated; dated evidence unchanged.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'Highlight validation failed: {exc}\n')


if __name__ == '__main__':
    main()
