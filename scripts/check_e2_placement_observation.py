#!/usr/bin/env python3
"""Audit real provider-specific observation negatives without claiming failover."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
from historical_source import verify_historical_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'c547c3f34badda0cb57ab0b496917dadb1485b04'
DIGESTS = {
    'development': '56db17efe633841faee910d62b64f51cc8ee100700a3b2c8489310d557d98fb8',
    'adonet': '1d06e1c7541b5a14f515bf720911302ec72dd3ce0383e042e5fc45f7eb818035',
}
MARKER = 'OBSERVATION_NEGATIVE_CONTROL_AFTER_FIRST_PROBE'
HISTORY = ROOT / 'evidence/runs/e2-c05-loopback-placement-failure-original.zip'


def main():
    assert hashlib.sha256(HISTORY.read_bytes()).hexdigest() == '55bed14ebac7f582b3d29a9dc13e97c6c75f11a48c64bfdf12a7b18db9fe5332'
    with zipfile.ZipFile(HISTORY) as z:
        old = z.read('e2-multiprocess.json')
    execution_ids = set()
    for provider, digest in DIGESTS.items():
        stem = ROOT / ('evidence/runs/e2-loopback-observation-' + provider + '-original')
        assert hashlib.sha256(stem.with_suffix('.zip').read_bytes()).hexdigest() == digest
        with zipfile.ZipFile(stem.with_suffix('.zip')) as z:
            raw = z.read('loopback-observation-negative-' + provider + '.json')
            assert raw == stem.with_suffix('.json').read_bytes()
            report = json.loads(raw)
            assert report['status'] == 'NEGATIVE_CONTROL_VERIFIED' and report['membershipProvider'] == provider
            assert report['sourceHeadSha'] == SOURCE and report['actualChildExitCode'] == 1
            assert report['financialCommandsAttempted'] == 0 and report['effects'] == [0, 0, 0]
            assert len(report['oracle']) == 7 and all(v is True for v in report['oracle'].values())
            assert z.read('e2-multiprocess.json') == old
            old_hash = hashlib.sha256(old).hexdigest()
            assert report['historicalSuccessInputSha256'] == old_hash
            manifest = json.loads(z.read(report['manifestFile']))
            failure = json.loads(z.read(report['failureFile']))
            execution_ids.add(manifest['executionId'])
            assert manifest['status'] == failure['status'] == 'FAIL'
            assert manifest['membershipProvider'] == failure['membershipProvider'] == provider
            assert manifest['sourceHeadSha'] == failure['sourceHeadSha'] == SOURCE
            assert manifest['worktreeDirty'] is False and manifest['negativeControlRequested'] is True
            assert 'successFile' not in manifest
            assert manifest['preexistingSuccessFiles']['e2-multiprocess.json'] == old_hash
            assert failure['phase'] == 'placement-convergence' and failure['error'] == MARKER
            assert failure['isSuccessfulFailoverEvidence'] is False
            state = failure['state']
            assert state['financialCommandsAttempted'] == state['financialClientInvocations'] == 0
            assert state['secondaryKillRequested'] is False and state['financialFaultInjected'] is False
            assert state['placementAttempts'] == 1
            processes = state['processes']
            assert all(v['returnCode'] is None for v in processes.values())
            pids = {v['pid'] for v in processes.values()}
            assert len(pids) == 2
            probe = state['lastClientProbe']
            assert set(probe['accountHostPids']) == {str(k) for k in range(1, 17)}
            assert set(probe['accountHostPids'].values()) == pids
            assert probe['clientPid'] not in pids
            counts = {role: sum(v == process['pid'] for v in probe['accountHostPids'].values())
                      for role, process in processes.items()}
            assert counts == ({'primary': 7, 'secondary': 9} if provider == 'development'
                              else {'primary': 10, 'secondary': 6})
            assert state['sql']['observationSucceeded'] and state['sql']['value'] == {
                'operations': [], 'postings': 0, 'outbox': 0}
            assert state['oracle']['observationSucceeded'] and all(v is True for v in state['oracle']['value'].values())
            if provider == 'adonet':
                assert state['sqlMembership']['observationSucceeded']
                assert {r[2]: r[4] for r in state['sqlMembership']['value']['membershipRows']} == {11150: 3, 11151: 3}
            else:
                assert failure['sqlMembershipApplicable'] is False and state['sqlMembership']['value'] is None
            assert set(failure['logs']) == {'primary', 'secondary'}
            for role, observation in failure['logs'].items():
                data = z.read(observation['file'])
                assert hashlib.sha256(data).hexdigest() == observation['sha256'] and len(data) == observation['bytes']
                assert b'E2_PLACEMENT_STRATEGY:Orleans.Runtime.ResourceOptimizedPlacement' in data
                assert ('E2_SILO_READY:' + role + ':' + str(processes[role]['pid'])).encode() in data
            journal_raw = z.read(failure['journalFile'])
            assert hashlib.sha256(journal_raw).hexdigest() == failure['journalSha256']
            events = [json.loads(line) for line in journal_raw.splitlines()]
            assert [e['sequence'] for e in events] == list(range(1, 7))
            assert [e['kind'] for e in events] == ['execution-started', 'preflight', 'silos-ready',
                                                 'client-process', 'placement-probe', 'execution-failed']
            assert all(e['executionId'] == manifest['executionId'] and e['membershipProvider'] == provider for e in events)
            assert events[-1]['phase'] == 'placement-convergence' and events[-1]['error'] == MARKER
            assert json.loads(events[3]['observation']['stdout']) == probe
            assert events[3]['observation']['exitCode'] == 0 and events[4]['attempt'] == 1
            provenance = z.read('observation-provenance.txt').decode()
            assert 'source_head_sha=' + SOURCE in provenance and 'checkout_sha=' + SOURCE in provenance
            hashes = {p: h for h, p in re.findall(r'^([0-9a-f]{64})  (.+)$', provenance, re.M)}
            assert len(hashes) == 69
            for p, h in failure['sourceSha256'].items():
                assert hashes['lab/' + p] == h
                # Archive provenance and disposable-container support evolved
                # later; these negative controls only evidence the pinned commit.
                if p in ('e2_orleans/test_multiprocess.py', 'e2_orleans/setup_adonet_membership.py'):
                    verify_historical_source(ROOT, SOURCE, 'lab/' + p, h)
                else:
                    assert hashlib.sha256((ROOT / 'lab' / p).read_bytes()).hexdigest() == h, p
    assert len(execution_ids) == 2
    print('E2 LOOPBACK OBSERVATION AUDIT: PASS (historical source bytes; 2 real induced FAIL controls; zero effects; root cause unproven)')


if __name__ == '__main__':
    main()
