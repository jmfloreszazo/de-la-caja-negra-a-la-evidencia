#!/usr/bin/env python3
"""Durable admission/UNKNOWN evidence on three disposable PostgreSQL databases.

The gateway is cooperative and NOT a bank-authorized enforcement boundary.
Controller, legacy and candidate commits are NOT a distributed transaction.
Never infer rollback or a safe second-writer retry from a missing response.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import psycopg

HERE = Path(__file__).resolve().parent
COEX = HERE.parent / "coexistence"
DURABLE = HERE.parent / "durable"
sys.path.insert(0, str(COEX))
from legacy_api import fingerprint
from two_store import (
    UnsafeCutover, connections, independent_oracle, reconcile, snapshot, stage,
    transition as two_store_transition,
)

PENDING = ("ADMITTED", "DISPATCHING", "UNKNOWN", "RECONCILIATION_REQUIRED")
TERMINAL = ("COMMITTED", "REJECTED")


def controller_dsn() -> str:
    connections()  # Also enforce the exact two existing disposable DB names.
    if os.environ.get("BROWNFIELD_DISPOSABLE") != "YES":
        raise UnsafeCutover("Explicit disposable fixture opt-in required")
    dsn = os.environ["BROWNFIELD_CONTROL_DSN"]
    with psycopg.connect(dsn) as db:
        if db.execute("SELECT current_database()").fetchone()[0] != "bf_control":
            raise UnsafeCutover("Refusing controller DB other than bf_control")
    return dsn


def bootstrap_controller() -> None:
    dsn = controller_dsn()
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS controller CASCADE")
        db.execute((HERE / "schema.sql").read_text(encoding="utf-8"))


def _control_authority(db: psycopg.Connection, lock: str = "FOR SHARE") -> tuple[str, int]:
    # Caller-supplied lock is never accepted: these are fixed internal SQL clauses.
    if lock not in ("FOR SHARE", "FOR UPDATE"):
        raise ValueError("Invalid lock mode")
    row = db.execute(
        "SELECT writer,epoch FROM controller.authority WHERE singleton=1 " + lock
    ).fetchone()
    if row is None:
        raise UnsafeCutover("Controller authority is missing")
    return row[0], row[1]


def _check_alignment(writer: str, epoch: int) -> None:
    _, candidate = connections()
    with psycopg.connect(candidate) as db:
        actual = db.execute(
            "SELECT writer,epoch FROM brownfield.authority WHERE id=1"
        ).fetchone()
    if actual != (writer, epoch):
        raise UnsafeCutover("Controller/candidate authority disagreement; BLOCK")


def _validate(operation_id: str, source: int, destination: int,
              amount: int, epoch: int) -> str:
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", operation_id):
        raise ValueError("Invalid operation ID")
    if (source not in range(1, 17) or destination not in range(1, 17)
            or source == destination or not 1 <= amount <= 1_000_000_000_000
            or epoch < 1):
        raise ValueError("Invalid synthetic CAP-007 scope")
    return fingerprint(source, destination, amount)


def _row(db: psycopg.Connection, operation_id: str) -> dict[str, Any] | None:
    with db.cursor() as cur:
        cur.execute(
            "SELECT operation_id,request_hash,writer,epoch,source_account,"
            "destination_account,amount_minor,state FROM controller.admission "
            "WHERE operation_id=%s FOR UPDATE", (operation_id,)
        )
        result = cur.fetchone()
    if result is None:
        return None
    keys = ("id", "hash", "writer", "epoch", "source", "destination", "amount", "state")
    return dict(zip(keys, result))


def _state(db: psycopg.Connection, operation_id: str, state: str) -> None:
    db.execute(
        "UPDATE controller.admission SET state=%s,changed_at=clock_timestamp() "
        "WHERE operation_id=%s", (state, operation_id)
    )


def admit(operation_id: str, source: int, destination: int,
          amount: int, epoch: int) -> dict[str, Any]:
    request_hash = _validate(operation_id, source, destination, amount, epoch)
    with psycopg.connect(controller_dsn()) as db:
        writer, actual_epoch = _control_authority(db)
        _check_alignment(writer, actual_epoch)
        if actual_epoch != epoch:
            raise UnsafeCutover("Stale controller authority epoch")
        prior = _row(db, operation_id)
        if prior is not None:
            if (prior["hash"], prior["source"], prior["destination"], prior["amount"]) != (
                    request_hash, source, destination, amount):
                return {"status": "ID_CONFLICT"}
            if prior["state"] in TERMINAL:
                return {"status": "DUPLICATE_" + prior["state"]}
            return {"status": "UNRESOLVED_PREVIOUS_ADMISSION", "state": prior["state"]}
        db.execute(
            "INSERT INTO controller.admission(operation_id,request_hash,capability_id,"
            "tenant_scope,actor_ref,mandate_ref,writer,epoch,source_account,"
            "destination_account,amount_minor,state) "
            "VALUES (%s,%s,'CAP-007','SYNTHETIC','UNVERIFIED_FIXTURE_ACTOR',"
            "'UNVERIFIED_FIXTURE_MANDATE',%s,%s,%s,%s,%s,'ADMITTED')",
            (operation_id, request_hash, writer, epoch, source, destination, amount)
        )
    return {"status": "ADMITTED", "writer": writer, "epoch": epoch}


def dispatch(operation_id: str, source: int, destination: int,
             amount: int, epoch: int, fault: str = "none") -> dict[str, Any]:
    """Persist admission before remote execution; preserve ambiguity on failure.

    The session advisory lock fences only *this gateway's* concurrent replays.
    A non-cooperating writer bypasses the gateway: this is an explicit gap.
    """
    if fault not in ("none", "adapter-lost-ack", "gateway-after-admit",
                     "gateway-before-send", "gateway-after-send"):
        raise ValueError("Unsupported fault")
    dsn = controller_dsn()
    with psycopg.connect(dsn) as session:
        session.execute("SELECT pg_advisory_lock(hashtextextended(%s,0))",
                        (operation_id,))
        try:
            result = admit(operation_id, source, destination, amount, epoch)
            if result["status"] != "ADMITTED":
                return result
            if fault == "gateway-after-admit":
                os._exit(93)  # Actual process death; admission is already committed.
            with psycopg.connect(dsn) as db:
                writer, current_epoch = _control_authority(db)
                if (writer, current_epoch) != (result["writer"], epoch):
                    raise UnsafeCutover("Writer changed after admission")
                _check_alignment(writer, current_epoch)
                current = _row(db, operation_id)
                if current is None or current["state"] != "ADMITTED":
                    raise UnsafeCutover("Admission missing or corrupted")
                _state(db, operation_id, "DISPATCHING")
            if fault == "gateway-before-send":
                os._exit(94)  # Not proof that a remote side effect is absent.
            if result["writer"] == "legacy":
                command = [sys.executable, str(COEX / "legacy_api.py"),
                           "transfer", operation_id, str(source), str(destination),
                           str(amount), str(epoch),
                           "lost-ack" if fault == "adapter-lost-ack" else "none"]
            else:
                binary = DURABLE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"
                command = [os.environ.get("DOTNET", "dotnet"), str(binary),
                           "transfer", operation_id, str(source), str(destination),
                           str(amount), "candidate", str(epoch),
                           "lost-ack" if fault == "adapter-lost-ack" else "none"]
            try:
                child = subprocess.run(command, capture_output=True, text=True,
                                       timeout=45, env=os.environ)
            except (subprocess.TimeoutExpired, OSError):
                child = None
            if fault == "gateway-after-send":
                os._exit(95)  # Remote COMMIT may already have occurred.
            # Even a normal ACK is NOT final until independently reconciled.
            with psycopg.connect(dsn) as db:
                _state(db, operation_id, "UNKNOWN")
        finally:
            # Session-scoped lock is automatically released on real SIGKILL.
            session.execute("SELECT pg_advisory_unlock(hashtextextended(%s,0))",
                            (operation_id,))
    decision = recover(operation_id)
    if child is not None:
        decision["childExitCode"] = child.returncode
    return decision


def _observed(row: dict[str, Any]) -> tuple[str | None, str]:
    old, new = connections()
    source = snapshot(old, "legacy")
    destination = snapshot(new, "candidate")
    if not all(independent_oracle(source).values()):
        return None, "SOURCE_ORACLE_FAILED"
    if not all(independent_oracle(destination).values()):
        return None, "TARGET_ORACLE_FAILED"
    matches = []
    for side, state in (("legacy", source), ("candidate", destination)):
        for op in state["operations"]:
            if op[0] != row["id"]:
                continue
            if (op[1], op[2], op[3], op[4], op[5], op[6]) != (
                    row["hash"], row["writer"], row["epoch"], row["source"],
                    row["destination"], row["amount"]):
                return None, "FINGERPRINT_OR_EPOCH_CONFLICT"
            matches.append((side, op[7]))
    if not matches:
        return None, "NO_DURABLE_DECISION_OBSERVED"
    origin = [status for side, status in matches if side == row["writer"]]
    copies = [status for side, status in matches if side != row["writer"]]
    # A staged read-only copy can mirror an earlier source operation. It is
    # not proof of independent execution; reject conflicting mirror decisions.
    if len(origin) != 1 or any(s != origin[0] for s in copies):
        return None, "CROSS_STORE_AMBIGUOUS_EFFECT"
    return origin[0], "PERSISTED_SQL_ORACLE_WITH_POSSIBLE_STAGED_COPY"


def recover(operation_id: str) -> dict[str, Any]:
    """No ACK-based verdicts. A missing SQL row stays UNKNOWN, never REJECTED."""
    dsn = controller_dsn()
    with psycopg.connect(dsn) as db:
        # Same operation lock prevents racing an active gateway dispatch.
        db.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                   (operation_id,))
        row = _row(db, operation_id)
        if row is None:
            raise UnsafeCutover("No journal entry for operation")
        if row["state"] not in TERMINAL:
            _state(db, operation_id, "UNKNOWN")
        status, evidence = _observed(row)
        if status is not None:
            _state(db, operation_id, status)
            return {"status": status, "evidence": evidence, "todmG6": "BLOCK"}
        if row["state"] in TERMINAL:
            _state(db, operation_id, "RECONCILIATION_REQUIRED")
        return {"status": "UNKNOWN" if evidence == "NO_DURABLE_DECISION_OBSERVED"
                else "RECONCILIATION_REQUIRED", "evidence": evidence,
                "todmG6": "BLOCK"}


def audit() -> dict[str, Any]:
    """Independent journal-to-ledger cross-check; unmatched effects are blocked."""
    old, new = connections()
    source, destination = snapshot(old, "legacy"), snapshot(new, "candidate")
    with psycopg.connect(controller_dsn()) as db:
        entries = db.execute(
            "SELECT operation_id,request_hash,writer,epoch,source_account,"
            "destination_account,amount_minor,state FROM controller.admission"
        ).fetchall()
    indexed = {r[0]: dict(zip(
        ("id", "hash", "writer", "epoch", "source", "destination", "amount", "state"), r
    )) for r in entries}
    observed = {(op[0], op[2]) for s in (source, destination) for op in s["operations"]}
    missing = sorted({op for op, _ in observed} - set(indexed))
    unresolved = sorted(r[0] for r in entries if r[7] not in TERMINAL)
    invalid = []
    for op_id, row in indexed.items():
        if row["state"] in TERMINAL:
            decision, _ = _observed(row)
            if decision != row["state"]:
                invalid.append(op_id)
    return {
        "passed": not (missing or unresolved or invalid)
          and all(independent_oracle(source).values())
          and all(independent_oracle(destination).values()),
        "unjournaledOperations": missing,
        "unresolved": unresolved,
        "mismatchedFinalDecisions": sorted(invalid),
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
    }


def switch(target: str, epoch: int) -> dict[str, Any]:
    """Cooperative rehearsal: no 2PC. Controller/candidate split must BLOCK."""
    if target not in ("legacy", "candidate"):
        raise UnsafeCutover("Invalid target")
    with psycopg.connect(controller_dsn()) as db:
        writer, actual_epoch = _control_authority(db, "FOR UPDATE")
        if actual_epoch != epoch or writer == target:
            raise UnsafeCutover("Stale transition")
        _check_alignment(writer, epoch)
        before = audit()
        if not before["passed"]:
            raise UnsafeCutover("PENDING_OR_UNJOURNALED_ADMISSION: BLOCK")
        if writer == "legacy" and target == "candidate":
            stage()
        change = two_store_transition(target, epoch)
        db.execute("UPDATE controller.authority SET writer=%s,epoch=epoch+1 "
                   "WHERE singleton=1", (target,))
    return {"status": "SYNTHETIC_SWITCH", "epoch": change["epoch"],
            "writer": target, "todmG6": "BLOCK",
            "warning": "Non-atomic controller/candidate authority update"}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("reset-controller")
    d = sub.add_parser("dispatch")
    d.add_argument("operation_id")
    d.add_argument("source", type=int)
    d.add_argument("destination", type=int)
    d.add_argument("amount", type=int)
    d.add_argument("epoch", type=int)
    d.add_argument("--fault", default="none")
    rec = sub.add_parser("recover")
    rec.add_argument("operation_id")
    sub.add_parser("audit")
    sw = sub.add_parser("switch")
    sw.add_argument("writer", choices=["legacy", "candidate"])
    sw.add_argument("epoch", type=int)
    args = parser.parse_args()
    if args.command == "reset-controller":
        bootstrap_controller()
        response = {"status": "RESET_ONLY_EXACT_DISPOSABLE_DB"}
    elif args.command == "dispatch":
        response = dispatch(args.operation_id, args.source, args.destination,
                            args.amount, args.epoch, args.fault)
    elif args.command == "recover":
        response = recover(args.operation_id)
    elif args.command == "audit":
        response = audit()
    else:
        response = switch(args.writer, args.epoch)
    print(json.dumps(response, sort_keys=True))


if __name__ == "__main__":
    main()
