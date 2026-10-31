#!/usr/bin/env python3
"""Verify the original 160/320 external B05 SQL COMMIT observations.

Offline validates the archived provenance, ES/EN interpretation and exact
missing-offer attribution. --original-zip replays source vector, client ID,
phase, PostgreSQL UTC COMMIT and every 60-bin histogram from the unaltered
source GitHub Actions artifact. No capacity-ceiling or production p99 claim.
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
MANIFEST = ROOT / "evidence/runs/e2-b05-160-320-sql-overload.json"
ZIP_SHA = "376f8053d3f70012a6ca2ad4088aa0f05ae71a57542ceb5fe027f6ce282837ce"
SOURCE_SHA = "d21af6e595ed790834280787ff53a41bb301e65c"
EXPECTED = {
    (160, "direct"): (9920, 0, {160: 60}, 35.195),
    (160, "orleans"): (9920, 0, {160: 60}, 15.578),
    (320, "direct"): (19840, 12, {320: 60}, 3.18),
    (320, "orleans"): (19840, 0, {319: 1, 320: 58, 321: 1}, 12.571),
}


def claim_gate(value: dict) -> None:
    assert value["schemaVersion"] == 1
    assert value["experiment"] == "E2-B05-160-320-Offer-Rate-Overload"
    assert value["status"] == (
        "SOURCE_CI_AND_INDEPENDENT_ORIGINAL_ZIP_VERIFIED_BOUNDED_OVERLOAD_NOT_CAPACITY"
    )
    assert value["capacityEvidence"] is False
    assert value["sustainedCapacityCeilingEstablished"] is False
    assert value["mainframeMipsEquivalence"] is False
    src = value["source"]
    assert src["sourcePullRequest"] == 48
    assert src["sourceHeadSha"] == SOURCE_SHA
    assert src["mergedMainSha"] == "fa125a2ab6b17f9cf764f6b3e25732037341b8cc"
    assert src["originalCiRunId"] == 41213914581
    assert str(src["originalCiRunId"]) in src["originalCiUrl"]
    assert src["originalArtifactId"] == 13047313472
    assert str(src["originalArtifactId"]) in src["originalArtifactUrl"]
    assert src["originalZipSha256"] == ZIP_SHA
    assert re.fullmatch(r"[0-9a-f]{64}", ZIP_SHA)
    assert src["sourceCiChecksPassing"] == src["sourceCiChecksTotal"] == 15
    assert src["originalZipEntries"] == 15
    setup = value["setup"]
    assert setup["postgresVersion"] == "16.13"
    assert setup["trackCommitTimestamp"] == "on"
    assert setup["serverCommitTimestampSource"] == (
        "pg_xact_commit_timestamp(operations.xmin)"
    )
    assert setup["accountCount"] == 1000
    assert setup["eligibleHotSourceAccounts"] == 50
    assert setup["hotSourceIntentFraction"] == 0.8
    assert setup["profile"] == "five_percent_hot"
    assert setup["routes"] == ["direct", "orleans"]
    assert setup["offeredRatesPerSecond"] == [160, 320]
    assert setup["repetitionsPerRateRoute"] == 1
    assert (setup["warmupSeconds"], setup["measurementSeconds"],
            setup["cooldownSeconds"]) == (1, 60, 1)
    assert setup["physicalLinuxHostCount"] == 1
    assert setup["podmanNamespaceCount"] == 4
    assert setup["maximumInflight"] == 32
    a = value["audit"]
    expected = {
        "trials": 4, "totalScheduled": 59520,
        "totalDispatched": 59508, "totalMissedInWarmup": 12,
        "totalMissedInMeasurement": 0, "totalAmbiguous": 0,
        "totalAcknowledged": 59508,
        "authoritativeSqlCommittedByRunEnd": 59508,
        "postings": 119016, "outboxEvents": 59508,
        "independentSqlOraclesPassed": 28,
        "independentSqlOraclesTotal": 28,
        "allServerCommitsCertainlyWithinAllMeasurementWindows": 57600,
        "allServerCommitsPossiblyWithinAllMeasurementWindows": 57600,
        "perOperationServerCommitTimestampsAudited": 59508,
        "sourceInputShaMatchingPairs": 2,
        "identicalPersistedStatePairsWhenAllOffersCommitted": 1,
        "nonIdenticalPersistedStatePairsWithKnownUndispatchedOffers": 1
    }
    assert all(a.get(k) == v for k, v in expected.items())
    cases = value["cases"]
    assert len(cases) == 4
    assert {(v["offeredPerSecond"], v["route"]) for v in cases} == set(EXPECTED)
    for c in cases:
        rate, route = c["offeredPerSecond"], c["route"]
        n, misses, freq, p99 = EXPECTED[(rate, route)]
        assert c["scheduled"] == n
        assert c["dispatched"] == c["durableByRunEnd"] == n - misses
        assert c["missedWarmup"] == c["ackedSamplesCensored"] == misses
        assert c["ambiguous"] == 0
        assert c["measurePhaseOffered"] == rate * 60
        assert c["certainSqlCommitInside60s"] == rate * 60
        assert c["possibleSqlCommitInside60s"] == rate * 60
        assert c["measuredSqlCommitPerSecond"] == rate
        assert {int(k): v for k, v in c["oneSecondCommitHistogramFrequency"].items()} == freq
        assert c["ackOnlyP99Ms"] == p99
        assert re.fullmatch(r"[a-f0-9]{64}", c["sourceVectorSha256"])
        assert re.fullmatch(r"[a-f0-9]{64}", c["finalSqlStateSha256"])
        if misses:
            assert c["missedOperationScheduledSecondsRange"] == [.1, .134]
    for rate in (160, 320):
        pairs = [c for c in cases if c["offeredPerSecond"] == rate]
        assert len(pairs) == 2
        assert pairs[0]["sourceVectorSha256"] == pairs[1]["sourceVectorSha256"]
        assert (pairs[0]["finalSqlStateSha256"] == pairs[1]["finalSqlStateSha256"]) == (rate == 160)
    es = value["interpretation"]["es"].lower()
    en = value["interpretation"]["en"].lower()
    assert all(x in es for x in ("59.520", "59.508", "119.016", "12", "160,0", "320,0", "no"))
    assert all(x in en for x in ("59,520", "59,508", "119,016", "12", "160.0", "320.0", "not"))
    limits = value["limitations"].lower()
    assert all(x in limits for x in (
        "one physical", "32 in-flight", "one trial", "no 3+",
        "mips", "partially_verified", "v2026.10.29"
    ))


def original_zip_gate(path: Path, record: dict) -> dict:
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ZIP_SHA, (
        "Wrong or modified original CI ZIP"
    )
    with ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist())) == 15
        data = {
            name: json.loads(z.read(name))
            for name in z.namelist() if name.endswith(".json")
        }
    summary = data["b05-overload-summary.json"]
    assert summary["schemaVersion"] == 1
    assert summary["capacityEvidence"] is False
    assert summary["predeclared"]["ratesOfferedPerSecond"] == [160, 320]
    assert summary["predeclared"]["expectedScheduledOffers"] == 59520
    assert summary["predeclared"]["measurementSeconds"] == 60
    assert summary["predeclared"]["repetitionsPerRateAndRoute"] == 1
    assert summary["topology"]["physicalLinuxHostCount"] == 1
    assert len(set(summary["topology"]["podmanNetworkNamespaces"].values())) == 4
    assert len(summary["trials"]) == 4
    totals = Counter()
    pairs = defaultdict(dict)
    for row in summary["trials"]:
        rate, route = row["offeredRatePerSecond"], row["route"]
        assert (rate, route) in EXPECTED
        assert route not in pairs[rate]
        name = f"five_percent_hot-{rate}tps-r0"
        vector = data[name + "-input.json"]
        client = data[name + f"-{route}-client.json"]
        separate = data[name + f"-{route}-observation.json"]
        assert row == separate and row["originalClient"] == client
        offers = vector["operations"]
        assert len(offers) == client["offered"] == rate * 62
        phase_expected = {"warmup": rate, "measurement": rate * 60,
                          "cooldown": rate}
        by_id = {offer["operationId"]: offer for offer in offers}
        assert len(by_id) == len(offers)
        assert Counter(x["phase"] for x in offers) == phase_expected
        for phase, expected in phase_expected.items():
            phase_offers = [o for o in offers if o["phase"] == phase]
            assert len(phase_offers) == expected
            assert sum(o["sourceAccountId"] <= 50 for o in phase_offers) * 5 == expected * 4
        canonical = json.dumps(
            offers, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        sha = hashlib.sha256(canonical).hexdigest()
        observed = row["originalIndependentResult"]
        assert sha == vector["offeredVectorSha256"] == (
            row["sourceVectorSha256"]
        ) == observed["offeredVectorSha256"]
        assert observed["capacityEvidence"] is False
        n, expected_miss, expected_freq, p99 = EXPECTED[(rate, route)]
        missed = {}
        acknowledged = {}
        assert len(client["samples"]) == n
        for offer, sample in zip(offers, client["samples"]):
            assert sample["operationId"] == offer["operationId"]
            assert sample["phase"] == offer["phase"]
            assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
            if sample["clientOutcome"] == "MISSED_OFFER_INFLIGHT_LIMIT":
                assert offer["phase"] == "warmup"
                assert sample["dispatchedAtNs"] is None
                assert sample["completedAtNs"] is None
                assert sample["ledgerStatus"] is None
                missed[offer["operationId"]] = offer
            else:
                assert sample["clientOutcome"] == "ACKNOWLEDGED"
                assert sample["ledgerStatus"] == "COMMITTED"
                assert offer["scheduledAtNs"] <= sample["dispatchedAtNs"] <= sample["completedAtNs"]
                acknowledged[offer["operationId"]] = offer
        assert len(missed) == expected_miss
        assert len(acknowledged) == n - expected_miss
        if expected_miss:
            ranges = [round(o["scheduledAtNs"] / 1e9, 3) for o in missed.values()]
            assert min(ranges) == .1 and max(ranges) == .134
        assert client["missed"] == observed["missed"] == expected_miss
        assert client["ambiguous"] == observed["ambiguous"] == 0
        assert client["dispatched"] == observed["dispatched"] == n - expected_miss
        assert client["acknowledgedCommitted"] == observed["acknowledgedCommitted"] == n - expected_miss
        assert observed["sqlDurableCommittedByRunEnd"] == n - expected_miss
        assert observed["postings"] == 2 * (n - expected_miss)
        assert observed["outboxEvents"] == n - expected_miss
        assert len(observed["independentSevenSqlOracles"]) == 7
        assert all(observed["independentSevenSqlOracles"].values())
        window = observed["serverCommitWindow"]
        assert window["serverConfig"] == "track_commit_timestamp=on"
        assert window["source"] == "pg_xact_commit_timestamp(operations.xmin)"
        timestamps = window["serverRecordedByOperation"]
        assert len(timestamps) == n - expected_miss
        t0 = datetime.fromisoformat(window["possibleWindowStartUtc"])
        t1 = datetime.fromisoformat(window["certainWindowStartUtc"])
        t2 = datetime.fromisoformat(window["certainWindowEndUtc"])
        t3 = datetime.fromisoformat(window["possibleWindowEndUtc"])
        assert t0 <= t1 < t2 <= t3
        frequency = Counter()
        ids = set()
        certainly = possibly = 0
        for item in timestamps:
            op_id = item["operationId"]
            assert op_id in acknowledged and op_id not in ids and op_id not in missed
            ids.add(op_id)
            assert item["phase"] == by_id[op_id]["phase"]
            when = datetime.fromisoformat(item["serverCommitTimestampUtc"])
            if t0 <= when < t3:
                possibly += 1
            if t1 <= when < t2:
                certainly += 1
                sec = int((when - t1).total_seconds())
                assert 0 <= sec < 60
                frequency[sec] += 1
        assert ids == set(acknowledged)
        assert certainly == possibly == rate * 60
        assert window["certainCommits"] == window["possibleCommits"] == rate * 60
        assert window["certainCommitsPerSecond"] == (
            window["possibleCommitsPerSecond"]
        ) == rate
        histogram = [frequency[i] for i in range(60)]
        assert window["perSecondCertainCommitHistogram"] == histogram
        assert dict(Counter(histogram)) == expected_freq
        assert observed["latency"]["omittedFailedOrMissedOffersFromLatencyPercentiles"] == expected_miss
        assert observed["latency"]["scheduledToAcknowledgedMsOnly"]["p99"] == p99
        case = next(x for x in record["cases"] if (
            x["offeredPerSecond"], x["route"]
        ) == (rate, route))
        assert case["sourceVectorSha256"] == sha
        assert case["finalSqlStateSha256"] == row["independentSqlStateSha256"]
        pairs[rate][route] = (sha, row["independentSqlStateSha256"])
        totals.update(offers=n, committed=n - expected_miss,
                      missed=expected_miss, inwindow=certainly,
                      postings=observed["postings"],
                      outbox=observed["outboxEvents"], oracles=7, cases=1)
    assert len(pairs) == 2
    assert pairs[160]["direct"] == pairs[160]["orleans"]
    assert pairs[320]["direct"][0] == pairs[320]["orleans"][0]
    assert pairs[320]["direct"][1] != pairs[320]["orleans"][1]
    assert dict(totals) == {
        "offers": 59520, "committed": 59508, "missed": 12,
        "inwindow": 57600, "postings": 119016,
        "outbox": 59508, "oracles": 28, "cases": 4
    }
    return dict(totals)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", type=Path)
    args = p.parse_args()
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    claim_gate(record)
    if args.original_zip:
        totals = original_zip_gate(args.original_zip, record)
        print("E2-B05 original 160/320 ZIP independently SQL-audited "
              + json.dumps(totals, sort_keys=True) + "; NOT a saturation capacity result")
    else:
        print("E2-B05 original 160/320 source CI/artifact SHA and ES/EN evidence "
              "claims pinned; full ZIP not downloaded in this invocation; "
              "NOT a saturation capacity result.")


if __name__ == "__main__":
    main()
