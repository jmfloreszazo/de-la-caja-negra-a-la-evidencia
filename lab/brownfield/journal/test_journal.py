#!/usr/bin/env python3
"""Original three-disposable-database failure exercise. No bank approval.

Actual subprocess exit codes, independent SQL state and negative controls
are retained. Any failed assertion must FAIL the original CI job.
"""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys

import psycopg

from journal import (
    UnsafeCutover, audit, bootstrap_controller, controller_dsn, dispatch,
    recover, recover_switch, switch,
)
HERE = Path(__file__).resolve().parent
COEX = HERE.parent / "coexistence"
DURABLE = HERE.parent / "durable"
RESULTS = HERE.parent.parent / "results" / "brownfield" / "journal"


def cli(*args: str, expected: int = 0) -> dict:
    result = subprocess.run([sys.executable, str(HERE / "journal.py"), *args],
                            capture_output=True, text=True, timeout=70,
                            env=os.environ)
    assert result.returncode == expected, {
        "command": args, "expected": expected, "actual": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr
    }
    return json.loads(result.stdout) if expected == 0 else {}


def count(dsn: str, sql: str, op: str) -> int:
    with psycopg.connect(dsn) as db:
        return db.execute(sql, (op,)).fetchone()[0]


def must_block(callback, marker: str) -> None:
    try:
        callback()
    except UnsafeCutover as exc:
        assert marker in str(exc), str(exc)
    else:
        raise AssertionError("Negative oracle control incorrectly accepted")


def kill_switch(target: str, epoch: int, point: str, observations: list) -> None:
    command = [sys.executable, str(HERE / "journal.py"), "switch", target,
               str(epoch), "--fault", "pause-after-" + point]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env=os.environ)
    try:
        readable, _, _ = select.select([process.stdout], [], [], 40)
        assert readable, "Transition did not reach its durable crash boundary"
        marker = process.stdout.readline().strip()
        assert marker == "TRANSITION_DURABLE_" + point.upper(), marker
        process.send_signal(signal.SIGKILL)
        stdout, stderr = process.communicate(timeout=15)
        assert process.returncode == -signal.SIGKILL, (process.returncode, stderr)
        with psycopg.connect(controller_dsn()) as db:
            controller = db.execute(
                "SELECT writer,epoch,mode FROM controller.authority WHERE singleton=1"
            ).fetchone()
            intent = db.execute(
                "SELECT from_writer,from_epoch,to_writer,to_epoch,state "
                "FROM controller.writer_transition WHERE state='PREPARED'"
            ).fetchone()
        assert controller[2] == "SWITCHING" and intent is not None
        from journal import connections
        _, candidate_dsn = connections()
        with psycopg.connect(candidate_dsn) as db:
            candidate = db.execute(
                "SELECT writer,epoch FROM brownfield.authority WHERE id=1"
            ).fetchone()
        observations.append({"command": command[2:], "marker": marker,
                             "signal": "SIGKILL", "exitCode": process.returncode,
                             "controller": controller, "candidate": candidate,
                             "preparedIntent": intent, "stdout": stdout, "stderr": stderr})
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=15)


