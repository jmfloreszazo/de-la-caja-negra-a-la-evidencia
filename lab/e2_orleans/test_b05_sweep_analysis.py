#!/usr/bin/env python3
"""Offline negative controls for B05 sweep attribution and overload censoring."""
import hashlib
import json
import unittest
from datetime import datetime, timezone, timedelta

from b05_sweep_analysis import summarize


class SweepAnalysisTests(unittest.TestCase):
    def fixture(self):
        now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
        ops = [
            {
                "operationId": f"op-{i}",
                "phase": "warmup" if i == 0 else "measurement",
                "scheduledAtNs": i * 5_000_000_000
            } for i in range(5)
        ]
        encoded = json.dumps(
            ops, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
        vector = {
            "operations": ops,
            "offeredVectorSha256": hashlib.sha256(encoded).hexdigest(),
            "phases": {
                "warmup": {"durationSeconds": 1},
                "measurement": {"durationSeconds": 60}
            }
        }
        samples = []
        statuses = ("ACKNOWLEDGED", "ACKNOWLEDGED",
                    "AMBIGUOUS_EXCEPTION", "MISSED_OFFER_INFLIGHT_LIMIT",
                    "ACKNOWLEDGED")
        for op, status in zip(ops, statuses):
            missing = status.startswith("MISSED_")
            samples.append({
                "operationId": op["operationId"],
                "phase": op["phase"],
                "scheduledAtNs": op["scheduledAtNs"],
                "clientOutcome": status,
                "ledgerStatus": "COMMITTED" if status == "ACKNOWLEDGED" else None,
                "dispatchedAtNs": None if missing else op["scheduledAtNs"] + 5_000_000,
                "completedAtNs": None if missing else op["scheduledAtNs"] + 80_000_000,
            })
        client = {
            "offered": 5, "dispatched": 4, "missed": 1, "ambiguous": 1,
            "acknowledgedCommitted": 3,
            "clockOriginUtcBefore": now.isoformat(),
            "clockOriginUtcAfter": (now + timedelta(microseconds=2)).isoformat(),
            "samples": samples
        }
        ids = ("op-0", "op-1", "op-2", "op-4")
        rows = [
            (op_id, "COMMITTED", now + timedelta(seconds=2 + i * 10))
            for i, op_id in enumerate(ids)
        ]
        posts = [(op_id, acct, delta)
                 for op_id in ids
                 for acct, delta in ((1, -1), (2, 1))]
        outbox = [(op_id, "{}") for op_id in ids]
        oracle = {f"oracle{i}": True for i in range(7)}
        return vector, client, rows, posts, outbox, oracle

    def test_ambiguity_can_be_durable_without_lying_about_misses(self):
        result = summarize(*self.fixture())
        self.assertEqual(result["offered"], 5)
        self.assertEqual(result["dispatched"], 4)
        self.assertEqual(result["sqlDurableCommittedByRunEnd"], 4)
        self.assertEqual(result["ambiguousButDurablyCommitted"], 1)
        self.assertEqual(result["ambiguousWithoutDurableOperation"], 0)
        self.assertEqual(result["missed"], 1)
        self.assertEqual(result["ambiguous"], 1)
        self.assertFalse(result["capacityEvidence"])
        self.assertEqual(result["postings"], 8)
        self.assertEqual(result["outboxEvents"], 4)
        self.assertEqual(
            result["latency"]["omittedFailedOrMissedOffersFromLatencyPercentiles"], 2
        )
        self.assertEqual(result["serverCommitWindow"]["measurementSeconds"], 60)
        self.assertEqual(len(result["serverCommitWindow"]["perSecondCertainCommitHistogram"]), 60)

    def test_ack_without_authoritative_commit_fails(self):
        args = self.fixture()
        rows = [row for row in args[2] if row[0] != "op-1"]
        with self.assertRaises(AssertionError):
            summarize(args[0], args[1], rows, args[3], args[4], args[5])

    def test_missed_offer_with_durable_commit_fails(self):
        args = self.fixture()
        rows = args[2] + [("op-3", "COMMITTED",
                           datetime(2026, 10, 31, 12, 0, 15,
                                    tzinfo=timezone.utc))]
        with self.assertRaises(AssertionError):
            summarize(args[0], args[1], rows, args[3], args[4], args[5])

    def test_missing_posting_fails(self):
        args = self.fixture()
        with self.assertRaises(AssertionError):
            summarize(args[0], args[1], args[2], args[3][1:], args[4], args[5])

    def test_failed_oracle_fails(self):
        args = self.fixture()
        checks = dict(args[5])
        checks["oracle3"] = False
        with self.assertRaises(AssertionError):
            summarize(*args[:5], checks)

    def test_client_dispatch_cannot_precede_scheduled_offer(self):
        args = self.fixture()
        args[1]["samples"][0]["dispatchedAtNs"] = -1
        with self.assertRaises(AssertionError):
            summarize(*args)

    def test_unknown_client_outcome_fails(self):
        args = self.fixture()
        args[1]["samples"][2]["clientOutcome"] = "SILENT_SUCCESS"
        with self.assertRaises(AssertionError):
            summarize(*args)

    def test_duplicate_sql_operation_id_fails(self):
        args = self.fixture()
        with self.assertRaises(AssertionError):
            summarize(args[0], args[1], args[2] + [args[2][0]],
                      args[3], args[4], args[5])

    def test_original_vector_hash_drift_fails(self):
        args = self.fixture()
        args[0]["operations"][0]["phase"] = "measurement"
        args[1]["samples"][0]["phase"] = "measurement"
        with self.assertRaises(AssertionError):
            summarize(*args)


if __name__ == "__main__":
    unittest.main()
