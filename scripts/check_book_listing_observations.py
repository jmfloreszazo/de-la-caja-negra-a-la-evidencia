#!/usr/bin/env python3
"""Audit the exact original bounded listing run without calling it full acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE='e8785e0a5c565e3b006c3d23feebc888130dce3b'
ZIP_SHA='9bff18d5ae6f44bcef890277d3afaa04bf98356f1eec04cb79b2e55b669f8cfa'


def main():
    folder=ROOT/'evidence/editorial'
    path=folder/'book-listing-native-original.zip'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==ZIP_SHA
    with zipfile.ZipFile(path) as z:
        assert len(z.namelist())==len(set(z.namelist()))==127
        raw=z.read('listing-checks.json')
        assert raw==(folder/'book-listing-native-original.json').read_bytes()
        d=json.loads(raw)
        assert d['status']=='PASS_BOUNDED_LISTING_CHECKS'
        assert d['sourceHeadSha']==SOURCE and d['runId']=='41680741456'
        assert d['pairedFences']==32 and d['canonicalExecutableFences']==27
        assert d['completeBookCompilationEstablished'] is d['crossPlatformEstablished'] is d['listingLabelsPromoted'] is False
        assert len(d['sourceHashes'])==43
        for path,digest in d['sourceHashes'].items():
            original=subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
            assert hashlib.sha256(original).hexdigest()==digest,path
        expected=json.loads(subprocess.check_output(['git','show',SOURCE+':lab/contracts/cases.json'],cwd=ROOT))
        assert d['cobol']['listing']=='26.1' and d['cobol']['passed']==58
        assert len(d['cobol']['cases'])==len(expected)==58
        for observed,case in zip(d['cobol']['cases'],expected):
            assert {k:observed[k] for k in ('id','input','expected')}==case
            assert observed['actual']==case['expected']
            assert z.read('cobol-'+case['id']+'.stdout.txt').decode().strip()==case['expected']
            assert z.read('cobol-'+case['id']+'.stderr.txt')==b''
        assert z.read('csharp.stdout.txt').decode().strip()=='PASS: 4 rounding expressions; 9 packed-decimal values; 6 negative controls'
        assert z.read('csharp.stderr.txt')==b''
        assert d['csharp']['roundExpressions']==4 and d['csharp']['packedValues']==9 and d['csharp']['packedNegativeControls']==6
        assert d['sqlite']['displayedPredicates']==4 and all(d['sqlite']['positive'].values())
        assert d['sqlite']['corruptedBalanceRejected'] is d['sqlite']['corruptedPostingsRejected'] is True
        assert d['sqlite']['fullSevenOracleAcceptance'] is False
    print('BOOK LISTING ORIGINAL AUDIT: PASS (43 source hashes; 58 COBOL cases; 4 rounding expressions; 9 packed values/6 negatives; bounded scope)')


if __name__=='__main__':
    main()
