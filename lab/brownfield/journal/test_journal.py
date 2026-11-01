#!/usr/bin/env python3
"""Original three-disposable-database failure exercise. No bank approval.

Actual subprocess exit codes, independent SQL state and negative controls
are retained. Any failed assertion must FAIL the original CI job.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg

from journal import (
    UnsafeCutover, audit, bootstrap_controller, controller_dsn, dispatch,
    recover, switch,
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

    assert dispatch("J-BASE", 1, 2, 100, 1)["status"] == "COMMITTED"
    assert dispatch("J-BASE", 1, 2, 100, 1)["status"] == "DUPLICATE_COMMITTED"
    assert dispatch("J-BASE", 1, 2, 101, 1)["status"] == "ID_CONFLICT"
    assert dispatch("J-REJECT", 1, 2, 200000, 1)["status"] == "REJECTED"
    assert audit()["passed"]
    controls.append("durableAdmissionIdempotencyAndRejectedDecision")

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
    must_block(lambda: switch("candidate", 1), "PENDING_OR_UNJOURNALED")
    with psycopg.connect(ctrl_dsn) as db:
        from legacy_api import fingerprint
        db.execute("UPDATE controller.admission SET request_hash=%s "
                   "WHERE operation_id='J-BASE'", (fingerprint(1, 2, 100),))
    assert audit()["passed"]
    controls.append("forgedTerminalJournalFailsIndependentOracleAndCutover")

    promoted = switch("candidate", 1)
    assert promoted["writer"] == "candidate" and promoted["epoch"] == 2
    # Source/candidate agreement was established by non-authoritative staging,
    # not by two independent financial executions.
    assert dispatch("J-NEW", 5, 6, 200, 2)["status"] == "COMMITTED"
    assert count(candidate_dsn,
                 "SELECT count(*) FROM brownfield.postings WHERE operation_id=%s",
                 "J-NEW") == 2
    assert count(legacy_dsn,
                 "SELECT count(*) FROM legacy.transactions WHERE request_id=%s",
                 "J-NEW") == 0
    assert audit()["passed"]
    must_block(lambda: switch("legacy", 2), "FORWARD_FIX_REQUIRED")
    controls.append("candidateWritesPreventUnsafeRollback")

    # Process dies after admission, before any remote execution. Even when
    # both SQL stores show NO operation, its uncertainty cannot be a REJECTED
    # verdict or a safe cutover approval.
    cli("dispatch", "J-ADMIT-DEAD", "7", "8", "10", "2",
        "--fault", "gateway-after-admit", expected=93)
    missing = recover("J-ADMIT-DEAD")
    assert missing["status"] == "UNKNOWN" and missing["evidence"] == "NO_DURABLE_DECISION_OBSERVED"
    controls.append("admittedButNotDispatchedStaysUnknown")

    cli("dispatch", "J-DISPATCH-DEAD", "8", "9", "12", "2",
        "--fault", "gateway-before-send", expected=94)
    assert recover("J-DISPATCH-DEAD")["status"] == "UNKNOWN"
    assert not audit()["passed"]
    must_block(lambda: switch("legacy", 2), "PENDING_OR_UNJOURNALED")
    controls.append("crashAfterDispatchMarkBlocksCutoverWithoutRemoteProof")

    # Simulate a controller/target split that can occur between independent
    # commits: any fresh admission must refuse it.
    with psycopg.connect(ctrl_dsn) as db:
        db.execute("UPDATE controller.authority SET epoch=77 WHERE singleton=1")
    must_block(lambda: dispatch("J-SPLIT", 10, 11, 10, 77), "authority disagreement")
    with psycopg.connect(ctrl_dsn) as db:
        db.execute("UPDATE controller.authority SET epoch=2 WHERE singleton=1")
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
        "transfer", "J-DIRECT-BYPASS", "10", "11", "7", "candidate", "2"
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

    # The older permissive mode remains selectable for historical CI. An
    # operator who disables strict controller admission can still bypass it.
    # Demonstrate and DETECT that bypass; do not call opt-in a real bank fence.
    permissive = os.environ.copy()
    permissive["BROWNFIELD_REQUIRE_CONTROLLER"] = "NO"
    permissive.pop("BROWNFIELD_CONTROL_NPGSQL", None)
    direct = subprocess.run(direct_command, capture_output=True, text=True,
                            env=permissive, timeout=35)
    assert direct.returncode == 0 and (
        json.loads(direct.stdout)["status"] == "COMMITTED"
    ), (direct.returncode, direct.stdout, direct.stderr)
    final = audit()
    assert not final["passed"] and len(final["unresolved"]) == 2, final
    assert "J-DIRECT-BYPASS" in final["unjournaledOperations"], final
    controls.append("configurationOptOutBypassDetectedNotPrevented")
    paths = [HERE / "schema.sql", HERE / "journal.py", HERE / "test_journal.py",
             COEX / "legacy_api.py", COEX / "two_store.py",
             DURABLE / "DurableBank" / "Program.cs"]
    report = {
        "status": "PASS",
        "claim": "SYNTHETIC_THREE_POSTGRESQL_CONTAINERS_ON_ONE_CI_RUNNER_C2_PARTIAL",
        "startUtc": start,
        "endUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": {str(p.relative_to(HERE.parent.parent.parent)):
                          hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "completedControls": controls,
        "lastJournalAudit": final,
        "sourceSqlOracle": source_oracle,
        "targetSqlOracle": target_oracle,
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
        "limitations": "Gateway-only cooperative fence; direct adapter calls bypass the third "
                       "controller; non-atomic dual authority commits, no independent "
                       "physical hosts or real incumbent/mandate/approved policy.",
    }
    (RESULTS / "c2-summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
