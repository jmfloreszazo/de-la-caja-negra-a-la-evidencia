#!/usr/bin/env python3
"""Own two disposable containers and retain every original observation, including failures."""
import concurrent.futures
import copy
import hashlib
import http.client
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import uuid
from fixture import connect, snapshot
from oracle import audit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'lab/results/channels'
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(ROOT)
os.environ['CHANNELS_DISPOSABLE'] = 'YES'
report = {'status': 'FAIL', 'cases': [], 'negative_controls': [], 'source_sha': os.environ.get('SOURCE_HEAD_SHA'),
          'run_id': os.environ.get('GITHUB_RUN_ID'), 'scope': {'synthetic': True, 'physical_cash': False,
          'bank_policy_approved': False, 'protocol_certified': False, 'capacity_claim': False, 'physical_ha': False}}
containers = []
server = None
logs = []
boot = 0
offered = {}
current = None


def command(args):
    result = subprocess.run(args, text=True, capture_output=True)
    report.setdefault('commands', []).append({'args': args, 'returncode': result.returncode,
                                             'stdout': result.stdout, 'stderr': result.stderr})
    result.check_returncode()
    return result.stdout.strip()


def wait_until(predicate, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if predicate():
                return
        except (OSError, http.client.HTTPException):
            pass
        time.sleep(.05)
    raise TimeoutError('Expected observation did not arrive')


def http(route, payload=None, expect_loss=False):
    request = urllib.request.Request('http://127.0.0.1:55444/' + route,
                                    data=json.dumps(payload).encode() if payload else None,
                                    headers={'Content-Type': 'application/json'})
    observation = {'route': route, 'request': payload}
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            observation.update(code=response.status, response=json.load(response))
    except urllib.error.HTTPError as error:
        observation.update(code=error.code, response=json.load(error))
    except (OSError, http.client.HTTPException) as error:
        observation.update(code=None, error=repr(error), client_status='UNKNOWN')
        if not expect_loss:
            raise
    finally:
        if current is not None:
            current['http'].append(observation)
    if expect_loss:
        assert observation['code'] is None, observation
        return observation
    assert observation['code'] in (200, 409), observation
    return observation['response']


def start():
    global server, boot
    boot += 1
    log = (OUT / f'core-{boot}.log').open('w')
    logs.append(log)
    server = subprocess.Popen(['dotnet', 'lab/results/channels/publish/ChannelsLab.dll'], stdout=log, stderr=subprocess.STDOUT)
    wait_until(lambda: server.poll() is None and http('health')['status'] == 'READY')


def stop(kill=False):
    if server and server.poll() is None:
        server.send_signal(signal.SIGKILL if kill else signal.SIGTERM)
        server.wait(timeout=10)
        return server.returncode


def reset(name):
    global current, offered
    offered = {}
    for marker in ['before-commit.json', 'release-commit', 'device-committed.json']:
        (OUT / marker).unlink(missing_ok=True)
    with connect('core') as db:
        db.execute('TRUNCATE outbox,postings,holds,operations,accounts CASCADE')
        db.execute('INSERT INTO accounts VALUES (1,10000),(2,10000),(3,0)')
    with connect('device') as db:
        db.execute('TRUNCATE device_commands,inventory CASCADE')
        db.execute("INSERT INTO inventory VALUES ('ATM-001',100000)")
    current = {'name': name, 'status': 'FAIL', 'http': []}
    report['cases'].append(current)


def intent(suffix='', channel='atm', amount=6000, ttl=60):
    op = {'operationId': str(uuid.uuid5(uuid.NAMESPACE_URL, 'channels-v1/' + current['name'] + suffix)),
          'channel': channel, 'sourceId': 1, 'targetId': 3 if channel == 'atm' else 2,
          'amountCents': amount, 'terminalId': 'ATM-001' if channel == 'atm' else '', 'ttlSeconds': ttl, 'fault': ''}
    offered[op['operationId']] = copy.deepcopy(op)
    return op


def prepared(op):
    assert http('authorize', op)['state'] == 'AUTHORIZED'
    value = http('prepare', op)
    assert value['status'] == 'UNKNOWN'
    return {'operationId': op['operationId'], 'commandId': value['commandId']}


def device(cmd, actual, lose=False):
    args = [sys.executable, 'lab/channels/device.py', json.dumps(cmd), str(actual)]
    if not lose:
        raw = command(args)
        current.setdefault('device', []).append(json.loads(raw))
        return
    log = (OUT / 'lost-device-response.log').open('w')
    logs.append(log)
    child = subprocess.Popen(args + ['--lose-response'], stdout=log, stderr=subprocess.STDOUT)
    try:
        wait_until(lambda: (OUT / 'device-committed.json').is_file())
        current['device_commit_marker'] = json.loads((OUT / 'device-committed.json').read_text())
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)
    assert child.returncode == -signal.SIGKILL
    current['device_process_exit'] = child.returncode


