#!/usr/bin/env python3
"""Directional stream-suppression campaign on the three exact disposable stores."""
from datetime import datetime,timezone
import copy
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import psycopg

from stream_partition import StreamPartition
from partition_oracle import evaluate
from test_controller_loss import decision_counts,wait_for
from journal import audit,bootstrap_controller,controller_dsn,dispatch,recover,switch
from two_store import bootstrap,connections,independent_oracle,snapshot

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'lab/results/brownfield/journal'
OBSERVER='host=127.0.0.1 port=55441 dbname=bf_control user=postgres password=bflocal connect_timeout=3'


def observe(sql,args=()):
    if os.environ.get('BROWNFIELD_DISPOSABLE')!='YES':raise RuntimeError('Disposable opt-in required')
    with psycopg.connect(OBSERVER) as db:
        db.execute('SET TRANSACTION READ ONLY')
        assert db.execute('SELECT current_database()').fetchone()[0]=='bf_control'
        return db.execute(sql,args).fetchall()


def authority():return list(observe('SELECT writer,epoch,mode FROM controller.authority WHERE singleton=1')[0])


def probe():
    with psycopg.connect(controller_dsn(),autocommit=True) as db:
        pid=db.execute('SELECT pg_backend_pid()').fetchone()[0]
        print(json.dumps({'pid':pid,'stage':'READY'}),flush=True)
        token=sys.stdin.readline().strip()
        assert token.startswith('C2-PROBE-') and token.replace('-','').isalnum()
        # The token is generated only by this fixture; SQL parameters are still used.
        row=db.execute('SELECT %s /* '+token+' */',(token,)).fetchone()
        print(json.dumps({'stage':'REPLIED','value':row[0]}),flush=True)


def cli(args,case,label):
    start=time.monotonic()
    result=subprocess.run([sys.executable,str(HERE/'journal.py'),*args],capture_output=True,text=True,timeout=10)
    case[label]={'args':args,'exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
                 'durationSeconds':time.monotonic()-start}
    assert result.returncode!=0,'Suppressed controller unexpectedly accepted '+label
    return result.returncode


