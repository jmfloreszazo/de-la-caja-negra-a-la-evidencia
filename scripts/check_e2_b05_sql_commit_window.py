#!/usr/bin/env python3
"""Audit the narrowly scoped E2-B05 server-recorded 60-second COMMIT claim.

Offline checks pin the archived ORIGINAL CI source, hash and measured figures.
--original-zip independently replays all four full source run observations
and PostgreSQL's per-operation COMMIT timestamps, not the Orleans ACK clock.
This proves ONE offered rate on ONE runner, NOT a capacity ceiling or MIPS.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "evidence/runs/e2-b05-sql-commit-window-60s.json"
ZIP_SHA = "4b2d444fedd8da5e064c117ebe5f7e7fc75727bb24d931649f5c4702860c88ac"
SOURCE_SHA = "545fa75bda1efa8659c5370f1a030fe64ded646b"


def validate_claim(record: dict) -> None:
    assert record["schemaVersion"] == 1
    assert record["experiment"] == "E2-B05-Independent-SQL-Commit-Window"
    assert record["status"] == (
        "CI_VERIFIED_FIRST_60_SECOND_SERVER_COMMIT_WINDOW_NOT_CAPACITY_CEILING"
    )
    assert record["capacityCeilingEstablished"] is False
    assert record["capacityEvidence"] is False
    source = record["source"]
    assert source["sourcePr"] == 41 and source["sourceHeadSha"] == SOURCE_SHA
    assert source["mergedMainSha"] == "c310b805e35e6afafd8df7c3a8196cd8e68c8f1c"
    assert source["originalCiRunId"] == 41207978844
    assert str(source["originalCiRunId"]) in source["originalCiUrl"]
    assert source["originalArtifactId"] == 13044689170
    assert str(source["originalArtifactId"]) in source["originalArtifactUrl"]
    assert source["originalZipSha256"] == ZIP_SHA
    assert re.fullmatch(r"[0-9a-f]{64}", ZIP_SHA)

    setup = record["setup"]
    assert setup["postgresVersion"] == "16.13"
    assert setup["postgresConfig"] == "track_commit_timestamp=on"
    assert setup["timestampSource"] == "pg_xact_commit_timestamp(operations.xmin)"
    assert setup["profiles"] == ["uniform", "five_percent_hot"]
    assert setup["offeredRatesPerSecond"] == [20]
    assert setup["repetitionsPerProfileRoute"] == 1
    assert setup["routes"] == ["direct", "orleans"]
    assert (setup["warmupSeconds"], setup["measurementSeconds"],
            setup["cooldownSeconds"]) == (1, 60, 1)
    assert setup["physicalHostCount"] == 1
    assert setup["podmanNetworkNamespaces"] == 4
    assert setup["sourceOfTruth"] == "PostgreSQL"
    audit = record["audit"]
    expected = {
        "originalCiChecksPassing": 13,
        "originalCiChecksTotal": 13,
        "originalZipMembers": 15,
        "distinctMatchedTrials": 4,
        "originalInputVectors": 2,
        "committedOperationsByTrialEnd": 4960,
        "postings": 9920,
        "outboxEvents": 4960,
        "independentSqlOracleChecksPassing": 28,
        "independentSqlOracleChecksTotal": 28,
        "perOperationPostgresCommitTimestampsAudited": 4960,
        "missedOffers": 0,
        "ambiguousOutcomes": 0,
        "measurementPhaseRequests": 4800,
        "postgresqlCommitsCertainlyWithinAllMeasurementWindows": 4800,
        "postgresqlCommitsPossiblyWithinAllMeasurementWindows": 4800,
        "independentMeasuredCommitRatePerSecondPerTrial": 20,
        "serverCommitTimestampsPerSecondPerTrial": 20,
        "secondBucketsPerTrial": 60,
        "distinctRouteMatchedInputAndSqlStatePairs": 2,
        "worstClientOriginCaptureUncertaintyMs": 0.004,
    }
    assert all(audit.get(key) == value for key, value in expected.items())
    assert audit["serverHostClockCheckPerformed"] is True
    assert audit["observedSaturation"] is False
    assert audit["mainframeParityDemonstrated"] is False
    assert len(record["cases"]) == 4
    assert {
        (row["profile"], row["route"]) for row in record["cases"]
    } == {
        (p, r) for p in setup["profiles"] for r in setup["routes"]
    }
    for case in record["cases"]:
        assert case["committedByRunEnd"] == 1240
        assert case["commitsCertainlyInWindow"] == 1200
        assert case["commitsPossiblyInWindow"] == 1200
        assert case["measuredServerCommitTps"] == 20
        assert case["perSecondBucketMin"] == 20
        assert case["perSecondBucketMax"] == 20
        assert re.fullmatch(r"[0-9a-f]{64}", case["stateSha256"])
    for profile in setup["profiles"]:
        pair = [row["stateSha256"] for row in record["cases"]
                if row["profile"] == profile]
        assert len(pair) == 2 and pair[0] == pair[1]

    es = record["interpretation"]["es"].lower()
    en = record["interpretation"]["en"].lower()
    assert all(term in es for term in ("4.960", "9.920", "28/28", "20,0", "no"))
    assert all(term in en for term in ("4,960", "9,920", "28/28", "20.0", "not"))
    limit = record["limitations"].lower()
    assert all(term in limit for term in (
        "one physical", "one repetition", "not a distributed",
        "mainframe", "partially_verified", "open"
    ))


def audit_original_zip(path: Path, record: dict) -> dict:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ZIP_SHA, (
        "Wrong original GitHub Actions ZIP: do not accept substitute inputs"
    )
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == 15 and len(set(names)) == 15
        data = {
            name: json.loads(archive.read(name))
            for name in names if name.endswith(".json")
        }
    summary = data["e2-b05-commit-window-summary.json"]
    assert summary["status"] == "PASS_60_SECOND_COMMIT_TIMESTAMP_SLICE_NOT_CAPACITY"
    assert summary["capacityEvidence"] is False
    assert summary["topology"]["physicalHostCount"] == 1
    assert len(summary["runs"]) == 4
    pairs = defaultdict(dict)
    totals = Counter()
    for observed in summary["runs"]:
        profile, route = observed["profile"], observed["route"]
        assert profile in record["setup"]["profiles"]
        assert route in ("direct", "orleans")
        assert observed["offeredRatePerSecond"] == 20
        assert observed["repetition"] == 0
        key = (profile, route)
        assert route not in pairs[profile]
        stem = f"{profile}-20tps-r0"
        vector = data[stem + "-input.json"]
        client = data[stem + f"-{route}-client.json"]
        raw = data[stem + f"-{route}-observation.json"]
        assert raw == observed and observed["rawClient"] == client
        offers = vector["operations"]
        assert len(offers) == 1240 and client["offered"] == 1240
        assert client["dispatched"] == client["acknowledgedCommitted"] == 1240
        assert client["missed"] == client["ambiguous"] == 0
        encoded = json.dumps(
            offers, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        input_sha = hashlib.sha256(encoded).hexdigest()
        assert input_sha == observed["offeredVectorSha256"] == vector["offeredVectorSha256"]
        by_id = {offer["operationId"]: offer for offer in offers}
        assert len(by_id) == len(offers)
        client_ids = set()
        for sample in client["samples"]:
            op_id = sample["operationId"]
            assert op_id in by_id and op_id not in client_ids
            client_ids.add(op_id)
            offer = by_id[op_id]
            assert sample["phase"] == offer["phase"]
            assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
            assert offer["scheduledAtNs"] <= sample["dispatchedAtNs"] <= sample["completedAtNs"]
            assert sample["clientOutcome"] == "ACKNOWLEDGED"
            assert sample["ledgerStatus"] == "COMMITTED"
        assert client_ids == set(by_id)

        sql = observed["independentSql"]
        assert sql["durableCommittedOperationCount"] == 1240
        assert sql["postingCount"] == 2480
        assert sql["outboxCount"] == 1240
        assert len(sql["independentSqlOracle"]) == 7
        assert all(sql["independentSqlOracle"].values())
        window = observed["serverRecordedCommitWindow"]
        assert window["serverConfig"] == "track_commit_timestamp=on"
        timestamps = window["originalServerCommitTimestampsByOperation"]
        assert len(timestamps) == 1240
        t0 = datetime.fromisoformat(window["possibleWindowStartUtc"])
        t1 = datetime.fromisoformat(window["certainWindowStartUtc"])
        t2 = datetime.fromisoformat(window["certainWindowEndUtc"])
        t3 = datetime.fromisoformat(window["possibleWindowEndUtc"])
        assert t0 <= t1 < t2 <= t3
        assert window["measurementDurationSeconds"] == 60
        assert window["timeBoundaryUncertaintySeconds"] <= .000004
        commits = {}
        for item in timestamps:
            op_id = item["operationId"]
            assert op_id in by_id and op_id not in commits
            assert item["sourcePhase"] == by_id[op_id]["phase"]
            commits[op_id] = datetime.fromisoformat(
                item["postgresCommitTimestampUtc"]
            )
        assert set(commits) == set(by_id)
        inside = [ts for ts in commits.values() if t1 <= ts < t2]
        possible = [ts for ts in commits.values() if t0 <= ts < t3]
        assert len(inside) == len(possible) == 1200
        assert window["serverCommitsCertainlyWithinWindow"] == 1200
        assert window["serverCommitsPossiblyWithinWindow"] == 1200
        buckets = Counter(
            math.floor((timestamp - t1).total_seconds())
            for timestamp in inside
        )
        assert set(buckets) == set(range(60))
        assert all(buckets[second] == 20 for second in range(60))
        assert window["certainServerCommitsPerMeasurementSecond"] == 20
        assert window["possibleServerCommitsPerMeasurementSecond"] == 20
        assert sum(
            op_id in by_id and by_id[op_id]["phase"] == "measurement"
            and t1 <= timestamp < t2
            for op_id, timestamp in commits.items()
        ) == 1200
        assert observed["measurementPhaseScheduledOffers"] == 1200
        assert observed["measurementPhaseDurableByRunEnd"] == 1200
        assert window["measurementPhaseIntents"] == 1200
        expected_case = next(
            row for row in record["cases"]
            if row["profile"] == profile and row["route"] == route
        )
        assert expected_case["stateSha256"] == sql["stateSha256"]
        pairs[profile][route] = (input_sha, sql["stateSha256"])
        totals.update(
            commits=1240, postings=2480, outbox=1240,
            oracle=7, inside_window=1200, cases=1
        )
    assert len(pairs) == 2
    assert all(
        set(v) == {"direct", "orleans"} and v["direct"] == v["orleans"]
        for v in pairs.values()
    )
    assert dict(totals) == {
        "commits": 4960, "postings": 9920, "outbox": 4960,
        "oracle": 28, "inside_window": 4800, "cases": 4
    }
    return dict(totals)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path)
    args = parser.parse_args()
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    validate_claim(record)
    if args.original_zip:
        counts = audit_original_zip(args.original_zip, record)
        print("Original PostgreSQL COMMIT timestamps fully verified: "
              + json.dumps(counts, sort_keys=True))
    else:
        print("B05 60-second SQL COMMIT claim/CI/SHA registry verified; "
              "raw original ZIP NOT re-audited by this invocation. "
              "One rate on one runner, not a capacity ceiling.")


if __name__ == "__main__":
    main()