def finish():
    current['snapshot'] = snapshot()
    current['offered'] = copy.deepcopy(offered)
    current['oracle'] = audit(current['snapshot'], offered)
    assert current['oracle']['status'] == 'PASS', current['oracle']
    current['status'] = 'PASS'


try:
    report['checkout_sha'] = command(['git', 'rev-parse', 'HEAD'])
    report['sources'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted((ROOT / 'lab/channels').glob('*')) if p.is_file()}
    report['tools'] = {tool: command([tool, '--version']) for tool in ['dotnet', 'podman']}
    report['python'] = sys.version
    image = 'docker.io/library/postgres:16.13'
    command(['podman', 'pull', image])
    report['image'] = json.loads(command(['podman', 'image', 'inspect', image]))
    for name, port in [('core', 55442), ('device', 55443)]:
        ident = command(['podman', 'run', '-d', '--name', 'channels-' + name + '-' + str(os.getpid()),
                         '-e', 'POSTGRES_PASSWORD=channelslocal', '-e', 'POSTGRES_DB=channelslab_' + name,
                         '-p', f'127.0.0.1:{port}:5432', image])
        containers.append(ident)
        wait_until(lambda i=ident: subprocess.run(['podman', 'exec', i, 'pg_isready', '-U', 'postgres'], capture_output=True).returncode == 0, 45)
        with connect(name, probe=False) as db:
            assert db.execute('SELECT current_database() AS db').fetchone()['db'] == 'channelslab_' + name
            db.execute((ROOT / f'lab/channels/{name}.sql').read_text())
        with connect(name) as db:
            report.setdefault('sql_settings', {})[name] = db.execute("SELECT name,setting FROM pg_settings WHERE name IN ('server_version','fsync','synchronous_commit','full_page_writes','transaction_isolation') ORDER BY name").fetchall()
    command(['dotnet', 'publish', 'lab/channels/ChannelsLab.csproj', '-c', 'Release', '-o', 'lab/results/channels/publish'])
    start()
    for label, actual in [('full', 6000), ('partial', 4000), ('zero', 0), ('device-response-lost', 6000), ('settlement-response-lost', 6000), ('core-crash-before-commit', 6000)]:
        reset(label)
        op = intent()
        cmd = prepared(op)
        assert http('settle', op)['status'] == 'UNKNOWN'
        device(cmd, actual, lose=label == 'device-response-lost')
        assert http('operations/' + op['operationId'])['status'] == 'UNKNOWN'
        if label == 'core-crash-before-commit':
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pending = pool.submit(http, 'settle', dict(op, fault='hold-before-commit'), True)
                wait_until(lambda: (OUT / 'before-commit.json').is_file())
                current['before_commit_marker'] = json.loads((OUT / 'before-commit.json').read_text())
                assert stop(kill=True) == -signal.SIGKILL
                pending.result()
            current['after_kill'] = snapshot()
            assert current['after_kill']['core']['operations'][0]['state'] == 'DISPENSE_PENDING'
            assert current['after_kill']['core']['postings'] == []
            assert len(current['after_kill']['device']['device_commands']) == 1
            start()
        if label == 'settlement-response-lost':
            http('settle', dict(op, fault='drop-response'), True)
        final = http('settle', op)
        assert final['state'] == ('POSTED' if actual else 'CANCELLED') and final['postedCents'] == actual
        assert http('settle', op)['duplicate']
        assert http('authorize', op)['duplicate']
        assert http('prepare', dict(op, amountCents=5000))['status'] == 'ID_CONFLICT'
        finish()
        if label == 'partial':
            mutant = copy.deepcopy(current['snapshot'])
            for row in mutant['core']['postings']:
                row['delta'] *= 2
            for row in mutant['core']['accounts']:
                row['balance'] = {1: 2000, 2: 10000, 3: 8000}[row['id']]
            verdict = audit(mutant, offered)
            assert verdict['status'] == 'FAIL' and verdict['checks']['postings'] and not verdict['checks']['conservation'] and not verdict['checks']['projection']
            report['negative_controls'].append({'name': 'conserved-extra-cash-posting', 'snapshot': mutant, 'oracle': verdict})
    reset('digital-response-lost')
    op = intent(channel='web')
    http('transfer', dict(op, fault='drop-response'), True)
    assert http('operations/' + op['operationId'])['state'] == 'COMMITTED'
    assert http('transfer', op)['duplicate']
    finish()
    reset('atm-mobile-race')
    atm, mobile = intent('atm'), intent('mobile', channel='mobile')
    with concurrent.futures.ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda pair: http(*pair), [('authorize', atm), ('transfer', mobile)]))
    assert sum(r['state'] == 'DECLINED' for r in results) == 1
    if results[0]['state'] == 'AUTHORIZED':
        device({'operationId': atm['operationId'], 'commandId': http('prepare', atm)['commandId']}, 6000)
        http('settle', atm)
    finish()
    reset('expiry-before-dispatch')
    op = intent(ttl=1)
    http('authorize', op)
    time.sleep(1.2)
    assert http('expire', op)['state'] == 'EXPIRED'
    assert http('prepare', op)['state'] == 'EXPIRED'
    finish()
    reset('pending-expiry-missing-journal')
    op = intent(ttl=1)
    prepared(op)
    time.sleep(1.2)
    assert http('expire', op)['status'] == 'UNKNOWN'
    assert http('settle', op)['status'] == 'UNKNOWN'
    finish()
    mutant = copy.deepcopy(current['snapshot'])
    mutant['core']['operations'][0]['state'] = 'POSTED'
    mutant['core']['operations'][0]['posted'] = 6000
    mutant['core']['holds'][0]['active'] = False
    verdict = audit(mutant, offered)
    assert verdict['status'] == 'FAIL' and verdict['checks']['postings'] and verdict['checks']['outbox'] and verdict['checks']['device']
    report['negative_controls'].append({'name': 'false-final-without-atomic-effects', 'snapshot': mutant, 'oracle': verdict})
    report['status'] = 'PASS'
except BaseException:
    report['error'] = traceback.format_exc()
    if current is not None:
        try:
            current['failure_snapshot'] = snapshot()
        except Exception:
            current['snapshot_error'] = traceback.format_exc()
    raise
finally:
    stop()
    for log in logs:
        log.close()
    for ident in containers:
        result = subprocess.run(['podman', 'logs', ident], capture_output=True, text=True)
        (OUT / (ident[:12] + '.log')).write_text(result.stdout + result.stderr)
        subprocess.run(['podman', 'rm', '-f', ident], capture_output=True)
    (OUT / 'original.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
    print(json.dumps({'status': report['status'], 'cases': len(report['cases']), 'report': str(OUT / 'original.json')}))
