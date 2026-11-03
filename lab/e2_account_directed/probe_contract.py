"""Bounded witnesses for ordinary AccountGrain request envelopes, not lifecycle census."""
import json

PREFIX = 'E2_TRANSFER_OBSERVER:'


def events(raw, prefix=PREFIX):
    return [json.loads(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]


def find_witness(primary_raw, secondary_raw, old_gate, states, original_ids):
    # Original processes must still be running. Replacement processes after
    # assisted recovery cannot supply the requested in-fault witness.
    if any(states[r]['status'] != 'running' or states[r]['id'] != original_ids[r]
           for r in ('primary', 'secondary')):
        return None
    if any(e['callId'] == old_gate['callId'] and e['kind'] != 'BEGIN'
           for e in events(secondary_raw)):
        return None
    for e in events(primary_raw):
        if (e['kind'] == 'BEGIN' and e['operationId'] == 'c05-contested-id'
                and e['source'] == 2 and e['target'] == 1 and e['amount'] in (31, 37)
                and e['grainId'] == old_gate['grainId']
                and e['activationId'] != old_gate['activationId']
                and e['session'] != old_gate['session']):
            return {'oldGate': old_gate, 'newBegin': e, 'processes': states}
    return None


def verify_complete_overlap(analysis, witness):
    old, new = witness['oldGate'], witness['newBegin']
    wanted = [(old['session'], old['callId']), (new['session'], new['callId'])]
    pairs = []
    for key in wanted:
        found = [c for c in analysis['completeCalls']
                 if (c['begin']['session'], c['begin']['callId']) == key]
        assert len(found) == 1, 'Witness has no complete request envelope'
        assert found[0]['end']['kind'] == 'END', 'Witness ended with an exception'
        pairs.append(found[0])
    assert pairs[0]['begin']['node'] == 'e2f10-secondary'
    assert pairs[1]['begin']['node'] == 'e2f10-primary'
    assert pairs[0]['begin']['grainId'] == pairs[1]['begin']['grainId']
    assert pairs[0]['begin']['activationId'] != pairs[1]['begin']['activationId']
    assert all(pairs[0]['begin'][k] == pairs[1]['begin'][k]
               for k in ('bootId', 'timeNamespace', 'frequency'))
    start = max(p['begin']['tick'] for p in pairs)
    end = min(p['end']['tick'] for p in pairs)
    assert start < end, 'Witness requests do not overlap'
    assert any({tuple(o['left']), tuple(o['right'])} == set(wanted)
               for o in analysis['overlappingRequestEnvelopes'])
    assert '--ports 11150,11151 -j DROP' in witness.get('outputRule', '')
    return {'overlapTicks': end - start, 'frequency': pairs[0]['begin']['frequency'],
            'oldResult': pairs[0]['end']['result'], 'newResult': pairs[1]['end']['result']}
