#!/usr/bin/env python3
"""Audit original C04 bytes and bounded claims; do not infer overall E2 PASS."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "evidence/runs"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def original(stem, digest, member):
    data = (RUNS / (stem + ".zip")).read_bytes()
    require(hashlib.sha256(data).hexdigest() == digest, "Original ZIP changed: " + stem)
    with zipfile.ZipFile(RUNS / (stem + ".zip")) as archive:
        raw = archive.read(member)
        require(raw == (RUNS / (stem + ".json")).read_bytes(), "Extracted original JSON changed")
        return json.loads(raw), archive.read("provenance.txt").decode()


def main():
    result, provenance = original(
        "e2-c04-gateway-original",
        "ea12b2363746504e2cf3fb3095ae361156a7844435938ec3aa2951e7a840a702",
        "e2-f10-c04-client-gateway.json")
    source = "434170ac03f63925b517992d744aae531eb38965"
    require("source_head_sha=" + source in provenance, "Wrong original source")
    require("checkout_sha=" + source in provenance, "Wrong original checkout")
    failed, negative_provenance = original(
        "e2-c04-first-failure-original",
        "b549005b14e72bd10a1a6a795f366756a3a85ea34b9b3fe1162bbeb3501019f7",
        "e2-f10-c04-failure.json")
    require(failed["status"] == "FAIL" and failed["stage"] == "both-client-gateways-blocked",
            "First failure must remain a failure")
    require("934d6e226c300850a88c070eb633af3fe31bc562" in negative_provenance,
            "Wrong first-failure source")
    require(result["status"] == "PASS", "Original C04 did not pass")
    topology = result["topology"]
    require(topology["physicalHostCount"] == 1, "Do not promote physical HA")
    require(len(set(topology["namespaces"].values())) == 4, "Missing independent namespaces")
    before = topology["containerStatesBefore"]
    for phase in ("containerStatesDuring", "containerStatesAfter"):
        for name, state in topology[phase].items():
            require(state["id"] == before[name]["id"] and
                    state["pidOnHost"] == before[name]["pidOnHost"] and
                    state["status"] == "running", "Fault changed a container/process")
    for key, primary, secondary in (("clientNetworkInitial", True, True),
                                    ("clientNetworkSingleCut", False, True),
                                    ("clientNetworkBothCut", False, False),
                                    ("clientNetworkFullyRestored", True, True)):
        probe = result[key]
        require(probe["databaseHealthy"] is True and
                probe["primaryGatewayReachable"] is primary and
                probe["secondaryGatewayReachable"] is secondary, "Wrong client fault scope")
    for probe in result["siloNetworkDuringFullClientCut"].values():
        require(all(probe[k] is True for k in (
            "databaseHealthy", "primaryGatewayReachable", "secondaryGatewayReachable")),
            "Both silos must retain SQL and internal gateway paths")
    require(result["clientOutputRulesBefore"] == result["clientOutputRulesVerifiedRestored"],
            "Firewall baseline was not restored")
    attempt = result["clientAttemptWhenBothGatewaysLost"]
    require(attempt["exitCode"] == 74 and attempt["acknowledgedCommitted"] is False,
            "Wrong bounded client outcome")
    require(attempt["diagnostic"] == {
        "status": "CLIENT_STARTUP_DEADLINE", "phase": "BEFORE_FINANCIAL_DISPATCH",
        "deadlineSeconds": 20, "financialCommandsDispatched": 0}, "Not a startup-only result")
    require(19 <= attempt["elapsedSeconds"] < 35, "Unobserved startup deadline")
    counts = {"operationRows": 1, "postingRows": 2, "outboxRows": 1}
    require(result["sourceGrainOriginalHost"] == "e2f10-primary", "Fallback placement changed")
    require(result["survivingGatewayFinancialResult"][0]["status"] == "COMMITTED", "No fallback")
    require(result["replayStatus"] == "COMMITTED" and
            result["secondReplayStatus"] == "DUPLICATE_COMMITTED", "Replay not idempotent")
    for key in ("baselineOperationCardinalityAfterRecovery", "fallbackOperationCardinalityAfterRecovery",
                "survivingGatewayOperationCardinality"):
        require(result[key] == counts, "Wrong per-operation cardinality")
    during = result["independentSqlBeforeAndDuringFullCut"]
    require(during["effects"] == {"committedOperations": 2, "postings": 4, "outboxEvents": 2},
            "Unexpected financial effects under full cut")
    require(during["blockedOperation"] == dict.fromkeys(counts, 0), "Blocked operation had effects")
    require(len(result["repeatedSqlObservationsDuringFullCut"]) == 3 and
            all(sample == during for sample in result["repeatedSqlObservationsDuringFullCut"]),
            "Missing stable repeated SQL observations")
    final = result["independentSqlAfterRestore"]
    require(final["effects"] == {"committedOperations": 3, "postings": 6, "outboxEvents": 3}
            and final["blockedOperation"] == counts, "Final ledger cardinality mismatch")
    for key in ("independentSqlInitial", "independentSqlSingleGatewayCut",
                "independentSqlBeforeAndDuringFullCut", "independentSqlAfterRestore"):
        oracle = result[key]["independentSqlOracles"]
        require(len(oracle) == 7 and all(value is True for value in oracle.values()), "SQL oracle failed")
    require(result["membershipBefore"] == result["membershipAfter"], "Membership changed")
    require({row[2]: row[3] for row in result["membershipAfter"]["rows"]} == {11150: 3, 11151: 3},
            "Not two active membership rows")
    print("E2 C04 ORIGINAL AUDIT: PASS (first failure preserved; startup outage only; E2 partial)")


if __name__ == "__main__":
    main()
