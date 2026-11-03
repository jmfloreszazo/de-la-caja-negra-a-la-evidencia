"""Synthetic negative controls for interpretation, never original E2 evidence."""
import json
import unittest
from observation import PREFIX, analyze, reconcile, validate_generation


def event(session, sequence, tick, kind, **changes):
    return dict(schemaVersion=1, session=session, sequence=sequence, tick=tick,
                kind=kind, node=session, pid=1, bootId='boot', timeNamespace='time:[1]',
                frequency=1000, callId='call', activationId=session, grainId='account/1',
                operationId='id', source=1, target=2, amount=5,
                result='COMMITTED' if kind == 'END' else None, exception=None, **changes)


def log(*events):
    return '\n'.join(PREFIX + json.dumps(e) for e in events)


class ObservationTests(unittest.TestCase):
    def test_generation_requires_readiness_and_matching_event_identity(self):
        e = event('a', 1, 10, 'BEGIN')
        marker = {k: e[k] for k in ('schemaVersion', 'session', 'node', 'pid', 'bootId',
                                   'timeNamespace', 'frequency')}
        ready = 'E2_TRANSFER_OBSERVER_READY:' + json.dumps(marker)
        validate_generation(ready, 'a')  # An idle generation is not financial coverage.
        validate_generation(ready + '\n' + log(e), 'a')
        for raw in (log(e), ready + '\n' + ready,
                    ready + '\n' + log(dict(e, session='other'))):
            with self.assertRaises(AssertionError):
                validate_generation(raw, 'a')

    def pair(self, session, start, end):
        return [event(session, 1, start, 'BEGIN'), event(session, 2, end, 'END')]

    def test_overlap_requires_distinct_activations_same_grain_and_clock(self):
        result = analyze([log(*self.pair('a', 10, 30)), log(*self.pair('b', 20, 40))])
        self.assertEqual(1, len(result['overlappingRequestEnvelopes']))
        self.assertEqual(10, result['overlappingRequestEnvelopes'][0]['overlapTicks'])
        self.assertFalse(result['activationExclusivityEstablished'])

    def test_disjoint_or_touching_envelopes_do_not_prove_exclusivity(self):
        for end in (19, 20):
            result = analyze([log(*self.pair('a', 10, end)), log(*self.pair('b', 20, 40))])
            self.assertEqual([], result['overlappingRequestEnvelopes'])
            self.assertFalse(result['activationExclusivityEstablished'])

    def test_distinct_grains_do_not_count(self):
        other = self.pair('b', 20, 40)
        for e in other:
            e['grainId'] = 'account/2'
        result = analyze([log(*self.pair('a', 10, 30)), log(*other)])
        self.assertEqual([], result['overlappingRequestEnvelopes'])

    def test_incomparable_clocks_and_killed_process_are_explicit(self):
        other = self.pair('b', 20, 40)
        for e in other:
            e['bootId'] = 'another-host'
        result = analyze([log(*self.pair('a', 10, 30)), log(*other),
                          log(event('killed', 1, 10, 'BEGIN'))])
        self.assertEqual(1, result['incomparablePairs'])
        self.assertEqual(1, len(result['incompleteCalls']))
        self.assertEqual('INCOMPLETE', result['coverage'])

    def test_empty_logs_are_incomplete(self):
        self.assertEqual('INCOMPLETE', analyze(['unrelated'])['coverage'])

    def test_truncated_duplicate_reordered_or_changed_events_fail(self):
        good = self.pair('a', 10, 30)
        variants = [[good[1]], [good[0], good[0]], [*good, good[1]]]
        for field, value in [('tick', 9), ('sequence', 3), ('activationId', 'other'),
                             ('amount', 6), ('frequency', 999), ('result', 'UNKNOWN')]:
            changed = dict(good[1], **{field: value})
            variants.append([good[0], changed])
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(AssertionError):
                analyze([log(*variant)])

    def test_ack_and_filter_success_must_match_sql(self):
        analysis = analyze([log(*self.pair('a', 10, 30))])
        state = dict(oracle={str(i): True for i in range(7)},
                     operations=[['id', 1, 2, 5, 'COMMITTED']],
                     effects=dict(committedOperations=1, postings=2, outboxEvents=1))
        ack = dict(status='ACKNOWLEDGED', command=dict(operationId='id', sourceAccountId=1,
                   targetAccountId=2, amountCents=5), result=dict(status='COMMITTED'))
        reconcile(analysis, state, [ack])
        state['operations'][0][3] = 6
        with self.assertRaises(AssertionError):
            reconcile(analysis, state, [ack])
        state['operations'][0][3] = 5
        ack['result']['status'] = 'DUPLICATE_COMMITTED'
        with self.assertRaises(AssertionError):
            reconcile(analysis, state, [ack])

    def test_lost_response_does_not_imply_rollback(self):
        begin = event('a', 1, 10, 'BEGIN')
        error = dict(event('a', 2, 30, 'ERROR'), exception='TimeoutException')
        analysis = analyze([log(begin, error)])
        state = dict(oracle={str(i): True for i in range(7)},
                     operations=[['id', 1, 2, 5, 'COMMITTED']],
                     effects=dict(committedOperations=1, postings=2, outboxEvents=1))
        reconcile(analysis, state, [dict(status='DISPATCH_AMBIGUOUS')])


if __name__ == '__main__':
    unittest.main()
