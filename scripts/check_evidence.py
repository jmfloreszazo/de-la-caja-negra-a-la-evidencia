#!/usr/bin/env python3
"""Fail closed when a planned experiment is represented as already executed."""
import json
from pathlib import Path
import sys
import argparse
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import time
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'evidence/claims.json').read_text(encoding='utf-8'))
errors=[]
allowed={'ci_verified','published','partially_verified','designed_not_executed','pending_reproduction','demonstrated_not_accepted'}
import hashlib
def repository_record_errors(label, evidence):
    """A demonstrated-not-accepted claim must point at a tracked record whose bytes still match."""
    found=[]
    if not isinstance(evidence,dict) or evidence.get('kind')!='repository_record':
        return [label+': demonstrated claims need a repository_record']
    rel=evidence.get('path','')
    target=(ROOT/rel)
    if not rel or not target.is_file() or ROOT.resolve() not in target.resolve().parents:
        return [label+': repository record missing']
    if hashlib.sha256(target.read_bytes()).hexdigest()!=evidence.get('sha256'):
        found.append(label+': repository record bytes changed since the claim was written')
    try:
        record=json.loads(target.read_text(encoding='utf-8'))
    except ValueError:
        return found+[label+': repository record is not JSON']
    classification=str(record.get('classification',''))
    if 'ACCEPT' in classification.upper() and 'NOT' not in classification.upper():
        found.append(label+': record classification claims acceptance')
    if 'NOT' not in classification.upper():
        found.append(label+': record classification must state what it is not')
    return found
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
        expected_kind = {'ci_verified': 'github_actions', 'published': 'github_release'}[st]
        if not isinstance(evidence, dict) or evidence.get('kind') != expected_kind:
            errors.append(label + ': ' + st + ' requires evidence kind ' + expected_kind)
        elif expected_kind == 'github_actions' and (type(evidence.get('run_id')) is not int or evidence['run_id'] <= 0):
            errors.append(label+': invalid CI run')
        elif expected_kind == 'github_release' and (not isinstance(evidence.get('assets'), list) or len(evidence['assets']) != 4):
            errors.append(label+': invalid release assets')
    elif st=='demonstrated_not_accepted':
        errors.extend(repository_record_errors(label,evidence))
        if not x.get('protocol') or not (ROOT/x.get('protocol','__missing__')).is_file(): errors.append(label+': no protocol')
    else:
        if evidence is not None: errors.append(label+': unexecuted status has purported proof')
        if not x.get('protocol') or not (ROOT/x.get('protocol','__missing__')).is_file(): errors.append(label+': no protocol')
    if label=='E1' and st!='partially_verified': errors.append('E1: expected partial verification status until full acceptance')
    if label in {'E3','E4'} and st not in {'designed_not_executed','demonstrated_not_accepted'}:
        errors.append(label+': acceptance needs an approved contract, comparative arms and a revised gate')
    if label=='E2' and st not in {'designed_not_executed','partially_verified'}:
        errors.append('E2: full acceptance requires a separately validated evidence gate')
e2_status=next((x['status'] for x in claims if x['id']=='E2'),None)
if e2_status=='partially_verified':
    # Promotion from a design-only umbrella is allowed ONLY when separate
    # independently traced, successful CI claims already exist. The umbrella
    # still must not claim distributed failover or sustained capacity.
    prerequisites=('E2-SMOKE','E2-LOAD','E2-PROCESS-KILL','E2-CROSSED','E2-REENTRANCY','E2-DEADLOCK','E2-MULTIPROCESS','E2-ADONET','E2-INFLIGHT','E2-PODMAN','E2-NETEM')
    for child in prerequisites:
        claim=next((x for x in claims if x['id']==child),{})
        if claim.get('status')!='ci_verified' or not claim.get('evidence'):
            errors.append('E2 partial verification missing CI provenance: '+child)
if any(next((x for x in claims if x['id']==key),{}).get('status')!='ci_verified' for key in ('E1A','E1B')):
    errors.append('E1 may be partially verified only if E1A/E1B have independent CI proof')
for f in ('docs/EVIDENCE.md','docs/EVIDENCE.es.md'):
    text=(ROOT/f).read_text(encoding='utf-8')
    for key in ids:
        if '`'+key+'`' not in text: errors.append(f+': missing '+key)
