#!/usr/bin/env python3
"""Fail closed when a planned experiment is represented as already executed."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'evidence/claims.json').read_text(encoding='utf-8'))
errors=[]
allowed={'ci_verified','published','designed_not_executed','pending_reproduction'}
claims=data['claims']
ids=[x['id'] for x in claims]
if len(ids)!=len(set(ids)): errors.append('duplicate claim IDs')
if data['edition']!='v2026.10.29': errors.append('unexpected edition change')
if not {'E1','E2','E3','E4'}.issubset(set(ids)): errors.append('missing experiment')
for x in claims:
    label=x['id']; st=x['status']; evidence=x.get('evidence')
    if st not in allowed: errors.append(label+': unrecognized status')
    if not all(x.get(k) for k in ('es','en','scope_es','scope_en')): errors.append(label+': missing bilingual fields')
    if st in {'ci_verified','published'}:
        if not evidence: errors.append(label+': verified without provenance')
        elif evidence.get('kind')=='github_actions' and not isinstance(evidence.get('run_id'),int): errors.append(label+': invalid CI run')
        elif evidence.get('kind')=='github_release' and len(evidence.get('assets',[]))!=4: errors.append(label+': invalid release assets')
    else:
        if evidence is not None: errors.append(label+': unexecuted status has purported proof')
        if not x.get('protocol') or not (ROOT/x.get('protocol','__missing__')).is_file(): errors.append(label+': no protocol')
    if label in {'E1','E2','E3','E4'} and st!='designed_not_executed': errors.append(label+': promotion needs new executed evidence and revised gate')
for f in ('docs/EVIDENCE.md','docs/EVIDENCE.es.md'):
    text=(ROOT/f).read_text(encoding='utf-8')
    for key in ids:
        if '`'+key+'`' not in text: errors.append(f+': missing '+key)
for error in errors: print('EVIDENCE FAIL:',error)
print('EVIDENCE CHECK:', 'PASS' if not errors else 'FAIL')
sys.exit(bool(errors))
