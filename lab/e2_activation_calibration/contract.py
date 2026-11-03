"""Calibration acceptance. Synthetic tests are not original activation evidence."""
from observation import analyze, validate_generation, reconcile

def accept(raw, node, positive):
    validate_generation(raw, node)
    observed = analyze([raw])
    assert observed['incompleteCalls'] == [] and observed['incomparablePairs'] == 0
    calls = observed['completeCalls']
    if not positive:
        assert len(calls) == 1 and calls[0]['end']['kind'] == 'ERROR'
        assert calls[0]['end']['exception'] == 'System.TimeoutException'
        assert observed['overlappingRequestEnvelopes'] == []
        return observed
    # The first pair alone must supply the witness; later replay cannot rescue it.
    assert len(calls) == 4
    first = calls[:2]
    assert {c['begin']['amount'] for c in first} == {31, 37}
    assert len({c['begin']['activationId'] for c in first}) == 2
    assert len({c['begin']['grainId'] for c in first}) == 1
    assert len({c['begin']['operationId'] for c in first}) == 1
    assert all(c['begin']['source'] == 1 and c['begin']['target'] == 2 for c in calls)
    assert sorted(c['end']['result'] for c in first) == ['COMMITTED', 'ID_CONFLICT']
    assert max(c['begin']['tick'] for c in first) < min(c['end']['tick'] for c in first)
    assert len(observed['overlappingRequestEnvelopes']) >= 1
    assert [c['end']['result'] for c in calls[2:]] == ['DUPLICATE_COMMITTED', 'ID_CONFLICT']
    return observed
