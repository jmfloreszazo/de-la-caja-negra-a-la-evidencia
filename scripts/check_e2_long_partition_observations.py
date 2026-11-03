#!/usr/bin/env python3
"""Audit original long schedules, packet bytes, lifecycle and sampled recovery."""
import hashlib
import json
import re
import zipfile
from check_e2_directional_partition_observations import ROOT, RUNS, CRITICAL, packets, sql

SOURCE = 'ee1e883e5e23d651e3408a90f8ec12fd9f7a2d58'
DIGESTS = {
    'primary': '999f2612e6a032305e0a7dc58b30e7cecbe8670626ce976f924e06c5141b46d0',
    'secondary': 'a0f2ed8039afae94eadf2bb1f255f0887c4fa69553cb16717229233aa201f922',
}
PINS = {p: h for p, h in CRITICAL.items() if p != '.github/workflows/e2-c05-c06-directional.yml'}
PINS.update({
    'lab/e2_orleans/test_long_partition.py': 'd0076c1c4cef52cdd9189259b6cc98ffdc2e24e1380448ddefe0122221b34e40',
    '.github/workflows/e2-long-partition.yml': '64f5575ef93f9abca4d3de666f9c88fe35daff8cd51fbe74a196b8af3b363931',
    'lab/e2_orleans/placement_observation.py': '0dba3f9f480a9586c8f7dc477efdbc80c67d25ac63cc6b50c41ae8e13e2066a0',
})


def original(stem, digest):
    path = RUNS / (stem + '.zip')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist()}
    assert files['long-partition-summary.json'] == (RUNS / (stem + '.json')).read_bytes()
    return json.loads(files['long-partition-summary.json']), files


def ack(outcome, operations):
    if outcome['status'] != 'ACKNOWLEDGED':
        return
    command, result = outcome['command'], outcome['result']['status']
    row = next(r for r in operations if r[0] == command['operationId'])
    same = row[1:4] == [command['sourceAccountId'], command['targetAccountId'], command['amountCents']]
    assert result in ('COMMITTED', 'DUPLICATE_COMMITTED') if same else result == 'ID_CONFLICT'
    assert outcome['financialCommandsDispatched'] == 1 and outcome['placementHintsUsed'] is False