def main() -> None:
    from journal import connections
    from two_store import bootstrap, independent_oracle, snapshot
    start = datetime.now(timezone.utc).isoformat()
    legacy_dsn, candidate_dsn = connections()
    ctrl_dsn = controller_dsn()
    RESULTS.mkdir(parents=True, exist_ok=True)
    build = subprocess.run(
        [os.environ.get("DOTNET", "dotnet"), "build", str(DURABLE / "DurableBank"),
         "-c", "Release", "-m:1", "--disable-build-servers"],
        capture_output=True, text=True, timeout=240
    )
    (RESULTS / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    assert build.returncode == 0, "See original build.log"
    bootstrap()  # Explicitly disposable bf_legacy/bf_lab only.
    bootstrap_controller()  # Explicitly disposable bf_control only.
    controls = []
    crashes = []

    # Re-enrollment cannot erase a live admission journal or clear the SQL latch.
    must_block(bootstrap_controller, "fresh disposable ledgers")
    controls.append("enrolledControllerCannotBeResetThroughRuntimeBootstrap")

    # Parse the controller target before connecting to any database. A familiar
    # database name cannot authorize a destructive remote reset.
    from unittest.mock import patch
    for override in (
        "host=192.0.2.1 port=55440 dbname=bf_control",
        "host=127.0.0.1 hostaddr=192.0.2.1 port=55440 dbname=bf_control",
        "host=127.0.0.1 port=55439 dbname=bf_control",
        "host=127.0.0.1 port=55440 dbname=bf_lab",
        "host=127.0.0.1 port=55440 dbname=bf_control service=external",
    ):
        with patch.dict(os.environ, {"BROWNFIELD_CONTROL_DSN": override}):
            with patch("psycopg.connect", side_effect=AssertionError("Unsafe connection attempted")):
                try:
                    controller_dsn()
                except RuntimeError as exc:
                    assert "loopback controller" in str(exc)
                else:
                    raise AssertionError("Unsafe controller DSN accepted")
    controls.append("controllerDsnOverridesRejectedBeforeAnyConnection")

    assert dispatch("J-BASE", 1, 2, 100, 1)["status"] == "COMMITTED"
    assert dispatch("J-BASE", 1, 2, 100, 1)["status"] == "DUPLICATE_COMMITTED"
    assert dispatch("J-BASE", 1, 2, 101, 1)["status"] == "ID_CONFLICT"
    assert dispatch("J-REJECT", 1, 2, 200000, 1)["status"] == "REJECTED"
    assert audit()["passed"]
    controls.append("durableAdmissionIdempotencyAndRejectedDecision")
    with ThreadPoolExecutor(max_workers=4) as pool:
        raced = list(pool.map(lambda _: dispatch("J-RACE", 3, 4, 13, 1), range(6)))
    assert sorted(r["status"] for r in raced) == ["COMMITTED"] + ["DUPLICATE_COMMITTED"] * 5
    assert count(legacy_dsn, "SELECT count(*) FROM legacy.entries WHERE request_id=%s", "J-RACE") == 2
    assert count(legacy_dsn, "SELECT count(*) FROM legacy.notices WHERE request_id=%s", "J-RACE") == 1
    controls.append("concurrentSameIdHasOneDecisionTwoPostingsOneOutbox")

    # Both adapters must fail closed when the C2 controller is unavailable.
    # This verifies the new optional C2 adapter fence under REQUIRE=YES.
    broken = os.environ.copy()
    broken["BROWNFIELD_CONTROL_DSN"] = (
        "host=127.0.0.1 port=1 dbname=bf_control user=postgres password=bflocal connect_timeout=1")
    broken["BROWNFIELD_CONTROL_NPGSQL"] = (
        "Host=127.0.0.1;Port=1;Database=bf_control;Username=postgres;Password=bflocal;Pooling=false;Timeout=1")
    old_call = subprocess.run(
        [sys.executable, str(COEX / "legacy_api.py"), "transfer",
         "J-CONTROLLER-OFF", "9", "10", "20", "1"],
        capture_output=True, text=True, env=broken, timeout=20)
    new_call = subprocess.run(
        [os.environ.get("DOTNET", "dotnet"),
         str(DURABLE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"),
         "transfer", "J-CONTROLLER-OFF-NEW", "9", "10", "20", "legacy", "1"],
        capture_output=True, text=True, env=broken, timeout=20)
    assert old_call.returncode != 0 and new_call.returncode != 0
    assert count(legacy_dsn,
                 "SELECT count(*) FROM legacy.transactions WHERE request_id=%s",
                 "J-CONTROLLER-OFF") == 0
    assert count(candidate_dsn,
                 "SELECT count(*) FROM brownfield.operations WHERE id=%s",
                 "J-CONTROLLER-OFF-NEW") == 0
    controls.append("controllerUnreachableFencesBothCooperatingAdapters")

    # Legacy dies after SQL COMMIT before its external response reaches gateway.
    lost = dispatch("J-LOST", 2, 3, 50, 1, fault="adapter-lost-ack")
    assert lost["status"] == "COMMITTED" and lost["childExitCode"] == 92, lost
    assert count(legacy_dsn, "SELECT count(*) FROM legacy.entries WHERE request_id=%s",
                 "J-LOST") == 2
    assert dispatch("J-LOST", 2, 3, 50, 1)["status"] == "DUPLICATE_COMMITTED"
    controls.append("remoteCommitLostAckIndependentRecoveryExactlyOneLedgerEffect")

    # The *gateway itself* exits without saving the remote success. The next
    # independent process sees persisted DISPATCHING and persisted SQL COMMIT.
    cli("dispatch", "J-GATEWAY", "3", "4", "125", "1",
        "--fault", "gateway-after-send", expected=95)
    with psycopg.connect(ctrl_dsn) as db:
        pending = db.execute(
            "SELECT state FROM controller.admission WHERE operation_id='J-GATEWAY'"
        ).fetchone()[0]
    assert pending == "DISPATCHING", pending
    assert recover("J-GATEWAY")["status"] == "COMMITTED"
    assert dispatch("J-GATEWAY", 3, 4, 125, 1)["status"] == "DUPLICATE_COMMITTED"
    assert count(legacy_dsn, "SELECT count(*) FROM legacy.notices WHERE request_id=%s",
                 "J-GATEWAY") == 1
    controls.append("gatewayCrashAfterRemoteCommitReconcilesDurableDecision")

    # Corrupt a terminal journal claim, not the financial ledger.
    with psycopg.connect(ctrl_dsn) as db:
        db.execute("UPDATE controller.admission SET request_hash=%s "
                   "WHERE operation_id='J-BASE'", ("0" * 64,))
    assert not audit()["passed"]
    assert recover("J-BASE")["status"] == "RECONCILIATION_REQUIRED"
    with psycopg.connect(ctrl_dsn) as db:
        assert db.execute("SELECT state FROM controller.admission "
                          "WHERE operation_id='J-BASE'").fetchone()[0] == "RECONCILIATION_REQUIRED"
    must_block(lambda: switch("candidate", 1), "PENDING_OR_UNJOURNALED")
    with psycopg.connect(ctrl_dsn) as db:
        from legacy_api import fingerprint
        db.execute("UPDATE controller.admission SET request_hash=%s "
                   "WHERE operation_id='J-BASE'", (fingerprint(1, 2, 100),))
    assert recover("J-BASE")["status"] == "COMMITTED"
    assert audit()["passed"]
    controls.append("forgedTerminalJournalFailsIndependentOracleAndCutover")

    # Real external SIGKILL after durable freeze, before candidate authority.
    kill_switch("candidate", 1, "prepare", crashes)
    must_block(lambda: dispatch("J-DURING-FREEZE", 4, 5, 1, 1), "TRANSITION_IN_PROGRESS")
    for command in (
        [sys.executable, str(COEX / "legacy_api.py"), "transfer", "J-FROZEN-OLD", "4", "5", "1", "1"],
        [os.environ.get("DOTNET", "dotnet"), str(DURABLE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"),
         "transfer", "J-FROZEN-NEW", "4", "5", "1", "legacy", "1"],
    ):
        frozen = subprocess.run(command, capture_output=True, text=True, env=os.environ, timeout=35)
        assert frozen.returncode == 0 and json.loads(frozen.stdout)["status"] == "FENCED_CONTROLLER_OR_EPOCH", (
            frozen.stdout, frozen.stderr)
    promoted = recover_switch()
    assert promoted["writer"] == "candidate" and promoted["epoch"] == 2
    assert recover_switch()["status"] == "NO_PENDING_TRANSITION"
    controls.append("sigkillAfterPreparedFreezeBlocksTrafficAndRecoversForward")

    # Before candidate-origin writes, synthetic reversal is still possible.
    # Kill after candidate COMMIT while controller still names candidate/2.
    kill_switch("legacy", 2, "candidate", crashes)
    must_block(lambda: dispatch("J-SPLIT-FREEZE", 4, 5, 1, 2), "TRANSITION_IN_PROGRESS")
    with psycopg.connect(candidate_dsn) as db:
        db.execute("UPDATE brownfield.authority SET epoch=99 WHERE id=1")
    must_block(recover_switch, "UNEXPECTED_AUTHORITY")
    with psycopg.connect(candidate_dsn) as db:
        db.execute("UPDATE brownfield.authority SET epoch=3 WHERE id=1")
        db.execute("DELETE FROM brownfield.outbox WHERE operation_id='J-BASE'")
    must_block(recover_switch, "recovery BLOCK")
    with psycopg.connect(ctrl_dsn) as db:
        assert db.execute("SELECT mode FROM controller.authority WHERE singleton=1").fetchone()[0] == "SWITCHING"
    with psycopg.connect(candidate_dsn) as db:
        db.execute("INSERT INTO brownfield.outbox(operation_id,event_type) "
                   "VALUES ('J-BASE','TransferCommitted')")
    restored = recover_switch()
    assert restored["writer"] == "legacy" and restored["epoch"] == 3
    controls.append("sigkillAfterCandidateAuthorityCommitReconcilesExactPreparedIntent")
    controls.append("unexpectedEpochOrMissingOutboxCannotThawDurableFreeze")
    promoted = switch("candidate", 3)
    assert promoted["epoch"] == 4
    must_block(lambda: dispatch("J-STALE", 4, 5, 1, 1), "Stale controller")
    controls.append("recoveredTransitionsPreserveMonotonicEpochAndRejectStaleReplay")
    # Source/candidate agreement was established by non-authoritative staging,
    # not by two independent financial executions.
    assert dispatch("J-NEW", 5, 6, 200, 4)["status"] == "COMMITTED"
    assert count(candidate_dsn,
                 "SELECT count(*) FROM brownfield.postings WHERE operation_id=%s",
                 "J-NEW") == 2
    assert count(legacy_dsn,
                 "SELECT count(*) FROM legacy.transactions WHERE request_id=%s",
                 "J-NEW") == 0
    assert audit()["passed"]
    must_block(lambda: switch("legacy", 4), "FORWARD_FIX_REQUIRED")
    controls.append("candidateWritesPreventUnsafeRollback")

    # Process dies after admission, before any remote execution. Even when
    # both SQL stores show NO operation, its uncertainty cannot be a REJECTED
    # verdict or a safe cutover approval.
    cli("dispatch", "J-ADMIT-DEAD", "7", "8", "10", "4",
        "--fault", "gateway-after-admit", expected=93)
    missing = recover("J-ADMIT-DEAD")
    assert missing["status"] == "UNKNOWN" and missing["evidence"] == "NO_DURABLE_DECISION_OBSERVED"
    controls.append("admittedButNotDispatchedStaysUnknown")

    cli("dispatch", "J-DISPATCH-DEAD", "8", "9", "12", "4",
        "--fault", "gateway-before-send", expected=94)
    assert recover("J-DISPATCH-DEAD")["status"] == "UNKNOWN"
    assert not audit()["passed"]
    must_block(lambda: switch("legacy", 4), "PENDING_OR_UNJOURNALED")
    controls.append("crashAfterDispatchMarkBlocksCutoverWithoutRemoteProof")

    # Simulate a controller/target split that can occur between independent
    # commits: any fresh admission must refuse it.
    with psycopg.connect(ctrl_dsn) as db:
        db.execute("UPDATE controller.authority SET epoch=77 WHERE singleton=1")
    must_block(lambda: dispatch("J-SPLIT", 10, 11, 10, 77), "authority disagreement")
    with psycopg.connect(ctrl_dsn) as db:
        db.execute("UPDATE controller.authority SET epoch=4 WHERE singleton=1")
    controls.append("controllerCandidateAuthoritySplitFailsClosed")

    # Source remains technically healthy despite intentionally unresolved work.
    from journal import connections
    old, new = connections()
    source_oracle = independent_oracle(snapshot(old, "legacy"))
    target_oracle = independent_oracle(snapshot(new, "candidate"))
    assert all(source_oracle.values()) and all(target_oracle.values())
    # The C2 adapter requires a real journal DISPATCHING admission and
    # controller epoch. A direct bypass in strict mode cannot financially post.
    direct_command = [
        os.environ.get("DOTNET", "dotnet"),
        str(DURABLE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"),
        "transfer", "J-DIRECT-BYPASS", "10", "11", "7", "candidate", "4"
    ]
    strict = subprocess.run(direct_command, capture_output=True, text=True,
                            env=os.environ, timeout=35)
    assert strict.returncode == 0 and (
        json.loads(strict.stdout)["status"] == "NOT_ADMITTED_BY_CONTROLLER"
    ), (strict.returncode, strict.stdout, strict.stderr)
    assert count(candidate_dsn,
                 "SELECT count(*) FROM brownfield.operations WHERE id=%s",
                 "J-DIRECT-BYPASS") == 0
    controls.append("directWithoutAdmissionPreventedInStrictC2Fixture")

    # Enrollment persists in SQL: neither adapter can opt out by stripping
    # process variables. Fresh historical fixtures remain unenrolled.
    permissive = os.environ.copy()
    permissive["BROWNFIELD_REQUIRE_CONTROLLER"] = "NO"
    permissive.pop("BROWNFIELD_CONTROL_NPGSQL", None)
    permissive.pop("BROWNFIELD_CONTROL_DSN", None)
    direct = subprocess.run(direct_command, capture_output=True, text=True,
                            env=permissive, timeout=35)
    assert direct.returncode != 0 and "controller required" in direct.stderr, direct.stderr
    legacy_direct = subprocess.run(
        [sys.executable, str(COEX / "legacy_api.py"), "transfer",
         "J-DIRECT-LEGACY", "10", "11", "7", "4"],
        capture_output=True, text=True, env=permissive, timeout=35)
    assert legacy_direct.returncode != 0 and "controller DSN required" in legacy_direct.stderr
    assert count(candidate_dsn, "SELECT count(*) FROM brownfield.operations WHERE id=%s", "J-DIRECT-BYPASS") == 0
    assert count(legacy_dsn, "SELECT count(*) FROM legacy.transactions WHERE request_id=%s", "J-DIRECT-LEGACY") == 0
    controls.append("sqlEnrollmentPreventsEnvironmentOptOutForBothAdapters")

    # A privileged direct-SQL writer is deliberately outside application
    # enforcement. Preserve this negative control: it must fail journal audit
    # even when the monetary invariants themselves still pass.
    with psycopg.connect(candidate_dsn) as db:
        db.execute("UPDATE brownfield.accounts SET balance=balance-7 WHERE id=10")
        db.execute("UPDATE brownfield.accounts SET balance=balance+7 WHERE id=11")
        db.execute("INSERT INTO brownfield.operations "
                   "(id,fingerprint,writer,epoch,src,dst,amount,status) "
                   "VALUES ('J-RAW-SQL',%s,'candidate',4,10,11,7,'COMMITTED')", (fingerprint(10, 11, 7),))
        clock = db.execute("UPDATE brownfield.commit_clock SET watermark=watermark+1 "
                           "WHERE id=1 RETURNING watermark").fetchone()[0]
        db.execute("UPDATE brownfield.accounts SET version=%s WHERE id IN (10,11)", (clock,))
        db.execute("INSERT INTO brownfield.postings(operation_id,account_id,delta) "
                   "VALUES ('J-RAW-SQL',10,-7),('J-RAW-SQL',11,7)")
        db.execute("INSERT INTO brownfield.outbox(operation_id,event_type) "
                   "VALUES ('J-RAW-SQL','TransferCommitted')")
    final = audit()
    assert not final["passed"] and len(final["unresolved"]) == 2, final
    assert "J-RAW-SQL" in final["unjournaledOperations"], final
    assert all(independent_oracle(snapshot(candidate_dsn, "candidate")).values())
    controls.append("privilegedRawSqlBypassDetectedDespiteBalancedLedger")
    paths = [HERE / "schema.sql", HERE / "journal.py", HERE / "test_journal.py",
             COEX / "legacy_api.py", COEX / "two_store.py",
             DURABLE / "DurableBank" / "Program.cs", DURABLE / "schema.sql"]
    report = {
        "status": "PASS",
        "claim": "SYNTHETIC_THREE_POSTGRESQL_CONTAINERS_ON_ONE_CI_RUNNER_C2_PARTIAL",
        "protocol": "C2_SQL_ENROLLMENT_AND_FROZEN_FORWARD_RECOVERY_V1",
        "sourceHeadSha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip(),
        "startUtc": start,
        "endUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": {str(p.relative_to(HERE.parent.parent.parent)):
                          hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "completedControls": controls,
        "transitionCrashObservations": crashes,
        "lastJournalAudit": final,
        "sourceSqlOracle": source_oracle,
        "targetSqlOracle": target_oracle,
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
        "limitations": "SQL-enrolled cooperative adapters; privileged direct SQL remains outside "
                       "enforcement. Durable freeze and forward recovery, not atomic cross-store "
                       "COMMIT. No in-flight network-partition proof, independent physical "
                       "hosts, real incumbent fence, mandate or approved policy.",
    }
    (RESULTS / "c2-summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
