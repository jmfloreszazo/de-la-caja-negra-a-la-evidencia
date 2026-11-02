#!/usr/bin/env python3
"""C05/C06: directional packet loss, SQL reconciliation, measured recovery.

One physical host. Fixed private endpoints. No claim of exclusive activation,
transparent recovery, production fencing or production RTO is made.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import test_podman_network as fx
import test_podman_disconnect as net
import test_controlled_placement as seed
from test_e2 import command
from oracle import verify

P = fx.podman
OUT = fx.OUT / 'c05-c06'
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'c05-baseline'
CONTEST = 'c05-contested-id'
RECOVERY = 'c06-recovery-new'


def helper(name, *args):
    return P('run', '--rm', '--network', 'container:' + name,
             '--cap-add', 'NET_ADMIN', '--cap-add', 'NET_RAW',
             '--entrypoint', args[0], net.NET_TOOL_IMAGE, *args[1:], timeout=45)


def rule(action, blocked, peer):
    return helper(blocked, 'iptables', '-w', '3', action, 'OUTPUT',
                  '-d', fx.NODES[peer], '-p', 'tcp', '-m', 'multiport',
                  '--ports', '11150,11151', '-j', 'DROP')


def rules(name):
    return helper(name, 'iptables', '-w', '3', '-S', 'OUTPUT')


def snapshot():
    with fx.connect() as db:
        operations = db.execute('SELECT id,src,dst,amount,status FROM operations ORDER BY id').fetchall()
    oracle = verify()
    assert len(oracle) == 7 and all(v is True for v in oracle.values()), oracle
    effects = fx.business_counts()
    assert effects['postings'] == 2 * effects['committedOperations'], effects
    assert effects['outboxEvents'] == effects['committedOperations'], effects
    return {'utc': seed.utc(), 'operations': [list(r) for r in operations],
            'effects': effects, 'oracle': oracle, 'membershipGenerations': seed.generations()}


def client(role, request=None):
    path = OUT / ('request-' + role + '.json')
    if request is not None:
        path.write_text(json.dumps({'route': 'orleans', 'concurrent': False, 'commands': [request]}) + '\n')
    result = subprocess.run(['podman', 'exec', '-e', 'E2_C05_TEST=1', 'e2f10-client',
                             'dotnet', '/app/OrleansLab.dll', 'cluster', 'client', 'partition-probe',
                             role, '/fixtures/c05-c06/' + path.name if request is not None else 'observe'],
                            capture_output=True, text=True, timeout=55)
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    observed = json.loads(result.stdout)
    assert observed['gateway'] == role and observed['placementHintsUsed'] is False
    assert observed['status'] in ('ACKNOWLEDGED', 'STARTUP_UNAVAILABLE',
                                  'DISPATCH_AMBIGUOUS', 'OBSERVED', 'OBSERVATION_UNAVAILABLE'), observed
    if request is not None:
        assert observed['financialCommandsDispatched'] in (0, 1)
        if observed['status'] == 'ACKNOWLEDGED':
            assert observed['financialCommandsDispatched'] == 1
            assert observed['result']['status'] in ('COMMITTED', 'DUPLICATE_COMMITTED', 'ID_CONFLICT'), observed
    else:
        assert observed['financialCommandsDispatched'] == 0
    observed['stderr'] = result.stderr
    return observed


def captures_start(containers):
    names = []
    for role in ('primary', 'secondary'):
        name = 'c05-capture-' + role
        P('run', '-d', '--name', name, '--network', 'container:e2f10-' + role,
          '--cap-add', 'NET_RAW', '--cap-add', 'NET_ADMIN',
          '-v', str(OUT.resolve()) + ':/capture', '--entrypoint', 'dumpcap',
          net.NET_TOOL_IMAGE, '-q', '-P', '-a', 'duration:45', '-i', 'any',
          '-w', '/capture/' + role + '.pcap',
          '-f',
          'tcp and host 10.78.30.11 and host 10.78.30.12 and (port 11150 or port 11151)')
        containers.append(name)
        names.append(name)
        seed.wait_for(lambda: 'File:' in subprocess.run(
            ['podman', 'logs', name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=10).stdout, 'native timed capture ready', timeout=15)
    return names


def captures_stop(names):
    for name in names:
        # Native dumpcap autostop avoids host-to-container signalling.
        assert P('wait', name, timeout=60) == '0'
    result = {}
    for role in ('primary', 'secondary'):
        path = OUT / (role + '.pcap')
        decoded = P('run', '--rm', '-v', str(OUT.resolve()) + ':/capture:ro',
                    '--entrypoint', 'tcpdump', net.NET_TOOL_IMAGE, '-nn', '-r', '/capture/' + path.name)
        (OUT / (role + '-packets.txt')).write_text(decoded + '\n')
        result[role] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'bytes': path.stat().st_size, 'decoded': decoded}
    return result


def verify_ack(observed, state):
    if observed['status'] != 'ACKNOWLEDGED':
        return
    request = observed['command']
    rows = [r for r in state['operations'] if r[0] == request['operationId']]
    assert len(rows) == 1, (observed, state)
    equal = rows[0][1:4] == [request['sourceAccountId'], request['targetAccountId'], request['amountCents']]
    assert (observed['result']['status'] == 'ID_CONFLICT') is (not equal), (observed, rows)
    assert rows[0][4] == 'COMMITTED'


def active_pair():
    rows = seed.generations()
    active = [r for r in rows if r[3] == 3]
    return rows if len(active) == 2 and {r[1] for r in active} == {11150, 11151} else None


def main():
    assert os.environ.get('E2_NETWORK_TEST') == '1'
    assert os.environ.get('E1_PG_DSN') == 'host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local'
    direction = os.environ.get('C05_BLOCKED_ROLE')
    assert direction in ('primary', 'secondary')
    blocked, peer = 'e2f10-' + direction, 'e2f10-' + ('secondary' if direction == 'primary' else 'primary')
    containers, capture_names = [], []
    network = installed = False
    stage = 'setup'
    report = {'status': 'FAIL', 'protocol': 'C05_C06_DIRECTIONAL_PACKET_LEDGER_RECOVERY_V1',
              'sourceHeadSha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'startUtc': seed.utc(), 'blockedRole': direction, 'runnerName': os.environ.get('RUNNER_NAME'),
              'runnerHost': os.uname().nodename, 'physicalHosts': 1, 'events': [],
              'activationExclusivityEstablished': False,
              'limitations': 'Two packet directions are distinct from bidirectional TCP availability. '
              'Management catalogs are non-atomic and may be unavailable: absence of duplicate activations '
              'is not proven. SQL owns effects. Recovery may need explicitly recorded process recreation. '
              'No physical HA, production RTO, sustained capacity or overall E2 acceptance.'}
    try:
        P('pull', net.NET_TOOL_IMAGE, timeout=150)
        P('network', 'create', '--subnet', '10.78.30.0/24', fx.NETWORK)
        network = True
        fx.start('e2f10-pg', '-e', 'POSTGRES_PASSWORD=e2local', '-e', 'POSTGRES_DB=e2lab',
                 '-p', '127.0.0.1:55435:5432', fx.POSTGRES, app=False)
        containers.append('e2f10-pg')
        report['sqlStartup'] = fx.wait_disposable_sql_ready(case='c05', output_dir=OUT)
        fx.reset()
        os.environ['E2_POSTGRES_CONTAINER'] = 'e2f10-pg'
        from setup_adonet_membership import main as install
        install()
        for role in ('primary', 'secondary'):
            name = 'e2f10-' + role
            fx.start(name, '--entrypoint', 'dotnet', fx.IMAGE, '/app/OrleansLab.dll',
                     'cluster', 'silo', role, silo_ip=fx.NODES[name])
            containers.append(name)
            fx.wait_silo(name, role, seconds=110)
        fx.start('e2f10-client', '--entrypoint', 'sleep', fx.IMAGE, '1200')
        containers.append('e2f10-client')
        report['containersBefore'] = {n: net.inspect(n) for n in containers}
        report['namespaces'] = {n: fx.namespace_id(n) for n in containers}
        assert len(set(report['namespaces'].values())) == 4
        assert len({s['pidOnHost'] for s in report['containersBefore'].values()}) == 4
        report['images'] = json.loads(P('image', 'inspect', fx.IMAGE, fx.POSTGRES, net.NET_TOOL_IMAGE))
        assert active_pair()
        report['initialSql'] = snapshot()
        report['controlledBaseline'] = seed.controlled_probe('alternating')
        assert seed.node_map(report['controlledBaseline']) == {
            k: 'e2f10-primary' if k % 2 else 'e2f10-secondary' for k in range(1, 17)}
        baseline = client('primary', command(BASE, 1, 2, 11))
        assert baseline['status'] == 'ACKNOWLEDGED' and baseline['result']['status'] == 'COMMITTED', baseline
        report['baselineAck'] = baseline
        report['baselineSql'] = snapshot()
        assert report['baselineSql']['effects'] == dict(committedOperations=1, postings=2, outboxEvents=1)
        report['catalogBefore'] = [client('primary'), client('secondary')]
        assert all(x['status'] == 'OBSERVED' for x in report['catalogBefore']), report['catalogBefore']
        baseline_rules = rules(blocked)
        report['rulesBefore'] = baseline_rules
        report['captureTool'] = helper(blocked, 'dumpcap', '--version')
        report['captureAutostopSeconds'] = 45
        stage = 'directional-drop'
        installed = True
        report['faultUtc'] = seed.utc()
        fault_clock = time.monotonic()
        rule('-A', blocked, peer)
        report['rulesDuring'] = rules(blocked)
        assert '--ports 11150,11151 -j DROP' in report['rulesDuring']
        capture_names = captures_start(containers)
        # A TCP handshake in either direction can fail under one-way loss.
        # Generate real SYNs, then use captures/counters to prove packet direction.
        report['handshakeProbes'] = {}
        for origin, destination, port in ((peer, blocked, '11150' if direction == 'primary' else '11151'),
                                          (blocked, peer, '11151' if direction == 'primary' else '11150')):
            result = helper(origin, 'sh', '-c', 'nc -z -w 2 ' + fx.NODES[destination] + ' ' + port + '; rc=$?; echo CONNECT_EXIT:$rc')
            assert result.strip() == 'CONNECT_EXIT:1', result
            report['handshakeProbes'][origin] = result
        report['duringNetworkChecks'] = {n: net.check(n) for n in ('e2f10-primary', 'e2f10-secondary', 'e2f10-client')}
        assert all(x['primaryGatewayReachable'] and x['secondaryGatewayReachable'] and x['databaseHealthy']
                   for x in report['duringNetworkChecks'].values())
        report['duringMembership'] = seed.generations()
        requests = [command(CONTEST, 2, 1, 31), command(CONTEST, 2, 1, 37)]
        stage = 'contending-requests-under-directional-loss'
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(client, role, req) for role, req in zip(('primary', 'secondary'), requests)]
            report['contendingOutcomes'] = [f.result() for f in futures]
        report['duringSql'] = snapshot()
        assert set(r[0] for r in report['duringSql']['operations']) <= {BASE, CONTEST}
        assert report['duringSql']['effects']['committedOperations'] in (1, 2)
        for observed in report['contendingOutcomes']:
            verify_ack(observed, report['duringSql'])
        report['catalogDuring'] = [client('primary'), client('secondary')]
        report['duringSqlAfterCatalog'] = snapshot()
        report['dropCounters'] = helper(blocked, 'iptables-save', '-c')
        matches = re.findall(r'\[(\d+):(\d+)\] -A OUTPUT .*--ports 11150,11151 -j DROP', report['dropCounters'])
        assert len(matches) == 1 and int(matches[0][0]) > 0, report['dropCounters']
        report['captures'] = captures_stop(capture_names)
        capture_names = []
        received = report['captures'][peer.removeprefix('e2f10-')]['decoded']
        # The unblocked host receives no selected-port TCP packets from the
        # blocked host, while its own SYN packets reach the opposite capture.
        denied_pattern = re.escape(fx.NODES[blocked]) + r'\.\d+ > ' + re.escape(fx.NODES[peer]) + r'\.\d+'
        allowed_pattern = re.escape(fx.NODES[peer]) + r'\.\d+ > ' + re.escape(fx.NODES[blocked]) + r'\.\d+'
        assert not re.search(denied_pattern, received), received
        assert re.search(allowed_pattern, report['captures'][direction]['decoded']), report['captures']
        report['faultObservedSeconds'] = time.monotonic() - fault_clock
        report['containersDuring'] = {n: net.inspect(n) for n in ('e2f10-primary', 'e2f10-secondary')}
        for n, observed in report['containersDuring'].items():
            assert observed['id'] == report['containersBefore'][n]['id']
            assert observed['networks'] == report['containersBefore'][n]['networks']
        stage = 'restore-and-measure'
        report['restoreUtc'] = seed.utc()
        restored_clock = time.monotonic()
        rule('-D', blocked, peer)
        installed = False
        report['rulesAfter'] = rules(blocked)
        assert report['rulesAfter'] == baseline_rules
        report['recoveryMembershipSamples'] = []
        transparent_deadline = time.monotonic() + 30
        converged = None
        while time.monotonic() < transparent_deadline:
            rows = seed.generations()
            report['recoveryMembershipSamples'].append({'elapsedSeconds': time.monotonic() - restored_clock, 'rows': rows})
            if active_pair() and all(net.inspect('e2f10-' + r)['status'] == 'running' for r in ('primary', 'secondary')):
                converged = rows
                break
            time.sleep(1)
        report['recoveryMode'] = 'NETWORK_RESTORATION_ONLY'
        if converged is None:
            # Explicitly preregistered assisted recovery; never call this
            # transparent network healing or erase the old Dead generations.
            report['recoveryMode'] = 'ASSISTED_BOTH_SILOS_RECREATED_AFTER_30S'
            report['beforeAssistedRestart'] = {n: net.inspect(n) for n in ('e2f10-primary', 'e2f10-secondary')}
            for role in ('primary', 'secondary'):
                P('rm', '-f', 'e2f10-' + role)
            for role in ('primary', 'secondary'):
                n = 'e2f10-' + role
                fx.start(n, '--entrypoint', 'dotnet', fx.IMAGE, '/app/OrleansLab.dll',
                         'cluster', 'silo', role, silo_ip=fx.NODES[n])
                fx.wait_silo(n, role, seconds=85)
            converged = seed.wait_for(active_pair, 'two Active recovery generations', timeout=30)
        report['membershipRecovered'] = converged
        recovery_attempts = []
        deadline = restored_clock + 240
        while time.monotonic() < deadline:
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(lambda role: client(role, command(CONTEST, 2, 1, 31)), ('primary', 'secondary')))
            recovery_attempts.append(outcomes)
            if all(o['status'] == 'ACKNOWLEDGED' for o in outcomes):
                break
            time.sleep(1)
        else:
            raise AssertionError('Recovery exceeded the preregistered 240s experiment bound')
        report['recoveryAttempts'] = recovery_attempts
        report['firstBothGatewayAckSecondsAfterRestore'] = time.monotonic() - restored_clock
        assert report['firstBothGatewayAckSecondsAfterRestore'] <= 240
        after = snapshot()
        assert {r[0] for r in after['operations']} == {BASE, CONTEST}
        winner = next(r for r in after['operations'] if r[0] == CONTEST)
        assert winner[1:3] == [2, 1] and winner[3] in (31, 37) and winner[4] == 'COMMITTED'
        replay = client('primary', command(CONTEST, 2, 1, winner[3]))
        conflict = client('secondary', command(CONTEST, 2, 1, 37 if winner[3] == 31 else 31))
        assert replay['status'] == 'ACKNOWLEDGED' and replay['result']['status'] == 'DUPLICATE_COMMITTED', replay
        assert conflict['status'] == 'ACKNOWLEDGED' and conflict['result']['status'] == 'ID_CONFLICT', conflict
        report['replayAfterRestore'], report['conflictAfterRestore'] = replay, conflict
        new = client('secondary', command(RECOVERY, 1, 2, 5))
        assert new['status'] == 'ACKNOWLEDGED' and new['result']['status'] == 'COMMITTED', new
        report['newAfterRestore'] = new
        report['finalSql'] = snapshot()
        assert report['finalSql']['effects'] == dict(committedOperations=3, postings=6, outboxEvents=3)
        assert {r[0] for r in report['finalSql']['operations']} == {BASE, CONTEST, RECOVERY}
        for observed in report['contendingOutcomes'] + [x for attempt in recovery_attempts for x in attempt] + [replay, conflict, new]:
            verify_ack(observed, report['finalSql'])
        report['networkAfter'] = {n: net.check(n) for n in ('e2f10-primary', 'e2f10-secondary', 'e2f10-client')}
        assert all(x['primaryGatewayReachable'] and x['secondaryGatewayReachable'] and x['databaseHealthy']
                   for x in report['networkAfter'].values())
        report['catalogAfter'] = [client('primary'), client('secondary')]
        assert all(x['status'] == 'OBSERVED' for x in report['catalogAfter'])
        report['containersAfter'] = {n: net.inspect(n) for n in ('e2f10-primary', 'e2f10-secondary')}
        report['status'] = 'PASS'
    except Exception as exc:
        report['error'] = repr(exc)
        raise
    finally:
        report['lastStage'] = stage
        report['endUtc'] = seed.utc()
        report['siloLogs'] = {n: P('logs', n, check=False)[-14000:]
                              for n in containers if n in ('e2f10-primary', 'e2f10-secondary')}
        if installed:
            try:
                rule('-D', blocked, peer)
            except Exception as exc:
                report['cleanupRuleError'] = repr(exc)
        for name in capture_names:
            # Autostop is native even on failure; never escalate signalling.
            P('wait', name, check=False, timeout=60)
        (OUT / 'directional-partition-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': report['status'], 'stage': stage, 'error': report.get('error')}))
        for name in reversed(containers):
            P('rm', '-f', name, check=False, timeout=50)
        if network:
            P('network', 'rm', fx.NETWORK, check=False, timeout=50)


if __name__ == '__main__':
    main()
