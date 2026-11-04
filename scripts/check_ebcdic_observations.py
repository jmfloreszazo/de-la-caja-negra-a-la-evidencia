#!/usr/bin/env python3
"""Audit untouched hosted-OS codec observations against frozen inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'evidence/editorial'


def main():
    manifest = json.loads((DIRECTORY / 'ebcdic-original-manifest.json').read_text())
    source = manifest['sourceHeadSha']

    def original(path):
        return subprocess.check_output(['git', 'show', source + ':' + path], cwd=ROOT)

    fixture = json.loads(original('lab/examples/ebcdic-boundaries/expected.json'))
    expected_paths = {'lab/examples/ebcdic-boundaries/' + name
                      for name in ['record.py', 'expected.json', 'run_checks.py']}
    assert {a['os'] for a in manifest['artifacts']} == {'ubuntu-24.04', 'macos-14', 'windows-2022'}
    expected_names = {f"documented-{ccsid}-{row['hex']}" for row in fixture['codePoints'] for ccsid in [37, 500]}
    expected_names.update(row['name'] for row in fixture['records'])
    expected_names.update(['wrong-ccsid-is-decodable-but-wrong', 'wrong-ccsid-roundtrip-still-passes',
                          'accent-expands-in-utf8', 'roundtrip-256-cp037', 'roundtrip-256-cp500',
                          'unsupported-ccsid-None', 'unsupported-ccsid-1047', "unsupported-ccsid-'37'",
                          'unsupported-ccsid-True', 'invalid-length-12', 'invalid-length-14',
                          'control-in-text', 'euro-not-representable-in-cp037', 'replacement-is-lossy',
                          'whole-record-conversion-changes-binary'])
    mutant_names = {'wrong-ccsid', 'strip-padding', 'text-converted-binary', 'little-endian-counter'}
    expected_names.update('reject-mutant-' + name for name in mutant_names)
    for artifact in manifest['artifacts']:
        raw = (DIRECTORY / artifact['file']).read_bytes()
        assert len(raw) == artifact['bytes'] and hashlib.sha256(raw).hexdigest() == artifact['sha256']
        with zipfile.ZipFile(DIRECTORY / artifact['file']) as archive:
            report = json.loads(archive.read('observations.json'))
        assert report['status'] == 'PASS' and report['scope'] == 'SYNTHETIC_PYTHON_CODEC_EXERCISE'
        assert report['sourceHeadSha'] == report['checkoutSha'] == source
        assert report['runId'] == manifest['runId'] and report['platform'] == artifact['platform']
        hashes = {p.replace('\\', '/'): h for p, h in report['sourceSha256'].items()}
        assert set(hashes) == expected_paths
        for path, digest in hashes.items():
            data = original(path)
            # Preserve the observed Windows checkout bytes; never rewrite its report.
            if artifact['checkoutLineEndings'] == 'CRLF':
                assert artifact['os'] == 'windows-2022' and b'\r' not in data
                data = data.replace(b'\n', b'\r\n')
            else:
                assert artifact['checkoutLineEndings'] == 'LF'
            assert hashlib.sha256(data).hexdigest() == digest, path
        observations = report['observations']
        assert len(observations) == 36 and all(x['status'] == 'PASS' for x in observations)
        by_name = {x['name']: x for x in observations}
        assert set(by_name) == expected_names
        for row in fixture['codePoints']:
            for ccsid in [37, 500]:
                value = by_name[f"documented-{ccsid}-{row['hex']}"]
                assert value['actual'] == value['expected'] == row[str(ccsid)]
        for row in fixture['records']:
            assert by_name[row['name']]['actual'] == by_name[row['name']]['expected'] == row['expected']
        assert len(report['mutants']) == 4 and {m['name'] for m in report['mutants']} == mutant_names
        assert all(m['rejected'] and m['actual'] != fixture['records'][0]['expected'] for m in report['mutants'])
    print(json.dumps({'status': 'PASS', 'originalJobs': 3, 'checksPerJob': 36,
                      'rejectedMutantsPerJob': 4, 'historicalFileHashesPerJob': 3,
                      'windowsCheckoutTransformation': 'LF_TO_CRLF', 'nativeHostClaim': False}))


if __name__ == '__main__':
    main()
