#!/usr/bin/env python3
"""Audit one original diagnostic ZIP: source, slot trace and persisted SQL rows."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'lab/e2_b05_dispatch'),str(ROOT/'lab/e2_orleans')]
from analysis import analyze_slots
from b05_sweep_analysis import summarize
from b05_arrival_contract import generate


def verify_state(sql,vector):
    state=sql['state']
    assert len(state['accounts'])==1000 and [r[0] for r in state['accounts']]==list(range(1,1001))
    offered={o['operationId']:o for o in vector['operations']}
    rows={r[0]:r for r in state['operations']}
    assert len(rows)==len(state['operations']) and set(rows)<=set(offered)
    postings=defaultdict(list)
    deltas=Counter()
    for op,account,delta in state['postings']:
        postings[op].append((account,delta));deltas[account]+=delta
    assert set(postings)==set(rows)
    for op,row in rows.items():
        o=offered[op]
        assert row[1:]==[o['sourceAccountId'],o['targetAccountId'],o['amountCents'],'COMMITTED']
        assert sorted(postings[op])==sorted([(row[1],-row[3]),(row[2],row[3])])
    assert len(state['outbox'])==len(rows)
    assert sorted(state['outbox'])==sorted([[op,'TransferCommitted'] for op in rows])
    assert all(balance>=0 and balance==100000+deltas[account] for account,balance in state['accounts'])
    assert sum(balance for _,balance in state['accounts'])==100000000
    digest=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest==sql['stateSha256']
    assert sql['oracleError'] is None and len(sql['sevenOracles'])==7
    assert all(v is True for v in sql['sevenOracles'].values())


def audit_bytes(raw,source):
    assert re.fullmatch('[0-9a-f]{40}',source)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        assert len(names)==len(set(names))
        files={n:z.read(n) for n in names}
    report=json.loads(files['summary.json'])
    assert report['sourceHeadSha']==report['checkoutSha']==source
    assert report['status']=='OBSERVED_DISPATCH_DIAGNOSTIC_NOT_CAPACITY'
    assert report['capacityEstablished'] is report['bottleneckAttributionEstablished'] is False
    cohort=report['cohort']
    assert cohort in (0,1,2) and report['capOrder']==([32,128] if cohort%2==0 else [128,32])
    expected=subprocess.check_output(['git','ls-tree','-r','--name-only',source,'--',
        'lab/e2_b05_dispatch','lab/e2_orleans/OrleansLab','lab/e2_orleans/b05_arrival_contract.py',
        'lab/e2_orleans/b05_sweep_analysis.py','lab/e2_orleans/oracle_workload.py',
        'lab/e1_pg/ledger.py','lab/e1_pg/schema.sql','lab/e1_pg/requirements.txt',
        '.github/workflows/e2-b05-dispatch.yml'],cwd=ROOT,text=True).splitlines()
    assert set(expected)==set(report['sourceHashes'])
    for p,h in report['sourceHashes'].items():
        original=subprocess.check_output(['git','show',source+':'+p],cwd=ROOT)
        assert hashlib.sha256(original).hexdigest()==h,p
    vector=json.loads(files['input.json'])
    assert vector == generate('five_percent_hot',320,1,60,1,20261031,0)
    assert vector['offeredVectorSha256']==report['vectorSha256']
    assert vector['accountCount']==1000 and vector['profile']=='five_percent_hot'
    assert vector['totalOfferedRequests']==19840 and vector['offeredRatePerSecond']==320
    assert vector['seed']==20261031 and vector['repetition']==0
    for phase in vector['phases'].values():
        assert phase['hotSourceIntents']*5==phase['offeredRequests']*4
    settings=report['postgresSettings']
    assert settings['fsync']==settings['synchronous_commit']==settings['track_commit_timestamp']=='on'
    assert len(report['trials'])==2 and len({t['processId'] for t in report['trials']})==2
    results=[]
    for trial in report['trials']:
        cap=trial['cap'];prefix='cap-'+str(cap)
        client=json.loads(files[prefix+'-client.json'])
        assert client['route']=='direct' and client['maximumInflight']==cap
        assert client['npgsqlMaximumPoolSize']==32 and client['capacityEvidence'] is False
        slots=analyze_slots(vector,client)
        assert slots==trial['slotAnalysis']
        assert max(e['atNs'] for e in client['slotEvents'])<=client['runWallClockNs']
        before=json.loads(files[prefix+'-before-sql.json'])
        assert before['state']['accounts']==[[i,100000] for i in range(1,1001)]
        assert before['state']['operations']==before['state']['postings']==before['state']['outbox']==[]
        sql=json.loads(files[prefix+'-sql.json'])
        verify_state(sql,vector)
        commits=[[op,status,datetime.fromisoformat(stamp)] for op,status,stamp in sql['commits']]
        financial=summarize(vector,client,commits,sql['state']['postings'],sql['state']['outbox'],sql['sevenOracles'])
        assert financial==trial['financialAnalysis'] and sql['stateSha256']==trial['sqlStateSha256']
        waits=json.loads(files[prefix+'-pg-waits.json'])
        assert waits and not any('error' in row for row in waits)
        results.append(dict(cap=cap,missed=financial['missed'],ambiguous=financial['ambiguous'],
            sqlCommitted=financial['sqlDurableCommittedByRunEnd'],
            certainCommitsPerSecond=financial['serverCommitWindow']['certainCommitsPerSecond'],
            phases=slots['phases']))
    assert {r['cap'] for r in results}=={32,128}
    return dict(status='AUDITED_DIAGNOSTIC_NOT_CAPACITY',source=source,cohort=cohort,
        bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),sourceHashes=len(expected),
        vectorSha256=vector['offeredVectorSha256'],trials=results,capacityEstablished=False,
        bottleneckAttributionEstablished=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip',type=Path)
    parser.add_argument('--source',required=True)
    args=parser.parse_args()
    print(json.dumps(audit_bytes(args.zip.read_bytes(),args.source),indent=2))
