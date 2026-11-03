#!/usr/bin/env python3
"""Preregistered pre-invoke delay plus original one-way 120s fault schedule.

No positive witness is presumed. Complete ordinary-grain overlap and SQL
reconciliation are required; a well-instrumented negative stays INCONCLUSIVE.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'e2_orleans'), str(HERE.parent / 'e2_activation_observer')]
import test_long_partition as experiment
from observation import analyze, reconcile, validate_generation
from probe_contract import events, find_witness, verify_complete_overlap


def main():
    assert os.environ.get('E2_ACCOUNT_DIRECTED_TEST') == '1'
    original_start, original_p = experiment.fx.start, experiment.P
    original_diagnostics, original_rule = experiment.create_diagnostics, experiment.rule
    out = experiment.OUT
    out.mkdir(parents=True, exist_ok=True)
    release = out / 'release-secondary'
    assert not release.exists(), 'Fresh fixture required; stale release marker'
    stop = threading.Event()
    fault_active = threading.Event()
    saved, seen, futures, extra_outcomes, monitor_errors = [], set(), [], [], []
    lock = threading.Lock()
    pool = ThreadPoolExecutor(max_workers=3)
    report = {'status': 'FAIL', 'protocol': 'E2_ACCOUNT_DIRECTED_PRE_INVOKE_GATE_V1',
              'physicalHosts': 1, 'siloHost': 'DirectedSilo', 'logs': saved,
              'activationExclusivityEstablished': False,
              'preInvokeDelayInjected': True, 'monitorErrors': monitor_errors,
              'extraOutcomes': extra_outcomes, 'probeLimitPerWorker': 12}
    monitor = None

    def request(role, amount, label):
        # Unique files prevent the concurrent stock client's role files from
        # overwriting a probe's payload before dispatch.
        path = out / ('directed-' + uuid.uuid4().hex + '.json')
        command = experiment.short.command(experiment.short.CONTEST, 2, 1, amount)
        path.write_text(json.dumps({'route': 'orleans', 'concurrent': False, 'commands': [command]}) + '\n')
        result = subprocess.run(['podman', 'exec', '-e', 'E2_C05_TEST=1', 'e2f10-client',
            'dotnet', '/app/OrleansLab.dll', 'cluster', 'client', 'partition-probe', role,
            '/fixtures/c05-c06/' + path.name], capture_output=True, text=True, timeout=55)
        observed = {'label': label, 'gateway': role, 'returncode': result.returncode,
                    'stdout': result.stdout, 'stderr': result.stderr}
        with lock:
            extra_outcomes.append(observed)
        assert result.returncode == 0, observed
        outcome = json.loads(result.stdout)
        assert outcome['gateway'] == role and outcome['placementHintsUsed'] is False
        assert outcome['status'] in ('ACKNOWLEDGED', 'STARTUP_UNAVAILABLE', 'DISPATCH_AMBIGUOUS')
        observed['outcome'] = outcome
        return outcome

    def probe_worker(index):
        for attempt in range(12):
            if stop.is_set():
                break
            request('primary', 37, 'probe-' + str(index) + '-' + str(attempt))
            if stop.wait(2):
                break

    def start(name, *command, **kwargs):
        if name in ('e2f10-primary', 'e2f10-secondary'):
            assert command == ('--entrypoint', 'dotnet', experiment.fx.IMAGE,
                               '/app/OrleansLab.dll', 'cluster', 'silo', name.removeprefix('e2f10-'))
            command = ('-e', 'E2_ACTIVATION_OBSERVATION_TEST=1',
                       '-e', 'E2_ACCOUNT_DIRECTED_TEST=1', '-v', str(out.resolve()) + ':/probe',
                       *command[:3], '/app/DirectedSilo.dll', *command[4:])
        return original_start(name, *command, **kwargs)

    def preserve(name):
        inspected = json.loads(original_p('inspect', name))
        assert len(inspected) == 1
        identity = inspected[0]['Id']
        if identity in seen:
            return
        raw = original_p('logs', name)
        path = out / ('directed-' + name + '-' + str(len(saved)) + '.log')
        path.write_text(raw + '\n')
        saved.append({'containerId': identity, 'node': name, 'file': path.name,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        seen.add(identity)

    def finish_probes():
        stop.set()
        release.touch()
        if monitor is not None:
            monitor.join(timeout=50)
            assert not monitor.is_alive(), 'Monitor failed to stop'
        for future in futures:
            future.result(timeout=60)

    def command(*args, **kwargs):
        try:
            if args and args[0] == 'rm':
                for name in args[1:]:
                    if name in ('e2f10-primary', 'e2f10-secondary'):
                        finish_probes()
                        preserve(name)
        finally:
            result = original_p(*args, **kwargs)
        return result

    def diagnostics(containers, parent_report, phase):
        original_diagnostics(containers, parent_report, phase)
        if phase != 'before-fault':
            return
        report['originalProcesses'] = {r: experiment.net.inspect('e2f10-' + r)
                                        for r in ('primary', 'secondary')}
        futures.append(pool.submit(request, 'secondary', 31, 'held-before-fault'))
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            raw = original_p('logs', 'e2f10-secondary')
            markers = events(raw, 'E2_ACCOUNT_GATE_WAIT:')
            if markers:
                assert len(markers) == 1
                report['oldGate'] = markers[0]
                return
            time.sleep(.1)
        raise AssertionError('Old ordinary-grain request did not reach the pre-invoke gate')

    def watch():
        try:
            original_ids = {r: s['id'] for r, s in report['originalProcesses'].items()}
            deadline = time.monotonic() + 130
            while not stop.is_set() and time.monotonic() < deadline:
                states = {r: experiment.net.inspect('e2f10-' + r) for r in ('primary', 'secondary')}
                primary = original_p('logs', 'e2f10-primary')
                secondary = original_p('logs', 'e2f10-secondary')
                witness = find_witness(primary, secondary, report['oldGate'], states, original_ids)
                if witness is not None:
                    output_rule = experiment.rules(report['faultBlockedContainer'])
                    if not fault_active.is_set() or '--ports 11150,11151 -j DROP' not in output_rule:
                        continue
                    witness['outputRule'] = output_rule
                    witness['observedUtc'] = experiment.seed.utc()
                    report['liveWitness'] = witness
                    release.touch()
                    return
                if stop.wait(.5):
                    break
        except Exception as error:
            monitor_errors.append(repr(error))
            release.touch()

    def rule(action, blocked, peer):
        nonlocal monitor
        if action == '-D':
            fault_active.clear()
            stop.set()
            release.touch()
            if monitor is not None:
                monitor.join(timeout=50)
                assert not monitor.is_alive(), 'Monitor failed to stop before namespace restoration'
        result = original_rule(action, blocked, peer)
        if action == '-A':
            report['faultBlockedContainer'] = blocked
            fault_active.set()
            report['faultRuleAppliedUtc'] = experiment.seed.utc()
            monitor = threading.Thread(target=watch, name='ordinary-grain-witness', daemon=True)
            monitor.start()
            futures.extend(pool.submit(probe_worker, i) for i in range(2))
        elif action == '-D':
            stop.set()
            release.touch()
        return result

    experiment.fx.start, experiment.P = start, command
    experiment.create_diagnostics, experiment.rule = diagnostics, rule
    try:
        experiment.main()
        finish_probes()
        assert not monitor_errors, monitor_errors
        schedule = json.loads((out / 'long-partition-summary.json').read_text())
        assert schedule['status'] == 'PASS'
        report['sourceHeadSha'] = schedule['sourceHeadSha']
        report['blockedRole'] = schedule['blockedRole']
        logs = [(out / item['file']).read_text() for item in saved]
        assert {item['node'] for item in saved} == {'e2f10-primary', 'e2f10-secondary'}
        report['generations'] = [validate_generation(raw, item['node']) for raw, item in zip(logs, saved)]
        assert len({m['session'] for m in report['generations']}) == len(saved)
        analysis = analyze(logs)
        report['observation'] = analysis
        acks = [schedule['baselineAck']] + schedule['firstContendingOutcomes'] + schedule['lateContendingOutcomes']
        acks += [o for a in schedule['unassistedAttempts'] for o in a['outcomes']]
        acks += schedule.get('assistedOutcomes', []) + schedule['replayConflictNew']
        acks += [o for s in schedule['stableSamples'] for o in s['outcomes']]
        acks += [o['outcome'] for o in extra_outcomes]
        reconcile(analysis, schedule['finalSql'], acks)
        report['sqlAndAcknowledgementsReconciled'] = True
        if 'liveWitness' in report:
            report['completeWitness'] = verify_complete_overlap(analysis, report['liveWitness'])
            report['status'] = 'PASS_DIRECTED_REQUEST_OVERLAP'
        else:
            report['status'] = 'INCONCLUSIVE_NO_LIVE_OVERLAP'
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        stop.set()
        release.touch()
        if monitor is not None:
            monitor.join(timeout=50)
            if monitor.is_alive():
                report["status"] = "FAIL"
                report["error"] = "Monitor remained alive during final cleanup"
        pool.shutdown(wait=True)
        experiment.fx.start, experiment.P = original_start, original_p
        experiment.create_diagnostics, experiment.rule = original_diagnostics, original_rule
        (out / 'account-directed-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': report['status'], 'error': report.get('error')}))
    if report['status'] != 'PASS_DIRECTED_REQUEST_OVERLAP':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
