"""Adversarial calibration controls; no synthetic fixture is original evidence."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'e2_activation_observer'))
from contract import accept
from observation import PREFIX

def fixture():
    events = []
    for seq, call, activation, tick, kind, amount, result in [
        (1,'a','one',10,'BEGIN',31,None), (2,'b','two',20,'BEGIN',37,None),
        (3,'a','one',30,'END',31,'COMMITTED'), (4,'b','two',40,'END',37,'ID_CONFLICT'),
        (5,'c','one',50,'BEGIN',31,None), (6,'c','one',60,'END',31,'DUPLICATE_COMMITTED'),
        (7,'d','one',70,'BEGIN',37,None), (8,'d','one',80,'END',37,'ID_CONFLICT')]:
        events.append(dict(schemaVersion=1, session='session', sequence=seq, tick=tick,
            kind=kind,node='node',pid=1,bootId='boot',timeNamespace='time',frequency=1000,
            callId=call,activationId=activation,grainId='calibration/1',
            operationId='e2-observer-calibration',source=1,target=2,amount=amount,
            result=result,exception=None))
    return events

def raw(events):
    ready=dict(schemaVersion=1,session='session',node='node',pid=1,
               bootId='boot',timeNamespace='time',frequency=1000)
    return 'E2_TRANSFER_OBSERVER_READY:'+json.dumps(ready)+'\n'+'\n'.join(PREFIX+json.dumps(e) for e in events)

class CalibrationContractTests(unittest.TestCase):
    def test_true_positive_control_requires_first_pair_overlap(self):
        result=accept(raw(fixture()),'node',True)
        self.assertEqual(1,len(result['overlappingRequestEnvelopes']))
        self.assertFalse(result['activationExclusivityEstablished'])

    def test_same_activation_missing_event_wrong_winner_or_no_overlap_fail(self):
        cases=[]
        same=fixture()
        for e in same: e['activationId']='one'
        cases.append(same)
        missing=fixture(); missing.pop(2); cases.append(missing)
        conflict=fixture(); conflict[3]['result']='COMMITTED'; cases.append(conflict)
        serial=fixture()
        for e in serial:
            if e['callId']=='b': e['tick']+=25
        # Keep event sequence monotonic for the non-overlap counterexample.
        serial=sorted(serial,key=lambda e:e['tick'])
        for i,e in enumerate(serial): e['sequence']=i+1
        cases.append(serial)
        for events in cases:
            with self.subTest(events=events),self.assertRaises(AssertionError):
                accept(raw(events),'node',True)

    def test_expected_single_request_timeout_is_sensitive_negative(self):
        events=fixture()[:1]
        end=dict(events[0],sequence=2,tick=30,kind='ERROR',exception='System.TimeoutException')
        accept(raw(events+[end]),'node',False)
        end['kind']='END';end['exception']=None;end['result']='COMMITTED'
        with self.assertRaises(AssertionError): accept(raw(events+[end]),'node',False)

if __name__ == '__main__': unittest.main()