def main():
    failures = {
        'primary': ('eb47f2302c5ddb880de2857e4c8e6d694518b1aeaae3cc8b2aa54572bbfc4439', 'dependent'),
        'secondary': ('52b51a65c1dd918d9d3c7778bda34fdb77a6032294c5366cb02b2da911a09e4e', 'Bad rule'),
    }
    for role, (digest, error) in failures.items():
        d, _ = original('e2-long-first-' + role + '-original', digest)
        assert d['status'] == 'FAIL' and error.lower() in d['error'].lower()
        assert d['sourceHeadSha'] == '62d78fbddc206babbe3cbd28630f33464271d619'
    for role, digest in DIGESTS.items():
        d, files = original('e2-long-' + role + '-original', digest)
        assert d['status'] == 'PASS' and d['sourceHeadSha'] == SOURCE and d['blockedRole'] == role
        assert d['physicalHosts'] == 1 and d['activationExclusivityEstablished'] is False
        provenance = files['long-partition-provenance.txt'].decode()
        assert 'source_head_sha=' + SOURCE in provenance and 'checkout_sha=' + SOURCE in provenance
        hashes = {p: h for h, p in re.findall(r'^([0-9a-f]{64})  (.+)$', provenance, re.M)}
        assert len(hashes) == 70
        for p, h in PINS.items():
            assert hashes[p] == h and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, p
        assert len(set(d['namespaces'].values())) == 4
        assert len({s['pidOnHost'] for s in d['containersBefore'].values()}) == 4
        assert d['seeding']['financialCommandsDispatched'] == 0 and d['seeding']['placementHintRetained'] is False
        assert {k: v.split(':', 1)[0] for k, v in d['seeding']['accountHostNodes'].items()} == {
            str(k): 'e2f10-primary' if k % 2 else 'e2f10-secondary' for k in range(1, 17)}
        assert d['requestedFaultScheduleSeconds'] == 120 and 120 <= d['faultScheduleElapsedSeconds'] <= 180
        assert len(d['diagnosticHelpers']) == 4
        for helper in d['diagnosticHelpers']:
            assert helper['inspection']['status'] == helper['target']['status'] == 'running'
        assert d['diagnosticEvents']
        for event in d['diagnosticEvents']:
            before, after = event['before'], event['after']
            assert before['id'] == after['id']
            assert not (before['status'] == 'exited' and after['status'] == 'running')
            if before['status'] == after['status'] == 'running':
                assert before['pidOnHost'] == after['pidOnHost']
        assert all(s['status'] == 'exited' and s['exitCode'] == 0 for s in d['captureHelpersAfter'].values())
        blocked, peer = ('10.78.30.11', '10.78.30.12') if role == 'primary' else ('10.78.30.12', '10.78.30.11')
        decoded = {}
        for side in ('primary', 'secondary'):
            raw = files[side + '.pcap']
            info = d['initialCaptures'][side]
            assert hashlib.sha256(raw).hexdigest() == info['sha256'] and len(raw) == info['bytes']
            assert files[side + '-packets.txt'].decode().rstrip() == info['decoded']
            decoded[side] = packets(raw)
        other = 'secondary' if role == 'primary' else 'primary'
        assert not any(p[:2] == (blocked, peer) for p in decoded[other])
        assert {p for p in decoded[other] if p[:2] == (peer, blocked)} & {
            p for p in decoded[role] if p[:2] == (peer, blocked)}
        assert all(p.strip() == 'CONNECT_EXIT:1' for p in d['tcpProbes'].values())
        for phase in ('initialDropCounters', 'finalDropCounters'):
            assert d[phase]['observationSucceeded']
            counter = re.findall(r'\[(\d+):(\d+)\] -A OUTPUT .*--ports 11150,11151 -j DROP', d[phase]['value'])
            assert len(counter) == 1 and int(counter[0][0]) > 0
        assert all(c['databaseHealthy'] and c['primaryGatewayReachable'] and c['secondaryGatewayReachable']
                   for c in d['initialNetworkChecks'].values())
        sql(d['initialSql'], (0, 0, 0))
        sql(d['baselineSql'], (1, 2, 1))
        samples = d['samples']
        for sample in samples:
            assert sample['elapsedSeconds'] <= sample['observationEndedSeconds']
            assert sample['outputRule']['observationSucceeded']
            assert '--ports 11150,11151 -j DROP' in sample['outputRule']['value']
            assert {r[0] for r in sample['sql']['operations']} <= {'c05-baseline', 'c05-contested-id'}
            assert all(v is True for v in sample['sql']['oracle'].values())
            assert sample['processes']['primary'] == d['containersBefore']['e2f10-primary']
        first_exit = next(s for s in samples if s['processes']['secondary']['status'] == 'exited')
        assert first_exit['observationEndedSeconds'] < 120
        assert samples[-1]['processes']['secondary']['status'] == 'exited'
        assert samples[-1]['processes']['secondary']['id'] == d['containersBefore']['e2f10-secondary']['id']
        assert d['recoveryMode'] == 'ASSISTED_BOTH_SILOS_RECREATED'
        assert d['ruleRestoration'] == ('PINNED_NAMESPACE_BASELINE_TARGET_RUNNING' if role == 'primary'
                                        else 'PINNED_NAMESPACE_BASELINE_TARGET_EXITED')
        assert len(d['unassistedAttempts']) == 2
        for attempt in d['unassistedAttempts']:
            assert attempt['outcomes'][1]['status'] == 'STARTUP_UNAVAILABLE'
            assert attempt['outcomes'][1]['financialCommandsDispatched'] == 0
        assert 0 < d['firstBothAckSecondsAfterRestore'] <= d['recoveryCriteriaSatisfiedSecondsAfterRestore'] <= 300
        for side in ('primary', 'secondary'):
            before, after = d['beforeAssistedRecreation'][side], d['containersAfter'][side]
            assert before['id'] != after['id'] and after['status'] == 'running' and after['pidOnHost'] > 0
        sql(d['finalSql'], (3, 6, 3))
        rows = d['finalSql']['operations']
        assert rows == [['c05-baseline', 1, 2, 11, 'COMMITTED'], ['c05-contested-id', 2, 1, 37, 'COMMITTED'],
                        ['c06-recovery-new', 1, 2, 5, 'COMMITTED']]
        assert [x['result']['status'] for x in d['replayConflictNew']] == ['DUPLICATE_COMMITTED', 'ID_CONFLICT', 'COMMITTED']
        old_generations = {(r[0], r[1], r[2]) for r in d['beforeAssistedMembership']}
        new_active = {(r[0], r[1], r[2]) for r in d['finalSql']['membershipGenerations'] if r[3] == 3}
        assert len(new_active) == 2 and not old_generations & new_active
        steady = d['stableSamples']
        assert [s['index'] for s in steady] == list(range(14))
        span = steady[-1]['elapsedSeconds'] - steady[0]['elapsedSeconds']
        assert span == d['stableObservationSpanSeconds'] and 60 <= span <= 150
        outcomes = d['firstContendingOutcomes'] + d['lateContendingOutcomes'] + d['assistedOutcomes'] + d['replayConflictNew']
        outcomes += [o for a in d['unassistedAttempts'] for o in a['outcomes']]
        for index, sample in enumerate(steady):
            sql(sample['sql'], (3, 6, 3))
            assert sample['sql']['operations'] == rows and sample['containers'] == d['containersAfter']
            assert sum(r[3] == 3 for r in sample['sql']['membershipGenerations']) == 2
            assert [o['gateway'] for o in sample['outcomes']] == ['primary', 'secondary']
            assert all(o['status'] == 'ACKNOWLEDGED' and o['result']['status'] == 'DUPLICATE_COMMITTED' for o in sample['outcomes'])
            if index:
                assert 0 < sample['elapsedSeconds'] - steady[index - 1]['elapsedSeconds'] <= 10
            outcomes += sample['outcomes']
        for outcome in outcomes:
            ack(outcome, rows)
    print('E2 LONG SCHEDULE AUDIT: PASS (2 assisted recoveries, sampled stability; 2 original FAILs retained; E2 partial)')


if __name__ == '__main__':
    main()
