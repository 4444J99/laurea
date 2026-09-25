"""Read-only census of public source snapshots; no activity-to-quality inference."""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
import re
import tarfile
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SOURCES = [
    ('skills', 'organvm-iv-taxis/a-i--skills'),
    ('narrative', 'organvm-ii-poiesis/narratological-algorithmic-lenses'),
    ('titan', 'organvm-iii-ergon/agentic-titan'),
    ('rege', '4444J99/recursive-engine--generative-entity'),
]
MAX_BYTES = 100 * 1024 * 1024


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'LAVREA-public-source-census'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Source exceeds read bound')
    return raw


def unpack(raw: bytes) -> dict[str, bytes]:
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe archive path')
            if not member.isfile() or len(path.parts) < 2:
                continue
            rel = '/'.join(path.parts[1:])
            if rel in files:
                raise ValueError('Duplicate archive path')
            total += member.size
            if total > MAX_BYTES:
                raise ValueError('Expanded source exceeds bound')
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('Unreadable archive entry')
            files[rel] = stream.read()
    return files


def frontmatter(raw: bytes) -> dict[str, str]:
    lines = raw.decode('utf-8').splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('Missing frontmatter')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise ValueError('Unclosed frontmatter')
    data = {}
    key = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line[:1].isspace():
            if key:
                data[key] += '\n' + line.strip()
            continue
        key, sep, value = line.partition(':')
        if not sep:
            raise ValueError('Malformed frontmatter')
        key = key.strip()
        if key in data:
            raise ValueError('Duplicate frontmatter key')
        data[key] = value.strip()
    return data


def skills_census(files: dict[str, bytes]) -> dict:
    canonical, excluded, errors = [], [], []
    for path, raw in sorted(files.items()):
        if PurePosixPath(path).name != 'SKILL.md':
            continue
        if path.split('/')[0] not in {'skills', 'document-skills', 'plugins'}:
            excluded.append(path)
            continue
        try:
            fm = frontmatter(raw)
        except (ValueError, UnicodeError) as exc:
            errors.append({'path': path, 'error': str(exc)})
            continue
        canonical.append({'path': path, 'id': fm.get('name', '').strip('\"\''),
                          'blob_sha': blob_sha(raw), 'fields': sorted(k for k,v in fm.items() if v),
                          'category': path.split('/')[1] if path.startswith('skills/') else path.split('/')[0],
                          'license': fm.get('license'),
                          'declared_provenance_fields': sorted(set(fm) & {'author','authors','source','source_url','adapted_from','attribution','origin'})})
    ids = Counter(r['id'] for r in canonical if r['id'])
    fields = Counter(f for r in canonical for f in r['fields'])
    return {'canonical_files': len(canonical), 'unique_declared_ids': len(ids),
            'duplicate_declared_ids': {k:v for k,v in ids.items() if v>1},
            'missing_id_files': sum(not r['id'] for r in canonical),
            'outside_canonical_roots': len(excluded), 'outside_paths': excluded,
            'categories': dict(Counter(r['category'] for r in canonical)),
            'field_presence': dict(sorted(fields.items())),
            'files_with_provenance_fields': sum(bool(r['declared_provenance_fields']) for r in canonical),
            'parse_errors': errors, 'inventory': canonical,
            'boundary': 'Metadata presence is not validated provenance or efficacy; distributions and noncanonical paths excluded. No sole-authorship inference.'}


def sequence(value):
    if value is None:
        return []
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, list):
        return value
    raise ValueError('Expected record sequence')


def narrative_census(raw: bytes) -> dict:
    data = json.loads(raw)
    studies = data['studies']
    if not isinstance(studies, dict):
        raise ValueError('Expected studies keyed by ID')
    inventory, identities, axiom_ids = [], [], []
    fields = Counter()
    for key, study in sorted(studies.items()):
        if 'core_algorithms' in study:
            algorithm_field = 'core_algorithms'
        elif 'algorithms' in study:
            algorithm_field = 'algorithms'
        else:
            raise ValueError(f'Missing algorithm collection in study {key}')
        algorithms = sequence(study[algorithm_field])
        axioms = sequence(study.get('axioms'))
        entries = []
        for i, a in enumerate(algorithms):
            if not isinstance(a, dict):
                raise ValueError('Expected algorithm object')
            ident = a.get('id') or a.get('name') or str(i)
            identities.append(f'{key}:{ident}')
            fields.update(k for k,v in a.items() if v)
            entries.append({'id':str(ident), 'fields': sorted(k for k,v in a.items() if v)})
        axiom_ids.extend(f'{key}:{a.get("id", i)}' for i,a in enumerate(axioms))
        inventory.append({'id':key, 'declared_id':study.get('id'), 'category':study.get('category'),
                          'algorithms':entries, 'axiom_count':len(axioms),
                          'study_fields':sorted(study), 'algorithm_field':algorithm_field,
                          'diagnostic_questions':len(sequence(study.get('diagnostic_questions')))})
    duplicates = [k for k,v in Counter(identities).items() if v>1]
    return {'source_blob_sha':blob_sha(raw), 'source_sha256':hashlib.sha256(raw).hexdigest(),
            'metadata_study_count':data.get('meta',{}).get('study_count'), 'enumerated_studies':len(inventory),
            'category_counts':dict(Counter(s['category'] for s in inventory)),
            'algorithm_records':len(identities), 'unique_study_algorithm_ids':len(set(identities)),
            'duplicate_study_algorithm_ids':duplicates, 'axiom_records':len(axiom_ids),
            'unique_study_axiom_ids':len(set(axiom_ids)),
            'algorithm_field_presence':dict(fields),
            'complete_algorithm_contracts':sum(all(k in a['fields'] for k in ('name','purpose','pseudocode','inputs','outputs')) for s in inventory for a in s['algorithms']),
            'diagnostic_questions':sum(s['diagnostic_questions'] for s in inventory),
            'cross_reference_sequences':len(sequence(data.get('cross_references',{}).get('sequences'))),
            'inventory':inventory,
            'boundary':'Counts formalized source records, not peer-reviewed papers or independently executed algorithms.'}


