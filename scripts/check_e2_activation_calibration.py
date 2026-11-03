#!/usr/bin/env python3
"""Audit original diagnostic-worker calibration, not ordinary-grain split brain."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'lab/e2_activation_observer'),str(ROOT/'lab/e2_activation_calibration')]
from contract import accept
from observation import reconcile

SOURCE='75dfccb8513d38f7fa70386be47c64014a981996'
SUMMARY_BLOB='0c65ed626a5edbf211116235ef3b673b10819751'

def main():
    raw=(ROOT/'evidence/runs/e2-activation-calibration-original.json').read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==SUMMARY_BLOB
    d=json.loads(raw)
    assert d['status']=='PASS_CALIBRATION_ONLY'
    assert d['sourceHeadSha']==d['checkoutSha']==SOURCE
    assert d['fixtureKind']=='STATELESS_WORKER_OBSERVER_CALIBRATION'
    assert d['physicalHosts']==1 and d['ordinaryAccountGrainConcurrencyEstablished'] is False
    expected=subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE,'--',
        'lab/e2_activation_calibration','lab/e2_activation_observer',
        'lab/e2_orleans/OrleansLab','lab/e1_pg',
        '.github/workflows/e2-activation-calibration.yml'],cwd=ROOT,text=True).splitlines()
    assert set(d['sourceHashes'])==set(expected) and len(expected)==39
    for p,h in d['sourceHashes'].items():
        source=subprocess.check_output(['git','show',SOURCE+':'+p],cwd=ROOT)
        assert hashlib.sha256(source).hexdigest()==h,p
    for mode,case in d['cases'].items():
        assert mode in ('single','positive') and case['returncode']==0
        ready=[json.loads(line.split(':',1)[1]) for line in case['stdout'].splitlines()
               if line.startswith('E2_TRANSFER_OBSERVER_READY:')]
        assert len(ready)==1
        observed=accept(case['stdout'],ready[0]['node'],mode=='positive')
        assert observed==case['observation']
        before=case['before']
        assert before['accounts']==[[i,100000] for i in range(1,17)]
        assert before['operations']==before['postings']==before['outbox']==[]
        assert before['effects']==dict(committedOperations=0,postings=0,outboxEvents=0)
        state=case['sql']
        assert len(state['oracle'])==7 and all(v is True for v in state['oracle'].values())
        assert len(before['oracle'])==7 and all(v is True for v in before['oracle'].values())
        if mode=='single':
            assert state['accounts']==before['accounts']
            assert state['operations']==state['postings']==state['outbox']==[]
            assert state['effects']==before['effects']
            assert case['result']['status']=='EXPECTED_BARRIER_TIMEOUT'
        else:
            operation='e2-observer-calibration'
            assert state['operations']==[[operation,1,2,37,'COMMITTED']]
            assert state['postings']==[[operation,1,-37],[operation,2,37]]
            assert state['outbox']==[[operation,'TransferCommitted']]
            assert state['accounts']==[[i,99963 if i==1 else 100037 if i==2 else 100000] for i in range(1,17)]
            assert state['effects']==dict(committedOperations=1,postings=2,outboxEvents=1)
            result=case['result']
            assert result['status']=='COMPLETED' and result['winner']==1
            pairs=list(zip(result['commands'],result['outcomes']))
            pairs += [(result['commands'][1],result['replay']),(result['commands'][0],result['conflict'])]
            acks=[dict(status='ACKNOWLEDGED',command=dict(operationId=c['OperationId'],
                sourceAccountId=c['SourceAccountId'],targetAccountId=c['TargetAccountId'],
                amountCents=c['AmountCents']),result=dict(status=o['Status'])) for c,o in pairs]
            reconcile(observed,state,acks)
            overlap=observed['overlappingRequestEnvelopes']
            assert len(overlap)==1 and overlap[0]['overlapTicks']==197293967
            assert all(c['begin']['frequency']==1000000000 for c in observed['completeCalls'])
    assert set(d['cases'])=={'single','positive'}
    print('E2 CALIBRATION AUDIT: PASS (real diagnostic overlap 197.294ms; SQL 1/2/1; ordinary-grain partition unproven)')

if __name__=='__main__':main()
