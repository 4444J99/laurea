"""Build audience-specific distinction reports from reviewed evidence; no network calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'evidence/2026-09-22-distinction-atlas.json'
AUDIENCES = {'applied-ai', 'creative-technology', 'learning-design', 'research'}
KINDS = {'comparison', 'external-acceptance', 'implementation', 'external-credit', 'released-artifact', 'lead'}
LABELS = {'comparison': 'Measured comparison', 'external-acceptance': 'Accepted upstream',
          'implementation': 'Inspected implementation', 'external-credit': 'Independent credit',
          'released-artifact': 'Published creative artifact', 'lead': 'Discovery lead'}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def indexed(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    require(isinstance(items, list), f'{label} must be a list')
    result = {}
    for item in items:
        key = item['id']
        require(isinstance(key, str) and bool(re.fullmatch(r'[a-z0-9-]+', key)), f'Invalid {label} id')
        require(key not in result, f'Duplicate {label}: {key}')
        result[key] = item
    return result


def validate(data: dict[str, Any], root: Path = ROOT) -> dict[str, dict[str, Any]]:
    require(data['schema_version'] == 'laurea.distinction-atlas.v1', 'Unsupported schema')
    require(data['subject'] == '4444J99', 'This atlas is subject-specific')
    date.fromisoformat(data['observed_on'])
    ref = data['canonical_evidence']
    root = root.resolve()
    source_path = (root / ref['path']).resolve()
    require(source_path.is_relative_to(root), 'Evidence path escapes repository')
    raw = source_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Canonical evidence changed; reconcile explicitly')
    canonical = json.loads(raw)
    require(canonical['subject']['login'] == data['subject'], 'Evidence subject mismatch')
    sources = indexed(data['sources'], 'source')
    claims = indexed(data['claims'], 'claim')
    indexed(data['pathways'], 'pathway')
    indexed(data['discovery_lanes'], 'discovery lane')
    for source in sources.values():
        url = urlparse(source['url'])
        require(url.scheme == 'https' and bool(url.netloc) and not url.username and not url.password, 'Invalid public source URL')
        require(source['visibility'] in {'public', 'restricted'}, 'Invalid source visibility')
        date.fromisoformat(source['observed_on'])
        require(bool(source['kind']) and bool(source['locator']), 'Missing source description')
        for pin in ('blob_sha', 'merge_sha'):
            if pin in source:
                require(bool(re.fullmatch(r'[0-9a-f]{40}', source[pin])), f'Invalid {pin}')
        if source['kind'] == 'independent-acceptance':
            matches = [m for m in canonical['upstream_merges'] if m['url'] == source['url']]
            require(len(matches) == 1 and matches[0]['merged'] is True, 'Acceptance missing from frozen evidence')
            require(source.get('merge_sha') == matches[0]['merge_sha'], 'Acceptance SHA mismatch')
    for item in claims.values():
        require(item['kind'] in KINDS, 'Invalid claim kind')
        require(item['visibility'] in {'public', 'restricted'}, 'Invalid claim visibility')
        for field in ('title', 'statement', 'mechanism', 'problem', 'boundary'):
            require(isinstance(item[field], str) and bool(item[field].strip()), f'Missing {field}')
        require(bool(item['audiences']) and set(item['audiences']) <= AUDIENCES, 'Invalid audience')
        require(bool(item['evidence']) and len(set(item['evidence'])) == len(item['evidence']), 'Invalid evidence list')
        require(all(ref in sources for ref in item['evidence']), 'Unknown evidence reference')
        if item['visibility'] == 'public':
            require(all(sources[ref]['visibility'] == 'public' for ref in item['evidence']), 'Restricted source cannot support a public claim')
        if item['kind'] == 'comparison':
            require(item.get('comparison_ref') == 'ranking', 'Comparison must use the existing ranking record')
            require(item['statement'].startswith(canonical['publication']['headline']), 'Comparison scope or wording changed')
        if item['kind'] == 'external-acceptance':
            require(all(sources[ref]['kind'] == 'independent-acceptance' for ref in item['evidence']), 'Self-description cannot establish external acceptance')
        require(not any(key in item for key in ('genius_score', 'rarity_score', 'global_rank')), 'Unsupported composite ranking')
    for pathway in data['pathways']:
        require(pathway['audience'] in AUDIENCES, 'Invalid pathway audience')
        require(len(set(pathway['claims'])) >= 2, 'A synthesis needs multiple distinct claims')
        require(all(ref in claims for ref in pathway['claims']), 'Unknown pathway claim')
        for field in ('title', 'thesis', 'problem', 'proof_product', 'outcome_measure'):
            require(bool(pathway[field]), f'Missing pathway {field}')
    for lane in data['discovery_lanes']:
        require(all(bool(lane[key]) for key in ('title', 'question', 'required_proof')), 'Incomplete discovery lane')
    return claims


def render(data: dict[str, Any], audience: str = 'all', root: Path = ROOT) -> str:
    require(audience == 'all' or audience in AUDIENCES, 'Unknown audience')
    validate(data, root)
    visible = [c for c in data['claims'] if c['visibility'] == 'public' and c['kind'] != 'lead'
               and (audience == 'all' or audience in c['audiences'])]
    ids = {c['id'] for c in visible}
    sources = {s['id']: s for s in data['sources']}
    lines = ['# Distinction Atlas — Anthony James Padavano', '',
             '**Systems, language, and creative practice — demonstrated in the work.**', '',
             f"Evidence edition: {data['observed_on']} · Audience: {audience}", '',
             'This atlas connects documented work to the capabilities it demonstrates. The problem-fit pathways are editorial hypotheses to test, not claims of universal superiority or guaranteed demand.', '',
             '## Documented distinctions', '']
    for item in visible:
        lines += [f"### {item['title']}", '', item['statement'], '',
                  f"**Capability:** {item['mechanism']}", '',
                  f"**Where it can help:** {item['problem']}", '',
                  '<details>', f"<summary>Evidence and scope · {LABELS[item['kind']]}</summary>", '']
        for ref in item['evidence']:
            source = sources[ref]
            lines += [f"[{ref}]({source['url']}) — {source['locator']}.", '']
            if 'blob_sha' in source:
                lines += [f"Inspected source blob: `{source['blob_sha']}`.", '']
            if source.get('limit'):
                lines += [source['limit'], '']
        lines += [item['boundary'], '', '</details>', '']
    lines += ['## Problem-fit pathways', '',
              'These combine the evidence above into specific proposed uses. Each includes the next demonstration and an outcome measure.', '']
    for pathway in data['pathways']:
        if (audience != 'all' and pathway['audience'] != audience) or not set(pathway['claims']) <= ids:
            continue
        lines += [f"### {pathway['title']}", '', pathway['thesis'], '',
                  f"**Problem:** {pathway['problem']}", '',
                  f"**Proof to put in front of someone:** {pathway['proof_product']}", '',
                  f"**Measure:** {pathway['outcome_measure']}", '']
    lines += ['## Continue the discovery', '',
              'These are research questions, not additional accomplishments already established. This offline builder does not collect evidence or launch scheduled work.', '']
    for lane in data['discovery_lanes']:
        lines += [f"### {lane['title']}", '', lane['question'], '', f"**Evidence needed:** {lane['required_proof']}", '']
    lines += ['## Publication contract', '', data['publication_policy']['pathways_are'], '',
              data['publication_policy']['privacy'], '', data['publication_policy']['authorship'], '',
              'Source registry: `evidence/2026-09-22-distinction-atlas.json`. Method: `docs/distinction-method.md`.', '']
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT)
    parser.add_argument('--audience', choices=['all'] + sorted(AUDIENCES), default='all')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true', help='Verify the chosen output matches the evidence-derived report')
    args = parser.parse_args()
    try:
        data = json.loads(args.catalog.read_text(encoding='utf-8'))
        text = render(data, args.audience)
        if args.check:
            output = args.output or ROOT / 'DISTINCTIONS.md'
            require(output.read_text(encoding='utf-8') == text, f'Generated report drift: {output}')
            print('Distinction atlas verified: evidence structure and generated report match.')
        elif args.output:
            args.output.write_text(text, encoding='utf-8')
        else:
            print(text, end='')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(1, f'Distinction atlas failed: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
