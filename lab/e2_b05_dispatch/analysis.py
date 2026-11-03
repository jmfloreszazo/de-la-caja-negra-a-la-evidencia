"""Reconstruct exact client slot accounting, without inferring a DB bottleneck."""
from collections import Counter


def percentiles(values):
    if not values:
        return None
    data=sorted(values)
    def p(q):
        rank=(len(data)-1)*q
        low=int(rank)
        return round(data[low]+(data[min(low+1,len(data)-1)]-data[low])*(rank-low),6)
    return dict(p50=p(.5),p95=p(.95),p99=p(.99),max=data[-1])


def analyze_slots(vector,client):
    offers,samples=vector['operations'],client['samples']
    assert len(samples)==len(offers)==client['offered']
    cap=client['maximumInflight']
    assert cap in (32,128) and client['npgsqlMaximumPoolSize']==32
    states={}
    active=0
    last_tick=-1
    phase_counts={p:Counter() for p in ('warmup','measurement','cooldown')}
    peaks=Counter()
    for sequence,event in enumerate(client['slotEvents'],1):
        assert event['sequence']==sequence
        index,kind,tick=event['offerIndex'],event['kind'],event['atNs']
        assert type(index) is int and 0<=index<len(offers)
        assert type(tick) is int and tick>=last_tick
        last_tick=tick
        offer,sample=offers[index],samples[index]
        phase=offer['phase']
        assert sample['operationId']==offer['operationId']
        assert sample['phase']==phase and sample['scheduledAtNs']==offer['scheduledAtNs']
        if kind in ('ADMIT','MISS'):
            assert index not in states
            assert tick==sample['decisionAtNs']>=offer['scheduledAtNs']
            if kind=='ADMIT':
                assert active<cap and sample['dispatchedAtNs']==tick
                active+=1
                states[index]='admitted'
            else:
                assert active==cap, 'Miss without an observed full client cap'
                assert sample['clientOutcome']=='MISSED_OFFER_INFLIGHT_LIMIT'
                assert sample['dispatchedAtNs'] is sample['completedAtNs'] is sample['slotReleasedAtNs'] is None
                states[index]='missed'
            phase_counts[phase][kind]+=1
        elif kind=='COMPLETE':
            assert states.get(index)=='admitted'
            assert tick==sample['completedAtNs']>=sample['dispatchedAtNs']
            assert sample['clientOutcome'] in ('ACKNOWLEDGED','AMBIGUOUS_EXCEPTION')
            states[index]='completed'
            phase_counts[phase][sample['clientOutcome']]+=1
        elif kind=='RELEASE':
            assert states.get(index)=='completed'
            assert tick==sample['slotReleasedAtNs']>=sample['completedAtNs']
            active-=1
            states[index]='released'
        else:
            raise AssertionError('Unknown client slot event: '+kind)
        assert 0<=active<=cap and event['activeSlots']==active
        if kind in ('ADMIT','MISS'):
            peaks[phase]=max(peaks[phase],active)
    assert active==0 and len(states)==len(offers)
    assert all(value in ('released','missed') for value in states.values())
    assert sum(value=='missed' for value in states.values())==client['missed']
    assert sum(value=='released' for value in states.values())==client['dispatched']
    phases={}
    for phase in phase_counts:
        rows=[s for s in samples if s['phase']==phase]
        phases[phase]=dict(offered=len(rows),counts=dict(phase_counts[phase]),
            peakActiveSlots=peaks[phase],
            allOfferDecisionLagMs=percentiles([(s['decisionAtNs']-s['scheduledAtNs'])/1e6 for s in rows]),
            completeToReleaseMs=percentiles([(s['slotReleasedAtNs']-s['completedAtNs'])/1e6
                for s in rows if s['completedAtNs'] is not None]))
    return dict(status='SLOT_ACCOUNTING_RECONCILED',phases=phases,
        clientCapMissesObserved=client['missed'],capacityEstablished=False,
        bottleneckAttributionEstablished=False,productionServiceP99Established=False,
        limitation='Slot misses are exact client-cap observations; their upstream cause and DB capacity are not established.')
