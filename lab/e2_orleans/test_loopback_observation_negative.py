#!/usr/bin/env python3
"""Real loopback/SQL negative: preserve an induced first-probe rejection.

No transfer, placement override or default-policy/root-cause claim is made.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from test_e2 import HERE, LAB, OUT
from ledger import connect
from oracle import verify

MARKER = 'OBSERVATION_NEGATIVE_CONTROL_AFTER_FIRST_PROBE'
PROVIDER = os.environ.get('E2_CLUSTER_PROVIDER', 'development')
HISTORY_DIGEST = '55bed14ebac7f582b3d29a9dc13e97c6c75f11a48c64bfdf12a7b18db9fe5332'


def main():
    assert PROVIDER in ('development', 'adonet')
    assert os.environ.get('E1_PG_DSN') == 'host=127.0.0.1 port=55434 dbname=e2lab user=postgres password=e2local'
    assert os.environ.get('E2_CLUSTER_TEST') != '1'
    history = LAB.parent / 'evidence/runs/e2-c05-loopback-placement-failure-original.zip'
    assert hashlib.sha256(history.read_bytes()).hexdigest() == HISTORY_DIGEST
    with zipfile.ZipFile(history) as z:
        old_success = z.read('e2-multiprocess.json')
    assert json.loads(old_success)['membershipProvider'] == 'development'
    # Unmodified historical input, explicitly NOT a success from this job.
    (OUT / 'e2-multiprocess.json').write_bytes(old_success)
    old_hash = hashlib.sha256(old_success).hexdigest()
    prior = set(OUT.glob('e2-loopback-*-manifest.json'))
    env = {**os.environ, 'E2_PLACEMENT_OBSERVATION_NEGATIVE': '1'}
    result = subprocess.run([sys.executable, str(HERE / 'test_multiprocess.py')], env=env,
                            text=True, capture_output=True, timeout=200)
    (OUT / 'observation-negative-child.stdout.log').write_text(result.stdout)
    (OUT / 'observation-negative-child.stderr.log').write_text(result.stderr)
    assert result.returncode == 1 and MARKER in result.stderr, (result.returncode, result.stderr[-3500:])
    manifests = set(OUT.glob('e2-loopback-*-manifest.json')) - prior
    assert len(manifests) == 1
    manifest_path = manifests.pop()
    manifest = json.loads(manifest_path.read_text())
    assert manifest['membershipProvider'] == PROVIDER and manifest['status'] == 'FAIL'
    assert manifest['negativeControlRequested'] is True
    assert manifest['worktreeDirty'] is False
    assert manifest['preexistingSuccessFiles']['e2-multiprocess.json'] == old_hash
    assert 'successFile' not in manifest
    failure_path = OUT / manifest['failureFile']
    failure = json.loads(failure_path.read_text())
    assert failure['status'] == 'FAIL' and failure['phase'] == 'placement-convergence'
    assert failure['isSuccessfulFailoverEvidence'] is False and failure['error'] == MARKER
    state = failure['state']
    assert state['financialCommandsAttempted'] == state['financialClientInvocations'] == 0
    assert state['financialFaultInjected'] is False and state['placementAttempts'] == 1
    assert state['secondaryKillRequested'] is False
    assert set(state['lastClientProbe']['accountHostPids']) == {str(i) for i in range(1, 17)}
    assert state['lastClientProbe']['diagnosticOnly'] is False
    pids = {r['pid'] for r in state['processes'].values()}
    assert len(pids) == 2 and all(r['returnCode'] is None for r in state['processes'].values())
    assert set(state['lastClientProbe']['accountHostPids'].values()) <= pids
    assert state['lastClientProbe']['clientPid'] not in pids
    assert state['sql']['observationSucceeded'] is True
    assert state['sql']['value'] == {'operations': [], 'postings': 0, 'outbox': 0}
    assert state['oracle']['observationSucceeded'] is True
    assert len(state['oracle']['value']) == 7 and all(v is True for v in state['oracle']['value'].values())
    if PROVIDER == 'adonet':
        assert state['sqlMembership']['observationSucceeded'] is True
        rows = state['sqlMembership']['value']['membershipRows']
        assert {r[2]: r[4] for r in rows} == {11150: 3, 11151: 3}
        assert all(r[0] == 'e2-local-recovery' for r in rows)
    else:
        assert state['sqlMembership']['value'] is None and failure['sqlMembershipApplicable'] is False
    for role, log in failure['logs'].items():
        raw = (OUT / log['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == log['sha256'] and len(raw) == log['bytes']
        assert b'E2_PLACEMENT_STRATEGY:Orleans.Runtime.ResourceOptimizedPlacement' in raw
        assert ('E2_SILO_READY:' + role + ':').encode() in raw
    assert set(failure['logs']) == {'primary', 'secondary'}
    journal_raw = (OUT / failure['journalFile']).read_bytes()
    assert hashlib.sha256(journal_raw).hexdigest() == failure['journalSha256']
    events = [json.loads(line) for line in journal_raw.splitlines()]
    assert [e['sequence'] for e in events] == list(range(1, len(events) + 1))
    probes = [e for e in events if e['kind'] == 'placement-probe']
    assert len(probes) == 1 and probes[0]['attempt'] == 1
    assert probes[0]['accountHostPids'] == state['lastClientProbe']['accountHostPids']
    client_events = [e for e in events if e['kind'] == 'client-process']
    assert len(client_events) == 1 and client_events[0]['observation']['exitCode'] == 0
    assert json.loads(client_events[0]['observation']['stdout']) == state['lastClientProbe']
    with connect() as db:
        effects = [db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                   for table in ('operations', 'postings', 'outbox')]
    assert effects == [0, 0, 0] and all(v is True for v in verify().values())
    assert (OUT / 'e2-multiprocess.json').read_bytes() == old_success
    report = {'status': 'NEGATIVE_CONTROL_VERIFIED', 'membershipProvider': PROVIDER,
              'sourceHeadSha': manifest['sourceHeadSha'], 'executionId': manifest['executionId'],
              'failureFile': failure_path.name, 'manifestFile': manifest_path.name,
              'historicalSuccessInputSha256': old_hash, 'historicalArchiveSha256': HISTORY_DIGEST,
              'financialCommandsAttempted': 0, 'effects': effects, 'oracle': verify(),
              'actualChildExitCode': result.returncode,
              'limitations': 'Induced observation failure after a real identity probe. Not a natural '
              'one-sided-placement reproduction, root-cause explanation, failover or overall E2 acceptance.'}
    (OUT / ('loopback-observation-negative-' + PROVIDER + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