def github_resource(path, token):
    url='https://api.github.com/repos/'+data['repository']+'/'+path
    req=Request(url, headers={
        'Authorization':'Bearer '+token,
        'Accept':'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28',
        'User-Agent':'Evidence-Audit-CI'
    })
    # GitHub's historical run API can briefly return 502/503. Retry
    # transient transport failures only; NEVER waive provenance checks.
    # Authentication failures, missing resources, mismatched SHA or CI
    # failures must still fail closed.
    for attempt in range(4):
        try:
            with urlopen(req, timeout=25) as stream:
                return json.load(stream)
        except HTTPError as ex:
            if ex.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise
        except URLError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError('GitHub provenance API did not recover')

def validate_live_provenance():
    token=os.environ.get('GITHUB_TOKEN')
    if not token:
        errors.append('GITHUB_TOKEN required for online evidence verification')
        return
    checked=set()
    for claim in claims:
        source=claim.get('evidence')
        if not source:
            continue
        if source['kind']=='github_actions':
            run_id=source['run_id']
            if run_id in checked:
                continue
            checked.add(run_id)
            run=github_resource('actions/runs/'+str(run_id),token)
            if run.get('conclusion')!='success' or run.get('status')!='completed':
                errors.append('CI run '+str(run_id)+' is not a completed success')
            if run.get('head_sha')!=source['head_sha']:
                errors.append('CI run '+str(run_id)+' has mismatched source commit')
            jobs=github_resource('actions/runs/'+str(run_id)+'/jobs?per_page=100',token)['jobs']
            expected={
                41607407356:{'Long fault schedule (primary outbound)','Long fault schedule (secondary outbound)'},
                41601478234:{'Loopback observation negative control (development)','Loopback observation negative control (adonet)'},
                41528812921:{'C05 C06 block primary outbound silo packets','C05 C06 block secondary outbound silo packets'},
                41523019075:{'C01 controlled placement cohort 1','C01 controlled placement cohort 2','C01 controlled placement cohort 3'},
                41513498050:{'E2-F10 C04 client gateway cuts and 7/7 independent SQL oracle'},
                40901043531:{'markdown','diagrams','links, es/en sync, generated files'},
                40901043412:{'offline','native','podman'},
                40919268337:{'postgres-evidence'},
                40919773614:{'postgres-evidence'},
                41024101879:{'postgres-evidence'},
                41031578923:{'postgres-evidence'},
                41032714628:{'postgres-evidence'},
                41033595770:{'postgres-evidence'},
                41034420329:{'postgres-evidence'},
                41040632819:{'sqlserver-evidence'},
                41041573996:{'sqlserver-evidence'},
                41042317263:{'sqlserver-evidence'},
                41043087791:{'sqlserver-evidence'},
                41053628769:{'Orleans grain and independent SQL oracle'},
                41055928136:{'Orleans grain, SQL oracle and synthetic workloads'},
                41056976342:{'Orleans grain, SQL oracle and synthetic workloads'},
                41059475191:{'Orleans grain, SQL oracle and synthetic workloads'},
                41060526872:{'Orleans grain, SQL oracle and synthetic workloads'},
                41072089559:{'Orleans grain, SQL oracle and synthetic workloads'},
                41084584229:{'Orleans grain, SQL oracle and synthetic workloads'},
                41098437285:{'Orleans grain, SQL oracle and synthetic workloads'},
                41102529778:{'Orleans grain, SQL oracle and synthetic workloads'},
                41126502385:{'E2-F10 four Podman netns and SQL-grain recovery oracle'},
                41132190043:{'E2-F10 actual tc/netem packet loss, unchanged silo PID, SQL and 7/7 oracle'},
            }.get(run_id,set())
            if not expected.issubset({j['name'] for j in jobs if j['conclusion']=='success'}):
                errors.append('CI run '+str(run_id)+' is missing a required successful job')
        if source['kind']=='github_release':
            published=github_resource('releases/tags/'+source['tag'],token)
            names={asset['name'] for asset in published['assets']}
            if not set(source['assets']).issubset(names):
                errors.append('Release '+source['tag']+' is missing one or more book assets')

parser=argparse.ArgumentParser()
parser.add_argument('--online',action='store_true')
args=parser.parse_args()
if args.online and not errors:
    try:
        validate_live_provenance()
    except Exception as exc:
        errors.append('Cannot validate GitHub provenance: '+str(exc))
for error in errors: print('EVIDENCE FAIL:',error)
print('EVIDENCE CHECK:', 'PASS' if not errors else 'FAIL')
sys.exit(bool(errors))
