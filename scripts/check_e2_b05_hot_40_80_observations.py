#!/usr/bin/env python3
"""Fail-closed B05 40/80 per-second SQL COMMIT evidence audit.

Default verifies immutable original CI claim, ES/EN interpretation and
noncapacity limits. --original-zip also independently recomputes every
operation, original PostgreSQL COMMIT histogram, accounting cardinality,
input hashes, and direct-vs-Orleans final persisted state.
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
RECORD = ROOT / "evidence/runs/e2-b05-hot-40-80-sql-commit-sweep.json"
ZIP_SHA = "7ea9062c80dc92f1354f5076c543e3105d8a6ebfccac25c266c8398fe35dc262"
HEAD_SHA = "6c1bb9b96d5118477b527f410fa66e08520055cf"

ORIGINAL_CASES = {
    (40, "direct"): (2480, 2400, {40: 60}, 53.682),
    (40, "orleans"): (2480, 2400, {40: 60}, 53.046),
    (80, "direct"): (4960, 4800, {79: 1, 80: 58, 81: 1}, 94.755),
    (80, "orleans"): (4960, 4800, {79: 2, 80: 56, 81: 2}, 154.345),
}


def claim_gate(record: dict) -> None:
    assert record["schemaVersion"] == 1
    assert record["experiment"] == "E2-B05-40-80-Offer-Rate-Sweep"
    assert record["status"] == (
        "CI_AND_ORIGINAL_ZIP_AUDITED_EXPLORATORY_COMMIT_WINDOWS_NOT_CAPACITY"
    )
    assert record["capacityEvidence"] is False
    assert record["saturationCeilingMeasured"] is False
    assert record["mainframeMipsEquivalence"] is False
    source = record["source"]
    assert source["sourcePr"] == 43 and source["sourceHeadSha"] == HEAD_SHA
    assert source["mergedMainSha"] == "6c9f8ea9989cb8c572a1e5bc51f4004c95e4a1ca"
    assert source["originalCiRunId"] == 41210913483
    assert str(source["originalCiRunId"]) in source["originalCiUrl"]
    assert source["originalArtifactId"] == 13045879294
    assert str(source["originalArtifactId"]) in source["originalArtifactUrl"]
    assert source["originalArtifactZipSha256"] == ZIP_SHA
    assert re.fullmatch(r"[a-f0-9]{64}", ZIP_SHA)
    assert source["originalCiChecksGreen"] == source["originalCiChecksTotal"] == 14
    assert source["originalArtifactZipMembers"] == 15

    setup = record["setup"]
    assert setup["postgresVersion"] == "16.13"
    assert setup["serverCommitTimestampSource"] == (
        "pg_xact_commit_timestamp(operations.xmin)"
    )
    assert setup["trackCommitTimestamp"] == "on"
    assert setup["accountCount"] == 1000
    assert setup["eligibleHotSourceAccountCount"] == 50
    assert setup["hotSourceOfferFraction"] == .8
    assert setup["profile"] == "five_percent_hot"
    assert setup["routes"] == ["direct", "orleans"]
    assert setup["offeredRequestsPerSecond"] == [40, 80]
    assert setup["repetitionsPerRateAndRoute"] == 1
    assert (setup["warmupSeconds"], setup["measurementSeconds"],
            setup["cooldownSeconds"]) == (1, 60, 1)
    assert setup["physicalLinuxHostCount"] == 1
    assert setup["networkNamespaces"] == 4
    assert setup["maxInFlightClientRequests"] == 32
    assert setup["sqlAuthority"] == "PostgreSQL"

    audit = record["audit"]
    assert audit["trialCount"] == 4
    assert audit["scheduledOffers"] == audit["dispatchedOffers"] == 14880
    assert audit["missedOffers"] == audit["ambiguousOutcomes"] == 0
    assert audit["acknowledgedCommits"] == 14880
    assert audit["independentDurableSqlCommitsByRunEnd"] == 14880
    assert audit["postings"] == 29760 and audit["outboxEvents"] == 14880
    assert audit["sqlInWindowCommitsCertainly"] == 14400
    assert audit["sqlInWindowCommitsPossibly"] == 14400
    assert audit["perOperationOriginalPostgresTimestampsReconciled"] == 14880
    assert audit["independentSqlOracleChecksPassed"] == 28
    assert audit["independentSqlOracleChecksTotal"] == 28
    assert audit["matchedSourceAndSqlFinalStatePairs"] == 2
    assert audit["originalRunPreserved"] is True

    cases = record["cases"]
    assert len(cases) == len(ORIGINAL_CASES)
    assert {(c["offeredRatePerSecond"], c["route"]) for c in cases} == (
        set(ORIGINAL_CASES)
    )
    for case in cases:
        expected_offered, expected_window, expected_bins, p99 = (
            ORIGINAL_CASES[(case["offeredRatePerSecond"], case["route"])]
        )
        assert case["totalScheduled"] == case["sqlCommittedByRunEnd"] == (
            expected_offered
        )
        assert case["serverCommitsCertainlyIn60s"] == expected_window
        assert case["serverCommitsPossiblyIn60s"] == expected_window
        assert case["serverCommitRatePerSecond"] == (
            case["offeredRatePerSecond"]
        )
        assert {int(k): v for k, v in case["perSecondBucketCounts"].items()} == (
            expected_bins
        )
        assert case["ackOnlyP99Ms"] == p99
        assert re.fullmatch(r"[0-9a-f]{64}", case["inputSha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", case["persistedStateSha256"])
    for rate in (40, 80):
        p = [c for c in cases if c["offeredRatePerSecond"] == rate]
        assert len(p) == 2
        assert p[0]["inputSha256"] == p[1]["inputSha256"]
        assert p[0]["persistedStateSha256"] == p[1]["persistedStateSha256"]

    neg = record["negativeOriginal"]
    assert neg["runId"] == 41210325811
    assert neg["originalArtifactId"] == 13046077362
    assert neg["originalArtifactSha256"] == (
        "91e19d4c5e2d84874b0f4c79ce0afde57dae43b9dc1d21a4861bfadfcc5ae097"
    )
    assert "issues/44" in neg["openInvestigation"]
    for term in ("14.880", "29.760", "28/28", "40,0", "80,0", "79", "81", "no"):
        assert term in record["interpretation"]["es"].lower(), term
    for term in ("14,880", "29,760", "28/28", "40.0", "80.0", "79", "81", "not"):
        assert term in record["interpretation"]["en"].lower(), term
    for term in ("one physical", "one", "saturation", "p99", "mips",
                 "partially_verified", "open", "v2026.10.29"):
        assert term in record["limits"].lower(), term


def original_zip_gate(path: Path, record: dict) -> dict:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ZIP_SHA, (
        "Wrong ZIP: original GitHub Actions artifact identity MUST match"
    )
    with ZipFile(path) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) == 15
        data = {
            name: json.loads(z.read(name))
            for name in names if name.endswith(".json")
        }
    report = data["b05-sweep-summary.json"]
    assert report["schemaVersion"] == 1
    assert report["capacityEvidence"] is False
    assert report["status"] == "OBSERVED_BOUNDED_SWEEP_WITH_SQL_ORACLES_NOT_CAPACITY"
    assert report["predeclared"]["expectedScheduledOffers"] == 14880
    assert report["predeclared"]["ratesOfferedPerSecond"] == [40, 80]
    assert report["predeclared"]["measurementSeconds"] == 60
    assert report["predeclared"]["repetitionsPerRateAndRoute"] == 1
    assert report["topology"]["physicalLinuxHostCount"] == 1
    assert len(set(report["topology"]["podmanNetworkNamespaces"].values())) == 4
    assert report["sqlHostClockBefore"]["postgresTrackCommitTimestamp"] == "on"
    assert len(report["trials"]) == 4

    totals = Counter()
    paired = defaultdict(dict)
    for observed in report["trials"]:
        rate, route = observed["offeredRatePerSecond"], observed["route"]
        assert (rate, route) in ORIGINAL_CASES
        assert route not in paired[rate]
        name = f"five_percent_hot-{rate}tps-r0"
        vector = data[name + "-input.json"]
        client = data[name + f"-{route}-client.json"]
        separate = data[name + f"-{route}-observation.json"]
        assert observed == separate and observed["originalClient"] == client
        offers = vector["operations"]
        assert len(offers) == rate * 62
        offer_ids = {x["operationId"]: x for x in offers}
        assert len(offer_ids) == len(offers)
        for phase, seconds in (("warmup", 1), ("measurement", 60),
                               ("cooldown", 1)):
            rows = [x for x in offers if x["phase"] == phase]
            assert len(rows) == rate * seconds
            assert sum(x["sourceAccountId"] <= 50 for x in rows) * 5 == (
                len(rows) * 4
            )
        encoded = json.dumps(
            offers, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        sha = hashlib.sha256(encoded).hexdigest()
        outcome = observed["originalIndependentResult"]
        assert sha == vector["offeredVectorSha256"] == (
            observed["sourceVectorSha256"]
        ) == outcome["offeredVectorSha256"]
        assert outcome["capacityEvidence"] is False
        assert outcome["offered"] == outcome["dispatched"] == rate * 62
        assert outcome["missed"] == outcome["ambiguous"] == 0
        assert outcome["acknowledgedCommitted"] == rate * 62
        assert outcome["sqlDurableCommittedByRunEnd"] == rate * 62
        assert outcome["postings"] == 2 * rate * 62
        assert outcome["outboxEvents"] == rate * 62
        assert len(outcome["independentSevenSqlOracles"]) == 7
        assert all(outcome["independentSevenSqlOracles"].values())
        assert client["offered"] == client["dispatched"] == rate * 62
        assert len(client["samples"]) == len(offers)
        for offer, sample in zip(offers, client["samples"]):
            assert sample["operationId"] == offer["operationId"]
            assert sample["phase"] == offer["phase"]
            assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
            assert sample["clientOutcome"] == "ACKNOWLEDGED"
            assert sample["ledgerStatus"] == "COMMITTED"
            assert offer["scheduledAtNs"] <= sample["dispatchedAtNs"] <= (
                sample["completedAtNs"]
            )
        window = outcome["serverCommitWindow"]
        assert window["source"] == "pg_xact_commit_timestamp(operations.xmin)"
        assert window["serverConfig"] == "track_commit_timestamp=on"
        assert len(window["serverRecordedByOperation"]) == len(offers)
        certain_start = datetime.fromisoformat(window["certainWindowStartUtc"])
        certain_end = datetime.fromisoformat(window["certainWindowEndUtc"])
        possible_start = datetime.fromisoformat(window["possibleWindowStartUtc"])
        possible_end = datetime.fromisoformat(window["possibleWindowEndUtc"])
        assert possible_start <= certain_start < certain_end <= possible_end
        count_per_second = Counter()
        certain = possible = 0
        seen = set()
        for operation in window["serverRecordedByOperation"]:
            op_id = operation["operationId"]
            assert op_id in offer_ids and op_id not in seen
            seen.add(op_id)
            assert operation["phase"] == offer_ids[op_id]["phase"]
            when = datetime.fromisoformat(operation["serverCommitTimestampUtc"])
            if possible_start <= when < possible_end:
                possible += 1
            if certain_start <= when < certain_end:
                certain += 1
                second = int((when - certain_start).total_seconds())
                assert 0 <= second < 60
                count_per_second[second] += 1
        assert seen == set(offer_ids)
        assert window["certainCommits"] == certain == rate * 60
        assert window["possibleCommits"] == possible == rate * 60
        assert window["certainCommitsPerSecond"] == rate
        assert window["possibleCommitsPerSecond"] == rate
        assert window["perSecondCertainCommitHistogram"] == [
            count_per_second[second] for second in range(60)
        ]
        expected_freq = {
            int(k): v for k, v in next(
                c for c in record["cases"] if (
                    c["offeredRatePerSecond"], c["route"]
                ) == (rate, route)
            )["perSecondBucketCounts"].items()
        }
        assert dict(Counter(window["perSecondCertainCommitHistogram"])) == (
            expected_freq
        )
        assert sum(count_per_second.values()) == rate * 60
        assert outcome["measurementPhaseOffered"] == rate * 60
        assert outcome["measurementPhaseDurableByRunEnd"] == rate * 60
        assert outcome["latency"][
            "omittedFailedOrMissedOffersFromLatencyPercentiles"
        ] == 0
        case = next(c for c in record["cases"] if (
            c["offeredRatePerSecond"], c["route"]
        ) == (rate, route))
        assert outcome["latency"]["scheduledToAcknowledgedMsOnly"]["p99"] == (
            case["ackOnlyP99Ms"]
        )
        assert observed["independentSqlStateSha256"] == (
            case["persistedStateSha256"]
        )
        paired[rate][route] = (sha, observed["independentSqlStateSha256"])
        totals.update(
            offers=len(offers), commits=len(seen),
            certain=certain, possible=possible, postings=outcome["postings"],
            outbox=outcome["outboxEvents"], oracles=7, trials=1
        )
    assert len(paired) == 2
    for rate in (40, 80):
        assert set(paired[rate]) == {"direct", "orleans"}
        assert paired[rate]["direct"] == paired[rate]["orleans"]
    assert dict(totals) == {
        "offers": 14880, "commits": 14880,
        "certain": 14400, "possible": 14400,
        "postings": 29760, "outbox": 14880, "oracles": 28, "trials": 4
    }
    return dict(totals)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path)
    args = parser.parse_args()
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    claim_gate(record)
    if args.original_zip:
        totals = original_zip_gate(args.original_zip, record)
        print("E2-B05 original corrected-head 40/80 SQL ZIP audited: "
              + json.dumps(totals, sort_keys=True)
              + "; NOT capacity proof")
    else:
        print("E2-B05 corrected-head original CI/source/ZIP SHA and bilingual "
              "evidence claims verified offline; full original ZIP NOT "
              "read in this invocation. NOT capacity proof.")


if __name__ == "__main__":
    main()
