"""Validate frozen achievement evidence offline; never infer one metric from another."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'evidence' / '2026-09-22-achievements.json'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(record: dict[str, Any]) -> dict[str, Any]:
    require(record['schema_version'] == 'laurea.achievement-evidence.v1', 'Unsupported schema')
    ranking = record['ranking']
    require(ranking['metric'] == 'observed_public_push_events', 'Do not relabel pushes as commits')
    target, cohort = ranking['target_result'], ranking['cohort_result']
    for name in ('push_events', 'repositories_pushed'):
        require(type(target[name]) is int and target[name] > 0, f'Invalid {name}')
    for name in ('active_accounts', 'accounts_strictly_above', 'accounts_tied', 'p99_pushes', 'total_push_events'):
        require(type(cohort[name]) is int and cohort[name] >= 0, f'Invalid {name}')
    population, above, tied = (cohort[k] for k in ('active_accounts', 'accounts_strictly_above', 'accounts_tied'))
    require(population > 0 and tied >= 1 and above + tied <= population, 'Invalid cohort or ties')
    require(cohort['total_push_events'] >= population and cohort['total_push_events'] >= target['push_events'], 'Invalid event total')
    require(cohort['p99_pushes'] > 0, 'Invalid p99')
    start, end = (ranking['window'][k] for k in ('start_inclusive', 'end_exclusive'))
    require(datetime.fromisoformat(start) < datetime.fromisoformat(end), 'Invalid window')
    require(start <= target['first_push'] <= target['last_push'] < end, 'Target outside cohort window')
    for query in (ranking['target_sql'], ranking['cohort_sql']):
        require(start in query and end in query and "event_type = 'PushEvent'" in query, 'SQL scope mismatch')
    require("actor_login != ''" in ranking['cohort_sql'], 'Cohort must exclude empty logins')
    require(f"pushes > {target['push_events']}" in ranking['cohort_sql'], 'SQL threshold mismatch')
    require(f"pushes = {target['push_events']}" in ranking['cohort_sql'], 'SQL tie threshold mismatch')
    rank = above + 1
    upper_tail = Decimal(above + tied) * 100 / Decimal(population)
    published = upper_tail.quantize(Decimal('0.001'), rounding=ROUND_CEILING)
    require(rank == ranking['derived']['rank'], 'Rank mismatch')
    require(published == Decimal(ranking['derived']['top_percent_conservative']), 'Percentage mismatch')
    require(0 < upper_tail < 1, 'This snapshot does not establish top 1%')
    profile = record['profile']
    require(profile['contribution_calendar_events'] == 35896, 'Historical calendar snapshot changed; append a new record')
    require(profile['current_commit_only_total'] is None, 'No current commit-only measurement in this evidence')
    require(profile['primary_language_labels'] == len(profile['languages']), 'Language-label count mismatch')
    require(sum(profile['languages'].values()) == profile['classified_original_repositories'], 'Repository language totals mismatch')
    require(profile['python_primary_repositories'] == profile['languages']['Python'], 'Python primary-language mismatch')
    require(re.fullmatch(r'[0-9a-f]{40}', profile['source_blob_sha']) is not None, 'Missing profile source pin')
    historic = record['historical_python_distinction']
    require(historic['status'] == 'owner_attested_recruiter_finding', 'Do not erase or promote the distinct historical finding')
    require(historic['original_recruiter_artifact_recovered'] is False, 'Original artifact is not in this frozen record')
    require(bool(historic['retention_rule']), 'Missing historical retention rule')
    seen = set()
    for item in record['upstream_merges']:
        identity = (item['repository'], item['number'])
        require(identity not in seen, 'Duplicate upstream merge')
        seen.add(identity)
        require(item['merged'] is True and item['author'] == record['subject']['login'], 'Unaccepted or misattributed upstream work')
        require(re.fullmatch(r'[0-9a-f]{40}', item['merge_sha']) is not None, 'Missing merge SHA')
        datetime.fromisoformat(item['merged_at'].replace('Z', '+00:00'))
        require(item['source_url'] == f"https://api.github.com/repos/{item['repository']}/pulls/{item['number']}", 'Merge source mismatch')
    require(len(seen) == 4, 'Frozen upstream evidence incomplete')
    return {'rank': rank, 'active_accounts': population, 'top_percent_conservative': str(published),
            'push_events': target['push_events'], 'contribution_calendar_events': profile['contribution_calendar_events'],
            'verified_upstream_merges': len(seen)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', nargs='?', type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.evidence.read_text(encoding='utf-8')))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'Evidence validation failed: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