def python_inventory(files: dict[str,bytes]) -> dict:
    modules, tests, failures = [], [], []
    for path, raw in sorted(files.items()):
        if not path.endswith('.py') or any(p in {'.venv','vendor','node_modules','dist','build'} for p in PurePosixPath(path).parts):
            continue
        try:
            tree = ast.parse(raw, filename=path)
        except (SyntaxError, UnicodeError) as exc:
            failures.append({'path':path,'error':type(exc).__name__})
            continue
        is_test = PurePosixPath(path).name.startswith('test_') or 'tests' in PurePosixPath(path).parts
        definitions = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        record = {'path':path,'blob_sha':blob_sha(raw),'functions':len(definitions),
                  'classes':sum(isinstance(n,ast.ClassDef) for n in ast.walk(tree))}
        if is_test:
            record['test_definitions'] = sum(n.name.startswith('test_') for n in definitions)
            tests.append(record)
        else:
            modules.append(record)
    return {'source_python_files':len(modules), 'test_python_files':len(tests),
            'test_function_definitions':sum(t['test_definitions'] for t in tests),
            'parse_errors':failures,'source_inventory':modules,'test_inventory':tests,
            'boundary':'AST definitions, not executed test cases. Parametrization, inherited tests and code duplication are not evaluated; no cross-project passing-test total.'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('census-output'))
    args = p.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    result = {'schema_version':'laurea.source-census.v1', 'observed_at':datetime.now(timezone.utc).isoformat(),
              'projects':{}, 'errors':{}, 'mode':'read-only unauthenticated public-source enumeration'}
    for key, repo in SOURCES:
        try:
            info = json.loads(get(f'https://api.github.com/repos/{repo}'))
            if info.get('private') is not False:
                raise ValueError('Public source required')
            canonical = info['full_name']
            commit = json.loads(get(f'https://api.github.com/repos/{canonical}/commits/{info["default_branch"]}'))['sha']
            if not re.fullmatch('[0-9a-f]{40}',commit):
                raise ValueError('Invalid source commit')
            url = f'https://codeload.github.com/{canonical}/tar.gz/{commit}'
            archive = get(url); files = unpack(archive)
            (args.output/f'{key}-source.tar.gz').write_bytes(archive)
            project = {'repository':canonical,'repository_id':info['id'],'commit':commit,
                       'archive_sha256':hashlib.sha256(archive).hexdigest(),'file_count':len(files),
                       'source_url':url,'python':python_inventory(files)}
            if key == 'skills':
                project['skills'] = skills_census(files)
            if key == 'narrative':
                path = 'specs/03-structured-data/narratological-algorithms-unified.json'
                project['narrative'] = narrative_census(files[path])
                (args.output/'narrative-source.json').write_bytes(files[path])
            result['projects'][key] = project
            # Retain only code/config necessary for offline inspection and verification.
            if key == 'skills':
                for name,content in files.items():
                    if name.startswith(('scripts/','skills/','document-skills/','plugins/')) and name.endswith(('.py','SKILL.md')):
                        target=args.output/'skills-source'/name
                        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(content)
            print(key, canonical, commit, 'enumerated', flush=True)
        except Exception as exc:
            result['errors'][key] = {'type':type(exc).__name__,'detail':str(exc)}
            print(key,'ERROR',type(exc).__name__,str(exc),flush=True)
    (args.output/'source-census.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{'repo':v['repository'],'python_files':v['python']['source_python_files'],
                         'test_definitions':v['python']['test_function_definitions'],
                         'skills':v.get('skills',{}).get('unique_declared_ids'),
                         'algorithms':v.get('narrative',{}).get('algorithm_records'),
                         'axioms':v.get('narrative',{}).get('axiom_records')} for k,v in result['projects'].items()},indent=2))
    return 1 if result['errors'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
