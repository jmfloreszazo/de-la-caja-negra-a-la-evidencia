#!/usr/bin/env python3
"""Adapt the fixed long-schedule fixture to a separate, instrumented silo host.

Capture full logs before every target removal, including assisted recreation.
Do not modify the original harness, financial implementation or oracle.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'e2_orleans'))
import test_long_partition as experiment
from observation import analyze, reconcile, validate_generation


def main():
    assert os.environ.get('E2_ACTIVATION_OBSERVATION_TEST') == '1'
    original_start, original_p = experiment.fx.start, experiment.P
    saved, containers_seen = [], set()
    out = experiment.OUT
    report = {'status': 'FAIL', 'protocol': 'E2_TRANSFER_ENVELOPES_V1',
              'activationExclusivityEstablished': False, 'logs': saved}

    def start(name, *command, **kwargs):
        if name in ('e2f10-primary', 'e2f10-secondary'):
            assert command == ('--entrypoint', 'dotnet', experiment.fx.IMAGE,
                               '/app/OrleansLab.dll', 'cluster', 'silo', name.removeprefix('e2f10-'))
            command = ('-e', 'E2_ACTIVATION_OBSERVATION_TEST=1', *command[:3],
                       '/app/ObservedSilo.dll', *command[4:])
        return original_start(name, *command, **kwargs)

    def preserve(name):
        inspected = json.loads(original_p('inspect', name))
        assert len(inspected) == 1
        identity = inspected[0]['Id']
        if identity in containers_seen:
            return
        raw = original_p('logs', name)
        path = out / ('activation-' + name + '-' + str(len(saved)) + '.log')
        path.write_text(raw + '\n')
        saved.append({'containerId': identity, 'node': name, 'file': path.name,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        containers_seen.add(identity)

    def command(*args, **kwargs):
        try:
            if args and args[0] == 'rm':
                for name in args[1:]:
                    if name in ('e2f10-primary', 'e2f10-secondary'):
                        preserve(name)
        finally:
            # A failed log capture must not suppress resource cleanup.
            result = original_p(*args, **kwargs)
        return result

    experiment.fx.start, experiment.P = start, command
    try:
        experiment.main()
        schedule = json.loads((out / 'long-partition-summary.json').read_text())
        assert schedule['status'] == 'PASS'
        report['sourceHeadSha'] = schedule['sourceHeadSha']
        report['blockedRole'] = schedule['blockedRole']
        report['financialHost'] = 'ObservedSilo; referenced unmodified AccountGrain and PgDurableLedger'
        logs = [(out / item['file']).read_text() for item in saved]
        assert {item['node'] for item in saved} == {'e2f10-primary', 'e2f10-secondary'}
        # A recovered generation can receive no financial calls: validate its
        # readiness without inventing coverage. Every observed ACK still needs
        # a real completed call somewhere in the complete retained log set.
        report['generations'] = [validate_generation(raw, item['node'])
                                 for raw, item in zip(logs, saved)]
        assert len({m['session'] for m in report['generations']}) == len(saved)
        analysis = analyze(logs)
        report['observation'] = analysis
        acknowledgements = [schedule['baselineAck']]
        acknowledgements += schedule['firstContendingOutcomes'] + schedule['lateContendingOutcomes']
        acknowledgements += [o for a in schedule['unassistedAttempts'] for o in a['outcomes']]
        acknowledgements += schedule.get('assistedOutcomes', []) + schedule['replayConflictNew']
        acknowledgements += [o for s in schedule['stableSamples'] for o in s['outcomes']]
        reconcile(analysis, schedule['finalSql'], acknowledgements)
        report['sqlAndAcknowledgementsReconciled'] = True
        report['status'] = 'PASS_OBSERVATION_ONLY'
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        experiment.fx.start, experiment.P = original_start, original_p
        (out / 'activation-observation-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'status': report['status'], 'error': report.get('error')}))


if __name__ == '__main__':
    main()
