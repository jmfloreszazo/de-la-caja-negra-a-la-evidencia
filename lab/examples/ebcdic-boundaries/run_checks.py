#!/usr/bin/env python3
"""Run fixed expectations, counterexamples and rejected transformation mutants."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

from record import CODECS, read_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def run():
    fixture = json.loads((HERE / 'expected.json').read_text(encoding='utf-8'))
    observations = []

    def check(name, condition, **values):
        observations.append({'name': name, 'status': 'PASS' if condition else 'FAIL', **values})
        if not condition:
            raise AssertionError(name)

    def rejects(name, action, error):
        try:
            action()
        except error as caught:
            check(name, True, exception=type(caught).__name__, message=str(caught))
        else:
            check(name, False)

    report = {'status': 'FAIL', 'scope': 'SYNTHETIC_PYTHON_CODEC_EXERCISE',
              'sourceHeadSha': os.environ.get('SOURCE_HEAD_SHA', subprocess.check_output(
                  ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()),
              'checkoutSha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'runId': os.environ.get('GITHUB_RUN_ID', 'LOCAL'),
              'python': sys.version, 'platform': platform.platform(),
              'sourceSha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [HERE / 'record.py', HERE / 'expected.json', Path(__file__).resolve()]},
              'observations': observations, 'mutants': [],
              'limitations': ['No native IBM execution', 'No dataset or transfer-tool conversion',
                              'No DBCS, variable records or packed-decimal arithmetic',
                              'No macOS/Windows Podman reproduction or business approval']}
    try:
        for row in fixture['codePoints']:
            raw = bytes.fromhex(row['hex'])
            for ccsid, codec in CODECS.items():
                actual = raw.decode(codec, errors='strict')
                check(f"documented-{ccsid}-{row['hex']}", actual == row[str(ccsid)],
                      inputHex=row['hex'], actual=actual, expected=row[str(ccsid)])
        for row in fixture['records']:
            raw = bytes.fromhex(row['hex'])
            actual = read_record(raw, row['ccsid'])
            check(row['name'], actual == row['expected'], actual=actual, expected=row['expected'])
        row = fixture['records'][0]
        raw = bytes.fromhex(row['hex'])
        wrong = read_record(raw, 500)
        check('wrong-ccsid-is-decodable-but-wrong', wrong != row['expected'], actual=wrong)
        check('wrong-ccsid-roundtrip-still-passes', raw[:8].decode('cp500').encode('cp500') == raw[:8])
        check('accent-expands-in-utf8', len(fixture['records'][2]['expected']['label'].encode('utf-8')) == 9,
              sourceTextBytes=8, targetTextBytes=9)
        # These loops show codec self-consistency, not independent semantic correctness.
        for codec in CODECS.values():
            all_bytes = bytes(range(256))
            check('roundtrip-256-' + codec, all_bytes.decode(codec).encode(codec) == all_bytes)
        for value in [None, 1047, '37', True]:
            rejects('unsupported-ccsid-' + repr(value), lambda v=value: read_record(raw, v), ValueError)
        for data in [raw[:-1], raw + b'\x00']:
            rejects('invalid-length-' + str(len(data)), lambda b=data: read_record(b, 37), ValueError)
        rejects('control-in-text', lambda: read_record(b'\x00' + raw[1:], 37), ValueError)
        rejects('euro-not-representable-in-cp037', lambda: 'EUR €'.encode('cp037', errors='strict'), UnicodeEncodeError)
        check('replacement-is-lossy', 'EUR €'.encode('cp037', errors='replace').decode('cp037') == 'EUR ?')
        # Preserve the binary suffix; whole-record text conversion changes its bytes.
        converted = raw.decode('cp037').encode('utf-8')
        check('whole-record-conversion-changes-binary', converted[8:] != raw[8:], actualHex=converted.hex())
        mutants = {
            'wrong-ccsid': wrong,
            'strip-padding': {**row['expected'], 'label': row['expected']['label'].rstrip()},
            'text-converted-binary': {**row['expected'], 'packedHex': converted[8:11].hex()},
            'little-endian-counter': {**row['expected'], 'counter': int.from_bytes(raw[11:], 'little')},
        }
        for name, result in mutants.items():
            rejected = result != row['expected']
            report['mutants'].append({'name': name, 'actual': result, 'rejected': rejected})
            check('reject-mutant-' + name, rejected)
        report['status'] = 'PASS'
    except Exception:
        report['failure'] = traceback.format_exc()
        raise
    finally:
        destination = ROOT / 'lab/results/ebcdic-boundaries'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'observations.json').write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n')
        print(json.dumps({'status': report['status'], 'checks': len(observations), 'mutants': len(report['mutants'])}))


if __name__ == '__main__':
    run()
