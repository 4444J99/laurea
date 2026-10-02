"""Validate the October 2 external-owner PR census."""
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-02-external-owner-pr-census.json'
PIN='634d43e18b2a64fb5a17179f3ecf7f9ac99f0ebc'
def load():
    raw=(ROOT/'evidence'/NAME).read_bytes()
    oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if oid != PIN: raise ValueError('evidence pin mismatch')
    return json.loads(raw)
def verify(d):
    rows=d['records']; keys={(r['repository_id'],r['number']) for r in rows}
    if len(rows)!=32 or len(keys)!=32 or len({r['repository_id'] for r in rows})!=30: raise ValueError('identity count mismatch')
    counts={k:sum(r['status']==k for r in rows) for k in ('merged','open','closed_unmerged')}
    if counts != {'merged':7,'open':13,'closed_unmerged':12}: raise ValueError('status count mismatch')
    if any(r['author']!='4444J99' or r['repository'].split('/',1)[0].casefold()=='4444j99' for r in rows): raise ValueError('scope mismatch')
    if d['continuity']['verified_independent_upstream_acceptances_remain']!=6: raise ValueError('acceptance boundary mismatch')
    return counts
if __name__=='__main__': print(verify(load()))
