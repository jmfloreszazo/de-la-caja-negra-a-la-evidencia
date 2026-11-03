#!/usr/bin/env python3
"""Audit a downloaded original observer ZIP against its exact Git source.

No network calls, extraction, acceptance promotion or rewriting of artifacts.
Usage: python3 scripts/audit_e2_activation_artifact.py original.zip --source SHA
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from check_e2_directional_partition_observations import packets, sql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/e2_activation_observer'))
from observation import analyze, reconcile, validate_generation


def audit(path, source):
    assert re.fullmatch('[0-9a-f]{40}', source)
    raw_zip = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP entries'
        files = {name: archive.read(name) for name in names}
    result = json.loads(files['activation-observation-summary.json'])
    schedule = json.loads(files['long-partition-summary.json'])
    assert result['status'] == 'PASS_OBSERVATION_ONLY' and schedule['status'] == 'PASS'
    assert result['sourceHeadSha'] == schedule['sourceHeadSha'] == source
    assert result['activationExclusivityEstablished'] is False
    assert schedule['activationExclusivityEstablished'] is False and schedule['physicalHosts'] == 1
    assert result['blockedRole'] == schedule['blockedRole'] in ('primary', 'secondary')
    provenance = files['long-partition-provenance.txt'].decode()
    assert 'source_head_sha=' + source in provenance and 'checkout_sha=' + source in provenance
    entries = re.findall(r'^([0-9a-f]{64})  (.+)$', provenance, re.M)
    hashes = {name: digest for digest, name in entries}
    assert len(entries) == len(hashes)
    expected = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', source, '--',
        'lab/e2_orleans', 'lab/e1_pg', 'lab/e2_activation_observer',
        '.github/workflows/e2-activation-observation.yml'], cwd=ROOT, text=True).splitlines()
    assert set(hashes) == set(expected), 'Missing/unexpected source hash'
    for name, digest in hashes.items():
        raw = subprocess.check_output(['git', 'show', source + ':' + name], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == digest, name
    logs = []
    generations = []
    assert {x['node'] for x in result['logs']} == {'e2f10-primary', 'e2f10-secondary'}
    assert len({x['containerId'] for x in result['logs']}) == len(result['logs'])
    for item in result['logs']:
        raw = files[item['file']]
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
        text = raw.decode()
        logs.append(text)
        generations.append(validate_generation(text, item['node']))
    assert generations == result['generations']
    assert len({g['session'] for g in generations}) == len(generations)
    observed = analyze(logs)
    assert observed == result['observation']
    acks = [schedule['baselineAck']] + schedule['firstContendingOutcomes'] + schedule['lateContendingOutcomes']
    acks += [o for a in schedule['unassistedAttempts'] for o in a['outcomes']]
    acks += schedule.get('assistedOutcomes', []) + schedule['replayConflictNew']
    acks += [o for s in schedule['stableSamples'] for o in s['outcomes']]
    reconcile(observed, schedule['finalSql'], acks)
    assert result['sqlAndAcknowledgementsReconciled'] is True
    assert 120 <= schedule['faultScheduleElapsedSeconds'] <= 180
    assert 0 < schedule['firstBothAckSecondsAfterRestore'] <= schedule['recoveryCriteriaSatisfiedSecondsAfterRestore'] <= 300
    sql(schedule['initialSql'], (0, 0, 0))
    sql(schedule['baselineSql'], (1, 2, 1))
    sql(schedule['finalSql'], (3, 6, 3))
    stable = schedule['stableSamples']
    assert [s['index'] for s in stable] == list(range(14))
    span = stable[-1]['elapsedSeconds'] - stable[0]['elapsedSeconds']
    assert span == schedule['stableObservationSpanSeconds'] and 60 <= span <= 150
    for i, sample in enumerate(stable):
        sql(sample['sql'], (3, 6, 3))
        assert sample['sql']['operations'] == schedule['finalSql']['operations']
        assert sample['containers'] == schedule['containersAfter']
        assert sum(r[3] == 3 for r in sample['sql']['membershipGenerations']) == 2
        assert [o['gateway'] for o in sample['outcomes']] == ['primary', 'secondary']
        assert all(o['status'] == 'ACKNOWLEDGED' and o['result']['status'] == 'DUPLICATE_COMMITTED'
                   for o in sample['outcomes'])
        if i:
            assert 0 < sample['elapsedSeconds'] - stable[i - 1]['elapsedSeconds'] <= 10
    decoded = {}
    for side in ('primary', 'secondary'):
        raw = files[side + '.pcap']
        info = schedule['initialCaptures'][side]
        assert hashlib.sha256(raw).hexdigest() == info['sha256'] and len(raw) == info['bytes']
        decoded[side] = packets(raw)
    role = schedule['blockedRole']
    other = 'secondary' if role == 'primary' else 'primary'
    blocked, peer = ('10.78.30.11', '10.78.30.12') if role == 'primary' else ('10.78.30.12', '10.78.30.11')
    assert not any(p[:2] == (blocked, peer) for p in decoded[other])
    assert {p for p in decoded[other] if p[:2] == (peer, blocked)} & {
        p for p in decoded[role] if p[:2] == (peer, blocked)}
    return dict(status='AUDITED_OBSERVATION_ONLY', source=source, role=role,
        bytes=len(raw_zip), sha256=hashlib.sha256(raw_zip).hexdigest(),
        sourceHashes=len(hashes), generations=len(generations),
        completeCalls=len(observed['completeCalls']), incompleteCalls=len(observed['incompleteCalls']),
        overlappingEnvelopes=len(observed['overlappingRequestEnvelopes']),
        incomparablePairs=observed['incomparablePairs'], coverage=observed['coverage'],
        activationExclusivityEstablished=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip', type=Path)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.zip, args.source), indent=2))
