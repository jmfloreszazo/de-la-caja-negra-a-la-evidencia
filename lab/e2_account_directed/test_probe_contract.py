"""Adversarial witness controls; synthetic fixtures are not original E2 evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'e2_activation_observer'))
from observation import analyze, PREFIX
from probe_contract import find_witness, verify_complete_overlap


def fixture():
    def event(role, activation, kind, tick, sequence):
        return dict(schemaVersion=1,session=role,node='e2f10-'+role,pid=1,
            sequence=sequence,tick=tick,kind=kind,callId=role,activationId=activation,
            grainId='account/2',operationId='c05-contested-id',source=2,target=1,
            amount=31 if role=='secondary' else 37,result=None if kind=='BEGIN' else
            'ID_CONFLICT' if role=='secondary' else 'COMMITTED',exception=None,
            bootId='boot',timeNamespace='time',frequency=1000)
    old=event('secondary','old','BEGIN',10,1)
    new=event('primary','new','BEGIN',20,1)
    old_end=event('secondary','old','END',40,2)
    new_end=event('primary','new','END',30,2)
    gate={k:old[k] for k in ('session','node','pid','callId','activationId','grainId','tick')}
    states={r:dict(id=r,status='running') for r in ('primary','secondary')}
    ids={r:r for r in states}
    return old,new,old_end,new_end,gate,states,ids


def log(*entries):
    return '\n'.join(PREFIX+json.dumps(e) for e in entries)


class WitnessTests(unittest.TestCase):
    def test_live_original_processes_and_complete_overlap(self):
        old,new,old_end,new_end,gate,states,ids=fixture()
        witness=find_witness(log(new),log(old),gate,states,ids)
        self.assertIsNotNone(witness)
        witness['outputRule'] = '-A OUTPUT --ports 11150,11151 -j DROP'
        analysis=analyze([log(old,old_end),log(new,new_end)])
        self.assertEqual(10,verify_complete_overlap(analysis,witness)['overlapTicks'])

    def test_dead_or_recreated_old_process_is_not_a_live_witness(self):
        old,new,_,_,gate,states,ids=fixture()
        for field,value in [('status','exited'),('id','replacement')]:
            changed=deepcopy(states);changed['secondary'][field]=value
            self.assertIsNone(find_witness(log(new),log(old),gate,changed,ids))

    def test_completed_old_call_wrong_key_same_activation_do_not_qualify(self):
        old,new,old_end,_,gate,states,ids=fixture()
        self.assertIsNone(find_witness(log(new),log(old,old_end),gate,states,ids))
        for field,value in [('grainId','account/3'),('activationId','old'),('source',3),
                            ('session','secondary')]:
            bad=dict(new,**{field:value})
            self.assertIsNone(find_witness(log(bad),log(old),gate,states,ids))

    def test_pending_or_failed_end_does_not_establish_complete_overlap(self):
        old,new,old_end,new_end,gate,states,ids=fixture()
        witness=find_witness(log(new),log(old),gate,states,ids)
        incomplete=analyze([log(old),log(new,new_end)])
        with self.assertRaises(AssertionError): verify_complete_overlap(incomplete,witness)
        error=dict(old_end,kind='ERROR',result=None,exception='TimeoutException')
        failed=analyze([log(old,error),log(new,new_end)])
        with self.assertRaises(AssertionError): verify_complete_overlap(failed,witness)


if __name__=='__main__':unittest.main()