def exercise(writer,direction,gate,report):
    bootstrap();bootstrap_controller();legacy,candidate=connections()
    epoch=1 if writer=='legacy' else switch('candidate',1)['epoch']
    dsn=legacy if writer=='legacy' else candidate
    schema,table,key=('legacy','transactions','request_id') if writer=='legacy' else ('brownfield','operations','id')
    operation='J-SILENT-'+writer.upper()+'-'+('CTS' if direction=='CLIENT_TO_SERVER' else 'STC')
    case={'writer':writer,'direction':direction,'operationId':operation,'epoch':epoch,'status':'FAIL'}
    report['cases'].append(case)
    with psycopg.connect(dsn) as db:
        db.execute(f"""CREATE FUNCTION {schema}.c2_silent_barrier() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.{key}='{operation}' THEN
            PERFORM set_config('lock_timeout','0',true);PERFORM pg_advisory_xact_lock(847127);
            END IF; RETURN NEW; END $$""")
        db.execute(f'CREATE TRIGGER c2_silent_barrier BEFORE INSERT ON {schema}.{table} FOR EACH ROW EXECUTE FUNCTION {schema}.c2_silent_barrier()')
    barrier=psycopg.connect(dsn,autocommit=True);barrier.execute('SELECT pg_advisory_lock(847127)')
    barrier_pid=barrier.execute('SELECT pg_backend_pid()').fetchone()[0]
    gateway=subprocess.Popen([sys.executable,str(HERE/'journal.py'),'dispatch',operation,'1','2','17',str(epoch)],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    witness=None
    try:
        def blocked():
            with psycopg.connect(dsn) as db:
                return db.execute("SELECT pid,wait_event_type,wait_event,query FROM pg_stat_activity WHERE %s=ANY(pg_blocking_pids(pid)) AND wait_event_type='Lock'",(barrier_pid,)).fetchone()
        case['sqlBlockedAdapter']=list(wait_for(blocked,'financial adapter at silent-fault barrier'))
        case['beforeCounts']=decision_counts(dsn,writer,operation);assert case['beforeCounts']==[0,0,0]
        holders=observe("SELECT DISTINCT a.pid FROM pg_stat_activity a JOIN pg_locks l ON a.pid=l.pid WHERE l.relation='controller.authority'::regclass AND l.granted AND a.xact_start IS NOT NULL")
        pids=[r[0] for r in holders];assert pids
        case['controllerPidsBeforeFault']=pids;before_authority=authority()
        witness=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--probe'],stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        ready,_,_=select.select([witness.stdout],[],[],20);assert ready,'Probe did not connect before fault'
        marker=json.loads(witness.stdout.readline());assert marker['stage']=='READY';case['probeReady']=marker
        case['faultStart']=gate.suppress(direction)
        token='C2-PROBE-'+writer.upper()+'-'+('CTS' if direction=='CLIENT_TO_SERVER' else 'STC')
        witness.stdin.write(token+'\n');witness.stdin.flush()
        wait_for(lambda:gate.snapshot()['droppedBytes'][direction]>0,'actual suppressed stream bytes')
        # Observe a silent interval without closing transport sessions. The query
        # reaches PostgreSQL only in the server-to-client suppression case.
        start=time.monotonic();time.sleep(1)
        case['silentObservation']=gate.snapshot();case['silentObservation']['sampledSeconds']=time.monotonic()-start
        alive=observe('SELECT pid,state,wait_event_type,wait_event,query FROM pg_stat_activity WHERE pid=ANY(%s)',(pids,))
        case['controllerPidsDuringFault']=[r[0] for r in alive];case['controllerSessionsDuringFault']=alive
        assert set(case['controllerPidsDuringFault'])==set(pids),'Suppression closed an existing holder session'
        probe_rows=observe('SELECT state,query FROM pg_stat_activity WHERE pid=%s',(marker['pid'],))
        assert probe_rows,'Probe backend disappeared'
        case['probeBackendDuringFault']=probe_rows[0]
        case['probeQueryObservedAtServer']=token in probe_rows[0][1]
        case['probeExitedDuringFault']=witness.poll() is not None
        assert not case['probeExitedDuringFault']
        gateway.kill();gateway.wait(timeout=5);assert gateway.returncode==-signal.SIGKILL
        case['gatewayExitCode']=gateway.returncode
        case['blockedReconnectExit']=cli(['dispatch',operation+'-NEW','1','2','17',str(epoch)],case,'blockedReconnect')
        case['switchAttemptExit']=cli(['switch','candidate' if writer=='legacy' else 'legacy',str(epoch)],case,'blockedSwitch')
        case['controllerAuthorityUnchanged']=authority()==before_authority
        assert decision_counts(dsn,writer,operation)==[0,0,0]
        barrier.execute('SELECT pg_advisory_unlock(847127)')
        wait_for(lambda:decision_counts(dsn,writer,operation)==[1,2,1],'financial COMMIT while controller bytes remain suppressed')
        case['financialCountsWhileSuppressed']=decision_counts(dsn,writer,operation)
        case['controllerSessionsAfterFinancialCommit']=observe('SELECT pid,state,wait_event_type,wait_event FROM pg_stat_activity WHERE pid=ANY(%s)',(pids,))
        case['admissionBeforeReset']=observe('SELECT operation_id,state,writer,epoch FROM controller.admission WHERE operation_id=%s',(operation,))
        case['snapshotBeforeReset']={'source':snapshot(legacy,'legacy'),'target':snapshot(candidate,'candidate')}
        case['recoveryReset']=gate.reset();case['recoveryIntervention']='CONTROLLED_SOCKET_RESET'
        wait_for(lambda:not observe('SELECT pid FROM pg_stat_activity WHERE pid=ANY(%s)',(pids,)),'controller holder sessions gone after explicit reset')
        case['reconciledStatus']=recover(operation)['status']
        case['replayStatus']=dispatch(operation,1,2,17,epoch)['status']
        case['finalCounts']=decision_counts(dsn,writer,operation)
        case['finalSnapshots']={'source':snapshot(legacy,'legacy'),'target':snapshot(candidate,'candidate')}
        case['sourceOracle']=independent_oracle(case['finalSnapshots']['source'])
        case['targetOracle']=independent_oracle(case['finalSnapshots']['target'])
        case['journalAuditPassed']=audit()['passed']
        case['observationOracle']=evaluate(case);assert not case['observationOracle'],case['observationOracle']
        case['status']='PASS'
    finally:
        gate.reset();barrier.close()
        for name,child in [('gateway',gateway),('probe',witness)]:
            if child is None:continue
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            stdout,stderr=child.communicate(timeout=10)
            case[name+'Output']={'exitCode':child.returncode,'stdout':stdout,'stderr':stderr}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'status':'FAIL','protocol':'C2_DIRECTIONAL_STREAM_SUPPRESSION_V1','startUtc':datetime.now(timezone.utc).isoformat(),
            'sourceHeadSha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'runId':os.environ.get('GITHUB_RUN_ID'),
            'cases':[],'negativeControls':[],'todmG2':'INCONCLUSIVE','todmG6':'BLOCK',
            'limitations':'Opaque application-stream suppression on live TCP sockets on one runner; TCP acknowledges proxy reads. Not kernel packet loss, transparent stream recovery, real bank fencing, native mainframe execution, physical HA or capacity.'}
    paths=[HERE/name for name in ['stream_partition.py','partition_oracle.py','test_stream_partition.py','test_controller_partition.py','test_controller_loss.py','journal.py','schema.sql']]
    paths += [HERE.parent/'coexistence'/name for name in ['legacy_api.py','two_store.py','legacy_schema.sql']]
    paths += [HERE.parent/'durable/DurableBank/Program.cs',HERE.parent/'durable/schema.sql',ROOT/'.github/workflows/brownfield-journal.yml']
    report['sourceSha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    try:
        with StreamPartition() as gate:
            for writer in ['legacy','candidate']:
                for direction in ['CLIENT_TO_SERVER','SERVER_TO_CLIENT']:exercise(writer,direction,gate,report)
            report['linkEvents']=gate.events
        for label,change in [('false-no-financial-effect',lambda c:c.update(financialCountsWhileSuppressed=[0,0,0])),
                             ('false-automatic-recovery',lambda c:c.update(recoveryIntervention='AUTOMATIC'))]:
            mutant=copy.deepcopy(report['cases'][0]);change(mutant);errors=evaluate(mutant);assert errors
            report['negativeControls'].append({'name':label,'mutatedObservation':mutant,'rejectedBy':errors})
        report['status']='PASS'
    except BaseException as error:
        report['error']=repr(error);raise
    finally:
        report['endUtc']=datetime.now(timezone.utc).isoformat()
        (OUT/'c2-controller-partition.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
        print(json.dumps({'status':report['status'],'cases':len(report['cases']),'report':'c2-controller-partition.json'}))

if __name__=='__main__':
    if sys.argv[1:]==['--probe']:probe()
    else:main()
