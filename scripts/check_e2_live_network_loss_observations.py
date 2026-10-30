#!/usr/bin/env python3
"""Fail-closed offline validation of the E2-F10-C02 original-CI summary.

This transcribed record references a genuine, ZIP-SHA-pinned original
GitHub Actions artifact. The raw artifact is the authoritative source;
this checker cannot replace the independent CI source-run validation.
"""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
record = json.loads(
    (root / "evidence/runs/e2-orleans-live-network-loss.json").read_text(
        encoding="utf-8"
    )
)
assert record["schemaVersion"] == 1
assert record["experiment"] == "E2-F10-C02-Real-Live-Silo-100Percent-Packet-Loss"
assert record["status"] == "PASS"
assert record["classification"] == (
    "TC_NETEM_LIVE_SILO_APP_EGRESS_DROP_SQL_PRESERVED_SINGLE_HOST"
)
provenance = record["provenance"]
assert provenance["sourceRunId"] == 41132190043
assert provenance["jobId"] == 124325598055
assert provenance["artifactId"] == 13013089253
assert provenance["rawFile"] == "e2-f10-c02-packet-loss.json"
assert re.fullmatch("[a-f0-9]{40}", provenance["headSha"])
assert re.fullmatch("[a-f0-9]{64}", provenance["artifactZipSha256"])
assert str(provenance["sourceRunId"]) in provenance["runUrl"]
assert str(provenance["artifactId"]) in provenance["originalArtifactUrl"]

v = record["observations"]
assert v["distinctNetworkNamespaces"] == 4
assert v["privateBridgeCount"] == 2
assert v["faultEgressLossPercent"] == 100
assert v["faultMethod"] == "tc qdisc replace dev eth0 root netem loss 100%"
assert v["qdiscDuringHasLoss100Percent"] is True
assert v["qdiscBefore"] == v["qdiscAfter"]
assert "noqueue" in v["qdiscAfter"]
assert len(v["victimHostPidBeforeDuringAfter"]) == 3
assert len(set(v["victimHostPidBeforeDuringAfter"])) == 1
assert all(pid > 0 for pid in v["victimHostPidBeforeDuringAfter"])
assert v["victimStateBeforeDuringAfter"] == ["running"] * 3
assert v["victimContainerIdUnchanged"] is True
assert v["victimNetworksUnchanged"] is True
assert v["sqlBridgeAvailableDuringFault"] is True
assert v["tcpExternalClientBefore"] == {"primary": True, "secondary": True}
assert v["tcpExternalClientDuring"] == {"primary": True, "secondary": False}
assert v["tcpExternalClientAfter"] == {"primary": True, "secondary": True}
assert v["membershipStatusesBeforeDuringAfter"] == {
    "primary": 3, "secondary": 3, "version": 4
}
assert v["businessEffectsBeforeDuringAfter"] == {
    "committedOperations": 1, "postings": 2, "outboxEvents": 1
}
expected_oracle_keys = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees"
}
assert set(v["independentSqlOraclesBeforeDuringAfter"]) == expected_oracle_keys
assert all(x is True for x in
           v["independentSqlOraclesBeforeDuringAfter"].values())
assert v["orleansApplicationConvergence"] == "NOT_TESTED"
assert v["externalFinancialCommandsDuringFault"] == 0

negative = record["negativeControl"]
assert negative["originalRunId"] == 41131370049
assert negative["originalArtifactId"] == 13012863038
assert "stopped" in negative["observed"]
limits = record["limitations"].casefold()
for excluded in ("one physical", "no banking commands",
                 "grain convergence", "fencing", "mainframe"):
    assert excluded in limits, excluded

print(
    "E2-F10-C02 ORIGINAL NETWORK LOSS: PASS "
    "(tc/netem real 100%, same live silo, SQL preserved, 7/7; "
    "no in-fault business writes or physical HA proof)"
)
