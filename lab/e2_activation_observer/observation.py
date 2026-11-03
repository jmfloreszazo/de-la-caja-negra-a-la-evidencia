"""Strict offline interpretation of disposable incoming-call observer logs.

Overlapping envelopes are not simultaneous SQL transactions, lifecycle overlap,
global activation exclusivity, continuous availability or physical resilience.
"""
import json

PREFIX = 'E2_TRANSFER_OBSERVER:'
IDENTITY = ('session', 'node', 'pid', 'bootId', 'timeNamespace', 'frequency',
            'callId', 'activationId', 'grainId', 'operationId', 'source', 'target', 'amount')


def validate_generation(raw, node):
    ready_prefix = 'E2_TRANSFER_OBSERVER_READY:'
    markers = [json.loads(line[len(ready_prefix):]) for line in raw.splitlines()
               if line.startswith(ready_prefix)]
    assert len(markers) == 1, 'Missing or duplicate observer readiness'
    marker = markers[0]
    assert marker['schemaVersion'] == 1 and marker['node'] == node
    for k in ('session', 'bootId', 'timeNamespace'):
        assert isinstance(marker[k], str) and marker[k]
    for k in ('pid', 'frequency'):
        assert type(marker[k]) is int and marker[k] > 0
    for line in raw.splitlines():
        if line.startswith(PREFIX):
            event = json.loads(line[len(PREFIX):])
            assert all(event[k] == marker[k] for k in
                       ('session', 'node', 'pid', 'bootId', 'timeNamespace', 'frequency'))
    return marker


def analyze(logs):
    sessions, calls, completed, incomplete = {}, {}, [], []
    for log in logs:
        for line in log.splitlines():
            if not line.startswith(PREFIX):
                continue
            e = json.loads(line[len(PREFIX):])
            assert e['schemaVersion'] == 1 and e['kind'] in ('BEGIN', 'END', 'ERROR'), e
            assert all(e[k] is not None for k in IDENTITY), e
            assert all(isinstance(e[k], str) and e[k] for k in
                       ('session', 'node', 'bootId', 'timeNamespace', 'callId',
                        'activationId', 'grainId', 'operationId')), e
            assert all(type(e[k]) is int and e[k] > 0 for k in
                       ('pid', 'frequency', 'tick', 'sequence', 'source', 'target', 'amount')), e
            previous = sessions.get(e['session'])
            if previous is None:
                assert e['sequence'] == 1, 'Log starts after the first event'
            else:
                assert e['sequence'] == previous['sequence'] + 1, 'Missing/duplicate event'
                assert e['tick'] >= previous['tick'], 'Non-monotonic event clock'
                assert all(e[k] == previous[k] for k in
                           ('node', 'pid', 'bootId', 'timeNamespace', 'frequency')), e
            sessions[e['session']] = e
            key = (e['session'], e['callId'])
            if e['kind'] == 'BEGIN':
                assert key not in calls, 'Duplicate call BEGIN'
                assert e['result'] is None and e['exception'] is None
                calls[key] = [e, None]
            else:
                assert key in calls and calls[key][1] is None, 'Orphan/duplicate call end'
                begin = calls[key][0]
                assert all(begin[k] == e[k] for k in IDENTITY), 'Call identity changed'
                if e['kind'] == 'END':
                    assert e['result'] in ('COMMITTED', 'DUPLICATE_COMMITTED', 'ID_CONFLICT')
                    assert e['exception'] is None
                else:
                    assert e['result'] is None and isinstance(e['exception'], str) and e['exception']
                calls[key][1] = e
    for begin, end in calls.values():
        if end is None:
            incomplete.append(begin)
        else:
            completed.append({'begin': begin, 'end': end})
    overlaps, incomparable = [], 0
    for i, left in enumerate(completed):
        a = left['begin']
        for right in completed[i + 1:]:
            b = right['begin']
            if a['grainId'] != b['grainId'] or (
                a['session'], a['activationId']) == (b['session'], b['activationId']):
                continue
            if not all(a[k] == b[k] for k in ('bootId', 'timeNamespace', 'frequency')):
                incomparable += 1
                continue
            start = max(a['tick'], b['tick'])
            end = min(left['end']['tick'], right['end']['tick'])
            if start < end:
                overlaps.append({'left': [a['session'], a['callId']],
                                 'right': [b['session'], b['callId']],
                                 'grainId': a['grainId'], 'overlapTicks': end - start})
    return {'events': sum(e['sequence'] for e in sessions.values()),
            'sessions': len(sessions), 'completeCalls': completed, 'incompleteCalls': incomplete,
            'overlappingRequestEnvelopes': overlaps, 'incomparablePairs': incomparable,
            'interpretation': ('OVERLAPPING_REQUEST_ENVELOPES_OBSERVED' if overlaps else
                               'NO_OVERLAP_IN_COMPLETE_COMPARABLE_REQUEST_ENVELOPES'),
            'coverage': 'INCOMPLETE' if incomplete or incomparable or not completed else 'RECORDED_CALLS_ONLY',
            'activationExclusivityEstablished': False}


def reconcile(analysis, state, acknowledgements):
    """Independent SQL snapshot and client ACKs remain the financial authority."""
    assert len(state['oracle']) == 7 and all(v is True for v in state['oracle'].values())
    rows = {r[0]: r for r in state['operations']}
    assert len(rows) == len(state['operations'])
    count = len(rows)
    assert state['effects'] == dict(committedOperations=count, postings=2 * count, outboxEvents=count)
    ends = analysis['completeCalls']
    assert ends, 'No observed financial calls'
    for pair in ends:
        e = pair['end']
        if e['kind'] == 'ERROR':
            continue  # An exception does not prove a rollback.
        assert e['operationId'] in rows, ('Observed success absent from SQL', e)
        row = rows[e['operationId']]
        same = row[1:4] == [e['source'], e['target'], e['amount']]
        assert row[4] == 'COMMITTED' and ((e['result'] == 'ID_CONFLICT') is (not same))
    for ack in acknowledgements:
        if ack['status'] != 'ACKNOWLEDGED':
            continue
        c = ack['command']
        assert any(p['end']['kind'] == 'END' and
                   [p['end'][k] for k in ('operationId', 'source', 'target', 'amount', 'result')] ==
                   [c['operationId'], c['sourceAccountId'], c['targetAccountId'], c['amountCents'],
                    ack['result']['status']] for p in ends), 'ACK has no observed completed call'
