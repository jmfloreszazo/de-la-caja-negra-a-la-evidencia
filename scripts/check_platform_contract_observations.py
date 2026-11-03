#!/usr/bin/env python3
"""Verify frozen catalog-check provenance without claiming native platform execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'evidence/platform-contracts'
record=json.loads((folder/'provenance.json').read_text())
assert record['source_sha']=='9f6d20267e137ff8de3c1559e8c2dbdc433215fa'
assert record['run_id']==41721242997 and record['artifact_id']==13272561653
archive=folder/'catalog-integrity-original.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==record['archive_sha256']=='a48ee9aef8d28cb0c66c170d77845d82c76ed257d4a9de59869774b26e0545ab'
with zipfile.ZipFile(archive) as original:
    assert original.read('platform-contracts-source.txt').decode().strip()==record['checkout_sha']
    result=json.loads(original.read('platform-contracts-original.json'))
assert result=={'status':'PASS','documented_capabilities':10,'sources':10,'rejected_catalog_mutants':6,
                'native_platform_execution':'NOT_EXECUTED','migration_verified':False}
assert record['checkout_sha']=='32a2956826ffb0ec1c0e4f0629af5f444722570c'
raw=(folder/'pr-test-merge-commit.txt').read_bytes()
assert hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==record['checkout_sha']
headers=raw.split(b'\n\n',1)[0].decode().splitlines()
assert 'parent '+record['source_sha'] in headers
source_tree=subprocess.check_output(['git','rev-parse',record['source_sha']+'^{tree}'],cwd=ROOT,text=True).strip()
assert 'tree '+source_tree in headers
for file,digest in record['source_hashes'].items():
    source=subprocess.check_output(['git','show',record['source_sha']+':'+file],cwd=ROOT)
    assert hashlib.sha256(source).hexdigest()==digest,file
print(json.dumps({'status':'PASS','historical_source_hashes':len(record['source_hashes']),
                  'metadata_mutants_rejected':6,'native_platform_execution':'NOT_EXECUTED','migration_verified':False}))
