#!/usr/bin/env python3
"""Original SQL exercise: lose C2 sessions while a debit is uncommitted.

Only three disposable loopback fixtures are reset. Backend 55441 is the
controller test endpoint behind the TCP link at canonical port 55440.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import psycopg

from controller_link import ControllerLink
from journal import (UnsafeCutover, audit, bootstrap_controller, controller_dsn,
                     dispatch, recover, switch)
from two_store import bootstrap, connections, independent_oracle, snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = ROOT / "lab/results/brownfield/journal"


def wait_for(observe, description, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = observe()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for " + description)


def decision_counts(dsn, writer, operation):
    tables = (("legacy.transactions", "request_id"), ("legacy.entries", "request_id"),
              ("legacy.notices", "request_id")) if writer == "legacy" else (
              ("brownfield.operations", "id"), ("brownfield.postings", "operation_id"),
              ("brownfield.outbox", "operation_id"))
    with psycopg.connect(dsn) as db:
        return [db.execute("SELECT count(*) FROM " + table + " WHERE " + key + "=%s",
                           (operation,)).fetchone()[0] for table, key in tables]


def exercise(writer, link, report):
    bootstrap()
    bootstrap_controller()
    legacy, candidate = connections()
    epoch = 1 if writer == "legacy" else switch("candidate", 1)["epoch"]
    dsn = legacy if writer == "legacy" else candidate
    schema = "legacy" if writer == "legacy" else "brownfield"
    table = "transactions" if writer == "legacy" else "operations"
    key = "request_id" if writer == "legacy" else "id"
    operation = "J-LINK-" + writer.upper()
    case = {"writer": writer, "epoch": epoch, "operationId": operation,
            "status": "STARTED"}
    report["cases"].append(case)
    # An independently held SQL advisory lock makes the BEFORE INSERT trigger
    # stop the adapter AFTER debit/credit SQL but BEFORE financial COMMIT.
    with psycopg.connect(dsn) as db:
        db.execute(f"""CREATE FUNCTION {schema}.c2_link_barrier() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN
            IF NEW.{key} = '{operation}' THEN
                PERFORM set_config('lock_timeout','0',true);
                PERFORM pg_advisory_xact_lock(847126);
            END IF; RETURN NEW; END $$""")
        db.execute(f"CREATE TRIGGER c2_link_barrier BEFORE INSERT ON {schema}.{table} "
                   f"FOR EACH ROW EXECUTE FUNCTION {schema}.c2_link_barrier()")
    barrier = psycopg.connect(dsn, autocommit=True)
    barrier.execute("SELECT pg_advisory_lock(847126)")
    barrier_pid = barrier.execute("SELECT pg_backend_pid()").fetchone()[0]
    child = subprocess.Popen(
        [sys.executable, str(HERE / "journal.py"), "dispatch", operation,
         "1", "2", "17", str(epoch)], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        def blocked_adapter():
            with psycopg.connect(dsn) as db:
                return db.execute(
                    "SELECT pid,wait_event_type,wait_event,query FROM pg_stat_activity "
                    "WHERE %s=ANY(pg_blocking_pids(pid)) AND wait_event_type='Lock'",
                    (barrier_pid,)).fetchone()
        observed = wait_for(blocked_adapter, "uncommitted adapter at SQL trigger")
        case["sqlBlockedAdapter"] = list(observed)
        case["beforeCutCounts"] = decision_counts(dsn, writer, operation)
        assert case["beforeCutCounts"] == [0, 0, 0]
        # Read-only backend observation is outside the fault link. This uses
        # the fixed local bf_control test endpoint, never a caller-supplied DSN.
        observer = "host=127.0.0.1 port=55441 dbname=bf_control user=postgres password=bflocal"
        with psycopg.connect(observer) as db:
            db.execute("SET TRANSACTION READ ONLY")
            holders = db.execute(
                "SELECT DISTINCT a.pid FROM pg_stat_activity a JOIN pg_locks l "
                "ON a.pid=l.pid WHERE l.relation='controller.authority'::regclass "
                "AND l.granted AND a.pid<>pg_backend_pid() AND a.xact_start IS NOT NULL"
            ).fetchall()
        assert holders, "Adapter had no controller authority transaction before cut"
        case["controllerTransactionPidsBeforeCut"] = [x[0] for x in holders]
        case["linkCut"] = link.cut()
        assert case["linkCut"]["activeConnections"] >= 2

        def controller_locks_gone():
            with psycopg.connect(observer) as db:
                db.execute("SET TRANSACTION READ ONLY")
                return db.execute("SELECT count(*) FROM pg_stat_activity WHERE pid=ANY(%s)",
                                  (case["controllerTransactionPidsBeforeCut"],)).fetchone()[0] == 0
        wait_for(controller_locks_gone, "actual controller session and lock loss")
        case["controllerSessionsActuallyGone"] = True
        # Existing gateway is killed independently while its financial child
        # remains alive behind the SQL barrier. A retry is a different process.
        child.send_signal(signal.SIGKILL)
        child.wait(timeout=5)
        assert child.returncode == -signal.SIGKILL
        case["gatewayExitCode"] = child.returncode
        try:
            with psycopg.connect(os.environ["BROWNFIELD_CONTROL_DSN"]):
                raise AssertionError("Controller link accepted a connection while cut")
        except psycopg.OperationalError as exc:
            case["blockedReconnect"] = type(exc).__name__
        assert decision_counts(dsn, writer, operation) == [0, 0, 0]
        link.restore()
        unresolved = recover(operation)
        assert unresolved["status"] == "UNKNOWN", unresolved
        assert not audit()["passed"]
        case["recoveredWhileFinancialTransactionInFlight"] = unresolved
        try:
            switch("candidate" if writer == "legacy" else "legacy", epoch)
        except UnsafeCutover as exc:
            assert "PENDING_OR_UNJOURNALED" in str(exc), str(exc)
            case["switchBlockedWhileUnknown"] = str(exc)
        else:
            raise AssertionError("Cutover accepted before durable financial reconciliation")
        barrier.execute("SELECT pg_advisory_unlock(847126)")
        # Predeclared behavior of this cooperative fixture: its separate
        # financial transaction can still COMMIT after losing the controller
        # session. The experiment must NOT claim immediate write cancellation.
        wait_for(lambda: decision_counts(dsn, writer, operation) == [1, 2, 1],
                 "one independently committed financial effect after link loss")
        case["reconciledDecision"] = recover(operation)
        assert case["reconciledDecision"]["status"] == "COMMITTED"
        assert dispatch(operation, 1, 2, 17, epoch)["status"] == "DUPLICATE_COMMITTED"
        case["finalCounts"] = decision_counts(dsn, writer, operation)
        assert case["finalCounts"] == [1, 2, 1]
        case["sourceSqlOracle"] = independent_oracle(snapshot(legacy, "legacy"))
        case["targetSqlOracle"] = independent_oracle(snapshot(candidate, "candidate"))
        assert all(case["sourceSqlOracle"].values()) and all(case["targetSqlOracle"].values())
        assert audit()["passed"]
        case["status"] = "PASS"
    finally:
        link.restore()
        barrier.close()  # Releases the test barrier even after failure.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = child.communicate(timeout=10)
        case["gatewayStdout"], case["gatewayStderr"] = stdout, stderr


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = {"status": "FAIL", "protocol": "C2_INFLIGHT_CONTROLLER_TCP_LOSS_V1",
              "startUtc": datetime.now(timezone.utc).isoformat(), "cases": [],
              "sourceHeadSha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
              "limitations": "Cooperative one-runner TCP session-loss fixture; not a silent "
              "blackhole, directional partition, atomic distributed COMMIT, immediate "
              "write cancellation, real bank fencing, physical HA or RTO/RPO."}
    paths = [HERE / name for name in ("controller_link.py", "test_controller_loss.py", "journal.py")]
    paths += [HERE.parent / "coexistence" / name for name in ("legacy_api.py", "two_store.py", "legacy_schema.sql")]
    paths += [HERE.parent / "durable/DurableBank/Program.cs", HERE.parent / "durable/schema.sql",
              ROOT / ".github/workflows/brownfield-journal.yml", HERE / "schema.sql"]
    report["sourceSha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    try:
        with ControllerLink() as link:
            for writer in ("legacy", "candidate"):
                exercise(writer, link, report)
            report["linkEvents"] = link.events
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = repr(exc)
        raise
    finally:
        report["endUtc"] = datetime.now(timezone.utc).isoformat()
        (RESULTS / "c2-controller-loss.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
