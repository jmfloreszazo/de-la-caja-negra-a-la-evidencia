#!/usr/bin/env python3
"""Fail-closed B05 repeatability evidence audit; optional original ZIP replay.

Offline checks pin the archived evidence claim, original run and original ZIP
SHA. --original-zip additionally recomputes ALL source-vector hashes and
independently checks each original client/SQL trial and paired state hash.
A passing audit is NOT sustained performance or mainframe capacity evidence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence/runs/e2-b05-repeatability-pilot.json"
SHA = "93a7be851b9cd17f4e848cf1ca773c770e2ebc74bfcd651f7bba66f9b0cb4510"
HEAD = "6b546c99f31fdd42f96da9960408df5716dd36c6"


def manifest_gate(record: dict) -> None:
    assert record["schemaVersion"] == 1
    assert record["experiment"] == "E2-B05-External-Repeatability-Pilot"
    assert record["status"] == "CI_VERIFIED_BOUNDED_REPEATABILITY_NOT_CAPACITY"
    assert record["capacityEvidence"] is False
    source = record["source"]
    assert source["originalCiRunId"] == 41204905763
    assert source["sourceHeadSha"] == HEAD
    assert source["sourcePr"] == 39
    assert source["mergedMainSha"] == "8de1e89f27dd7e269e9cccdb1b0d586ab7c0f1ce"
    assert source["originalRawArtifactId"] == 13044531582
    assert source["originalZipSha256"] == SHA
    assert re.fullmatch(r"[0-9a-f]{64}", source["originalZipSha256"])
    assert str(source["originalCiRunId"]) in source["originalCiUrl"]
    assert str(source["originalRawArtifactId"]) in source["originalRawArtifactUrl"]

    setup = record["setup"]
    assert setup["testProfiles"] == ["uniform", "five_percent_hot"]
    assert setup["sourceAccounts"] == 1000 and setup["eligibleHotAccounts"] == 50
    assert setup["offeredArrivalRatesPerSecond"] == [20, 40]
    assert setup["repetitionsPerProfileRate"] == 3
    assert setup["routes"] == ["direct", "orleans"]
    assert (setup["warmupSeconds"], setup["measurementSeconds"],
            setup["cooldownSeconds"]) == (1, 8, 1)
    assert setup["physicalLinuxRunners"] == 1
    assert setup["podmanNetworkNamespaces"] == 4
    assert setup["independentExternalClientProcess"] is True
    assert setup["authoritativeLedger"] == "PostgreSQL"

    audit = record["auditResults"]
    expected = {
        "originalCiChecksPassed": 12, "originalCiChecksTotal": 12,
        "originalZipEntries": 65, "independentMatchedTrialRecords": 24,
        "matchedSourceVectors": 12, "originalScheduledOffers": 7200,
        "independentSqlCommittedOperations": 7200,
        "durablePostings": 14400, "durableOutboxEvents": 7200,
        "sevenSqlOraclesPassedForAllTrials": 168,
        "sevenSqlOraclesTotalForAllTrials": 168,
        "individualClientTimingSamplesAudited": 7200,
        "missedOffers": 0, "ambiguousClientOutcomes": 0,
        "directDurableOperations": 3600,
        "orleansDurableOperations": 3600,
        "routeIdenticalInputAndFinalFourTableStateShaPairs": 12,
        "scheduledMeasurementPhaseOperationsDurableByEndOfTrial": 5760,
    }
    assert all(audit.get(key) == value for key, value in expected.items())
    for key in (
        "independentlyObservedInWindowCommitRatePerSecond",
        "sustainedCapacityThresholdMeasured",
        "steadyStateP99Established", "mainframeMipsEquivalenceMeasured",
    ):
        assert audit.get(key) is None if key.endswith("RatePerSecond") else audit.get(key) is False

    es = record["interpretation"]["es"].lower()
    en = record["interpretation"]["en"].lower()
    assert "7.200" in es and "14.400" in es and "168" in es
    assert "7,200" in en and "14,400" in en and "168" in en
    assert "no" in es and "not" in en
    limits = record["limitations"].lower()
    for term in ("one physical", "eight measured seconds", "mainframe", "partially_verified", "open"):
        assert term in limits, (term, limits)


def original_zip_gate(archive: Path, record: dict) -> dict:
    raw = archive.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record["source"]["originalZipSha256"], (
        "Original ZIP SHA mismatch; never accept a substitute artifact"
    )
    with ZipFile(archive) as z:
        assert z.testzip() is None, "Corrupt original ZIP"
        names = z.namelist()
        assert len(names) == 65 and len(names) == len(set(names)), "File count changed"
        payloads = {
            name: json.loads(z.read(name))
            for name in names if name.endswith(".json")
        }
    summary = payloads["e2-b05-repeatability-summary.json"]
    assert summary["status"] == "PASS_BOUNDED_PILOT_NOT_CAPACITY"
    assert summary["capacityEvidence"] is False
    assert summary["topology"]["physicalHostCount"] == 1
    assert len(set(summary["topology"]["distinctNetworkNamespaces"].values())) == 4
    assert len(summary["runs"]) == 24
    observed = defaultdict(dict)
    totals = defaultdict(int)
    for row in summary["runs"]:
        profile, rate, rep, route = (
            row["profile"], row["offeredRatePerSecond"],
            row["repetition"], row["route"]
        )
        assert profile in ("uniform", "five_percent_hot")
        assert rate in (20, 40) and rep in (0, 1, 2)
        assert route in ("direct", "orleans")
        key = (profile, rate, rep)
        assert route not in observed[key], "Duplicate matched-route result"
        stem = f"{profile}-{rate}tps-r{rep}"
        input_vector = payloads[stem + "-input.json"]
        original_client = payloads[stem + "-" + route + "-client.json"]
        original_observation = payloads[stem + "-" + route + "-observation.json"]
        assert row == original_observation and row["rawClient"] == original_client
        assert input_vector["status"] == "GENERATED_NOT_EXECUTED"
        assert input_vector["capacityEvidence"] is False
        encoded = json.dumps(
            input_vector["operations"], sort_keys=True,
            separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        assert digest == row["offeredVectorSha256"] == input_vector["offeredVectorSha256"]
        offers = input_vector["operations"]
        samples = original_client["samples"]
        assert len(samples) == len(offers) == rate * 10
        assert original_client["offered"] == original_client["dispatched"] == len(samples)
        assert original_client["acknowledgedCommitted"] == len(samples)
        assert original_client["missed"] == original_client["ambiguous"] == 0
        assert row["clientSummary"]["scheduled"] == row["clientSummary"]["dispatched"] == len(samples)
        assert row["clientSummary"]["missed"] == row["clientSummary"]["ambiguous"] == 0
        assert row["measurementPhaseScheduledOffers"] == rate * 8
        assert row["measurementPhaseDurableByRunEnd"] == rate * 8
        assert row["measuredInWindowSqlCommitsPerSecond"] is None
        ids = set()
        for sample, offer in zip(samples, offers):
            assert sample["operationId"] == offer["operationId"]
            assert offer["operationId"] not in ids
            ids.add(offer["operationId"])
            assert sample["phase"] == offer["phase"]
            assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
            assert sample["clientOutcome"] == "ACKNOWLEDGED"
            assert sample["ledgerStatus"] == "COMMITTED"
            assert offer["scheduledAtNs"] <= sample["dispatchedAtNs"] <= sample["completedAtNs"]
        sql = row["independentSql"]
        assert sql["durableCommittedOperationCount"] == len(samples)
        assert sql["postingCount"] == len(samples) * 2
        assert sql["outboxCount"] == len(samples)
        assert len(sql["independentSqlOracle"]) == 7
        assert all(sql["independentSqlOracle"].values())
        observed[key][route] = (digest, sql["stateSha256"])
        totals["offers"] += len(samples)
        totals["postings"] += sql["postingCount"]
        totals["outbox"] += sql["outboxCount"]
        totals["oracle"] += 7
        totals["measurement"] += rate * 8
        totals["trials"] += 1
    assert len(observed) == 12
    for variants in observed.values():
        assert set(variants) == {"direct", "orleans"}
        assert variants["direct"] == variants["orleans"], (
            "Direct and Orleans inputs or persistent results do not match"
        )
    assert dict(totals) == {
        "offers": 7200, "postings": 14400, "outbox": 7200,
        "oracle": 168, "measurement": 5760, "trials": 24
    }
    return dict(totals)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path)
    args = parser.parse_args()
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_gate(record)
    if args.original_zip is not None:
        totals = original_zip_gate(args.original_zip, record)
        print("E2-B05: original immutable ZIP independently audited: "
              + json.dumps(totals, sort_keys=True)
              + "; bounded repeatability only; NOT capacity.")
    else:
        print("E2-B05: original CI/run artifact SHA and bounded ES/EN "
              "evidence CLAIM verified offline; raw ZIP NOT re-downloaded "
              "by this invocation; NOT sustained capacity.")


if __name__ == "__main__":
    main()
