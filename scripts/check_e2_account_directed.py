#!/usr/bin/env python3
"""Freeze the first directed trial: one positive, one INCONCLUSIVE; stderr gap retained."""
import hashlib
import json
import zipfile
from audit_e2_account_directed import ROOT, audit

SOURCE = 'bfc7662df377632a34d1fb076cdc2de0291e4021'
DIGESTS = {
    'primary': 'd1543a98505cef134efab17dedc263678ba1fc2cb09c1343787f1f85233ea5ac',
    'secondary': 'e018ad1f5d738ba3c1f21e119dd08b63dd60dc47f5dc29c95899b9423f61e5e5',
}


def main():
    for role,digest in DIGESTS.items():
        path = ROOT/'evidence/runs'/('e2-account-directed-'+role+'-original.zip')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        with zipfile.ZipFile(path) as z:
            assert z.read('account-directed-summary.json') == path.with_suffix('.json').read_bytes()
        result = audit(path,SOURCE)
        assert result['role'] == role and result['sourceHashes'] == 84
        assert result['financialAcceptanceAudited'] is True
        assert result['fullLogStreamsRetained'] is False  # Do not retrofit missing stderr.
        assert result['status'] == ('INCONCLUSIVE_NO_LIVE_OVERLAP' if role=='primary'
                                    else 'PASS_DIRECTED_REQUEST_OVERLAP')
        assert result['incompleteCalls'] == 0
        if role == 'secondary':
            assert result['directedWitness'] == dict(overlapTicks=5059981,frequency=1000000000,
                oldResult='DUPLICATE_COMMITTED',newResult='COMMITTED')
    repeat_source = 'c1d174d263b453c9e1a55420f90ad42f091ef88a'
    repeat_digests = {
        'primary': '5a40e80ef394005b3e6dbffb9299472fd5204a64750488ed7ae79d961b28b375',
        'secondary': 'a25d19553937f309801eeb094b048c48203a6ac40a823822510a44ea9b6231f1',
    }
    for role,digest in repeat_digests.items():
        path = ROOT/'evidence/runs'/('e2-account-directed-'+role+'-stderr-original.zip')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        result = audit(path,repeat_source)
        assert result['status'] == 'INCONCLUSIVE_NO_LIVE_OVERLAP'
        assert result['fullLogStreamsRetained'] is True and result['financialAcceptanceAudited'] is True
        assert result['sourceHashes'] == 84 and result['completeCalls'] == 37
        assert result['incompleteCalls'] == result['overlappingEnvelopes'] == 0
        with zipfile.ZipFile(path) as z:
            raw = z.read('account-directed-summary.json')
            assert raw == path.with_suffix('.json').read_bytes()
            d = json.loads(raw)
            old_id = d['originalProcesses']['primary']['id']
            records = [item for item in d['logs'] if item['containerId'] == old_id]
            assert len(records) == 1
            stderr = z.read(records[0]['stderrFile']).decode()
            assert 'FATAL EXCEPTION from Orleans.Runtime.MembershipService.MembershipTableManager' in stderr
            assert 'I should be Dead according to the membership table' in stderr
            assert 'MembershipTableManager.KillMyselfLocally' in stderr
            parent = json.loads(z.read('long-partition-summary.json'))
            exits = [x for x in parent['samples'] if x['processes']['primary']['status'] == 'exited']
            assert exits and exits[0]['processes']['primary']['exitCode'] == 139
            assert any(r[0] == '10.78.30.11' and r[1] == 11150 and r[3] == 6
                       for r in exits[0]['sql']['membershipGenerations'])
    print('DIRECTED ARCHIVE AUDIT: PASS (1 directed positive / 3 INCONCLUSIVE; stderr repeat identifies membership fatal path; E2 partial)')


if __name__=='__main__':main()
