#!/usr/bin/env python3
"""Audit original stream-fault evidence with historical pure SQL oracles."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE='a9ae65dcf0704147d99b2af16fae4a538daa0189'
ARCHIVE=ROOT/'evidence/brownfield/c2-directional-original.zip'
DIGEST='7c402c85cdee0b3481edeac5a2a6518f2843b419887d7537014c256ec373a523'


def original_function(path,name):
    # Extract only the original dependency-free function, not DB connection code.
    source=subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT,text=True)
    tree=ast.parse(source);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    isolated=ast.Module(body=[function],type_ignores=[]);namespace={}
    exec(compile(isolated,path,'exec'),namespace)
    return namespace[name]


def main():
    assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==DIGEST
    with zipfile.ZipFile(ARCHIVE) as z:
        report=json.loads(z.read('c2-controller-partition.json'))
        provenance=z.read('provenance.txt').decode()
    assert 'source_head_sha='+SOURCE in provenance and 'checkout_sha='+SOURCE in provenance
    assert report['sourceHeadSha']==SOURCE and report['runId']=='41792899739'
    assert report['status']=='PASS' and report['protocol']=='C2_DIRECTIONAL_STREAM_SUPPRESSION_V1'
    assert report['todmG2']=='INCONCLUSIVE' and report['todmG6']=='BLOCK'
    assert len(report['sourceSha256'])==13
    for path,digest in report['sourceSha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)).hexdigest()==digest,path
    sql_oracle=original_function('lab/brownfield/coexistence/two_store.py','independent_oracle')
    observation_oracle=original_function('lab/brownfield/journal/partition_oracle.py','evaluate')
    assert [(c['writer'],c['direction']) for c in report['cases']]==[
        (w,d) for w in ['legacy','candidate'] for d in ['CLIENT_TO_SERVER','SERVER_TO_CLIENT']]
    for case in report['cases']:
        assert case['status']=='PASS' and not observation_oracle(case)
        assert case['gatewayExitCode']==-9 and case['sqlBlockedAdapter'][1]=='Lock'
        assert set(case['controllerPidsBeforeFault'])==set(case['controllerPidsDuringFault'])
        assert all(row[1]=='idle in transaction' and 'FOR SHARE' in row[4] for row in case['controllerSessionsDuringFault'])
        assert case['silentObservation']['sampledSeconds']>=1
        assert case['admissionBeforeReset']==[[case['operationId'],'DISPATCHING',case['writer'],case['epoch']]]
        for side,key in [('source','sourceOracle'),('target','targetOracle')]:
            checks=sql_oracle(case['finalSnapshots'][side]);assert checks==case[key] and len(checks)==10 and all(checks.values())
            assert not any(op[0].endswith('-NEW') for op in case['finalSnapshots'][side]['operations'])
            prior=sql_oracle(case['snapshotBeforeReset'][side]);assert all(prior.values())
        after=case['controllerSessionsAfterFinancialCommit'];assert after
        # Report this observed difference, not a universal protocol guarantee.
        expected='idle in transaction' if case['direction']=='CLIENT_TO_SERVER' else 'idle'
        assert all(row[1]==expected for row in after)
        assert case['recoveryReset']['event']=='CONTROLLED_SOCKET_RESET'
    assert len(report['negativeControls'])==2
    for control in report['negativeControls']:
        errors=observation_oracle(control['mutatedObservation']);assert errors==control['rejectedBy'] and errors
    print(json.dumps({'status':'PASS','source_hashes':13,'directional_cases':4,'sql_checks_per_store':10,
                      'rejected_observation_mutants':2,'automatic_recovery_claim':False,'todmG2':'INCONCLUSIVE','todmG6':'BLOCK'}))

if __name__=='__main__':main()
