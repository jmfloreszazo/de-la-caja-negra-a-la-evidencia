#!/usr/bin/env python3
"""Fresh-process negative/positive calibration with a read-only SQL oracle."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'lab/e1_pg'))
sys.path.insert(0, str(ROOT / 'lab/e2_activation_observer'))
from ledger import reset, connect
from oracle import verify
from contract import accept
from observation import reconcile

OUT = ROOT / 'lab/results/e2-calibration'
OUT.mkdir(parents=True, exist_ok=True)

def snapshot():
    with connect() as db:
        operations = [list(r) for r in db.execute('SELECT id,src,dst,amount,status FROM operations ORDER BY id')]
        postings = [list(r) for r in db.execute('SELECT op,account,delta FROM postings ORDER BY op,account')]
        outbox = [list(r) for r in db.execute('SELECT op,event FROM outbox ORDER BY op')]
        accounts = [list(r) for r in db.execute('SELECT id,balance FROM accounts ORDER BY id')]
    oracle = verify()
    assert len(oracle) == 7 and all(v is True for v in oracle.values())
    return dict(operations=operations, postings=postings, outbox=outbox, accounts=accounts,
                oracle=oracle, effects=dict(committedOperations=len(operations),
                                           postings=len(postings), outboxEvents=len(outbox)))

def main():
    assert os.environ.get('E2_CALIBRATION_TEST') == '1'
    assert os.environ.get('E1_PG_DSN') == 'host=127.0.0.1 port=55438 dbname=e2calibration user=postgres password=e2local'
    assert os.environ.get('E2_CALIBRATION_NPGSQL') == 'Host=127.0.0.1;Port=55438;Database=e2calibration;Username=postgres;Password=e2local'
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert source == os.environ['SOURCE_HEAD_SHA']
    report = dict(status='FAIL', fixtureKind='STATELESS_WORKER_OBSERVER_CALIBRATION',
                  sourceHeadSha=source, checkoutSha=source, physicalHosts=1,
                  ordinaryAccountGrainConcurrencyEstablished=False, cases={})
    try:
        paths = subprocess.check_output(['git','ls-files','lab/e2_activation_calibration',
            'lab/e2_activation_observer','lab/e2_orleans/OrleansLab','lab/e1_pg',
            '.github/workflows/e2-activation-calibration.yml'], text=True).splitlines()
        report['sourceHashes'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
        report['runtime'] = subprocess.check_output(['dotnet', '--info'], text=True)
        for mode in ('single', 'positive'):
            reset()
            before = snapshot()
            assert before['effects'] == dict(committedOperations=0, postings=0, outboxEvents=0)
            started = time.monotonic()
            process = subprocess.run(['dotnet',str(OUT / 'app/Calibration.dll'),mode],
                                     capture_output=True,text=True,timeout=65)
            case = dict(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr,
                        elapsedSeconds=time.monotonic()-started, before=before)
            report['cases'][mode] = case
            (OUT / (mode + '.stdout.log')).write_text(process.stdout)
            (OUT / (mode + '.stderr.log')).write_text(process.stderr)
            case['sql'] = snapshot()
            assert process.returncode == 0, case
            markers = [line.split(':',1)[1] for line in process.stdout.splitlines()
                       if line.startswith('E2_CALIBRATION_RESULTS:')]
            assert len(markers) == 1
            result = json.loads(markers[0])
            case['result'] = result
            # Readiness supplies the actual node name; no invented activation identity.
            ready = [json.loads(line.split(':',1)[1]) for line in process.stdout.splitlines()
                     if line.startswith('E2_TRANSFER_OBSERVER_READY:')]
            assert len(ready) == 1
            case['observation'] = accept(process.stdout, ready[0]['node'], mode == 'positive')
            if mode == 'single':
                assert result['status'] == 'EXPECTED_BARRIER_TIMEOUT'
                assert case['sql']['effects'] == dict(committedOperations=0, postings=0, outboxEvents=0)
            else:
                assert result['status'] == 'COMPLETED'
                assert case['sql']['effects'] == dict(committedOperations=1, postings=2, outboxEvents=1)
                assert len(case['sql']['operations']) == 1
                row = case['sql']['operations'][0]
                assert row[:3] == ['e2-observer-calibration',1,2] and row[3] in (31,37) and row[4] == 'COMMITTED'
                reconcile(case['observation'], case['sql'], [])
        report['status'] = 'PASS_CALIBRATION_ONLY'
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        payload = json.dumps(report, separators=(',', ':')) + '\n'
        (OUT / 'summary.json').write_text(payload)
        print('E2_CALIBRATION_SUMMARY:' + payload, end='')

if __name__ == '__main__':
    main()
