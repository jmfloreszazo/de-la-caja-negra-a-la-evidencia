#!/usr/bin/env python3
"""Audit original directional faults independently from PCAP bytes and SQL."""
from pathlib import Path
import hashlib
import ipaddress
import json
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'evidence/runs'
SOURCE = '958961906de0ca5d3945d410c64d465ba7d34a3e'
DIGESTS = {
    'primary': '06d471e856c514b4007f8dc54e1c975de0801a7bc67048d97e71868534d08d6f',
    'secondary': '8c865621cae8b72c4d66bb46aabfd1e76e3cbe4ba5ad7364fda3c09148706c73',
}
CRITICAL = {
    ".github/workflows/e2-c05-c06-directional.yml": "e518bc850331605eae5a640df51d398ae831179f53533aa958819287ae83f4eb",
    "lab/e1_pg/PgBank/Program.cs": "eb61acea9673cf14e999adf2c01a03df418c385dee0e3e1f6d777bbca53f5f32",
    "lab/e2_orleans/OrleansLab/B05LoadClient.cs": "16e39e8a3e14efcac94edae03994b0e0e83a67414f8b0055ac00d33b3ffdb596",
    "lab/e2_orleans/OrleansLab/ClusterModes.cs": "f495025017de01438e5a4fe5ad4ea6d4e11845d45c17af21f17dc50ea4337ecd",
    "lab/e2_orleans/OrleansLab/Contracts.cs": "f3afb0096a594e8ec18a29f8775de21ab0df40ebc55c89ad3486ef2f4cc943e0",
    "lab/e2_orleans/OrleansLab/ControlledPlacementProbe.cs": "a4b791df825799e41d4b1f1528d40248e77aaa8d5477fb7459799c8c58d10319",
    "lab/e2_orleans/OrleansLab/PartitionProbeClient.cs": "d7f6aa4c7e9f2eb0d9837f21652daf3fb6f69ba78ea81a001f78693706659a40",
    "lab/e2_orleans/OrleansLab/PgDurableLedger.cs": "50f4a26e74ee28f754dd39854098bd4333f8cef2faf2d39d269e38a8db4581ff",
    "lab/e2_orleans/OrleansLab/Program.cs": "d78d52c3cca03f401cbe40c5b96b7707003b53d0fd4c8bef94b1e3639c228dcc",
    "lab/e2_orleans/OrleansLab/UnsafeReentrancyNegative.cs": "9f083e0977bcc9b995d0ce89e3b1bfbbdc493790c0ddba347985310abbce34e6",
    "lab/e2_orleans/test_controlled_placement.py": "379a4eb698cc2fe563b7374eb98308201b3e2433446b84e2b8abece8323f784e",
    "lab/e2_orleans/test_directional_partition.py": "995c2fee1f20a914e28b1c95479c547f44a07c8805e1f4d0e15a401014bf1ddd",
    "lab/e2_orleans/test_podman_disconnect.py": "b5798306940348721a24e6702722c04f7b31b6f4b29c4626f2130820e6b74f9d",
    "lab/e2_orleans/test_podman_network.py": "0f7bc2ff7dda678150212768c80aa5854c7aefcbac6a540b67b500f170ced2f6"
}


def original(stem, digest):
    path = RUNS / (stem + '.zip')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Original ZIP changed'
    with zipfile.ZipFile(path) as z:
        raw = z.read('directional-partition-summary.json')
        assert raw == (RUNS / (stem + '.json')).read_bytes(), 'Original extraction changed'
        return json.loads(raw), {n: z.read(n) for n in z.namelist()}


def sql(state, expected):
    assert state['effects'] == dict(zip(('committedOperations', 'postings', 'outboxEvents'), expected))
    assert len(state['oracle']) == 7 and all(v is True for v in state['oracle'].values())
    assert len(state['operations']) == expected[0]
    assert all(row[4] == 'COMMITTED' for row in state['operations'])


