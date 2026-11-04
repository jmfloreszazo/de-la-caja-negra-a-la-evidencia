#!/usr/bin/env python3
"""Real, disposable PostgreSQL W01 tests with preserved negative outcomes.

No actual mainframe, CDC subscription, bank authorization, HA or production SLO.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import psycopg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from projection import (
    InvalidSource, UnsafeFixture, authoritative_snapshot, balance,
    observed_source_clock, projection_snapshot, refresh, validated_dsns,
    FORBIDDEN_ENV,
)

LEGACY_SCHEMA = HERE.parent / "coexistence" / "legacy_schema.sql"
REPORT = ROOT / "lab/results/brownfield/w01/w01-original.json"


def _checked_reset_dsn(env_key: str, dbname: str, port: str) -> str:
    """Never execute destructive fixture SQL before validating the endpoint."""
    if os.environ.get("W01_DISPOSABLE") != "YES":
        raise UnsafeFixture("Disposable test database requires explicit opt-in")
    if any(os.environ.get(name) for name in FORBIDDEN_ENV):
        raise UnsafeFixture("Implicit PostgreSQL environment overrides prohibited")
    dsn = os.environ[env_key]
    params = psycopg.conninfo.conninfo_to_dict(dsn)
    if (any(params.get(k) for k in ("hostaddr", "service", "servicefile",
                                    "target_session_attrs", "options"))
            or (params.get("host"), params.get("port"), params.get("dbname"),
                params.get("user"))
            != ("127.0.0.1", port, dbname, "postgres")):
        raise UnsafeFixture("Refusing destructive test access outside named fixture")
    with psycopg.connect(dsn) as db:
        if db.execute("SELECT current_database(),current_user").fetchone() != (
                dbname, "postgres"):
            raise UnsafeFixture("Unexpected test database or role identity")
    return dsn


def admin_dsn() -> str:
    """Test-only superuser, never imported by the projection application."""
    return _checked_reset_dsn("W01_LEGACY_ADMIN_DSN", "bf_legacy", "55438")


def reset_disposable() -> tuple[str, str]:
    """Test-only destructive reset, before validating the restricted read role."""
    # Preflight BOTH destructive fixture destinations before touching either.
    # An invalid target cannot trigger an irreversible source reset.
    source_admin = admin_dsn()
    target_admin = _checked_reset_dsn("W01_PROJECTION_DSN", "bf_projection", "55442")
    # Only this test harness contains the superuser credentials. An actual
    # projection process must receive the reader DSN, not the admin DSN.
    with psycopg.connect(source_admin) as db:
        if db.execute("SELECT current_database(),current_user").fetchone() != (
                "bf_legacy", "postgres"):
            raise UnsafeFixture("Wrong source test-admin identity")
        db.execute("DROP SCHEMA IF EXISTS legacy CASCADE")
        db.execute(LEGACY_SCHEMA.read_text(encoding="utf-8"))
        exists = db.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='w01_reader')"
        ).fetchone()[0]
        if not exists:
            db.execute("CREATE ROLE w01_reader LOGIN PASSWORD 'w01readerlocal'")
        else:
            db.execute("ALTER ROLE w01_reader LOGIN PASSWORD 'w01readerlocal'")
        db.execute("REVOKE ALL ON SCHEMA legacy FROM PUBLIC")
        db.execute("REVOKE ALL ON ALL TABLES IN SCHEMA legacy FROM PUBLIC")
        db.execute("GRANT USAGE ON SCHEMA legacy TO w01_reader")
        db.execute("GRANT SELECT ON legacy.accounts,legacy.clock TO w01_reader")
    with psycopg.connect(target_admin) as db:
        if db.execute("SELECT current_database(),current_user").fetchone() != (
                "bf_projection", "postgres"):
            raise UnsafeFixture("Wrong projection database identity")
        db.execute("DROP SCHEMA IF EXISTS projection CASCADE")
        db.execute((HERE / "schema.sql").read_text(encoding="utf-8"))
    return validated_dsns()


def source_transfer(operation: str, amount=83, source_acc=1, target_acc=2):
    """Test writer belongs to the source fixture, never to projection.py."""
    with psycopg.connect(admin_dsn()) as db:
        for acc in sorted((source_acc, target_acc)):
            db.execute(
                "SELECT account_no FROM legacy.accounts WHERE account_no=%s FOR UPDATE",
                (acc,))
        prior = db.execute("SELECT decision FROM legacy.transactions WHERE request_id=%s",
                           (operation,)).fetchone()
        if prior is not None:
            return "DUPLICATE_" + prior[0]
        if db.execute("SELECT ledger_minor FROM legacy.accounts WHERE account_no=%s",
                      (source_acc,)).fetchone()[0] < amount:
            raise AssertionError("Test fixture requires sufficient funds")
        db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor-%s "
                   "WHERE account_no=%s", (amount, source_acc))
        db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor+%s "
                   "WHERE account_no=%s", (amount, target_acc))
        clock = db.execute(
            "UPDATE legacy.clock SET sequence_no=sequence_no+1 "
            "WHERE singleton=1 RETURNING sequence_no").fetchone()[0]
        db.execute("UPDATE legacy.accounts SET revision=%s "
                   "WHERE account_no IN (%s,%s)", (clock, source_acc, target_acc))
        digest = hashlib.sha256(f"w01|{source_acc}|{target_acc}|{amount}".encode()).hexdigest()
        db.execute(
            "INSERT INTO legacy.transactions(request_id,request_hash,source_no,"
            "destination_no,value_minor,decision,authority_epoch) "
            "VALUES (%s,%s,%s,%s,%s,'COMMITTED',1)",
            (operation, digest, source_acc, target_acc, amount))
        db.execute("INSERT INTO legacy.entries(request_id,account_no,amount_minor) "
                   "VALUES (%s,%s,%s),(%s,%s,%s)",
                   (operation, source_acc, -amount, operation, target_acc, amount))
        db.execute("INSERT INTO legacy.notices(request_id,kind) "
                   "VALUES (%s,'TransferCommitted')", (operation,))
    return "COMMITTED"


def ledger_oracle(source: str):
    """Independent persisted-state accounting check, not projection-derived."""
    with psycopg.connect(source) as db:
        db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        balances = db.execute(
            "SELECT account_no,ledger_minor,revision FROM legacy.accounts "
            "ORDER BY account_no").fetchall()
        operations = db.execute(
            "SELECT request_id,source_no,destination_no,value_minor "
            "FROM legacy.transactions WHERE decision='COMMITTED'").fetchall()
        entries = db.execute(
            "SELECT request_id,account_no,amount_minor FROM legacy.entries").fetchall()
        notices = db.execute(
            "SELECT request_id,kind FROM legacy.notices").fetchall()
        clock = db.execute(
            "SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()[0]
    by_op = {}
    for ident, acc, amount in entries:
        by_op.setdefault(ident, []).append((acc, amount))
    committed = {r[0]: r for r in operations}
    return {
        "balanceConservation": sum(r[1] for r in balances) == 1_600_000,
        "pairedPostings": (
            len(entries) == 2 * len(committed)
            and set(by_op) == set(committed)
            and all(sorted(by_op[ident]) == sorted([(r[1], -r[3]), (r[2], r[3])])
                    for ident, r in committed.items())
        ),
        "oneOutbox": (
            len(notices) == len(committed)
            and {r[0] for r in notices} == set(committed)
            and all(r[1] == "TransferCommitted" for r in notices)
        ),
        "clockMatchesDecisions": clock == len(committed),
        "boundedRevisions": all(0 <= r[2] <= clock for r in balances),
    }


class W01ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.source, self.target = reset_disposable()

    def test_01_empty_projection_uses_authoritative_fallback(self):
        result = balance(1)
        self.assertEqual(result["status"], "AUTHORITATIVE_FALLBACK")
        self.assertEqual(result["bookedMinor"], 100000)
        self.assertFalse(result["isSpendableFunds"])

    def test_02_refresh_and_projection_read(self):
        before = authoritative_snapshot(self.source)
        result = refresh()
        self.assertEqual(result["watermark"], 0)
        self.assertEqual(balance(1)["status"], "PROJECTION_OBSERVED_CURRENT")
        self.assertEqual(before, authoritative_snapshot(self.source))
        self.assertTrue(all(ledger_oracle(admin_dsn()).values()))

    def test_03_source_commit_marks_projection_stale_then_fallback(self):
        refresh()
        self.assertEqual(source_transfer("W01-ONE"), "COMMITTED")
        result = balance(1)
        self.assertEqual(result["status"], "AUTHORITATIVE_FALLBACK")
        self.assertEqual(result["bookedMinor"], 99917)
        self.assertEqual(result["sourceWatermark"], 1)
        self.assertEqual(result["projectionWatermark"], 0)
        self.assertTrue(all(ledger_oracle(admin_dsn()).values()))

    def test_04_refresh_catches_up_and_replay_is_idempotent(self):
        refresh()
        source_transfer("W01-TWO")
        before = authoritative_snapshot(self.source)
        first = refresh()
        second = refresh()
        self.assertEqual(first["digest"], second["digest"])
        self.assertEqual(first["watermark"], 1)
        self.assertEqual(projection_snapshot(self.target)["digest"], before["digest"])
        self.assertEqual(source_transfer("W01-TWO"), "DUPLICATE_COMMITTED")
        self.assertEqual(observed_source_clock(self.source), 1)
        self.assertEqual(before, authoritative_snapshot(self.source))
        self.assertEqual(balance(1)["status"], "PROJECTION_OBSERVED_CURRENT")

    def test_05_client_minimum_watermark_uses_source(self):
        refresh()
        source_transfer("W01-THREE")
        result = balance(1, minimum_watermark=1)
        self.assertEqual(result["status"], "AUTHORITATIVE_FALLBACK")
        self.assertEqual(result["sourceWatermark"], 1)

    def test_06_unattainable_minimum_watermark_blocks(self):
        refresh()
        result = balance(1, minimum_watermark=1)
        self.assertEqual(result["status"], "BLOCKED_MINIMUM_WATERMARK")
        self.assertNotIn("bookedMinor", result)

    def test_07_corrupted_projection_forces_fallback_and_repair(self):
        refresh()
        with psycopg.connect(self.target) as conn:
            conn.execute("UPDATE projection.accounts SET booked_minor=42 "
                         "WHERE account_no=1")
        bad = projection_snapshot(self.target)
        self.assertFalse(bad["integrity"])
        self.assertEqual(balance(1)["status"], "AUTHORITATIVE_FALLBACK")
        refresh()
        self.assertTrue(projection_snapshot(self.target)["integrity"])
        self.assertEqual(balance(1)["bookedMinor"], 100000)
        self.assertEqual(balance(1)["status"], "PROJECTION_OBSERVED_CURRENT")

    def test_08_source_writes_without_watermark_refuse_rebuild(self):
        refresh()
        # A privileged/noncooperative writer is outside the synthetic source
        # clock contract; same-clock mutation must not silently be certified.
        with psycopg.connect(admin_dsn()) as conn:
            conn.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor-1 "
                         "WHERE account_no=1")
            conn.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor+1 "
                         "WHERE account_no=2")
        with self.assertRaisesRegex(InvalidSource, "UNVERSIONED_SOURCE_MUTATION"):
            refresh()
        # A watermark-only read cannot discover this mutation at query time.
        # It is deliberately NOT a production source-fencing proof.

    def test_09_regressing_source_clock_refuses_rebuild(self):
        refresh()
        source_transfer("W01-FOUR")
        refresh()
        with psycopg.connect(admin_dsn()) as conn:
            conn.execute("UPDATE legacy.accounts SET revision=0")
            conn.execute("UPDATE legacy.clock SET sequence_no=0 WHERE singleton=1")
        with self.assertRaisesRegex(InvalidSource, "SOURCE_WATERMARK_REGRESSION"):
            refresh()

    def test_10_projection_unavailable_uses_source(self):
        refresh()
        with patch("projection.projection_snapshot", side_effect=psycopg.OperationalError("down")):
            result = balance(1)
        self.assertEqual(result["status"], "AUTHORITATIVE_FALLBACK")

    def test_11_source_unavailable_blocks_even_if_projection_was_valid(self):
        refresh()
        with patch("projection.observed_source_clock", side_effect=psycopg.OperationalError("down")):
            result = balance(1)
        self.assertEqual(result["status"], "BLOCKED_SOURCE_UNAVAILABLE")
        self.assertNotIn("bookedMinor", result)

    def test_12_source_fallback_unavailable_blocks(self):
        refresh()
        source_transfer("W01-FIVE")
        with patch("projection.authoritative_snapshot", side_effect=psycopg.OperationalError("down")):
            result = balance(1)
        self.assertEqual(result["status"], "BLOCKED_FALLBACK_UNAVAILABLE")
        self.assertNotIn("bookedMinor", result)

    def test_13_invalid_read_inputs_rejected(self):
        for account, minimum in ((0, 0), (17, 0), (True, 0), (1, -1),
                                 (1, True), ("1", 0)):
            with self.subTest(account=account, minimum=minimum):
                with self.assertRaises(ValueError):
                    balance(account, minimum)

    def test_14_nonloopback_and_missing_optin_refused(self):
        with patch.dict(os.environ, {"W01_DISPOSABLE": "NO"}):
            with self.assertRaises(UnsafeFixture):
                validated_dsns()
        with patch.dict(os.environ, {"W01_LEGACY_DSN":
                                     "host=192.0.2.1 port=55438 dbname=bf_legacy user=w01_reader"}):
            with self.assertRaises(UnsafeFixture):
                validated_dsns()

    def test_15_two_actual_database_clusters_but_one_physical_runner(self):
        with psycopg.connect(admin_dsn()) as s, psycopg.connect(self.target) as p:
            sid = s.execute("SELECT system_identifier FROM pg_control_system()").fetchone()[0]
            pid = p.execute("SELECT system_identifier FROM pg_control_system()").fetchone()[0]
        self.assertNotEqual(sid, pid)

    def test_16_source_financial_tables_unchanged_by_repeated_projection_reads(self):
        source_transfer("W01-SIX")
        state_before = authoritative_snapshot(self.source)
        financial_before = ledger_oracle(admin_dsn())
        refresh()
        for _ in range(3):
            self.assertEqual(balance(1)["status"], "PROJECTION_OBSERVED_CURRENT")
        self.assertEqual(state_before, authoritative_snapshot(self.source))
        self.assertEqual(financial_before, ledger_oracle(admin_dsn()))
        self.assertTrue(all(financial_before.values()))

    def test_17_source_reader_sql_permissions_reject_financial_mutations(self):
        """SQL privilege rejection, even after session chooses READ WRITE."""
        with psycopg.connect(self.source) as db:
            db.execute("SET TRANSACTION READ WRITE")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("UPDATE legacy.accounts SET ledger_minor=0 WHERE account_no=1")
        with psycopg.connect(self.source) as db:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("UPDATE legacy.clock SET sequence_no=1 WHERE singleton=1")
        with psycopg.connect(self.source) as db:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("SELECT request_id FROM legacy.transactions")
        self.assertTrue(all(ledger_oracle(admin_dsn()).values()))

    def test_18_reader_only_cli_has_no_test_admin_credentials(self):
        """Separate process gets only the reader secret, never source superuser."""
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "W01_DISPOSABLE": "YES",
            "W01_LEGACY_DSN": self.source,
            "W01_PROJECTION_DSN": self.target,
        }
        self.assertNotIn("W01_LEGACY_ADMIN_DSN", environment)
        p = subprocess.run(
            [sys.executable, str(HERE / "projection.py"), "balance", "1"],
            env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        payload = json.loads(p.stdout)
        self.assertEqual(payload["status"], "AUTHORITATIVE_FALLBACK")
        self.assertEqual(payload["sourceAuthority"], "LEGACY")
        self.assertFalse(payload["isSpendableFunds"])

    def test_19_application_rejects_postgres_superuser_as_source(self):
        with patch.dict(os.environ, {"W01_LEGACY_DSN": admin_dsn()}):
            with self.assertRaises(UnsafeFixture):
                validated_dsns()

    def test_20_both_destructive_endpoints_preflight_before_reset(self):
        before = authoritative_snapshot(self.source)
        with patch.dict(os.environ, {"W01_PROJECTION_DSN":
                                     "host=192.0.2.1 port=55442 dbname=bf_projection user=postgres"}):
            with self.assertRaises(UnsafeFixture):
                reset_disposable()
        self.assertEqual(authoritative_snapshot(self.source), before)
        with patch.dict(os.environ, {"W01_LEGACY_ADMIN_DSN":
                                     "host=192.0.2.1 port=55438 dbname=bf_legacy user=postgres"}):
            with self.assertRaises(UnsafeFixture):
                reset_disposable()
        self.assertEqual(authoritative_snapshot(self.source), before)



if __name__ == "__main__":
    import datetime
    import platform

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(W01ProjectionTests)
    count = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stderr).run(suite)
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    case_failures = [case.id() for case, _ in result.failures + result.errors]
    report = {
        "classification": "REAL_POSTGRESQL_SYNTHETIC_W01_NOT_BANK_ACCEPTANCE",
        "status": "PASS_BOUNDED_SYNTHETIC_TESTS" if result.wasSuccessful() else "FAIL",
        "sourceHeadSha": source_sha, "checkoutSha": source_sha,
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python": platform.python_version(), "testsRun": result.testsRun,
        "testsPlanned": count,
        "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "failedCaseIds": case_failures,
        "negativeControls": ["projection_corruption", "unknown_source_write",
                             "watermark_regression", "source_sql_role_denial",
                             "reader_only_cli", "superuser_dsn_denial",
                             "preflight_destructive_endpoints", "source_failure",
                             "source_fallback_failure", "invalid_endpoint"],
        "physicalHosts": 1, "independentFailureDomains": False,
        "sourceAuthority": "LEGACY", "sourceReadOnlyInProjectionCode": True,
        "sourceReaderRole": "w01_reader", "sourceSuperuserRejected": True,
        "sourceFinancialWritesDeniedByDatabase": True,
        "readFreshness": "SAMPLED_WATERMARK_NOT_LINEARIZABLE",
        "incrementalCdcImplemented": False, "isSpendableBalance": False,
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
        "customerApproval": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps(report, sort_keys=True), flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)
