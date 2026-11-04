#!/usr/bin/env python3
"""Negative and recovery controls against two real disposable PostgreSQL servers."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest
from unittest.mock import patch

import psycopg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "w01_projection"))
import test_projection as baseline
from feed import (
    GENESIS, FeedBlocked, audit, bootstrap, canonical_digest, catchup,
    checked_dsns, event_digest, install_snapshot, source_snapshot, target_state,
)

REPORT = ROOT / "lab/results/brownfield/w01-feed/feed-original.json"


def reset_disposable_feed():
    """Destructive test reset preflighted by original W01 fixture-only harness."""
    baseline.reset_disposable()
    with psycopg.connect(baseline.admin_dsn()) as source:
        source.execute((HERE / "source.sql").read_text(encoding="utf-8"))
        if not source.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='w01_feed_reader')"
        ).fetchone()[0]:
            source.execute(
                "CREATE ROLE w01_feed_reader LOGIN PASSWORD 'w01feedlocal'")
        else:
            source.execute(
                "ALTER ROLE w01_feed_reader LOGIN PASSWORD 'w01feedlocal'")
        source.execute("GRANT USAGE ON SCHEMA legacy TO w01_feed_reader")
        source.execute(
            "GRANT SELECT ON legacy.accounts,legacy.clock,legacy.balance_feed "
            "TO w01_feed_reader")
    with psycopg.connect(os.environ["W01_PROJECTION_DSN"]) as target:
        target.execute((HERE / "target.sql").read_text(encoding="utf-8"))
    return checked_dsns()


def committed_transfer(operation: str, amount=17, debit=1, credit=2,
                       fail_before_commit=False):
    """Test-only writer: ledger, journal, paired entries and clock one COMMIT."""
    with psycopg.connect(baseline.admin_dsn()) as db:
        for account in sorted((debit, credit)):
            db.execute("SELECT 1 FROM legacy.accounts WHERE account_no=%s FOR UPDATE",
                       (account,)).fetchone()
        existing = db.execute(
            "SELECT decision FROM legacy.transactions WHERE request_id=%s",
            (operation,)).fetchone()
        if existing:
            return "DUPLICATE_" + existing[0]
        d_before = db.execute(
            "SELECT ledger_minor FROM legacy.accounts WHERE account_no=%s",
            (debit,)).fetchone()[0]
        c_before = db.execute(
            "SELECT ledger_minor FROM legacy.accounts WHERE account_no=%s",
            (credit,)).fetchone()[0]
        if amount <= 0 or d_before < amount:
            raise ValueError("Invalid disposable operation")
        previous = db.execute(
            "SELECT event_hash FROM legacy.balance_feed "
            "ORDER BY sequence_no DESC LIMIT 1").fetchone()
        previous = previous[0] if previous else GENESIS
        clock = db.execute(
            "UPDATE legacy.clock SET sequence_no=sequence_no+1 "
            "WHERE singleton=1 RETURNING sequence_no").fetchone()[0]
        db.execute("UPDATE legacy.accounts SET ledger_minor=%s,revision=%s "
                   "WHERE account_no=%s", (d_before-amount, clock, debit))
        db.execute("UPDATE legacy.accounts SET ledger_minor=%s,revision=%s "
                   "WHERE account_no=%s", (c_before+amount, clock, credit))
        request_hash = hashlib.sha256(
            f"w01-feed|{debit}|{credit}|{amount}".encode()).hexdigest()
        db.execute(
            "INSERT INTO legacy.transactions(request_id,request_hash,source_no,"
            "destination_no,value_minor,decision,authority_epoch) "
            "VALUES(%s,%s,%s,%s,%s,'COMMITTED',1)",
            (operation,request_hash,debit,credit,amount))
        db.execute(
            "INSERT INTO legacy.entries(request_id,account_no,amount_minor) "
            "VALUES(%s,%s,%s),(%s,%s,%s)",
            (operation,debit,-amount,operation,credit,amount))
        db.execute(
            "INSERT INTO legacy.notices(request_id,kind) "
            "VALUES(%s,'TransferCommitted')", (operation,))
        event = {
            "sequence_no": clock, "request_id": operation,
            "debit_account": debit, "credit_account": credit,
            "amount_minor": amount, "debit_before": d_before,
            "debit_after": d_before-amount, "credit_before": c_before,
            "credit_after": c_before+amount, "previous_hash": previous,
        }
        event["event_hash"] = event_digest(event)
        db.execute(
            "INSERT INTO legacy.balance_feed(sequence_no,request_id,"
            "debit_account,credit_account,amount_minor,debit_before,"
            "debit_after,credit_before,credit_after,previous_hash,event_hash)"
            " VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            tuple(event[k] for k in (
                "sequence_no", "request_id", "debit_account", "credit_account",
                "amount_minor", "debit_before", "debit_after", "credit_before",
                "credit_after", "previous_hash", "event_hash")))
        if fail_before_commit:
            raise FeedBlocked("INJECTED_SOURCE_ABORT_BEFORE_COMMIT")
    return "COMMITTED"


class W01SourceFeedTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = reset_disposable_feed()

    def test_01_empty_consistent_bootstrap(self):
        result = bootstrap()
        self.assertEqual(result["watermark"], 0)
        self.assertEqual(target_state(self.target)["lastHash"], GENESIS)
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_02_committed_source_write_replayed_in_one_batch(self):
        bootstrap()
        self.assertEqual(committed_transfer("F-02"), "COMMITTED")
        result = catchup()
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["eventsApplied"], 1)
        self.assertEqual(target_state(self.target)["watermark"], 1)
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")
        self.assertTrue(all(baseline.ledger_oracle(baseline.admin_dsn()).values()))

    def test_03_batch_one_catches_up_then_noop_replay(self):
        bootstrap()
        for i in range(1, 4):
            committed_transfer(f"F-03-{i}", amount=13 + i)
        results = [catchup(batch_size=1) for _ in range(3)]
        self.assertEqual([r["targetWatermark"] for r in results], [1, 2, 3])
        self.assertEqual(catchup()["status"], "ALREADY_CURRENT")
        self.assertEqual(committed_transfer("F-03-3", amount=16),
                         "DUPLICATE_COMMITTED")
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_04_removed_source_sequence_blocks_without_target_promotion(self):
        bootstrap()
        for i in range(1, 4):
            committed_transfer(f"F-04-{i}")
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("DELETE FROM legacy.balance_feed WHERE sequence_no=2")
        with self.assertRaisesRegex(FeedBlocked, "MISSING_SEQUENCES"):
            catchup()
        self.assertEqual(target_state(self.target)["watermark"], 0)

    def test_05_tampered_pending_event_hash_rejected(self):
        bootstrap()
        committed_transfer("F-05")
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("UPDATE legacy.balance_feed SET event_hash=%s "
                       "WHERE sequence_no=1", ("f"*64,))
        with self.assertRaisesRegex(FeedBlocked, "CORRUPTION"):
            catchup()
        self.assertEqual(target_state(self.target)["watermark"], 0)

    def test_06_valid_hash_but_wrong_previous_chain_rejected(self):
        bootstrap()
        committed_transfer("F-06")
        with psycopg.connect(baseline.admin_dsn()) as db:
            from feed import _events
            event = _events(db)[0]
            event["previous_hash"] = "a"*64
            db.execute(
                "UPDATE legacy.balance_feed SET previous_hash=%s,event_hash=%s "
                "WHERE sequence_no=1",
                (event["previous_hash"], event_digest(event)))
        with self.assertRaisesRegex(FeedBlocked, "CORRUPTION"):
            catchup()

    def test_07_projection_tamper_rejected_before_replay(self):
        bootstrap()
        with psycopg.connect(self.target) as db:
            db.execute("UPDATE projection.feed_accounts SET booked_minor=5 "
                       "WHERE account_no=1")
        committed_transfer("F-07")
        with self.assertRaisesRegex(FeedBlocked, "TARGET_STATE"):
            catchup()

    def test_08_injected_crash_rolls_back_rows_and_cursor_together(self):
        bootstrap()
        committed_transfer("F-08")
        before = target_state(self.target)
        with self.assertRaisesRegex(FeedBlocked, "INJECTED_TARGET_CRASH"):
            catchup(crash_after_rows=True)
        self.assertEqual(before, target_state(self.target))
        self.assertEqual(catchup()["targetWatermark"], 1)
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_09_source_aborted_transaction_has_no_journal_or_money_effect(self):
        bootstrap()
        with self.assertRaisesRegex(FeedBlocked, "INJECTED_SOURCE_ABORT"):
            committed_transfer("F-09", fail_before_commit=True)
        self.assertEqual(source_snapshot(self.source)["watermark"], 0)
        self.assertTrue(all(baseline.ledger_oracle(baseline.admin_dsn()).values()))
        self.assertEqual(catchup()["status"], "ALREADY_CURRENT")

    def test_10_privileged_bypass_same_clock_rejected_by_full_audit(self):
        bootstrap()
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor-1 "
                       "WHERE account_no=1")
            db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor+1 "
                       "WHERE account_no=2")
        with self.assertRaisesRegex(FeedBlocked, "HISTORY_STATE_DIVERGENCE"):
            audit()
        # A clock-only read would miss this. Reconciliation is not continual.

    def test_11_source_checkpoint_committed_after_capture_caught_up(self):
        committed_transfer("F-11-1")
        snap = source_snapshot(self.source)
        self.assertEqual(snap["watermark"], 1)
        committed_transfer("F-11-2")
        install_snapshot(self.target, snap)
        self.assertEqual(target_state(self.target)["watermark"], 1)
        self.assertEqual(catchup()["targetWatermark"], 2)
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_12_restricted_feed_reader_cannot_modify_legacy(self):
        checked_dsns()
        with psycopg.connect(self.source) as db:
            db.execute("SET TRANSACTION READ WRITE")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("UPDATE legacy.accounts SET ledger_minor=0")
        with psycopg.connect(self.source) as db:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("DELETE FROM legacy.balance_feed")
        with psycopg.connect(self.source) as db:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("SELECT request_id FROM legacy.transactions")

    def test_13_source_superuser_connection_rejected(self):
        with patch.dict(os.environ, {"W01_FEED_SOURCE_DSN": baseline.admin_dsn()}):
            with self.assertRaises(FeedBlocked):
                checked_dsns()

    def test_14_bootstrap_with_missing_source_history_rejected(self):
        committed_transfer("F-14")
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("DELETE FROM legacy.balance_feed WHERE sequence_no=1")
        with self.assertRaisesRegex(FeedBlocked, "SOURCE_HISTORY_GAP"):
            bootstrap()
        self.assertIsNone(target_state(self.target))

    def test_15_clock_advanced_without_journal_blocks_catchup(self):
        bootstrap()
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("UPDATE legacy.clock SET sequence_no=1 WHERE singleton=1")
        with self.assertRaisesRegex(FeedBlocked, "MISSING_SEQUENCES"):
            catchup()
        self.assertEqual(target_state(self.target)["watermark"], 0)

    def test_16_deleted_already_applied_history_detected_by_audit(self):
        bootstrap()
        committed_transfer("F-16")
        catchup()
        with psycopg.connect(baseline.admin_dsn()) as db:
            db.execute("DELETE FROM legacy.balance_feed WHERE sequence_no=1")
        # No new feed events; a tail-only consumer cannot detect deletion.
        self.assertEqual(catchup()["status"], "ALREADY_CURRENT")
        with self.assertRaisesRegex(FeedBlocked, "SOURCE_HISTORY_GAP"):
            audit()

    def test_17_source_journal_digest_tied_to_source_account_images(self):
        bootstrap()
        committed_transfer("F-17", amount=101, debit=3, credit=5)
        result = catchup()
        self.assertEqual(result["eventsApplied"], 1)
        self.assertEqual(target_state(self.target)["accounts"][2], [3, 99899, 1])
        self.assertEqual(target_state(self.target)["accounts"][4], [5, 100101, 1])
        self.assertEqual(audit()["status"], "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_18_feed_reader_only_separate_process_without_admin_secret(self):
        bootstrap()
        env = {
            "PATH": os.environ.get("PATH", ""),
            "W01_DISPOSABLE": "YES",
            "W01_FEED_SOURCE_DSN": self.source,
            "W01_FEED_TARGET_DSN": self.target,
        }
        self.assertNotIn("W01_LEGACY_ADMIN_DSN", env)
        proc = subprocess.run(
            [sys.executable, str(HERE/"feed.py"), "audit"],
            env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"],
                         "MATCHED_BOUNDED_SOURCE_SNAPSHOT")

    def test_19_invalid_batch_and_uninitialized_consumer_fail_closed(self):
        with self.assertRaisesRegex(FeedBlocked, "SNAPSHOT_REQUIRED"):
            catchup()
        for batch in (0, 33, True, -1, "1"):
            with self.subTest(batch=batch), self.assertRaises(ValueError):
                catchup(batch_size=batch)

    def test_20_double_bootstrap_cannot_rewind_cursor(self):
        bootstrap()
        committed_transfer("F-20")
        catchup()
        with self.assertRaisesRegex(FeedBlocked, "ALREADY_BOOTSTRAPPED"):
            bootstrap()
        self.assertEqual(target_state(self.target)["watermark"], 1)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(W01SourceFeedTests)
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stderr).run(suite)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = {
        "classification": "REAL_PG_SYNTHETIC_SOURCE_OWNED_JOURNAL_NOT_MAINFRAME_CDC",
        "status": "PASS_BOUNDED_SYNTHETIC_TESTS" if result.wasSuccessful() else "FAIL",
        "headSha": head, "checkoutSha": head,
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python": platform.python_version(), "testsRun": result.testsRun,
        "testsPlanned": 20,
        "passed": result.testsRun - len(result.failures) - len(result.errors)
                  - len(result.skipped),
        "failedCaseIds": [t.id() for t, _ in result.failures + result.errors],
        "negativeControls": [
            "source_feed_gap", "source_hash_tamper", "prev_chain_divergence",
            "target_tamper", "injected_target_partial_commit", "source_abort",
            "unversioned_source_mutation", "missing_old_history",
            "clock_without_feed", "source_role_write_denied", "double_bootstrap"],
        "physicalHosts": 1, "sourceAuthority": "LEGACY",
        "twoPostgresqlClusters": True, "sourceJournalAtomicity": "TEST_HARNESS_SINGLE_SQL_COMMIT",
        "changeCaptureType": "SYNTHETIC_OWNER_WRITTEN_JOURNAL_NOT_CDC",
        "sourceReadRole": "w01_feed_reader", "targetRole": "postgres_TEST_ONLY",
        "scalesToBank": False, "clockReadsLinearizable": False,
        "realIncumbentFence": False, "businessApproval": False,
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps(report, sort_keys=True), flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)