def packets(raw):
 endian = '<' if raw[:4] in (b'\xd4\xc3\xb2\xa1',b'\x4d\x3c\xb2\xa1') else '>'
 assert raw[:4] in (b'\xd4\xc3\xb2\xa1',b'\xa1\xb2\xc3\xd4',b'\x4d\x3c\xb2\xa1',b'\xa1\xb2\x3c\x4d')
 link=struct.unpack(endian+'IHHIIII',raw[:24])[-1];offset={276:20,113:16,1:14}[link];pos=24;out=[]
 while pos<len(raw):
  assert pos+16<=len(raw)
  _,_,caplen,wirelen=struct.unpack_from(endian+'IIII',raw,pos);pos+=16
  assert caplen<=wirelen and pos+caplen<=len(raw)
  frame=raw[pos:pos+caplen];pos+=caplen;ip=frame[offset:]
  if not ip or ip[0]>>4!=4 or ip[9]!=6:continue
  ihl=(ip[0]&15)*4; tcp=ip[ihl:];assert len(tcp)>=20
  src,dst=str(ipaddress.ip_address(ip[12:16])),str(ipaddress.ip_address(ip[16:20]))
  sport,dport,seq,ack=struct.unpack_from('!HHII',tcp)
  if 11150 not in (sport,dport) and 11151 not in (sport,dport):continue
  out.append((src,dst,sport,dport,seq,ack,tcp[13],struct.unpack('!H',ip[4:6])[0]))
 return out


