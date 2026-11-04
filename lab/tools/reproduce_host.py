#!/usr/bin/env python3
"""Collect one isolated Podman reproduction; unavailable engines never become PASS."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import traceback
import uuid

from audit_host_results import audit

LAB = Path(__file__).resolve().parents[1]
REPO = LAB.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Build and run the full synthetic lab')
    parser.add_argument('--output', type=Path, help='New output directory; an existing path is refused')
    args = parser.parse_args()
    token = uuid.uuid4().hex
    destination = (args.output or LAB / 'results/host-reproduction' / token).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    report = {'status': 'INCONCLUSIVE', 'sourceHeadSha': os.environ.get('SOURCE_HEAD_SHA', source),
              'checkoutSha': source, 'runId': os.environ.get('GITHUB_RUN_ID', 'LOCAL'),
              'host': {'system': platform.system(), 'release': platform.release(),
                       'machine': platform.machine(), 'python': sys.version,
                       'isWsl': 'microsoft' in platform.release().lower()},
              'mode': 'EXECUTE' if args.execute else 'PREFLIGHT', 'commands': [],
              'startedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'limits': 'Synthetic Linux-container lab; not native host DB/HA/capacity or bank acceptance.'}
    podman = shutil.which('podman')
    container = 'lab-reproduction-' + token
    created_container = False

    def command(stage, argv, timeout=60):
        stdout = destination / (stage + '.stdout.txt')
        stderr = destination / (stage + '.stderr.txt')
        observation = {'stage': stage, 'argv': argv, 'exitCode': None, 'timedOut': False,
                       'stdout': stdout.name, 'stderr': stderr.name}
        report['commands'].append(observation)
        with stdout.open('wb') as out, stderr.open('wb') as err:
            try:
                execution = subprocess.run(argv, cwd=LAB, stdout=out, stderr=err, timeout=timeout)
                observation['exitCode'] = execution.returncode
            except subprocess.TimeoutExpired:
                observation['timedOut'] = True
        return observation['exitCode'] == 0

    try:
        report['worktreeDirty'] = bool(subprocess.check_output(
            ['git', 'status', '--porcelain'], cwd=REPO, text=True).strip())
        paths = subprocess.check_output(['git', 'ls-files', '-z', 'lab'], cwd=REPO).decode().split('\0')
        report['sourceSha256'] = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
                                 for p in paths if p and (REPO / p).is_file()}
        if podman is None:
            report['reason'] = 'PODMAN_NOT_INSTALLED'
            return 2
        if not command('podman-version', [podman, 'version', '--format', 'json']):
            report['reason'] = 'PODMAN_VERSION_UNAVAILABLE'
            return 2
        if not command('engine-host', [podman, 'info', '--format', '{{json .Host}}']):
            report['reason'] = 'PODMAN_ENGINE_UNAVAILABLE'
            return 2
        if not args.execute:
            report['status'] = 'READY'
            report['reason'] = 'ENGINE_REACHABLE_LAB_NOT_EXECUTED'
            return 0
        report['status'] = 'FAIL'
        if report['worktreeDirty'] or source != report['sourceHeadSha']:
            raise ValueError('Execution requires a clean checkout at the declared source SHA')
        image = 'localhost/lab-reproduction:' + token
        if not command('build', [podman, 'build', '--iidfile', str(destination / 'image-id.txt'),
                                 '-t', image, '-f', 'Containerfile', '.'], timeout=1200):
            report['reason'] = 'BUILD_FAILED_OR_TIMED_OUT'
            return 1
        image_id = (destination / 'image-id.txt').read_text().strip()
        report['imageId'] = image_id
        if not image_id.startswith('sha256:'):
            raise ValueError('Build did not record a content-addressed image ID')
        if not command('image-identity', [podman, 'image', 'inspect', '--format',
                                        '{{.Id}} {{.Digest}} {{.Architecture}} {{.Os}}', image_id]):
            raise ValueError('Cannot inspect the built image')
        data = destination / 'outputs'
        data.mkdir()
        mount = str(data) + ':/work/results' + (':Z' if platform.system() == 'Linux' else '')
        created_container = True
        if not command('walkthrough', [podman, 'run', '--name', container, '--rm', '--network=none',
                                       '-v', mount, image_id, 'python3', 'walkthrough.py', '--auto', '--bank'], 900):
            report['reason'] = 'LAB_FAILED_OR_TIMED_OUT'
            return 1
        report['independentAudit'] = audit(data)
        report['status'] = 'PASS'
        report['reason'] = 'FULL_SYNTHETIC_LAB_AND_HOST_SIDE_ACCOUNTING_AUDIT_PASSED'
        return 0
    except Exception:
        report['status'] = 'FAIL'
        report['failure'] = traceback.format_exc()
        return 1
    finally:
        if created_container:
            # Limit cleanup to this invocation's unique container; keep its image for review.
            command('cleanup-own-container', [podman, 'rm', '--force', container])
        report['endedUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['artifactSha256'] = {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in destination.rglob('*') if p.is_file() and p.name != 'report.json'}
        (destination / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n')
        print(json.dumps({'status': report['status'], 'reason': report.get('reason'), 'report': str(destination / 'report.json')}))


if __name__ == '__main__':
    sys.exit(main())
