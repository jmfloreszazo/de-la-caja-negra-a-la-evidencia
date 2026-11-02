#!/usr/bin/env python3
"""Fail-closed audit of independently downloaded B05 original CI smoke summary.

The raw original GitHub artifact is authoritative; this repo summary is a
commit-pinned, narrowly scoped audit trail. No sustained capacity claim.
"""
import json
from pathlib import Path
import re

path = Path(__file__).resolve().parents[1] / "evidence/runs/e2-b05-external-smoke.json"
record = json.loads(path.read_text(encoding="utf-8"))
assert record["schemaVersion"] == 1
assert record["experiment"] == "E2-B05-External-Client-Open-Loop-Smoke"
assert record["status"] == "CI_VERIFIED_BOUNDED_FUNCTIONAL_SMOKE_NOT_CAPACITY"
assert record["capacityEvidence"] is False
p = record["source"]
assert p["runId"] == 41196070831
assert p["sourceHeadSha"] == "e545b861045d3a6f6bee9262028fd05fb5bb9c63"
assert p["originalArtifactId"] == 13040601633
assert p["originalArtifactName"] == (
    "e2-b05-external-openloop-smoke-original-not-sustained-capacity"
)
assert p["rawFile"] == "e2-b05-smoke-summary.json"
assert p["downloadedOriginalZipSha256"] == (
    "6b2ba79ed6379118a20b890050d198862443d248aaf2cf7fc5d271bc84afa4c0"
)
assert re.fullmatch(r"[0-9a-f]{64}", p["downloadedOriginalZipSha256"])
assert str(p["runId"]) in p["runUrl"]
assert str(p["originalArtifactId"]) in p["originalArtifactUrl"]

o = record["observations"]
assert o["physicalHostCount"] == 1
assert o["distinctPodmanNetworkNamespaces"] == 4
assert o["liveSilos"] == 2
assert o["externalClientInSeparateProcess"] is True
assert o["loadProcessPersistentPerVector"] is True
assert o["clientAheadOfScheduleObserved"] is False
assert o["accounts"] == 1000 and o["hotEligibleAccountCount"] == 50
assert o["profiles"] == ["uniform", "five_percent_hot"]
assert o["routes"] == ["direct", "orleans"]
assert o["repetitionsPerPoint"] == 1
assert o["routeProfileTrials"] == 4
assert o["scheduledOffersPerTrial"] == 80
assert o["totalScheduledOffers"] == 320
assert o["offeredRequestsPerSecond"] == 20
assert o["durationSecondsPerTrial"] == 4
assert o["measurementSecondsPerTrial"] == 2
assert o["totalDispatched"] == o["totalScheduledOffers"]
assert o["totalMissedOffers"] == 0
assert o["totalAmbiguousClientResults"] == 0
assert o["totalAckCommitted"] == o["independentlyVerifiedDurableCommitted"] == 320
assert o["totalPostings"] == 640 and o["totalOutboxEvents"] == 320
assert o["independentSqlOracleChecksPerTrial"] == 7
assert o["allFourTrialsSevenOracleChecksPassed"] is True
assert o["exactAccountOperationIdCardinalityVerified"] is True
assert o["directAndOrleansPersistedStateHashesEqualForEachProfile"] is True
assert o["latencyComparisonValidAsCapacityStudy"] is False
assert o["persistedStateHashesPerProfile"] == {
    "uniform": "cf191635f452",
    "five_percent_hot": "8601e7b61372",
}
assert record["negativeOriginal"]["runId"] == 41195913857
assert record["negativeOriginal"]["artifactId"] == 13040616454
exclusions = record["limitations"].lower()
for exclusion in (
    "four seconds", "one repetition", "one linux physical runner",
    "no sustained capacity", "3+ repetitions", "mips parity",
):
    assert exclusion in exclusions, exclusion

print(
    "E2-B05 external-client four-second SMOKE: original artifact audited; "
    "320 offered/dispatch/SQL COMMIT, 640 postings, 320 outbox, "
    "7/7 per trial; NOT sustained TPS or mainframe capacity evidence"
)
