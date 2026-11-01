#!/usr/bin/env python3
"""Real two-Podman-PostgreSQL-container black-box coexistence scenario.

All destructive operations are guarded to the exact disposable database names.
Intentionally negative tests are mandatory; no business G2/G6 promotion.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg

from gateway import (authority as gateway_authority, balance as gateway_balance,
                     shadow as gateway_shadow, transfer as gateway_transfer)

from two_store import (
    UnsafeCutover, bootstrap, connections, independent_oracle, reconcile,
    shadow_prediction, snapshot, stage, transition
)

HERE = Path(__file__).resolve().parent
DURABLE = HERE.parent / "durable"
DLL = DURABLE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"
OUT = HERE.parent.parent / "results" / "brownfield" / "coexistence"
DOTNET = os.environ.get("DOTNET", "dotnet")


def cmd(args: list[str], expected_code: int = 0) -> dict:
    result = subprocess.run(args, text=True, capture_output=True, timeout=50,
                            env=os.environ)
    if result.returncode != expected_code:
        raise AssertionError(
            f"Unexpected exit {result.returncode}, wanted {expected_code}: "
            f"{args}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return json.loads(result.stdout) if expected_code == 0 else {}


def legacy(op: str, source: int, dest: int, amount: int, epoch: int,
           fault: str = "none", code: int = 0) -> dict:
    return cmd([sys.executable, str(HERE / "legacy_api.py"), "transfer",
                op, str(source), str(dest), str(amount), str(epoch), fault],
               expected_code=code)


def candidate(op: str, source: int, dest: int, amount: int, epoch: int,
              fault: str = "none", code: int = 0) -> dict:
    return cmd([DOTNET, str(DLL), "transfer", op, str(source), str(dest),
                str(amount), "candidate", str(epoch), fault], expected_code=code)


def must_block(call, expected_text: str) -> None:
    try:
        call()
    except UnsafeCutover as ex:
        assert expected_text in str(ex), str(ex)
    else:
        raise AssertionError("Unsafe cutover unexpectedly approved")


def assert_sql_healthy(label: str) -> None:
    old, new = connections()
    source = independent_oracle(snapshot(old, "legacy"))
    target = independent_oracle(snapshot(new, "candidate"))
    assert all(source.values()), (label, "source", source)
    assert all(target.values()), (label, "target", target)


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    old_dsn, target_dsn = connections()
    OUT.mkdir(parents=True, exist_ok=True)
    build = subprocess.run([DOTNET, "build", str(DURABLE / "DurableBank"),
                            "-c", "Release", "-m:1", "--disable-build-servers"],
                           capture_output=True, text=True, timeout=240)
    (OUT / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    assert build.returncode == 0, build.stdout + build.stderr
    bootstrap()
    # Two PostgreSQL containers must have different cluster identifiers, not
    # merely two DSNs addressing the same server under different names.
    with psycopg.connect(old_dsn) as source_db, psycopg.connect(target_dsn) as target_db:
        legacy_cluster=source_db.execute("SELECT system_identifier::text FROM pg_control_system()").fetchone()[0]
        candidate_cluster=target_db.execute("SELECT system_identifier::text FROM pg_control_system()").fetchone()[0]
    assert legacy_cluster!=candidate_cluster, "Both databases share one PostgreSQL cluster"
    controls = ["distinctPostgresqlClusterIdentifiers"]
    assert gateway_authority()==("legacy",1)
    assert gateway_balance(1)["routedTo"]=="legacy"
    try:
        gateway_balance(1,1)
        raise AssertionError("Legacy adapter ignored minimum balance version")
    except RuntimeError as ex:
        assert "minimum version" in str(ex)
    controls.append("gatewayRefusesUnavailableLegacyFreshness")

    # Legacy is the only authoritative writer; target remains unchanged.
    with ThreadPoolExecutor(max_workers=5) as pool:
        values = list(pool.map(
            lambda n: legacy(f"SRC-{n}", 1, 2, 10, 1), range(5)))
    assert all(x["status"] == "COMMITTED" for x in values), values
    assert legacy("SRC-0", 1, 2, 10, 1)["status"] == "DUPLICATE_COMMITTED"
    assert gateway_transfer("SRC-0",1,2,10)["routedTo"]=="legacy"
    assert gateway_transfer("SRC-0",1,2,10)["status"]=="DUPLICATE_COMMITTED"
    assert legacy("SRC-0", 1, 2, 11, 1)["status"] == "ID_CONFLICT"
    assert legacy("SRC-REJECT", 1, 2, 200000, 1)["status"] == "REJECTED"
    legacy("SRC-ACK-LOST", 2, 1, 250, 1, fault="lost-ack", code=92)
    assert legacy("SRC-ACK-LOST", 2, 1, 250, 1)["status"] == "DUPLICATE_COMMITTED"
    before_stage = reconcile()
    assert not before_stage["allEqual"]
    assert before_stage["sourceCount"] == 7 and before_stage["targetCount"] == 0
    assert shadow_prediction(2, 1, 100000)["equal"] is False
    controls.append("unmirroredLegacyCannotClaimShadowParity")
    must_block(lambda: transition("candidate", 1), "stores differ")
    controls.append("cutoverBlockedUntilSourceTargetReconciled")

    staged = stage()
    assert staged["status"] == "STAGED_NON_AUTHORITATIVE"
    assert staged["reconciliation"]["allEqual"]
    baseline_target = snapshot(target_dsn, "candidate")
    forecast = shadow_prediction(1, 2, 30)
    assert gateway_shadow(1,2,30)["isActualCandidateExecution"] is False
    assert forecast["equal"] and forecast["targetFinancialWrites"] == 0
    assert snapshot(target_dsn, "candidate") == baseline_target
    controls.append("shadowReadOnlyNoDuplicatePosting")

    # Source changed after staging; no stale cutover is permitted.
    assert legacy("SRC-DRIFT", 4, 5, 300, 1)["status"] == "COMMITTED"
    must_block(lambda: transition("candidate", 1), "stores differ")
    assert stage()["reconciliation"]["allEqual"]
    controls.append("postStageLegacyDriftFalsifiesCutover")

    # Any missing target event prevents promotion even with equal balance totals.
    with psycopg.connect(target_dsn) as db:
        lost_event = db.execute(
            "DELETE FROM brownfield.outbox WHERE operation_id='SRC-0' "
            "RETURNING operation_id,event_type").fetchone()
    assert lost_event is not None
    must_block(lambda: transition("candidate", 1), "stores differ")
    with psycopg.connect(target_dsn) as db:
        db.execute("INSERT INTO brownfield.outbox(operation_id,event_type) "
                   "VALUES (%s,%s)", lost_event)
    assert reconcile()["allEqual"]
    controls.append("missingOutboxBlocksCutover")

    # Valid transition locks the cooperative legacy adapter out of new writes.
    switched = transition("candidate", 1)
    assert (switched["status"], switched["epoch"], switched["todmG6"]) == (
        "SYNTHETIC_CUTOVER", 2, "BLOCK")
    assert legacy("LATE-LEGACY", 1, 2, 10, 1)["status"] == "FENCED_WRITER_OR_EPOCH"
    assert gateway_authority()==("candidate",2)
    assert gateway_transfer("SRC-0",1,2,10)["routedTo"]=="candidate"
    assert gateway_transfer("SRC-0",1,2,10)["status"]=="DUPLICATE_COMMITTED"
    controls.append("capabilityGatewayRoutesOneAuthoritativeWriter")
    assert_sql_healthy("after initial cutover")
    controls.append("lateLegacyEpochFenced")

    # Before any candidate-originated write, identical stores permit a
    # *synthetic* rollback and another deliberate cutover.
    back = transition("legacy", 2)
    assert (back["writer"], back["epoch"]) == ("legacy", 3)
    assert gateway_authority()==("legacy",3)
    assert candidate("STALE-CANDIDATE", 7, 8, 10, 2)["status"] == "FENCED_WRITER_OR_EPOCH"
    assert stage()["reconciliation"]["allEqual"]
    forward = transition("candidate", 3)
    assert forward["epoch"] == 4
    controls.append("reversibleOnlyBeforeCandidateOriginatedWrites")

    source_frozen = snapshot(old_dsn, "legacy")
    assert candidate("CAND-ONE", 7, 8, 400, 4)["status"] == "COMMITTED"
    candidate("CAND-ACK-LOST", 8, 9, 200, 4, fault="lost-ack", code=92)
    assert candidate("CAND-ACK-LOST", 8, 9, 200, 4)["status"] == "DUPLICATE_COMMITTED"
    assert candidate("STALE-CAND-4", 7, 8, 10, 2)["status"] == "FENCED_WRITER_OR_EPOCH"
    assert snapshot(old_dsn, "legacy") == source_frozen
    must_block(lambda: transition("legacy", 4), "FORWARD_FIX_REQUIRED")
    assert_sql_healthy("post candidate writes")
    controls.append("candidateWritesVetoUnsafeRollback")

    # Demonstrate that rogue direct SQL can violate cooperative fencing:
    # do NOT claim this prevents an uncontrolled real incumbent from writing.
    with psycopg.connect(old_dsn) as db:
        db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor+1 "
                   "WHERE account_no=10")
    try:
        assert not all(independent_oracle(snapshot(old_dsn, "legacy")).values())
        must_block(lambda: transition("legacy", 4), "FORWARD_FIX_REQUIRED")
    finally:
        with psycopg.connect(old_dsn) as db:
            db.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor-1 "
                       "WHERE account_no=10")
    assert snapshot(old_dsn, "legacy") == source_frozen
    controls.append("rogueWriterDetectedNotPrevented")

    post = reconcile()
    assert not post["allEqual"]
    assert all(post["sourceOracle"].values())
    assert all(post["targetOracle"].values())
    assert post["targetCount"] == post["sourceCount"] + 2, post
    assert post["todmG6"] == "BLOCK"
    files = [HERE / "legacy_schema.sql", HERE / "legacy_api.py",
             HERE / "two_store.py", HERE / "test_coexistence.py",
             DURABLE / "schema.sql", DURABLE / "DurableBank" / "Program.cs"]
    report = {
        "status": "PASS",
        "classification": "SYNTHETIC_TWO_POSTGRESQL_CONTAINERS_SINGLE_RUNNER",
        "startedUtc": started,
        "endedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": {
            str(path.relative_to(HERE.parent.parent.parent)): hashlib.sha256(
                path.read_bytes()).hexdigest() for path in files
        },
        "completedControls": controls,
        "sourceOperations": post["sourceCount"],
        "targetOperations": post["targetCount"],
        "distinctPostgresqlClusterIdentifiers": True,
        "sourceOracle": post["sourceOracle"],
        "targetOracle": post["targetOracle"],
        "rollback": "BLOCK_FORWARD_FIX_REQUIRED",
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
        "limitations": (
            "Independent logical PostgreSQL containers on one CI host; "
            "no CICS/Db2, no customer Golden Master or mandate, no 2PC, "
            "no post-crash external routing admission journal, no HA. "
            "Direct rogue legacy writes are DETECTED but not prevented."
        )
    }
    (OUT / "two-store-summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
