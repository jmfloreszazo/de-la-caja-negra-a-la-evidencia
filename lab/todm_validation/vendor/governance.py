#!/usr/bin/env python3
"""Two-plane governance research demonstrator. Standard-library only; no real deployment."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
from reference import ROOT, candidate, load_baseline, verify

BASE=ROOT/'governance'

def parse_time(value):
    if not isinstance(value,str): return None
    try:
        result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        return result if result.tzinfo is not None else None
    except ValueError: return None

def authority_verdict(mandates,request):
    needed=('principal','action','scope','at')
    if not isinstance(request,dict) or any(not request.get(k) for k in needed):
        return {'verdict':'INCONCLUSIVE','reason':'Authorization request is incomplete'}
    agent=mandates['mandates'].get(request['principal'])
    if agent is None:return {'verdict':'FAIL','reason':'Unknown principal'}
    if agent.get('revoked'):return {'verdict':'FAIL','reason':'Mandate revoked'}
    instant=parse_time(request['at']);start=parse_time(agent.get('validFrom'));end=parse_time(agent.get('validUntil'))
    if any(x is None for x in (instant,start,end)):
        return {'verdict':'INCONCLUSIVE','reason':'Missing or invalid authorization time'}
    if not start<=instant<end:return {'verdict':'FAIL','reason':'Outside mandate validity window'}
    if request['action'] not in agent.get('actions',[]):return {'verdict':'FAIL','reason':'Action not delegated'}
    if request['scope'] not in agent.get('scopes',[]):return {'verdict':'FAIL','reason':'Scope not delegated'}
    return {'verdict':'PASS','reason':'Synthetic mandate permits this action at fixture time'}

def release_verdict(oracle,authority,approval):
    if oracle!='PASS' or authority!='PASS':return {'outcome':'BLOCK','reason':'Oracle and mandate must both PASS'}
    if not isinstance(approval,dict) or approval.get('kind')!='DEMO_SIMULATED' or approval.get('approved') is not True or approval.get('approverRole')!='release-owner':
        return {'outcome':'BLOCK','reason':'G6 release approval absent or denied'}
    return {'outcome':'SIMULATED_ALLOW','reason':'Both controls PASS; G6 approval simulated; no deployment performed'}

def gate_trace(oracle,authority,outcome):
    trace=[{'gate':'G0','state':'PASS','detail':'Synthetic scope fixed'},
           {'gate':'G1','state':'PASS','detail':'Synthetic policy evidence'},
           {'gate':'G2','state':'SIMULATED','detail':'Digest-bound baseline; no human signature'},
           {'gate':'G3','state':'DEMO_ONLY','detail':'Positive/negative/inconclusive qualification'},
           {'gate':'G4','state':'PASS','detail':'Deterministic candidate executed'},
           {'gate':'G5','state':oracle,'detail':'Independent five-family oracle evaluation'}]
    if oracle=='FAIL':
        trace.append({'gate':'RETURN_TO_G4','state':'REWORK','detail':'Candidate defect; baseline remains unchanged'})
    elif oracle=='INCONCLUSIVE':
        trace.append({'gate':'RETURN_TO_G1','state':'REVIEW','detail':'Acquire missing evidence or clarify rule'})
    else:
        trace.append({'gate':'G6','state':'SIMULATED' if outcome=='SIMULATED_ALLOW' else 'BLOCK',
                      'detail':'Mandate '+authority+'; simulated release decision'})
        if outcome=='SIMULATED_ALLOW':trace.append({'gate':'G7','state':'DEMO_ONLY','detail':'Monitoring not connected'})
    return trace

def run_case(fixture,models,mandates,baseline_digest):
    s=json.loads((ROOT/'scenarios'/f"{fixture['scenario']}.json").read_text())
    if 'overrideAmount' in fixture:s['amount']=fixture['overrideAmount']
    observation=candidate(s,fixture.get('mutation','none'))
    for field in fixture.get('dropFields',[]):observation.pop(field,None)
    oracle=verify(models,observation)
    authority=authority_verdict(mandates,fixture['authorization'])
    release=release_verdict(oracle['verdict'],authority['verdict'],fixture.get('releaseApproval'))
    result={'caseId':fixture['id'],'profile':s['profile'],'scenario':fixture['scenario'],
            'mutation':fixture.get('mutation','none'),'oracleVerdict':oracle['verdict'],
            'authorityVerdict':authority['verdict'],'authorityReason':authority['reason'],
            'releaseOutcome':release['outcome'],'releaseReason':release['reason'],
            'baselineManifestSha256':baseline_digest,'oracleFamilies':oracle['families'],
            'findings':oracle['findings'],'gates':gate_trace(oracle['verdict'],authority['verdict'],release['outcome']),
            'expected':{'oracle':fixture['expectedOracle'],'authority':fixture['expectedAuthority'],'release':fixture['expectedOutcome']}}
    actual=(result['oracleVerdict'],result['authorityVerdict'],result['releaseOutcome'])
    expected=(fixture['expectedOracle'],fixture['expectedAuthority'],fixture['expectedOutcome'])
    if actual!=expected:raise AssertionError(f"{fixture['id']}: expected {expected}, got {actual}")
    return result

def experiment():
    _,models=load_baseline()
    mandates=json.loads((BASE/'mandates.json').read_text())
    fixtures=json.loads((BASE/'fixtures.json').read_text())
    digest=hashlib.sha256((ROOT/'contracts/v1/manifest.json').read_bytes()).hexdigest()
    cases=[run_case(f,models,mandates,digest) for f in fixtures['cases']]
    summary={'caseCount':len(cases),'oraclePass':sum(c['oracleVerdict']=='PASS' for c in cases),
             'oracleFail':sum(c['oracleVerdict']=='FAIL' for c in cases),
             'oracleInconclusive':sum(c['oracleVerdict']=='INCONCLUSIVE' for c in cases),
             'mandateFail':sum(c['authorityVerdict']=='FAIL' for c in cases),
             'simulatedAllow':sum(c['releaseOutcome']=='SIMULATED_ALLOW' for c in cases),
             'blocked':sum(c['releaseOutcome']=='BLOCK' for c in cases)}
    result={'kind':'SYNTHETIC_TWO_PLANE_REFERENCE_NOT_PRODUCTION','version':'0.2.0',
            'evaluationTime':fixtures['referenceTime'],'summary':summary,'cases':cases}
    output=ROOT/'results/governance-execution.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('TODM governance reference:',summary)
    print('Wrote',output)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['experiment']);args=p.parse_args()
    experiment()
