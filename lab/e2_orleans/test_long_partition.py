#!/usr/bin/env python3
"""Two 120s fault schedules and a sampled, bounded recovery observation.

Reuse verified private-fixture helpers without modifying the short experiment.
One physical host per job. No exclusive-activation or production HA claim.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import test_directional_partition as short
from placement_observation import capture

fx, net, seed, P, OUT = short.fx, short.net, short.seed, short.P, short.OUT
HOLD_SECONDS = 120
STABLE_SAMPLES = 14
STABLE_INTERVAL = 5


def pair(requests):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(short.client, role, request)
                   for role, request in zip(('primary', 'secondary'), requests)]
        return [f.result() for f in futures]


def same_id_pair(amount):
    return pair([short.command(short.CONTEST, 2, 1, amount)] * 2)


def running_silos():
    return all(net.inspect('e2f10-' + role)['status'] == 'running'
               for role in ('primary', 'secondary'))


def observe(phase, origin, blocked, peer):
    result = {'utc': seed.utc(), 'phase': phase, 'elapsedSeconds': time.monotonic() - origin,
              'sql': short.snapshot(), 'processes': {}, 'outputRule': None}
    for role in ('primary', 'secondary'):
        result['processes'][role] = net.inspect('e2f10-' + role)
    if result['processes'][blocked.removeprefix('e2f10-')]['status'] == 'running':
        result['outputRule'] = capture(lambda: short.rules(blocked))
        if result['outputRule']['observationSucceeded']:
            assert '--ports 11150,11151 -j DROP' in result['outputRule']['value']
    else:
        result['outputRule'] = {'observationSucceeded': False,
                                'reason': 'TARGET_PROCESS_EXITED_NAMESPACE_NOT_ASSUMED_LIVE'}
    return result


def check_durable(state, allowed, count=None):
    assert {r[0] for r in state['operations']} <= set(allowed), state
    if count is not None:
        assert state['effects'] == dict(committedOperations=count, postings=2 * count, outboxEvents=count)


def main():
    assert os.environ.get('E2_LONG_PARTITION_TEST') == '1'
    assert os.environ.get('E2_NETWORK_TEST') == '1'
    assert os.environ.get('E1_PG_DSN') == 'host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local'
    role = os.environ.get('C05_BLOCKED_ROLE')
    assert role in ('primary', 'secondary')
    blocked = 'e2f10-' + role
    peer = 'e2f10-' + ('secondary' if role == 'primary' else 'primary')
    containers, captures = [], []
    network = installed = False
    phase = 'setup'
    report = {'status': 'FAIL', 'protocol': 'E2_LONG_DIRECTIONAL_120_SAMPLED_RECOVERY_60_V1',
              'sourceHeadSha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'blockedRole': role, 'startUtc': seed.utc(), 'physicalHosts': 1,
              'requestedFaultScheduleSeconds': HOLD_SECONDS, 'samples': [], 'catalogObservations': [],
              'activationExclusivityEstablished': False,
              'limitations': 'A 120s scheduled fault can include silo exit and namespace loss; '
              'actual liveness/rule samples determine scope. Catalogs are non-atomic and may fail. '
              'Assisted restart is an operator choice after bounded attempts, not proof of necessity. '
              'Recovery sampling is not continuous availability, an RTO/SLA, physical HA, capacity '
              'or overall E2 acceptance.'}
    try:
        P('pull', net.NET_TOOL_IMAGE, timeout=150)
        P('network', 'create', '--subnet', '10.78.30.0/24', fx.NETWORK)
        network = True
        fx.start('e2f10-pg', '-e', 'POSTGRES_PASSWORD=e2local', '-e', 'POSTGRES_DB=e2lab',
                 '-p', '127.0.0.1:55435:5432', fx.POSTGRES, app=False)
        containers.append('e2f10-pg')
        report['startup'] = fx.wait_disposable_sql_ready(case='c05', output_dir=OUT)
        fx.reset()
        os.environ['E2_POSTGRES_CONTAINER'] = 'e2f10-pg'
        from setup_adonet_membership import main as install
        install()
        for name_role in ('primary', 'secondary'):
            name = 'e2f10-' + name_role
            fx.start(name, '--entrypoint', 'dotnet', fx.IMAGE, '/app/OrleansLab.dll',
                     'cluster', 'silo', name_role, silo_ip=fx.NODES[name])
            containers.append(name)
            fx.wait_silo(name, name_role, seconds=110)
        fx.start('e2f10-client', '--entrypoint', 'sleep', fx.IMAGE, '1800')
        containers.append('e2f10-client')
        report['containersBefore'] = {n: net.inspect(n) for n in containers}
        report['namespaces'] = {n: fx.namespace_id(n) for n in containers}
        assert len(set(report['namespaces'].values())) == 4
        report['images'] = json.loads(P('image', 'inspect', fx.IMAGE, fx.POSTGRES, net.NET_TOOL_IMAGE))
        assert short.active_pair()
        report['seeding'] = seed.controlled_probe('alternating')
        assert seed.node_map(report['seeding']) == {
            k: 'e2f10-primary' if k % 2 else 'e2f10-secondary' for k in range(1, 17)}
        report['initialSql'] = short.snapshot()
        check_durable(report['initialSql'], [], 0)
        baseline = short.client('primary', short.command(short.BASE, 1, 2, 11))
        assert baseline['status'] == 'ACKNOWLEDGED' and baseline['result']['status'] == 'COMMITTED'
        report['baselineAck'] = baseline
        report['baselineSql'] = short.snapshot()
        check_durable(report['baselineSql'], [short.BASE], 1)
        report['rulesBefore'] = {r: short.rules('e2f10-' + r) for r in ('primary', 'secondary')}
        phase = 'fault-injection'
        installed = True
        report['faultUtc'] = seed.utc()
        fault_clock = time.monotonic()
        short.rule('-A', blocked, peer)
        captures = short.captures_start(containers)
        report['tcpProbes'] = {}
        for origin, destination, port in ((peer, blocked, '11150' if role == 'primary' else '11151'),
                                          (blocked, peer, '11151' if role == 'primary' else '11150')):
            result = short.helper(origin, 'sh', '-c', 'nc -z -w 2 ' + fx.NODES[destination] + ' ' + port + '; rc=$?; echo CONNECT_EXIT:$rc')
            assert result.strip() == 'CONNECT_EXIT:1'
            report['tcpProbes'][origin] = result
        report['initialNetworkChecks'] = {n: net.check(n) for n in ('e2f10-primary', 'e2f10-secondary', 'e2f10-client')}
        assert all(v['databaseHealthy'] and v['primaryGatewayReachable'] and v['secondaryGatewayReachable']
                   for v in report['initialNetworkChecks'].values())
        phase = 'scheduled-long-fault'
        requests = [short.command(short.CONTEST, 2, 1, amount) for amount in (31, 37)]
        report['firstContendingOutcomes'] = pair(requests)
        first_sql = short.snapshot()
        check_durable(first_sql, [short.BASE, short.CONTEST])
        for outcome in report['firstContendingOutcomes']:
            short.verify_ack(outcome, first_sql)
        report['samples'].append(observe(phase, fault_clock, blocked, peer))
        report['catalogObservations'].append({'elapsedSeconds': time.monotonic() - fault_clock,
            'outcomes': [short.client('primary'), short.client('secondary')]})
        report['initialCaptures'] = short.captures_stop(captures)
        captures = []
        blocked_ip, peer_ip = fx.NODES[blocked], fx.NODES[peer]
        receiver = report['initialCaptures'][peer.removeprefix('e2f10-')]['decoded']
        assert not re.search(re.escape(blocked_ip) + r'\.\d+ > ' + re.escape(peer_ip) + r'\.\d+', receiver)
        assert re.search(re.escape(peer_ip) + r'\.\d+ > ' + re.escape(blocked_ip) + r'\.\d+',
                         report['initialCaptures'][role]['decoded'])
        report['initialDropCounters'] = capture(lambda: short.helper(blocked, 'iptables-save', '-c'))
        assert report['initialDropCounters']['observationSucceeded']
        matched = re.findall(r'\[(\d+):(\d+)\] -A OUTPUT .*--ports 11150,11151 -j DROP',
                             report['initialDropCounters']['value'])
        assert len(matched) == 1 and int(matched[0][0]) > 0
        second_sent = False
        while time.monotonic() - fault_clock < HOLD_SECONDS:
            sample = observe(phase, fault_clock, blocked, peer)
            check_durable(sample['sql'], [short.BASE, short.CONTEST])
            report['samples'].append(sample)
            if not second_sent and time.monotonic() - fault_clock >= 60:
                report['lateContendingOutcomes'] = pair(requests)
                report['lateContendingElapsedSeconds'] = time.monotonic() - fault_clock
                late_sql = short.snapshot()
                for outcome in report['lateContendingOutcomes']:
                    short.verify_ack(outcome, late_sql)
                second_sent = True
            time.sleep(min(2, max(0, HOLD_SECONDS - (time.monotonic() - fault_clock))))
        report['faultScheduleElapsedSeconds'] = time.monotonic() - fault_clock
        assert 120 <= report['faultScheduleElapsedSeconds'] <= 180
        assert second_sent
        report['samples'].append(observe(phase, fault_clock, blocked, peer))
        report['finalDropCounters'] = capture(lambda: short.helper(blocked, 'iptables-save', '-c'))
        phase = 'restore-and-reconcile'
        restore_clock = time.monotonic()
        report['restoreUtc'] = seed.utc()
        if net.inspect(blocked)['status'] == 'running':
            short.rule('-D', blocked, peer)
            installed = False
            assert short.rules(blocked) == report['rulesBefore'][role]
            report['ruleRestoration'] = 'EXACT_LIVE_NAMESPACE_BASELINE'
        else:
            installed = False
            report['ruleRestoration'] = 'TARGET_EXITED_OLD_NAMESPACE_NOT_ASSUMED_RESTORED'
        before_restore_sql = short.snapshot()
        check_durable(before_restore_sql, [short.BASE, short.CONTEST])
        report['unassistedAttempts'] = []
        for _ in range(2):
            outcomes = same_id_pair(31)
            elapsed = time.monotonic() - restore_clock
            if all(o['status'] == 'ACKNOWLEDGED' for o in outcomes):
                report.setdefault('firstBothAckSecondsAfterRestore', elapsed)
            report['unassistedAttempts'].append({'elapsedSeconds': elapsed,
                                                'outcomes': outcomes})
            if all(o['status'] == 'ACKNOWLEDGED' for o in outcomes) and short.active_pair() and running_silos():
                break
            if time.monotonic() - restore_clock >= 60:
                break
        report['recoveryMode'] = 'NETWORK_RESTORATION_ONLY'
        if not (all(o['status'] == 'ACKNOWLEDGED' for o in outcomes) and short.active_pair() and running_silos()):
            report['recoveryMode'] = 'ASSISTED_BOTH_SILOS_RECREATED'
            report['beforeAssistedRecreation'] = {r: net.inspect('e2f10-' + r) for r in ('primary', 'secondary')}
            report['beforeAssistedMembership'] = seed.generations()
            for r in ('primary', 'secondary'):
                P('rm', '-f', 'e2f10-' + r)
            for r in ('primary', 'secondary'):
                n = 'e2f10-' + r
                fx.start(n, '--entrypoint', 'dotnet', fx.IMAGE, '/app/OrleansLab.dll',
                         'cluster', 'silo', r, silo_ip=fx.NODES[n])
                fx.wait_silo(n, r, seconds=85)
            seed.wait_for(short.active_pair, 'two Active restored silo generations', timeout=30)
            for r in ('primary', 'secondary'):
                assert short.rules('e2f10-' + r) == report['rulesBefore'][r]
            outcomes = same_id_pair(31)
            report['assistedOutcomes'] = outcomes
        assert all(o['status'] == 'ACKNOWLEDGED' for o in outcomes)
        report.setdefault('firstBothAckSecondsAfterRestore', time.monotonic() - restore_clock)
        report['recoveryCriteriaSatisfiedSecondsAfterRestore'] = time.monotonic() - restore_clock
        assert report['recoveryCriteriaSatisfiedSecondsAfterRestore'] <= 300
        recovered = short.snapshot()
        check_durable(recovered, [short.BASE, short.CONTEST], 2)
        winner = next(r for r in recovered['operations'] if r[0] == short.CONTEST)
        assert winner[1:3] == [2, 1] and winner[3] in (31, 37) and winner[4] == 'COMMITTED'
        report['winner'] = winner
        replay = short.client('primary', short.command(short.CONTEST, 2, 1, winner[3]))
        conflict = short.client('secondary', short.command(short.CONTEST, 2, 1, 37 if winner[3] == 31 else 31))
        new = short.client('secondary', short.command(short.RECOVERY, 1, 2, 5))
        assert replay['status'] == conflict['status'] == new['status'] == 'ACKNOWLEDGED'
        assert [x['result']['status'] for x in (replay, conflict, new)] == ['DUPLICATE_COMMITTED', 'ID_CONFLICT', 'COMMITTED']
        report['replayConflictNew'] = [replay, conflict, new]
        phase = 'sampled-stable-recovery'
        expected_containers = {r: net.inspect('e2f10-' + r) for r in ('primary', 'secondary')}
        report['stableSamples'] = []
        steady_clock = None
        for index in range(STABLE_SAMPLES):
            if steady_clock is not None:
                delay = steady_clock + index * STABLE_INTERVAL - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
            responses = same_id_pair(winner[3])
            assert all(o['status'] == 'ACKNOWLEDGED' and o['result']['status'] == 'DUPLICATE_COMMITTED' for o in responses)
            if steady_clock is None:
                steady_clock = time.monotonic()
            state = short.snapshot()
            check_durable(state, [short.BASE, short.CONTEST, short.RECOVERY], 3)
            assert short.active_pair()
            actual_containers = {r: net.inspect('e2f10-' + r) for r in ('primary', 'secondary')}
            assert actual_containers == expected_containers and running_silos()
            sample = {'index': index, 'utc': seed.utc(), 'elapsedSeconds': time.monotonic() - steady_clock,
                      'outcomes': responses, 'sql': state, 'containers': actual_containers}
            report['stableSamples'].append(sample)
            if index:
                assert sample['elapsedSeconds'] - report['stableSamples'][index - 1]['elapsedSeconds'] <= 10
        report['stableObservationSpanSeconds'] = report['stableSamples'][-1]['elapsedSeconds'] - report['stableSamples'][0]['elapsedSeconds']
        assert 60 <= report['stableObservationSpanSeconds'] <= 150
        report['finalSql'] = short.snapshot()
        check_durable(report['finalSql'], [short.BASE, short.CONTEST, short.RECOVERY], 3)
        observed_outcomes = report['firstContendingOutcomes'] + report.get('lateContendingOutcomes', [])
        observed_outcomes += [o for attempt in report['unassistedAttempts'] for o in attempt['outcomes']]
        observed_outcomes += report.get('assistedOutcomes', []) + report['replayConflictNew']
        observed_outcomes += [o for sample in report['stableSamples'] for o in sample['outcomes']]
        for outcome in observed_outcomes:
            short.verify_ack(outcome, report['finalSql'])
        report['catalogAfter'] = [short.client('primary'), short.client('secondary')]
        report['containersAfter'] = expected_containers
        report['status'] = 'PASS'
    except Exception as exc:
        report['error'] = repr(exc)
        raise
    finally:
        report['lastPhase'] = phase
        report['endUtc'] = seed.utc()
        report['siloLogs'] = {n: P('logs', n, check=False)[-18000:]
                              for n in containers if n in ('e2f10-primary', 'e2f10-secondary')}
        if installed:
            report['cleanupRule'] = capture(lambda: short.rule('-D', blocked, peer))
        for n in captures:
            P('wait', n, check=False, timeout=60)
        (OUT / 'long-partition-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': report['status'], 'phase': phase, 'error': report.get('error')}))
        for n in reversed(containers):
            P('rm', '-f', n, check=False, timeout=50)
        if network:
            P('network', 'rm', fx.NETWORK, check=False, timeout=50)


if __name__ == '__main__':
    main()
