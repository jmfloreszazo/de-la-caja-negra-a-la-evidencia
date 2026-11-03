#!/usr/bin/env python3
"""Audit frozen original native campaigns; never turn synthetic evidence into approval."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/channels'))
from oracle import audit

ATTEMPTS = [
    ('attempt-1-original.zip', '85eb1340a2fa70479b50b2734159e0485614bf63ab4fc126ba86fefac3da4114',
     'b057a875fc1485ae804222d7035e4d602271bbaf', '41710509139', 'FAIL'),
    ('attempt-3-original.zip', 'e0ca91ca2f1ec1b4fe818d6cea02fac51ff5ddca3fa696979b6a28aec83dc53c',
     '1b206b137074c3ab175c4234d8f69780217fbb97', '41711512319', 'FAIL'),
    ('attempt-4-original.zip', '0f9b9862c0be03e159d6916545eaaf95537ffdd6c3e0ae921cd71fe9be7277da',
     '065b82b3b1b6ac2f8b7a1dab0622afbf08719732', '41711792802', 'FAIL'),
    ('attempt-2-original.zip', 'edbf39f2052739510fdfc36ec30b0e0a9eaed93a5e1fafff60716880b3a0165f',
     'dd6cbb5c455907d6555fd1196f504be73eadc7eb', '41711114693', 'PASS'),
]
EXPECTED = ['full', 'partial', 'zero', 'device-response-lost', 'settlement-response-lost',
            'core-crash-before-commit', 'digital-response-lost', 'atm-mobile-race',
            'expiry-before-dispatch', 'pending-expiry-missing-journal']


def need(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    count = 0
    for filename, digest, source, run_id, status in ATTEMPTS:
        path = ROOT / 'evidence/channels' / filename
        need(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Original archive digest changed')
        with zipfile.ZipFile(path) as archive:
            report = json.loads(archive.read('original.json'))
            need(report['source_sha'] == report['checkout_sha'] == source and report['run_id'] == run_id,
                 'Source/run identity changed')
            need(report['status'] == status, 'Original status changed')
            need(report['scope'] == {'synthetic': True, 'physical_cash': False, 'bank_policy_approved': False,
                                    'protocol_certified': False, 'capacity_claim': False, 'physical_ha': False}, 'Scope inflation')
            for file, expected in report['sources'].items():
                original = subprocess.check_output(['git', 'show', source + ':' + file], cwd=ROOT)
                need(hashlib.sha256(original).hexdigest() == expected, 'Source digest mismatch: ' + file)
                count += 1
            if filename != 'attempt-3-original.zip':
                need(any(c['returncode'] == 0 and 'ChannelsLab.dll' in c['stdout'] for c in report['commands']), 'Missing native compiler observation')
            if status == 'FAIL':
                expected_error = {'attempt-1-original.zip': 'AttributeError', 'attempt-3-original.zip': 'OperationalError', 'attempt-4-original.zip': 'TimeoutError'}[filename]
                if filename == 'attempt-4-original.zip':
                    need('address already in use' in archive.read('core-1.log').decode(), 'Original HTTP port conflict hidden')
                need(not report['cases'] and expected_error in report['error'], 'Original startup failure hidden')
                continue
            need([c['name'] for c in report['cases']] == EXPECTED, 'Changed native case inventory')
            for case in report['cases']:
                need(case['status'] == 'PASS', 'Failed case relabelled')
                verdict = audit(case['snapshot'], case['offered'])
                need(verdict == case['oracle'] and verdict['status'] == 'PASS', 'Independent SQL audit failed')
            cases = {c['name']: c for c in report['cases']}
            for name, amount, state in [('full', 6000, 'POSTED'), ('partial', 4000, 'POSTED'), ('zero', 0, 'CANCELLED')]:
                op = cases[name]['snapshot']['core']['operations'][0]
                need(op['requested'] == 6000 and op['posted'] == amount and op['state'] == state, 'Wrong actual cash decision')
            lost = cases['device-response-lost']
            need(lost['device_process_exit'] == -9 and lost['device_commit_marker']['dispensed'] == 6000, 'Missing external device kill proof')
            crash = cases['core-crash-before-commit']
            before = crash['after_kill']
            need(crash['before_commit_marker']['stage'] == 'BEFORE_COMMIT' and before['core']['postings'] == []
                 and before['core']['operations'][0]['state'] == 'DISPENSE_PENDING'
                 and before['core']['holds'][0]['active'] and len(before['device']['device_commands']) == 1, 'Core rollback/device survival not observed')
            for name in ['settlement-response-lost', 'digital-response-lost', 'core-crash-before-commit']:
                need(any(h.get('client_status') == 'UNKNOWN' and h['code'] is None for h in cases[name]['http']), 'Missing actual HTTP loss')
            race = cases['atm-mobile-race']['snapshot']['core']['operations']
            need(sum(o['state'] == 'DECLINED' for o in race) == 1 and sum(o['state'] in ('POSTED', 'COMMITTED') for o in race) == 1, 'Race did not select one financial winner')
            pending = cases['pending-expiry-missing-journal']['snapshot']
            need(pending['core']['operations'][0]['state'] == 'DISPENSE_PENDING' and pending['core']['holds'][0]['active']
                 and pending['device']['device_commands'] == [], 'Missing evidence was treated as zero')
            need(len(report['negative_controls']) == 2, 'Missing mutation controls')
            for mutant in report['negative_controls']:
                original_case = cases['partial'] if mutant['name'] == 'conserved-extra-cash-posting' else cases['pending-expiry-missing-journal']
                verdict = audit(mutant['snapshot'], original_case['offered'])
                need(verdict == mutant['oracle'] and verdict['status'] == 'FAIL', 'Mutation escaped independent oracle')
            need(not report['negative_controls'][0]['oracle']['checks']['projection'] and not report['negative_controls'][0]['oracle']['checks']['conservation'], 'Mutation no longer isolates conserved excess posting')
    print(json.dumps({'status': 'PASS', 'source_hashes': count, 'native_cases': 10, 'rejected_mutants': 2,
                      'original_startup_failure_retained': True, 'production_authorized': False}))

if __name__ == '__main__':
    main()
