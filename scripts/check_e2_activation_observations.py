#!/usr/bin/env python3
"""Pin and audit the two original incoming Transfer observation artifacts."""
import hashlib
import zipfile
from audit_e2_activation_artifact import ROOT, audit

SOURCE = '362ee5a7537e1523caad2bd7033ec7a99977ac2d'
DIGESTS = {
    'primary': '9ffb4ef62e7ee040a139490b3dc3dc6df46fdeff6fedbfd9a07a5b92b1213e62',
    'secondary': '84ee1d79ed0021dc7fb9c3e7a81f270c78076bee7ccaddd3631f5c80d5470368',
}


def main():
    for role, digest in DIGESTS.items():
        path = ROOT / 'evidence/runs' / ('e2-activation-' + role + '-original.zip')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        with zipfile.ZipFile(path) as archive:
            assert archive.read('activation-observation-summary.json') == path.with_suffix('.json').read_bytes()
        result = audit(path, SOURCE)
        assert result['role'] == role and result['sourceHashes'] == 77
        assert result['completeCalls'] == (38 if role == 'primary' else 39)
        assert result['incompleteCalls'] == result['incomparablePairs'] == result['overlappingEnvelopes'] == 0
        assert result['generations'] == 4 and result['activationExclusivityEstablished'] is False
    print('E2 ACTIVATION OBSERVATION AUDIT: PASS (38/39 calls; no observed overlap; exclusivity unproven; E2 partial)')


if __name__ == '__main__':
    main()
