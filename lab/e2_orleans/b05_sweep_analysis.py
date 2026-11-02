#!/usr/bin/env python3
"""Pure, fail-closed analysis of bounded B05 rate-sweep evidence.

A missed offer is an observed load-generator admission failure, not a
negative business transaction. An exception may hide a durable SQL COMMIT.
No client acknowledgment may substitute for PostgreSQL persisted evidence.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json


def summarize(vector: dict, client: dict, rows: list, postings: list,
              outbox: list, oracles: dict) -> dict:
    offers = vector["operations"]
    offered_ids = {x["operationId"] for x in offers}
    by_id = {x["operationId"]: x for x in offers}
    assert len(offered_ids) == len(offers) == client["offered"]
    samples = client["samples"]
    assert len(samples) == len(offers)
    assert [x["operationId"] for x in samples] == [x["operationId"] for x in offers]
    assert all(oracles.values()) and len(oracles) == 7, oracles

    classes = Counter()
    acknowledged = set()
    missed = set()
    ambiguous = set()
    successful_client_latencies_ms = []
    client_dispatch_delays_ms = []
    for offer, sample in zip(offers, samples):
        assert sample["phase"] == offer["phase"]
        assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
        outcome = sample["clientOutcome"]
        classes[outcome] += 1
        if outcome == "MISSED_OFFER_INFLIGHT_LIMIT":
            missed.add(offer["operationId"])
            assert sample["dispatchedAtNs"] is None
            assert sample["completedAtNs"] is None
            assert sample["ledgerStatus"] is None
        elif outcome == "ACKNOWLEDGED":
            assert sample["ledgerStatus"] == "COMMITTED"
            acknowledged.add(offer["operationId"])
        elif outcome == "AMBIGUOUS_EXCEPTION":
            assert sample["ledgerStatus"] is None
            ambiguous.add(offer["operationId"])
        else:
            raise AssertionError("Unknown client classification: " + outcome)
        if outcome != "MISSED_OFFER_INFLIGHT_LIMIT":
            dispatched = sample["dispatchedAtNs"]
            completed = sample["completedAtNs"]
            assert isinstance(dispatched, int) and isinstance(completed, int)
            assert offer["scheduledAtNs"] <= dispatched <= completed
            client_dispatch_delays_ms.append(
                (dispatched - offer["scheduledAtNs"]) / 1_000_000
            )
            if outcome == "ACKNOWLEDGED":
                successful_client_latencies_ms.append(
                    (completed - offer["scheduledAtNs"]) / 1_000_000
                )

    assert len(missed) == client["missed"]
    assert len(ambiguous) == client["ambiguous"]
    assert len(acknowledged) == client["acknowledgedCommitted"]
    assert len(acknowledged) + len(missed) + len(ambiguous) == len(offers)
    assert client["dispatched"] == len(offers) - len(missed)
    statuses = {op_id: status for op_id, status, _ in rows}
    assert len(statuses) == len(rows) and set(statuses) <= offered_ids, (
        "Unexpected or duplicate durable operation ID", rows
    )
    # This single-cent synthetic scenario has no explicit business rejection
    # command. Any non-COMMITTED operation is a separate correctness failure.
    assert all(status == "COMMITTED" for status in statuses.values()), statuses
    committed = set(statuses)
    assert acknowledged <= committed, (
        "ACKNOWLEDGED as committed but no authoritative SQL operation",
        sorted(acknowledged - committed)
    )
    assert not (missed & committed), (
        "An offer never dispatched was somehow persisted", missed & committed
    )

    posting_counts = Counter(row[0] for row in postings)
    outbox_counts = Counter(row[0] for row in outbox)
    assert set(posting_counts) == set(outbox_counts) == committed
    assert all(posting_counts[op_id] == 2 and outbox_counts[op_id] == 1
               for op_id in committed)
    assert all(ts is not None for _, _, ts in rows), (
        "Every persisted COMMIT must have an original server-side timestamp"
    )

    utc_before = datetime.fromisoformat(client["clockOriginUtcBefore"])
    utc_after = datetime.fromisoformat(client["clockOriginUtcAfter"])
    assert utc_before.tzinfo is not None and utc_after.tzinfo is not None
    bracket_s = (utc_after - utc_before).total_seconds()
    assert 0 <= bracket_s <= .1, ("Clock bracket too wide", bracket_s)
    warmup_s = vector["phases"]["warmup"]["durationSeconds"]
    measurement_s = vector["phases"]["measurement"]["durationSeconds"]
    assert warmup_s == 1 and measurement_s == 60
    t0 = utc_before + timedelta(seconds=warmup_s)
    t1 = utc_after + timedelta(seconds=warmup_s)
    t2 = utc_before + timedelta(seconds=warmup_s + measurement_s)
    t3 = utc_after + timedelta(seconds=warmup_s + measurement_s)
    timestamps = {op_id: ts for op_id, _, ts in rows}
    certain = {op_id for op_id, ts in timestamps.items() if t1 <= ts < t2}
    possible = {op_id for op_id, ts in timestamps.items() if t0 <= ts < t3}
    assert certain <= possible
    bins = Counter(
        int((timestamps[op_id] - t1).total_seconds())
        for op_id in certain
    )
    assert all(0 <= b < measurement_s for b in bins)
    histogram = [bins.get(second, 0) for second in range(measurement_s)]
    measurement_intents = {
        offer["operationId"] for offer in offers
        if offer["phase"] == "measurement"
    }
    def percentiles(values):
        if not values:
            return None
        data = sorted(values)
        def p(q):
            rank = (len(data) - 1) * q / 100
            low = int(rank)
            return round(data[low] + (data[min(low + 1, len(data) - 1)]
                     - data[low]) * (rank - low), 3)
        return {"p50": p(50), "p95": p(95), "p99": p(99), "max": round(data[-1], 3)}

    encoded = json.dumps(
        offers, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    assert digest == vector["offeredVectorSha256"]
    return {
        "classification": "OBSERVED_BOUNDED_RATE_SWEEP_NOT_CAPACITY",
        "capacityEvidence": False,
        "offeredVectorSha256": digest,
        "offered": len(offers),
        "dispatched": client["dispatched"],
        "missed": len(missed),
        "ambiguous": len(ambiguous),
        "acknowledgedCommitted": len(acknowledged),
        "sqlDurableCommittedByRunEnd": len(committed),
        "ambiguousButDurablyCommitted": len(committed & ambiguous),
        "ambiguousWithoutDurableOperation": len(ambiguous - committed),
        "dispatchedButNotDurablyCommitted": len(
            (offered_ids - missed) - committed
        ),
        "measurementPhaseOffered": len(measurement_intents),
        "measurementPhaseDurableByRunEnd": len(measurement_intents & committed),
        "serverCommitWindow": {
            "source": "pg_xact_commit_timestamp(operations.xmin)",
            "serverConfig": "track_commit_timestamp=on",
            "originUtcBefore": utc_before.isoformat(),
            "originUtcAfter": utc_after.isoformat(),
            "originBracketSeconds": round(bracket_s, 6),
            "certainWindowStartUtc": t1.isoformat(),
            "certainWindowEndUtc": t2.isoformat(),
            "possibleWindowStartUtc": t0.isoformat(),
            "possibleWindowEndUtc": t3.isoformat(),
            "measurementSeconds": measurement_s,
            "certainCommits": len(certain),
            "possibleCommits": len(possible),
            "certainCommitsPerSecond": round(len(certain) / measurement_s, 4),
            "possibleCommitsPerSecond": round(len(possible) / measurement_s, 4),
            "certainMeasurementPhaseCommits": len(certain & measurement_intents),
            "possibleMeasurementPhaseCommits": len(possible & measurement_intents),
            "perSecondCertainCommitHistogram": histogram,
            "serverRecordedByOperation": [
                {
                    "operationId": op_id,
                    "phase": by_id[op_id]["phase"],
                    "serverCommitTimestampUtc": ts.isoformat()
                }
                for op_id, ts in sorted(timestamps.items())
            ]
        },
        "latency": {
            "scheduledToAcknowledgedMsOnly": percentiles(
                successful_client_latencies_ms
            ),
            "dispatchDelayMsForDispatchedOnly": percentiles(
                client_dispatch_delays_ms
            ),
            "omittedFailedOrMissedOffersFromLatencyPercentiles": (
                len(missed) + len(ambiguous)
            ),
            "warning": (
                "ACK-only latency percentiles are survivor-biased under overload "
                "and CANNOT be presented as complete service p99/SLA."
            )
        },
        "clientOutcomeCounts": dict(classes),
        "postings": len(postings),
        "outboxEvents": len(outbox),
        "independentSevenSqlOracles": oracles,
        "limits": (
            "One physical Linux runner, no independent load-host or production "
            "SLA. Offered load and UTC-bounded SQL COMMIT interval distinguish "
            "demand from capacity. A failed client outcome may still commit; "
            "no result is inferred solely from ACK. No mainframe MIPS parity."
        )
    }