def main():
    negatives = [
        ('e2-c05-first-preflight-primary', 'bba4c3af2b15b3b7d50ba88fb351c34ede8953c9d148fca406078ba48d61b13e', 'setup', "AssertionError('c05')"),
        ('e2-c05-first-preflight-secondary', '8eabe4d141b8430f5d426bfbcf53bce87886b307c6b2a393f7c299d5430d7f17', 'setup', "AssertionError('c05')"),
        ('e2-c05-second-capture-primary', 'f717bd165745bc4cd0d95485df559fc35bb15262ad6eff6562c1d63fb6fdfc41', 'contending-requests-under-directional-loss', 'Permission denied'),
        ('e2-c05-second-capture-secondary', '63e3778c681a73a08cd08330d441957e46d3e8d3d0f17fdee461e1b8b2848a55', 'contending-requests-under-directional-loss', 'Permission denied'),
    ]
    for stem, digest, stage, error in negatives:
        d, _ = original(stem, digest)
        assert d['status'] == 'FAIL' and d['lastStage'] == stage and error in d['error']
    regression = RUNS / 'e2-c05-loopback-placement-failure-original.zip'
    assert hashlib.sha256(regression.read_bytes()).hexdigest() == '55bed14ebac7f582b3d29a9dc13e97c6c75f11a48c64bfdf12a7b18db9fe5332'
    with zipfile.ZipFile(regression) as z:
        development = json.loads(z.read('e2-multiprocess.json'))
        assert development['membershipProvider'] == 'development' and development['status'] == 'PASS'
        assert 'e2-adonet-recovery.json' not in z.namelist()
    log = (RUNS / 'e2-c05-loopback-placement-failure-job.log').read_bytes()
    assert hashlib.sha256(log).hexdigest() == '677bad5736b70539523349d9da3dde0cf8fad5ee0c398d2077e337ca90b7440a'
    assert b'Cannot establish that BOTH independent silos host grains' in log
    assert b'Process completed with exit code 1' in log
    default_zip = RUNS / 'e2-c05-default-baseline-failure-original.zip'
    assert hashlib.sha256(default_zip.read_bytes()).hexdigest() == 'e9a703eaf4aec8cf1269ab953ea0ecce306fdb521be1163f3fd13c0ae3cb728a'
    with zipfile.ZipFile(default_zip) as z:
        raw = z.read('e2-f10-c01-placement-negative-original.json')
        assert raw == (RUNS / 'e2-c05-default-baseline-failure-original.json').read_bytes()
        negative = json.loads(raw)
        assert negative['status'] == 'FAIL_PRECONDITION_NOT_BUSINESS_FAILURE'
        assert negative['isSuccessfulFailoverEvidence'] is False
        assert set(negative['originalAccountHostNodes']) == {str(k) for k in range(1, 17)}
        assert set(negative['originalAccountHostNodes'].values()) == {'e2f10-primary'}
    runners, initial_ids = set(), set()
    for role, digest in DIGESTS.items():
        d, files = original('e2-c05-c06-' + role + '-original', digest)
        assert d['status'] == 'PASS' and d['sourceHeadSha'] == SOURCE and d['blockedRole'] == role
        assert d['physicalHosts'] == 1 and d['activationExclusivityEstablished'] is False
        runners.add(d['runnerName'])
        provenance = files['provenance.txt'].decode()
        assert 'source_head_sha=' + SOURCE in provenance and 'checkout_sha=' + SOURCE in provenance
        hashes = {p: h for h, p in re.findall(r'^([0-9a-f]{64})  (.+)$', provenance, re.M)}
        assert len(hashes) == 64 and all(hashes[p] == h for p, h in CRITICAL.items())
        for p, h in CRITICAL.items():
            assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, p
        assert len(set(d['namespaces'].values())) == 4
        assert len({s['pidOnHost'] for s in d['containersBefore'].values()}) == 4
        initial_ids.update(s['id'] for s in d['containersBefore'].values())
        assert d['controlledBaseline']['financialCommandsDispatched'] == 0
        assert d['controlledBaseline']['placementHintRetained'] is False
        expected = {str(k): 'e2f10-primary' if k % 2 else 'e2f10-secondary' for k in range(1, 17)}
        assert {k: v.split(':', 1)[0] for k, v in d['controlledBaseline']['accountHostNodes'].items()} == expected
        assert d['rulesBefore'] == d['rulesAfter'] and '--ports 11150,11151 -j DROP' in d['rulesDuring']
        counter = re.findall(r'\[(\d+):(\d+)\] -A OUTPUT .*--ports 11150,11151 -j DROP', d['dropCounters'])
        assert len(counter) == 1 and int(counter[0][0]) > 0
        assert d['captureAutostopSeconds'] == 45
        blocked = '10.78.30.11' if role == 'primary' else '10.78.30.12'
        peer = '10.78.30.12' if role == 'primary' else '10.78.30.11'
        decoded = {}
        for side in ('primary', 'secondary'):
            raw = files[side + '.pcap']
            assert hashlib.sha256(raw).hexdigest() == d['captures'][side]['sha256']
            assert len(raw) == d['captures'][side]['bytes']
            assert files[side + '-packets.txt'].decode().rstrip() == d['captures'][side]['decoded']
            decoded[side] = packets(raw)
        receiving = decoded['secondary' if role == 'primary' else 'primary']
        assert not any(p[:2] == (blocked, peer) for p in receiving)
        sent = {p for p in receiving if p[:2] == (peer, blocked)}
        arrived = {p for p in decoded[role] if p[:2] == (peer, blocked)}
        assert sent & arrived, 'No identical TCP packet observed at both endpoints'
        assert all(x.strip() == 'CONNECT_EXIT:1' for x in d['handshakeProbes'].values())
        for phase in ('duringNetworkChecks', 'networkAfter'):
            assert len(d[phase]) == 3
            assert all(x['databaseHealthy'] and x['primaryGatewayReachable'] and x['secondaryGatewayReachable']
                       for x in d[phase].values())
        sql(d['initialSql'], (0, 0, 0))
        sql(d['baselineSql'], (1, 2, 1))
        sql(d['duringSql'], (2, 4, 2))
        sql(d['duringSqlAfterCatalog'], (2, 4, 2))
        sql(d['finalSql'], (3, 6, 3))
        assert {r[0] for r in d['finalSql']['operations']} == {'c05-baseline', 'c05-contested-id', 'c06-recovery-new'}
        first, second = d['contendingOutcomes']
        assert first['status'] == 'DISPATCH_AMBIGUOUS' and first['financialCommandsDispatched'] == 1
        assert first['exceptionType'] == 'System.TimeoutException'
        assert second['status'] == 'ACKNOWLEDGED' and second['result']['status'] == 'COMMITTED'
        assert first['command']['amountCents'] == 31 and second['command']['amountCents'] == 37
        winner = next(r for r in d['finalSql']['operations'] if r[0] == 'c05-contested-id')
        assert winner[1:] == [2, 1, 37, 'COMMITTED']
        assert all(x['status'] == 'OBSERVATION_UNAVAILABLE' for x in d['catalogDuring'])
        assert all(x['status'] == 'OBSERVED' for x in d['catalogBefore'] + d['catalogAfter'])
        assert d['recoveryMode'] == 'NETWORK_RESTORATION_ONLY'
        assert 45 <= d['faultObservedSeconds'] < 60
        assert 0 < d['firstBothGatewayAckSecondsAfterRestore'] <= 240
        assert all(x['status'] == 'ACKNOWLEDGED' for x in d['recoveryAttempts'][-1])
        assert d['membershipRecovered'] == d['duringMembership']
        for phase in ('containersDuring', 'containersAfter'):
            for name, state in d[phase].items():
                assert state == d['containersBefore'][name] and state['status'] == 'running'
        assert d['replayAfterRestore']['result']['status'] == 'DUPLICATE_COMMITTED'
        assert d['conflictAfterRestore']['result']['status'] == 'ID_CONFLICT'
        assert d['newAfterRestore']['result']['status'] == 'COMMITTED'
    assert len(runners) == 2 and len(initial_ids) == 8
    print('C05/C06 ORIGINAL AUDIT: PASS (2 directions, original PCAP parsing, 4 preserved failures; E2 partial)')


if __name__ == '__main__':
    main()
