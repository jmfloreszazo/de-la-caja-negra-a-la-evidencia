#!/usr/bin/env python3
"""Recompute all six original dispatch trials without rerunning their workload."""
import json
from audit_b05_dispatch import ROOT,audit_bytes
SOURCE='97e2efcf399c9ef75b4b093c22e36cfb5622cb17'
DIGESTS=['8af2ed76c58e728e08a47e603d8559acae67a6db9db1911e7c74dfe3aa54faea',
'75df6ce95cbbedf13944b8de9da947ec0aee2ee8d49b25eb3e922ddd36155294',
'd7158dbe740886815cab4a2b27a89da2312df598cacfe88388b08add499d837a']
folder=ROOT/'evidence/runs/b05-dispatch-41656639275'
expected=json.loads((folder/'audit.json').read_text())
results=[]
for cohort,digest in enumerate(DIGESTS):
    result=audit_bytes((folder/f'cohort-{cohort}-original.zip').read_bytes(),SOURCE)
    assert result['cohort']==cohort and result['sha256']==digest
    assert result==expected[cohort]
    results.append(result)
assert len({r['vectorSha256'] for r in results})==1
assert sum(t['missed'] for r in results for t in r['trials'])==153
assert sum(t['sqlCommitted'] for r in results for t in r['trials'])==118887
assert all(t['ambiguous']==0 for r in results for t in r['trials'])
print('PASS: three original ZIPs; six exact slot traces and SQL states; 42 invariant checks. Diagnostic only.')
