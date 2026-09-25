"""Render dated census and audience stat blocks from pinned evidence; offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'evidence/2026-09-24-source-census.json'
PIN = '6dbde1f6049ed48a1bbccbf9b0f6fbfb59a82cb38c0d03fe0f0b481eee36549b'
START = '<!-- LAVREA:SOURCE-CENSUS:START -->'
END = '<!-- LAVREA:SOURCE-CENSUS:END -->'
AUDIENCES = ('engineering', 'research', 'creative', 'learning')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(root=ROOT):
    raw = (root / RECORD).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN, 'Census evidence pin mismatch')
    d = json.loads(raw)
    validate(d)
    for check in [d['projects']['skills']['skills']['validator'], *d['checks'].values()]:
        path = (root / check['log']).resolve()
        require(path.is_relative_to(root.resolve()), 'Log path escapes repository')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == check['log_sha256'], 'Execution log pin mismatch')
    return d


def validate(d):
    require(d['schema_version'] == 'laurea.source-census-evidence.v1' and d['subject'] == '4444J99', 'Wrong evidence subject/schema')
    require(d['edition_date_local'] == '2026-09-24', 'Use a new dated record for refreshes')
    for p in d['projects'].values():
        require(type(p['repository_id']) is int and p['repository_id'] > 0, 'Stable repository ID required')
        require(re.fullmatch('[0-9a-f]{40}', p['commit']) is not None, 'Immutable commit required')
    s = d['projects']['skills']['skills']; n = d['projects']['narrative']['narrative']
    require(s['unique_declared_ids'] == s['canonical_files'] == sum(s['categories'].values()), 'Canonical skill totals disagree')
    require(not s['duplicate_declared_ids'] and not s['missing_id_files'] and not s['parse_errors'], 'Skill identity errors')
    v = s['validator']
    require(v['exit_code'] == 0 and v['passed'] == v['checked'] == s['canonical_files'], 'Structural validator did not pass all canonical skills')
    require(n['enumerated_studies'] == sum(n['category_counts'].values()), 'Study/category totals disagree')
    require(n['algorithm_records'] == n['unique_study_algorithm_ids'] and not n['duplicate_study_algorithm_ids'], 'Algorithm identity errors')
    require(n['complete_algorithm_contracts'] == n['algorithm_records'], 'Incomplete five-field contracts')
    require(all(n['algorithm_field_presence'][key] == n['algorithm_records'] for key in ('name','purpose','pseudocode','inputs','outputs')), 'Contract field totals disagree')
    for key, check in d['checks'].items():
        c = check['counts']
        require(all(type(v) is int and v >= 0 for v in c.values()), 'Invalid execution counts')
        require(c['tests'] == sum(c[k] for k in ('passed','failures','errors','skipped')), 'Execution totals disagree')
        require(bool(check['selection']) and bool(check['environment']), 'Execution scope required')
        if check['exit_code'] == 0:
            require(c['failures'] == c['errors'] == 0, 'Success cannot hide failures')
        else:
            require(c['failures'] + c['errors'] > 0, 'Failed selection needs visible failures')
    return d


def numbers(d):
    s=d['projects']['skills']['skills']; n=d['projects']['narrative']['narrative']; t=d['checks']['narrative']['counts']
    return s,n,t


def block(d):
    s,n,t=numbers(d)
    return '\n'.join([START, '## Source-verified depth — September 24, 2026', '',
        f"**{s['unique_declared_ids']} canonical AI skills, all passing native structural validation.** The inventory excludes {s['outside_canonical_roots']} SKILL.md paths outside the canonical roots; it does not count generated copies as additional skills.", '',
        f"**{n['enumerated_studies']} studies · {n['algorithm_records']} algorithm records · {n['axiom_records']} axioms · {n['diagnostic_questions']} diagnostic questions.** All {n['complete_algorithm_contracts']} algorithm records contain the five required descriptive fields. These quantities were enumerated from the pinned source, upgrading the earlier README-reported counts.", '',
        f"**Narrative core/CLI/API tests: {t['passed']} passed, {t['skipped']} skipped.** Local execution, separately scoped from record completeness; the skipped optional-provider tests and environment are disclosed in the report.", '',
        '**[Source census and execution evidence](SOURCE_CENSUS.md)** · **[Audience stat blocks](docs/stat-blocks/engineering.md)**', '',
        'This new edition complements the dated September 22 findings; it does not relabel activity as commits, corpus completeness as efficacy, or maintained third-party material as sole authorship.', END])


def report(d):
    s,n,t=numbers(d)
    lines=['# Source census — Anthony James Padavano', '',
        f"Local evidence edition: {d['edition_date_local']} (America/New_York). Collection timestamp: {d['observed_at']}.", '',
        '## AI instruction library', '',
        f"**{s['unique_declared_ids']} unique canonical skills; {s['validator']['passed']}/{s['validator']['checked']} passed native structural validation.**", '',
        '169 subject-category skills across 12 categories, four document skills and 11 plugin skills. Canonical roots are skills/, document-skills/ and plugins/. The 692 outside-root paths are not counted as additional canonical skills.', '',
        '| Category | Canonical files |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in s['categories'].items()]
    lines += ['', 'The validator ran with --unique, without --check-links. Metadata validity is not a measurement of task success, licensing originality or sole authorship. This is a maintained and extended corpus.', '',
        '## Narrative formalization — independently counted', '',
        '| Source dimension | Enumerated result |','|---|---:|',
        f"| Studies / categories | {n['enumerated_studies']} / {len(n['category_counts'])} |",
        f"| Algorithm records / unique study-scoped identities | {n['algorithm_records']} / {n['unique_study_algorithm_ids']} |",
        f"| Axioms | {n['axiom_records']} |", f"| Diagnostic questions | {n['diagnostic_questions']} |",
        f"| Complete name/purpose/pseudocode/inputs/outputs records | {n['complete_algorithm_contracts']} / {n['algorithm_records']} |",
        f"| Cross-reference sequences | {n['cross_reference_sequences']} |", '',
        'The core_algorithms field was enumerated directly; these are not 141 independently validated executable algorithms or 28 peer-reviewed publications. Seven cross-reference sequences are a separate count from the earlier seven protocol levels.', '',
        '## Executed verification — no combined passing-test score', '',
        '| Project and selection | Passed | Skipped | Failed | Errors |','|---|---:|---:|---:|---:|']
    for key, check in d['checks'].items():
        c=check['counts']; lines += [f"| {key} | {c['passed']} | {c['skipped']} | {c['failures']} | {c['errors']} |"]
    for key,check in d['checks'].items():
        lines += ['',f'### {key}', '',check['selection'],'',f"Command: `{check['command']}`", '',f"[Execution log]({check['log']})", '']
        if check['exceptions']:
            lines += [f"- {e['kind']}: `{e['test']}` — {e['reason']}" for e in check['exceptions']]
        if check.get('additional_boundary'): lines += ['',check['additional_boundary']]
    lines += ['', 'The local environment used Python 3.13 and preinstalled packages, without installing the projects’ locked environments or calling paid models. The two narrative skips were for missing optional Anthropic and OpenAI packages. RE:GE is not certified green: its bounded completed selection has two failures, and the full-suite REPL path timed out. Titan’s 48 passes cover the named three-file selection, not its entire suite.', '',
        '## Definition counts — not execution claims', '',
        '| Corpus | Source Python files | Test Python files | Test function definitions |','|---|---:|---:|---:|']
    for key in ('narrative','titan','rege'):
        p=d['projects'][key]['python'];lines += [f"| {key} | {p['source_python_files']} | {p['test_python_files']} | {p['test_function_definitions']} |"]
    lines += ['', 'These AST counts retain repeated definitions across files, include parameterized function definitions only once each, and are not test-coverage measurements. Generated copies in the larger skills repository are not used as a source-code-volume headline.', '', '## Immutable source identities', '']
    for key,p in d['projects'].items():
        lines += [f"**{key}:** repository ID `{p['repository_id']}`, [`{p['commit'][:12]}`](https://github.com/{p['repository']}/tree/{p['commit']}).", '']
    lines += [f"The [successful census run](https://github.com/4444J99/laurea/actions/runs/{d['collector']['workflow_run']}) executed the collector and native skill validator. Its original downloadable artifact expires on {d['collector']['artifact_expiry']}; this permanent record retains the hashes, source identities and reproducible collector. The initial wrong-field collector run is explicitly superseded, not promoted as a zero-algorithm result.", '',
        f'Canonical evidence: [{RECORD}]({RECORD}).', '', '## Reuse', '',
        'Audience-specific, source-scoped stat blocks: [engineering](docs/stat-blocks/engineering.md), [research](docs/stat-blocks/research.md), [creative practice](docs/stat-blocks/creative.md), and [learning design](docs/stat-blocks/learning.md).', '',
        'Private teaching and client source records are stored separately. No private correspondence, student records, client asset contents or font files are included in this public package.', '']
    return '\n'.join(lines)


def stat_block(d,audience):
    s,n,t=numbers(d)
    require(audience in AUDIENCES,'Unknown audience')
    text={
     'engineering': f"{s['unique_declared_ids']} canonical AI skills passing native structural validation; {t['passed']} passing and {t['skipped']} skipped tests in the narrative core/CLI/API selection; 48 passing selected Titan decision, replay and migration tests. Each result has an immutable source snapshot and a named execution scope.",
     'research': f"{n['enumerated_studies']} studies across {len(n['category_counts'])} categories, containing {n['algorithm_records']} algorithm records, {n['axiom_records']} axioms and {n['diagnostic_questions']} diagnostic questions. All {n['complete_algorithm_contracts']} algorithm records provide a name, purpose, pseudocode, inputs and outputs. Corpus size and structural completeness are measured separately from research novelty and empirical validation.",
     'creative': f"An independently enumerated narrative-formalization corpus with {n['algorithm_records']} algorithm records and {n['diagnostic_questions']} diagnostic questions across eight categories. The separately dated September 22 catalog records five ETCETER4 releases, 63 listed tracks and 4:10:51 of displayed audio duration, including a remix collection. This pairs released practice with a substantial analytical tool corpus without claiming reception or sales.",
     'learning': f"{s['unique_declared_ids']} canonical instruction modules passing native structural checks, including four education-category skills; a narrative corpus with {n['diagnostic_questions']} diagnostic questions and {n['axiom_records']} axioms. These are instructional and evaluative structures, not measured learner-outcome gains. Private teaching-source reconciliation is ongoing."
    }[audience]
    return f'# {audience.title()} — reusable measured stat block\n\nEvidence edition: September 24, 2026.\n\n{text}\n\n[Source census](../../SOURCE_CENSUS.md) · [Earlier statistical evidence](../../STATISTICS.md).\n'


def replace_block(text, new):
    require(text.count(START)==text.count(END)==1, 'Exactly one census marker pair required')
    a=text.index(START);b=text.index(END)+len(END)
    require(a<b,'Reversed markers')
    return text[:a]+new+text[b:]


def outputs(d,root=ROOT):
    return {root/'SOURCE_CENSUS.md':report(d),**{root/'docs'/'stat-blocks'/f'{a}.md':stat_block(d,a) for a in AUDIENCES}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    try:
        d=load();out=outputs(d);readme=ROOT/'README.md'
        out[readme]=replace_block(readme.read_text(),block(d))
        for path,text in out.items():
            if a.check: require(path.read_text()==text,f'Generated output drift: {path.name}')
            else: path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    except (OSError,ValueError,KeyError,TypeError) as exc: p.exit(1,f'Source census publication failed: {exc}\n')
    print('Source census outputs and evidence verified.' if a.check else 'Source census outputs generated.')
    return 0

if __name__=='__main__': raise SystemExit(main())
