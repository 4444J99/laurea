"""Validate the October 2 external-owner PR census and public summary."""
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-02-external-owner-pr-census.json'
PIN='634d43e18b2a64fb5a17179f3ecf7f9ac99f0ebc'
START='<!-- LAVREA:EXTERNAL-PR-CENSUS:START -->'
END='<!-- LAVREA:EXTERNAL-PR-CENSUS:END -->'
def load():
    raw=(ROOT/'evidence'/NAME).read_bytes()
    oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if oid!=PIN: raise ValueError('evidence pin mismatch')
    return json.loads(raw)
def verify(d):
    rows=d['records']; keys={(r['repository_id'],r['number']) for r in rows}; repos={r['repository_id'] for r in rows}
    if (len(rows),len(keys),len(repos))!=(32,32,30): raise ValueError('identity count mismatch')
    counts={k:sum(r['status']==k for r in rows) for k in ('merged','open','closed_unmerged')}
    if counts!={'merged':7,'open':13,'closed_unmerged':12}: raise ValueError('status count mismatch')
    if any(r['author']!='4444J99' or r['repository'].split('/',1)[0].casefold()=='4444j99' for r in rows): raise ValueError('scope mismatch')
    if d['continuity']['verified_independent_upstream_acceptances_remain']!=6: raise ValueError('acceptance boundary mismatch')
    if d['continuity']['extra_merged_namespace_record']!='unnamedplay-r/etceter4#1': raise ValueError('namespace boundary mismatch')
    return counts
def render(d):
    c=verify(d)
    return '\n'.join([START,'## External contribution reach — October 2, 2026','',f"**32 public pull requests authored by `4444J99` across 30 current repository identities outside the `4444J99` namespace:** **{c['merged']} merged · {c['open']} open · {c['closed_unmerged']} closed unmerged**.",'','This is a dated current-owner namespace census from GitHub search, not a lifetime-submission total or a claim that every repository is independent of Anthony. The separately verified independent upstream-acceptance set remains **six projects**; the seventh merged record in this namespace census is `unnamedplay-r/etceter4#1` and is deliberately not promoted into that independent set.','','**[Inspect the census and boundaries](EXTERNAL_PR_CENSUS.md)** · **[Machine-readable evidence](evidence/2026-10-02-external-owner-pr-census.json)**',END])
def check_readme(d):
    text=(ROOT/'README.md').read_text()
    if text.count(START)!=1 or text.count(END)!=1: raise ValueError('README marker mismatch')
    before,rest=text.split(START); _,after=rest.split(END)
    if before+render(d)+after!=text: raise ValueError('README census drift')
if __name__=='__main__':
    data=load(); print(verify(data)); check_readme(data); print('README census block matches evidence.')
