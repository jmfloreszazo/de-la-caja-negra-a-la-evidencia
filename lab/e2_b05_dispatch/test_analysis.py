"""Adversarial slot-trace controls; these fixtures are not observed load evidence."""
from copy import deepcopy
import unittest
from analysis import analyze_slots


def fixture():
    offers=[dict(operationId=str(i),phase='warmup',scheduledAtNs=i) for i in range(33)]
    samples=[dict(operationId=str(i),phase='warmup',scheduledAtNs=i,decisionAtNs=i,
        dispatchedAtNs=i if i<32 else None,completedAtNs=100+i if i<32 else None,
        slotReleasedAtNs=200+i if i<32 else None,
        clientOutcome='ACKNOWLEDGED' if i<32 else 'MISSED_OFFER_INFLIGHT_LIMIT') for i in range(33)]
    events=[]
    def add(i,kind,tick,n):
        events.append(dict(sequence=len(events)+1,offerIndex=i,kind=kind,atNs=tick,activeSlots=n))
    for i in range(32): add(i,'ADMIT',i,i+1)
    add(32,'MISS',32,32)
    for i in range(32): add(i,'COMPLETE',100+i,32)
    for i in range(32): add(i,'RELEASE',200+i,31-i)
    return dict(operations=offers),dict(offered=33,maximumInflight=32,npgsqlMaximumPoolSize=32,
        samples=samples,slotEvents=events,missed=1,dispatched=32)


class SlotTests(unittest.TestCase):
    def test_exact_cap_miss_and_separate_release_are_visible(self):
        vector,client=fixture()
        result=analyze_slots(vector,client)
        self.assertEqual(1,result['clientCapMissesObserved'])
        self.assertEqual(32,result['phases']['warmup']['peakActiveSlots'])
        self.assertFalse(result['bottleneckAttributionEstablished'])

    def test_false_miss_missing_release_reordered_event_and_early_decision_fail(self):
        vector,client=fixture()
        variants=[]
        bad=deepcopy(client);bad['slotEvents'][32]['activeSlots']=31;variants.append(bad)
        bad=deepcopy(client);bad['slotEvents'].pop();variants.append(bad)
        bad=deepcopy(client);bad['slotEvents'][33]['sequence']=1;variants.append(bad)
        bad=deepcopy(client);bad['samples'][1]['decisionAtNs']=0;variants.append(bad)
        bad=deepcopy(client);bad['slotEvents'][33]['kind']='RELEASE';variants.append(bad)
        for changed in variants:
            with self.assertRaises(AssertionError):analyze_slots(vector,changed)

    def test_ack_latency_does_not_establish_service_capacity(self):
        vector,client=fixture()
        result=analyze_slots(vector,client)
        self.assertFalse(result['capacityEstablished'])
        self.assertFalse(result['productionServiceP99Established'])


if __name__=='__main__':unittest.main()
