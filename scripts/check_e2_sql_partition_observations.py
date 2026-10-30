#!/usr/bin/env python3
"""Fail-closed offline audit of the verified E2-F10-C03 original-CI record.

The canonical raw artifact, not this condensed summary, owns the original
network, process and SQL observations. Online CI provenance is verified by
scripts/check_evidence.py --online via the structured claims registry.
"""
import json
from pathlib import Path
import re

record = json.loads((
    Path(__file__).resolve().parents[1] /
    "evidence/runs/e2-orleans-sql-partition.json"
).read_text(encoding="utf-8"))
assert record["schemaVersion"] == 1
assert record["experiment"] == "E2-F10-C03-Live-Secondary-SQL-Partition"
assert record["status"] == "PASS"
assert record["classification"] == (
    "SQL_ONLY_TC_NETEM_CUT_ONE_HOST_NOT_DISTRIBUTED_HA"
)

source = record["provenance"]
assert source["sourceRunId"] == 41136779085
assert source["jobId"] == 124341069078
assert source["headSha"] == "c91959521e7b10934f10f47e30f09496f555056a"
assert source["artifactId"] == 13017097945
assert source["artifactName"] == "e2-f10-c03-original-sql-partition"
assert source["rawFile"] == "e2-f10-c03-sql-partition.json"
assert re.fullmatch(r"[0-9a-f]{64}", source["artifactZipSha256"])
assert source["artifactZipSha256"] == (
    "9d66d1168d311e4363ef333a2707a29310845a60527c9deb2b053355628b28fe"
)
assert str(source["artifactId"]) in source["originalArtifactUrl"]
assert str(source["sourceRunId"]) in source["runUrl"]

v = record["observations"]
assert v["networkNamespaces"] == 4 and v["physicalHosts"] == 1
assert v["privateBridges"] == 2
assert v["injectedMethod"] == (
    "tc qdisc replace dev eth1 root netem loss 100%"
)
assert v["sqlEgressLossPercent"] == 100
assert v["victimHostPidBeforeDuringAfter"] == [4090, 4090, 4090]
assert v["victimStatusBeforeDuringAfter"] == ["running"] * 3
assert v["sameVictimContainerAndNetworks"] is True
assert v["secondarySqlReachableBeforeDuringAfter"] == [True, False, True]
assert v["primarySqlReachableDuring"] is True
assert v["clientSqlReachableDuring"] is True
assert v["appGatewaysReachableBeforeDuringAfter"] is True
assert v["sourceGrainOriginallyOnSecondary"] is True
assert v["actualOrleansRunningActivationDuringFault"] is True
assert v["clientAckedCommitDuringFault"] is False
assert v["clientTimeoutSemantics"] == "AMBIGUOUS_NOT_ROLLBACK_PROOF"
assert v["initialAndDuringFaultEffects"] == {
    "committedOperations": 1, "postings": 2, "outboxEvents": 1
}
assert v["isolatedOperationRowsDuringFault"] == 0
assert v["restoredEffects"] == {
    "committedOperations": 2, "postings": 4, "outboxEvents": 2
}
assert v["isolatedOperationRowsAfterRestoration"] == 1
assert v["stableIdReplay"] == "COMMITTED"
assert v["sqlMembershipBeforeDuringAfter"] == "BOTH_ACTIVE_VERSION_4"

expected_oracles = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees"
}
oracle = v["independentSqlOraclesBeforeDuringAfter"]
assert set(oracle) == expected_oracles
assert all(value is True for value in oracle.values())

limits = record["limitations"].lower()
for explicit_exclusion in (
    "one physical", "non-ha", "symmetric/asymmetric",
    "fencing", "sustained throughput", "mainframe mips"
):
    assert explicit_exclusion in limits, explicit_exclusion

print(
    "E2-F10-C03 ORIGINAL SQL-ONLY PARTITION: PASS "
    "(live silo, 100% SQL cut, running-grain timeout NOT a rollback, "
    "zero in-fault durable effects, one stable-ID COMMIT on recovery, "
    "independent SQL 7/7; no distributed HA claim)"
)
