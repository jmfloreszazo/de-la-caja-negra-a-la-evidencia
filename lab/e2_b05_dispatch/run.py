#!/usr/bin/env python3
"""Three fresh cohorts compare direct-client caps with independent SQL COMMITs."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'lab/e1_pg'),str(ROOT/'lab/e2_orleans')]
from ledger import connect,reset
from oracle_workload import verify
from b05_arrival_contract import generate
from b05_sweep_analysis import summarize
from analysis import analyze_slots

OUT=ROOT/'lab/results/b05-dispatch'
OUT.mkdir(parents=True,exist_ok=True)


def ready():
    observations=[]
    deadline=time.monotonic()+70
    while time.monotonic()<deadline:
        try:
            with connect() as db:
                pid,stamp=db.execute('SELECT pg_backend_pid(),clock_timestamp()').fetchone()
                tracking=db.execute('SHOW track_commit_timestamp').fetchone()[0]
            observations.append(dict(pid=pid,utc=stamp.isoformat(),tracking=tracking))
            if len(observations)>=2 and all('pid' in x for x in observations[-2:]) and observations[-1]['pid']!=observations[-2]['pid'] and tracking=='on':
                return observations
        except Exception as error:
            observations.append(dict(error=repr(error)))
        time.sleep(.5)
    raise AssertionError('Two independent timestamp-enabled SQL sessions were not ready: '+repr(observations))


def sql_snapshot():
    with connect() as db:
        accounts=db.execute('SELECT id,balance FROM accounts ORDER BY id').fetchall()
        operations=db.execute('SELECT id,src,dst,amount,status FROM operations ORDER BY id').fetchall()
        postings=db.execute('SELECT op,account,delta FROM postings ORDER BY op,account').fetchall()
        outbox=db.execute('SELECT op,event FROM outbox ORDER BY op').fetchall()
        commits=db.execute('SELECT id,status,pg_xact_commit_timestamp(xmin) FROM operations ORDER BY id').fetchall()
    oracle_error=None
    try:
        checks=verify()
    except Exception as error:
        checks={}
        oracle_error=repr(error)
    state=dict(accounts=accounts,operations=operations,postings=postings,outbox=outbox)
    digest=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(state=state,stateSha256=digest,commits=commits,sevenOracles=checks,oracleError=oracle_error)


def wait_samples(stop,rows):
    try:
        with connect() as db:
            while not stop.is_set():
                observed=db.execute("SELECT state,wait_event_type,wait_event,count(*) "
                    "FROM pg_stat_activity WHERE datname='e2dispatch' AND pid<>pg_backend_pid() "
                    "GROUP BY state,wait_event_type,wait_event ORDER BY 1,2,3").fetchall()
                rows.append(dict(utc=datetime.now(timezone.utc).isoformat(),states=observed))
                stop.wait(1)
    except Exception as error:
        rows.append(dict(error=repr(error)))


def main():
    assert os.environ.get('E2_DISPATCH_DIAGNOSTIC')=='1'
    assert os.environ.get('E1_PG_DSN')=='host=127.0.0.1 port=55439 dbname=e2dispatch user=postgres password=e2local'
    cohort=int(os.environ['DISPATCH_COHORT'])
    assert cohort in (0,1,2)
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert source==os.environ['SOURCE_HEAD_SHA']
    report=dict(status='FAIL',sourceHeadSha=source,checkoutSha=source,cohort=cohort,
        capacityEstablished=False,bottleneckAttributionEstablished=False,
        topology='One physical host; separate native direct client and Docker PostgreSQL; no Orleans route',trials=[])
    try:
        report['readiness']=ready()
        paths=subprocess.check_output(['git','ls-files','lab/e2_b05_dispatch',
            'lab/e2_orleans/OrleansLab','lab/e2_orleans/b05_arrival_contract.py',
            'lab/e2_orleans/b05_sweep_analysis.py','lab/e2_orleans/oracle_workload.py',
            'lab/e1_pg/ledger.py','lab/e1_pg/schema.sql','lab/e1_pg/requirements.txt',
            '.github/workflows/e2-b05-dispatch.yml'],text=True).splitlines()
        report['sourceHashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
        report['host']=dict(uname=list(platform.uname()),cpuCount=os.cpu_count(),
            cpuMax=Path('/sys/fs/cgroup/cpu.max').read_text() if Path('/sys/fs/cgroup/cpu.max').exists() else None,
            memoryMax=Path('/sys/fs/cgroup/memory.max').read_text() if Path('/sys/fs/cgroup/memory.max').exists() else None)
        with connect() as db:
            report['postgresSettings']={key:db.execute('SHOW '+key).fetchone()[0] for key in
                ('server_version','fsync','synchronous_commit','transaction_isolation','max_connections','track_commit_timestamp')}
        assert report['postgresSettings']['fsync']=='on' and report['postgresSettings']['synchronous_commit']=='on'
        assert report['postgresSettings']['track_commit_timestamp']=='on'
        vector=generate('five_percent_hot',320,1,60,1,20261031,0)
        vector_path=OUT/'input.json'
        vector_path.write_text(json.dumps(vector,separators=(',',':'))+'\n')
        report['vectorSha256']=vector['offeredVectorSha256']
        report['capOrder']=[32,128] if cohort%2==0 else [128,32]
        for cap in report['capOrder']:
            prefix='cap-'+str(cap)
            reset()
            with connect() as db:
                db.execute('INSERT INTO accounts(id,balance) SELECT n,100000 FROM generate_series(17,1000) n')
            before=sql_snapshot()
            (OUT/(prefix+'-before-sql.json')).write_text(json.dumps(before,default=str,separators=(',',':'))+'\n')
            assert len(before['sevenOracles'])==7 and all(before['sevenOracles'].values())
            assert before['state']['operations']==[] and len(before['state']['accounts'])==1000
            waits=[]
            stop=threading.Event()
            monitor=threading.Thread(target=wait_samples,args=(stop,waits),daemon=True)
            monitor.start()
            try:
                result=subprocess.run(['dotnet',str(OUT/'app/DispatchProbe.dll'),str(vector_path),str(cap)],
                    capture_output=True,text=True,timeout=195)
            except subprocess.TimeoutExpired as error:
                (OUT/(prefix+'-client.json')).write_bytes(error.stdout or b'')
                (OUT/(prefix+'-client.stderr.log')).write_bytes(error.stderr or b'')
                raise
            finally:
                stop.set();monitor.join(timeout=15)
            (OUT/(prefix+'-client.json')).write_text(result.stdout)
            (OUT/(prefix+'-client.stderr.log')).write_text(result.stderr)
            (OUT/(prefix+'-pg-waits.json')).write_text(json.dumps(waits,separators=(',',':'))+'\n')
            sql=sql_snapshot()
            (OUT/(prefix+'-sql.json')).write_text(json.dumps(sql,default=str,separators=(',',':'))+'\n')
            assert not monitor.is_alive() and not any('error' in row for row in waits)
            assert result.returncode==0,result.stderr
            assert len(sql['sevenOracles'])==7 and all(v is True for v in sql['sevenOracles'].values())
            client=json.loads(result.stdout)
            assert client['experiment']=='E2_B05_DISPATCH_DIAGNOSTIC_V1' and client['maximumInflight']==cap
            slots=analyze_slots(vector,client)
            financial=summarize(vector,client,sql['commits'],sql['state']['postings'],sql['state']['outbox'],sql['sevenOracles'])
            report['trials'].append(dict(cap=cap,slotAnalysis=slots,financialAnalysis=financial,
                sqlStateSha256=sql['stateSha256'],clientReturncode=result.returncode,
                processId=client['independentExternalProcessId'],cpuMilliseconds=client['cpuMilliseconds'],
                gcCollections=client['gcCollections'],peakWorkingSetBytes=client['peakWorkingSetBytes']))
        assert len(report['trials'])==2 and len({t['processId'] for t in report['trials']})==2
        report['status']='OBSERVED_DISPATCH_DIAGNOSTIC_NOT_CAPACITY'
    except Exception as error:
        report['error']=repr(error)
        raise
    finally:
        (OUT/'summary.json').write_text(json.dumps(report,default=str,indent=2)+'\n')
        print(json.dumps(dict(status=report['status'],cohort=cohort,error=report.get('error'),
            trials=[dict(cap=t['cap'],missed=t['financialAnalysis']['missed'],
                sqlCommitted=t['financialAnalysis']['sqlDurableCommittedByRunEnd'],
                measurementCommits=t['financialAnalysis']['serverCommitWindow']['certainCommits'])
                for t in report['trials']])))


if __name__=='__main__':main()
