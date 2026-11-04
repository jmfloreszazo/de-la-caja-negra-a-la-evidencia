"""Pure independent interpretation of persisted SQL and transport observations."""


def evaluate(case):
    errors=[]
    def check(condition,message):
        if not condition:errors.append(message)
    mode=case['direction'];reverse='SERVER_TO_CLIENT' if mode=='CLIENT_TO_SERVER' else 'CLIENT_TO_SERVER'
    check(mode in ('CLIENT_TO_SERVER','SERVER_TO_CLIENT'),'Unknown fault direction')
    check(case['beforeCounts']==[0,0,0],'Unexpected precommit decision')
    observed=case['silentObservation']
    check(observed['droppedBytes'][mode]>0 and observed['droppedBytes'][reverse]==0,'Directional suppression not observed')
    check(observed['activeConnections']>=1 and bool(case['controllerPidsDuringFault']),'Silent fault lost all controller sessions')
    check(not case['probeExitedDuringFault'],'Live probe did not remain unresolved')
    check(case['probeQueryObservedAtServer']==(mode=='SERVER_TO_CLIENT'),'Query reception contradicts fault direction')
    check(case['blockedReconnectExit']!=0 and case['switchAttemptExit']!=0,'Unreachable controller accepted a command')
    check(case['controllerAuthorityUnchanged'],'Authority changed during suppression')
    check(case['financialCountsWhileSuppressed']==[1,2,1],'Separate financial COMMIT not observed')
    check(case['finalCounts']==[1,2,1] and case['reconciledStatus']=='COMMITTED' and case['replayStatus']=='DUPLICATE_COMMITTED','Final decision/replay mismatch')
    check(all(case['sourceOracle'].values()) and all(case['targetOracle'].values()) and case['journalAuditPassed'],'Persisted SQL oracle failed')
    check(case['recoveryIntervention']=='CONTROLLED_SOCKET_RESET','Recovery intervention misclassified')
    return errors
