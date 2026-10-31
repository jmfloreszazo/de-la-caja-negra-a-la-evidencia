#!/usr/bin/env python3
"""Fail-closed audit of B05 hot-source 40/80 PostgreSQL COMMIT evidence.

Default mode pins original source SHA/run/ZIP digest and ES/EN limits. With
--original-zip, independently verify the ACTUAL 14,880 server COMMIT times,
all original samples, both immutable route inputs and every 1-second bucket.
A single-host two-rate pilot cannot establish the sustainable capacity ceiling.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "evidence/runs/e2-b05-hot-40-80-sql-sweep.json"
ZIP_SHA = "7ea9062c80dc92f1354f5076c543e3105d8a6ebfccac25c266c8398fe35dc262"
SOURCE_SHA = "6c1bb9b96d5118477b527f410fa66e08520055cf"


def check_manifest(record: dict) -> None:
    assert record["schemaVersion"] == 1
    assert record["experiment"] == "E2-B05-40-80-Offer-Rate-Sweep"
    assert record["status"] == "CI_VERIFIED_BOUNDED_HOT_40_80_SQL_COMMIT_RATES_NOT_CAPACITY"
    assert record["capacityCeilingEstablished"] is False
    assert record["capacityEvidence"] is False
    p = record["source"]
    assert p["sourcePr"] == 43 and p["sourceHeadSha"] == SOURCE_SHA
    assert p["mergedMainSha"] == "6c9f8ea9989cb8c572a1e5bc51f4004c95e4a1ca"
    assert p["originalCiRunId"] == 41210913483
    assert str(p["originalCiRunId"]) in p["originalCiUrl"]
    assert p["originalArtifactId"] == 13045879294
    assert str(p["originalArtifactId"]) in p["originalArtifactUrl"]
    assert p["originalArtifactZipSha256"] == ZIP_SHA
    assert re.fullmatch(r"[a-f0-9]{64}", ZIP_SHA)

    original = p["originalPrecorrectionAttempt"]
    assert original["ciRunId"] == 41210325810
    assert original["originalArtifactId"] == 13046247153
    assert original["originalArtifactZipSha256"] == (
        "7c418d9c3ad8682b22c5043bbc88cec2123079fae93c5ea25a688976bf14cbf2"
    )
    assert "7,440" in original["issue"] and "14,880" in original["issue"]
    assert original["firstRunC01Failure"]["ciRunId"] == 41210325811
    assert original["firstRunC01Failure"]["artifactId"] == 13046077362
    assert "/issues/44" in original["firstRunC01Failure"]["issueUrl"]

    setup = record["setup"]
    assert setup["accounts"] == 1000
    assert setup["eligibleHotSourceAccounts"] == 50
    assert setup["hotSourceIntentPercent"] == 80
    assert setup["profile"] == "five_percent_hot"
    assert setup["routes"] == ["direct", "orleans"]
    assert setup["offeredRatesPerSecond"] == [40, 80]
    assert setup["repetitionsPerPoint"] == 1
    assert setup["warmupSeconds"] == setup["cooldownSeconds"] == 1
    assert setup["measurementSeconds"] == 60
    assert setup["maximumInFlightClientRequests"] == 32
    assert setup["physicalLinuxHostCount"] == 1
    assert setup["podmanNetworkNamespaces"] == 4
    assert setup["timestampSource"] == "pg_xact_commit_timestamp(operations.xmin)"
    assert setup["noFinancialRequestRetries"] is True

    audit = record["audit"]
    expected = {
        "finalSourceCiChecksPassing": 14, "finalSourceCiChecksTotal": 14,
        "originalZipMembers": 15, "trials": 4,
        "distinctSourceVectors": 2, "scheduledRequests": 14880,
        "dispatchedRequests": 14880,
        "independentlyVerifiedDurableCommittedByRunEnd": 14880,
        "postings": 29760, "outboxEvents": 14880,
        "sqlSevenOracleChecksPassing": 28,
        "sqlSevenOracleChecksTotal": 28,
        "originalServerCommitTimestampsAudited": 14880,
        "conservativeServerCommitsInsideAllFourMeasurementWindows": 14400,
        "conservativePossibleServerCommitsInsideAllFourMeasurementWindows": 14400,
        "scheduledMeasurementPhaseIntents": 14400,
        "missedOffers": 0, "ambiguousOutcomes": 0,
        "matchedDirectOrleansInputAndFinalStatePairs": 2,
    }
    assert all(audit.get(key) == value for key, value in expected.items())
    assert audit["monotonicClientSchedulesValidated"] is True
    assert audit["all60OneSecondServerCommitBucketsPerTrialRecomputed"] is True
    assert audit["actualSaturationObserved"] is False
    assert audit["productionP99Established"] is False
    assert audit["mainframeMipsEquivalenceEstablished"] is False
    cases = record["cases"]
    assert len(cases) == 4
    assert {(c["rateOfferedPerSecond"], c["route"]) for c in cases} == {
        (rate, route) for rate in (40, 80) for route in ("direct", "orleans")
    }
    for case in cases:
        rate = case["rateOfferedPerSecond"]
        assert case["durableByRunEnd"] == rate * 62
        assert case["commitsCertainInside60s"] == rate * 60
        assert case["commitsPossibleInside60s"] == rate * 60
        assert case["actualServerCommitRatePerSecond"] == rate
        assert case["missed"] == case["ambiguous"] == 0
        assert 0 <= case["perSecondCommitHistogramMinimum"] <= rate
        assert rate <= case["perSecondCommitHistogramMaximum"]
        assert case["p99AckOnlyMilliseconds"] > 0

    es, en = record["interpretation"]["es"].lower(), record["interpretation"]["en"].lower()
    assert all(item in es for item in (
        "14.880", "29.760", "28/28", "40,0", "80,0", "no"
    ))
    assert all(item in en for item in (
        "14,880", "29,760", "28/28", "40.0", "80.0", "not"
    ))
    limits = record["limitations"].lower()
    assert all(item in limits for item in (
        "one physical", "one seeded repetition", "not sustainable", "mainframe",
        "partially_verified", "open", "v2026.10.29"
    ))


def check_original_zip(path: Path, record: dict) -> dict:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha == record["source"]["originalArtifactZipSha256"], (
        "Downloaded original ZIP hash differs; cannot substitute evidence",
        sha
    )
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == 15 and len(names) == len(set(names))
        raw = {
            name: json.loads(archive.read(name))
            for name in names if name.endswith(".json")
        }
    summary = raw["b05-sweep-summary.json"]
    assert summary["experiment"] == "E2-B05-40-80-Offer-Rate-Sweep"
    assert summary["status"] == "OBSERVED_BOUNDED_SWEEP_WITH_SQL_ORACLES_NOT_CAPACITY"
    assert summary["capacityEvidence"] is False
    assert summary["predeclared"]["expectedScheduledOffers"] == 14880
    assert summary["predeclared"]["ratesOfferedPerSecond"] == [40, 80]
    assert summary["topology"]["physicalLinuxHostCount"] == 1
    assert len(summary["trials"]) == 4

    totals = Counter()
    paired = defaultdict(dict)
    expected_cases = {
        (c["rateOfferedPerSecond"], c["route"]): c
        for c in record["cases"]
    }
    for trial in summary["trials"]:
        rate, route = trial["offeredRatePerSecond"], trial["route"]
        assert rate in (40, 80) and route in ("direct", "orleans")
        assert trial["profile"] == "five_percent_hot"
        assert trial["repetition"] == 0
        stem = f"five_percent_hot-{rate}tps-r0"
        vector = raw[f"{stem}-input.json"]
        client = raw[f"{stem}-{route}-client.json"]
        observation = raw[f"{stem}-{route}-observation.json"]
        assert trial == observation
        assert trial["originalClient"] == client
        operations = vector["operations"]
        samples = client["samples"]
        assert len(operations) == len(samples) == rate * 62
        assert vector["totalOfferedRequests"] == rate * 62
        assert vector["status"] == "GENERATED_NOT_EXECUTED"
        assert vector["capacityEvidence"] is False
        encoded = json.dumps(
            operations, sort_keys=True,
            separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        assert vector["offeredVectorSha256"] == trial["sourceVectorSha256"] == digest
        offered = {x["operationId"]: x for x in operations}
        assert len(offered) == len(operations)
        assert 5 * sum(
            x["sourceAccountId"] <= 50 for x in operations
        ) == 4 * len(operations)

        for offer, sample in zip(operations, samples):
            assert sample["operationId"] == offer["operationId"]
            assert sample["phase"] == offer["phase"]
            assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
            assert sample["clientOutcome"] == "ACKNOWLEDGED"
            assert sample["ledgerStatus"] == "COMMITTED"
            assert (offer["scheduledAtNs"] <= sample["dispatchedAtNs"]
                    <= sample["completedAtNs"])

        accounting = trial["originalIndependentResult"]
        assert accounting["offered"] == accounting["dispatched"] == rate * 62
        assert accounting["acknowledgedCommitted"] == accounting["sqlDurableCommittedByRunEnd"] == rate * 62
        assert accounting["missed"] == accounting["ambiguous"] == 0
        assert accounting["postings"] == rate * 62 * 2
        assert accounting["outboxEvents"] == rate * 62
        assert len(accounting["independentSevenSqlOracles"]) == 7
        assert all(accounting["independentSevenSqlOracles"].values())
        commit_window = accounting["serverCommitWindow"]
        original_stamps = commit_window["serverRecordedByOperation"]
        assert len(original_stamps) == len(offered)
        seen = set()
        timepoints = {}
        for item in original_stamps:
            op_id = item["operationId"]
            assert op_id in offered and op_id not in seen
            assert item["phase"] == offered[op_id]["phase"]
            seen.add(op_id)
            timepoints[op_id] = datetime.fromisoformat(
                item["serverCommitTimestampUtc"]
            )
        assert seen == set(offered)
        t0 = datetime.fromisoformat(commit_window["possibleWindowStartUtc"])
        t1 = datetime.fromisoformat(commit_window["certainWindowStartUtc"])
        t2 = datetime.fromisoformat(commit_window["certainWindowEndUtc"])
        t3 = datetime.fromisoformat(commit_window["possibleWindowEndUtc"])
        assert t0 <= t1 < t2 <= t3
        assert commit_window["measurementSeconds"] == 60
        certain = [ts for ts in timepoints.values() if t1 <= ts < t2]
        possible = [ts for ts in timepoints.values() if t0 <= ts < t3]
        assert len(certain) == len(possible) == rate * 60
        buckets = Counter(int((timestamp - t1).total_seconds()) for timestamp in certain)
        histogram = [buckets.get(second, 0) for second in range(60)]
        assert histogram == commit_window["perSecondCertainCommitHistogram"]
        assert sum(histogram) == rate * 60
        assert commit_window["certainCommits"] == commit_window["possibleCommits"] == rate * 60
        assert commit_window["certainCommitsPerSecond"] == commit_window["possibleCommitsPerSecond"] == rate
        expected = expected_cases[(rate, route)]
        assert expected["perSecondCommitHistogramMinimum"] == min(histogram)
        assert expected["perSecondCommitHistogramMaximum"] == max(histogram)
        assert expected["p99AckOnlyMilliseconds"] == accounting["latency"]["scheduledToAcknowledgedMsOnly"]["p99"]
        paired[rate][route] = (
            digest, trial["independentSqlStateSha256"]
        )
        totals.update(
            offered=rate * 62, committed=rate * 62,
            postings=rate * 62 * 2, outbox=rate * 62,
            oracles=7, in_window=rate * 60,
            trials=1,
        )
    assert set(paired) == {40, 80}
    assert all(
        set(v) == {"direct", "orleans"} and v["direct"] == v["orleans"]
        for v in paired.values()
    )
    assert dict(totals) == {
        "offered": 14880, "committed": 14880,
        "postings": 29760, "outbox": 14880,
        "oracles": 28, "in_window": 14400, "trials": 4
    }
    return dict(totals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path)
    args = parser.parse_args()
    record = json.loads(PATH.read_text(encoding="utf-8"))
    check_manifest(record)
    if args.original_zip:
        print("E2-B05 ORIGINAL ZIP AUDIT: " + json.dumps(
            check_original_zip(args.original_zip, record), sort_keys=True
        ) + "; two single-host load points, NOT capacity.")
    else:
        print("E2-B05 archived metadata/ES-EN/original ZIP-SHA verified; "
              "raw ZIP NOT re-downloaded in this invocation. "
              "40.0/80.0 SQL COMMIT/s measured, NOT maximum capacity.")


if __name__ == "__main__":
    main()
