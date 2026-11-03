#!/usr/bin/env python3
"""Audit an original directed-probe archive without relabeling FAIL/INCONCLUSIVE.

Usage: python3 scripts/audit_e2_account_directed.py original.zip --source SHA
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
sys.path[:0] = [str(ROOT/'lab/e2_activation_observer'), str(ROOT/'lab/e2_account_directed')]
from observation import analyze, reconcile, validate_generation
from probe_contract import events, verify_complete_overlap


def audit(path, source):
    assert re.fullmatch('[0-9a-f]{40}', source)
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        files = {name: archive.read(name) for name in names}
    d = json.loads(files['account-directed-summary.json'])
    parent = json.loads(files['long-partition-summary.json'])
    assert parent['sourceHeadSha'] == source
    assert d['protocol'] == 'E2_ACCOUNT_DIRECTED_PRE_INVOKE_GATE_V1'
    assert d['preInvokeDelayInjected'] is True and d['physicalHosts'] == 1
    assert d['siloHost'] == 'DirectedSilo' and d['activationExclusivityEstablished'] is False
    provenance = files['long-partition-provenance.txt'].decode()
    assert 'source_head_sha='+source in provenance and 'checkout_sha='+source in provenance
    pairs = re.findall(r'^([0-9a-f]{64})  (.+)$', provenance, re.M)
    hashes = {p:h for h,p in pairs}
    expected = subprocess.check_output(['git','ls-tree','-r','--name-only',source,'--',
        'lab/e2_orleans','lab/e1_pg','lab/e2_activation_observer','lab/e2_account_directed',
        '.github/workflows/e2-account-directed.yml'],cwd=ROOT,text=True).splitlines()
    assert len(hashes) == len(pairs) and set(hashes) == set(expected)
    for p,h in hashes.items():
        data = subprocess.check_output(['git','show',source+':'+p],cwd=ROOT)
        assert hashlib.sha256(data).hexdigest() == h,p
    result = dict(status=d['status'],source=source,role=parent['blockedRole'],
                  bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),sourceHashes=len(hashes),
                  financialAcceptanceAudited=False,activationExclusivityEstablished=False)
    logs = []
    complete_streams = []
    for item in d['logs']:
        data = files[item['file']]
        assert hashlib.sha256(data).hexdigest() == item['sha256']
        logs.append(data.decode())
        complete_streams.append('stderrFile' in item)
        if 'stderrFile' in item:
            assert hashlib.sha256(files[item['stderrFile']]).hexdigest() == item['stderrSha256']
    result['fullLogStreamsRetained'] = bool(complete_streams) and all(complete_streams)
    if d.get('logStreamsCaptured') == 'stdout_and_stderr':
        assert result['fullLogStreamsRetained'] is True
    if d['status'] == 'FAIL':
        assert d.get('error') or parent.get('error')
        result['error'] = d.get('error') or parent.get('error')
        result['parentPhase'] = parent['lastPhase']
        return result  # Original engineering FAIL is preserved, not SQL acceptance.
    assert d['status'] in ('PASS_DIRECTED_REQUEST_OVERLAP','INCONCLUSIVE_NO_LIVE_OVERLAP')
    assert parent['status'] == 'PASS' and d['sourceHeadSha'] == source
    assert d['monitorErrors'] == [] and d['sqlAndAcknowledgementsReconciled'] is True
    generations = [validate_generation(raw,item['node']) for raw,item in zip(logs,d['logs'])]
    assert generations == d['generations']
    assert len({g['session'] for g in generations}) == len(generations)
    observation = analyze(logs)
    assert observation == d['observation']
    markers = [m for raw in logs for m in events(raw,'E2_ACCOUNT_GATE_WAIT:')]
    assert markers == [d['oldGate']]
    acks = [parent['baselineAck']] + parent['firstContendingOutcomes'] + parent['lateContendingOutcomes']
    acks += [o for a in parent['unassistedAttempts'] for o in a['outcomes']]
    acks += parent.get('assistedOutcomes',[]) + parent['replayConflictNew']
    acks += [o for s in parent['stableSamples'] for o in s['outcomes']]
    for extra in d['extraOutcomes']:
        assert extra['returncode'] == 0 and json.loads(extra['stdout']) == extra['outcome']
        assert extra['outcome']['placementHintsUsed'] is False
        acks.append(extra['outcome'])
    reconcile(observation,parent['finalSql'],acks)
    sql(parent['initialSql'],(0,0,0))
    sql(parent['baselineSql'],(1,2,1))
    sql(parent['finalSql'],(3,6,3))
    assert 120 <= parent['faultScheduleElapsedSeconds'] <= 180
    assert 0 < parent['firstBothAckSecondsAfterRestore'] <= parent['recoveryCriteriaSatisfiedSecondsAfterRestore'] <= 300
    stable = parent['stableSamples']
    assert [s['index'] for s in stable] == list(range(14))
    span = stable[-1]['elapsedSeconds'] - stable[0]['elapsedSeconds']
    assert span == parent['stableObservationSpanSeconds'] and 60 <= span <= 150
    for i,sample in enumerate(stable):
        sql(sample['sql'],(3,6,3))
        assert sample['sql']['operations'] == parent['finalSql']['operations']
        assert sample['containers'] == parent['containersAfter']
        assert sum(r[3]==3 for r in sample['sql']['membershipGenerations']) == 2
        assert all(o['status']=='ACKNOWLEDGED' and o['result']['status']=='DUPLICATE_COMMITTED'
                   for o in sample['outcomes'])
        if i:
            assert 0 < sample['elapsedSeconds']-stable[i-1]['elapsedSeconds'] <= 10
    decoded = {}
    for role in ('primary','secondary'):
        raw_packets = files[role+'.pcap']
        info = parent['initialCaptures'][role]
        assert hashlib.sha256(raw_packets).hexdigest() == info['sha256']
        assert len(raw_packets) == info['bytes']
        decoded[role] = packets(raw_packets)
    role = parent['blockedRole']
    other = 'secondary' if role=='primary' else 'primary'
    blocked,peer = ('10.78.30.11','10.78.30.12') if role=='primary' else ('10.78.30.12','10.78.30.11')
    assert not any(p[:2] == (blocked,peer) for p in decoded[other])
    assert {p for p in decoded[role] if p[:2] == (peer,blocked)} & {
        p for p in decoded[other] if p[:2] == (peer,blocked)}
    if d['status'] == 'PASS_DIRECTED_REQUEST_OVERLAP':
        witness = d['liveWitness']
        assert witness['oldGate'] == d['oldGate']
        for role in ('primary','secondary'):
            assert witness['processes'][role]['status'] == 'running'
            assert witness['processes'][role]['id'] == d['originalProcesses'][role]['id']
        assert verify_complete_overlap(observation,witness) == d['completeWitness']
        result['directedWitness'] = d['completeWitness']
    else:
        assert 'liveWitness' not in d and 'completeWitness' not in d
    result.update(financialAcceptanceAudited=True,
                  completeCalls=len(observation['completeCalls']),
                  incompleteCalls=len(observation['incompleteCalls']),
                  overlappingEnvelopes=len(observation['overlappingRequestEnvelopes']),
                  extraClientOutcomes=len(d['extraOutcomes']))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip',type=Path)
    parser.add_argument('--source',required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.zip,args.source),indent=2))
