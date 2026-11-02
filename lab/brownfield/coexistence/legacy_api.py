#!/usr/bin/env python3
"""Synthetic legacy black-box CLI, deliberately independent of candidate code.

It models an incumbent's external transfer/balance contract with a different
storage schema. It is NOT COBOL/CICS/Db2 and is not a real incumbent fence.
"""
import hashlib
from contextlib import ExitStack
import json
import os
import re
import sys
from time import sleep

import psycopg

RETRYABLE = {"40001", "40P01", "55P03"}


def require_fixture() -> tuple[str, str]:
    if os.environ.get("BROWNFIELD_DISPOSABLE") != "YES":
        raise RuntimeError("Explicit disposable opt-in required")
    legacy = os.environ["BROWNFIELD_LEGACY_DSN"]
    target = os.environ["BROWNFIELD_PG_DSN"]
    for dsn, expected, port in ((legacy, "bf_legacy", "55438"),
                                (target, "bf_lab", "55439")):
        params = psycopg.conninfo.conninfo_to_dict(dsn)
        if any(params.get(extra) for extra in ("hostaddr", "service", "servicefile")) or os.environ.get("PGHOSTADDR") or os.environ.get("PGSERVICE"):
            raise RuntimeError("Connection address overrides are forbidden for disposable fixtures")
        if (params.get("dbname"), params.get("host"), params.get("port")) != (
                expected, "127.0.0.1", port):
            raise RuntimeError("Refusing a non-loopback or non-fixture database")
    with psycopg.connect(legacy) as db:
        if db.execute("SELECT current_database()").fetchone()[0] != "bf_legacy":
            raise RuntimeError("Refusing non-bf_legacy database")
    with psycopg.connect(target) as db:
        if db.execute("SELECT current_database()").fetchone()[0] != "bf_lab":
            raise RuntimeError("Refusing non-bf_lab authority database")
    return legacy, target


def fingerprint(src: int, dst: int, amount: int) -> str:
    # Match the *external request contract* of DurableBank, not its source code.
    canonical = (f"v1|source={src}|destination={dst}|amountMinor={amount}"
                 "|currency=EUR|mandate=SYNTHETIC")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fixture_controller_dsn() -> str:
    """Validate before opening any controller connection, including resets."""
    dsn = os.environ.get("BROWNFIELD_CONTROL_DSN")
    if not dsn:
        raise RuntimeError("C2 controller DSN required: fail closed")
    params = psycopg.conninfo.conninfo_to_dict(dsn)
    if (any(params.get(k) for k in ("hostaddr", "service", "servicefile"))
            or any(os.environ.get(k) for k in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"))
            or (params.get("dbname"), params.get("host"), params.get("port"))
            != ("bf_control", "127.0.0.1", "55440")):
        raise RuntimeError("Only the named, loopback controller fixture is accepted")
    return dsn


def transfer(legacy_dsn: str, control_dsn: str, request_id: str,
             src: int, dst: int, amount: int, epoch: int,
             fault: str = "none") -> dict:
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", request_id) or not (
        1 <= src <= 16 and 1 <= dst <= 16 and src != dst
        and 1 <= amount <= 1_000_000_000_000 and epoch > 0
    ) or fault not in {"none", "lost-ack"}:
        raise ValueError("Invalid synthetic legacy request")
    requested_hash = fingerprint(src, dst, amount)
    with psycopg.connect(control_dsn) as config:
        enrolled = config.execute(
            "SELECT controller_required FROM brownfield.authority WHERE id=1"
        ).fetchone()
        if enrolled is None:
            raise RuntimeError("Missing fixture authority")
    controller_required = enrolled[0] or os.environ.get("BROWNFIELD_REQUIRE_CONTROLLER") == "YES"
    # The central controller is read-locked for the entire remote SQL write.
    # Switch() uses FOR UPDATE: this blocks cutover until this command ends.
    # This is a cooperative fixture; a real unfenced legacy writer may bypass it.
    for attempt in range(6):
        try:
            with ExitStack() as stack:
                # A *cooperating* C2 adapter must hold controller FOR SHARE
                # throughout the remote SQL COMMIT, not merely at admission.
                if controller_required:
                    controller_dsn = fixture_controller_dsn()
                    coordinator = stack.enter_context(psycopg.connect(controller_dsn))
                    if coordinator.execute("SELECT current_database()").fetchone()[0] != "bf_control":
                        raise RuntimeError("Not a disposable bf_control controller")
                    active = coordinator.execute(
                        "SELECT writer,epoch,mode FROM controller.authority "
                        "WHERE singleton=1 FOR SHARE"
                    ).fetchone()
                    if active != ("legacy", epoch, "ACTIVE"):
                        return {"status": "FENCED_CONTROLLER_OR_EPOCH"}
                    # C2 writer-side admission check: gateway intent must
                    # already be durable before this financial SQL COMMIT.
                    admitted = coordinator.execute(
                        "SELECT request_hash,source_account,destination_account,"
                        "amount_minor,state,writer,epoch FROM controller.admission "
                        "WHERE operation_id=%s FOR SHARE", (request_id,)
                    ).fetchone()
                    if admitted != (requested_hash, src, dst, amount,
                                    "DISPATCHING", "legacy", epoch):
                        return {"status": "NOT_ADMITTED_BY_CONTROLLER"}
                ctrl = stack.enter_context(psycopg.connect(control_dsn))
                ctrl.execute("SET LOCAL lock_timeout='750ms'")
                row = ctrl.execute(
                    "SELECT writer,epoch,controller_required FROM brownfield.authority "
                    "WHERE id=1 FOR SHARE").fetchone()
                if row is None or row[:2] != ("legacy", epoch):
                    return {"status": "FENCED_WRITER_OR_EPOCH"}
                # Enrollment may have occurred since the unlocked config read.
                # Refuse this call instead of writing outside the new fence.
                if row[2] and not controller_required:
                    return {"status": "CONTROLLER_ENROLLMENT_CHANGED"}
                with psycopg.connect(legacy_dsn) as old:
                    old.execute("SET LOCAL lock_timeout='750ms'")
                    old.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                                (request_id,))
                    prior = old.execute(
                        "SELECT request_hash,decision FROM legacy.transactions "
                        "WHERE request_id=%s", (request_id,)
                    ).fetchone()
                    if prior:
                        result = {"status": ("DUPLICATE_" + prior[1]
                                             if prior[0] == requested_hash
                                             else "ID_CONFLICT")}
                    else:
                        for account in sorted((src, dst)):
                            assert old.execute(
                                "SELECT account_no FROM legacy.accounts "
                                "WHERE account_no=%s FOR UPDATE", (account,)
                            ).fetchone(), "Missing account in synthetic fixture"
                        debit = old.execute(
                            "UPDATE legacy.accounts "
                            "SET ledger_minor=ledger_minor-%s "
                            "WHERE account_no=%s AND ledger_minor >= %s "
                            "RETURNING account_no", (amount, src, amount)
                        ).fetchone()
                        status = "COMMITTED" if debit else "REJECTED"
                        if debit:
                            old.execute(
                                "UPDATE legacy.accounts "
                                "SET ledger_minor=ledger_minor+%s "
                                "WHERE account_no=%s", (amount, dst))
                        old.execute(
                            "INSERT INTO legacy.transactions"
                            "(request_id,request_hash,source_no,destination_no,"
                            "value_minor,decision,authority_epoch)"
                            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (request_id, requested_hash, src, dst, amount, status, epoch))
                        seq = old.execute(
                            "UPDATE legacy.clock SET sequence_no=sequence_no+1 "
                            "WHERE singleton=1 RETURNING sequence_no"
                        ).fetchone()[0]
                        if debit:
                            old.execute(
                                "UPDATE legacy.accounts SET revision=%s "
                                "WHERE account_no IN (%s,%s)", (seq, src, dst))
                            old.execute(
                                "INSERT INTO legacy.entries(request_id,account_no,amount_minor)"
                                "VALUES (%s,%s,%s),(%s,%s,%s)",
                                (request_id, src, -amount, request_id, dst, amount))
                            old.execute(
                                "INSERT INTO legacy.notices(request_id,kind) "
                                "VALUES (%s,'TransferCommitted')", (request_id,))
                        result = {"status": status, "watermark": seq}
                    # The legacy transaction commits while the control FOR SHARE
                    # lock remains held, before control commits/relinquishes it.
                # Close the control transaction after the legacy COMMIT.
            if fault == "lost-ack" and result["status"] == "COMMITTED":
                os._exit(92)
            return result
        except psycopg.Error as ex:
            if ex.sqlstate not in RETRYABLE or attempt == 5:
                raise
            sleep(0.025 * (attempt + 1))
    raise RuntimeError("Legacy retry policy exhausted")


def balance(dsn: str, account_no: int, minimum_version: int) -> dict:
    if account_no not in range(1, 17) or minimum_version < 0:
        raise ValueError("Invalid balance request")
    with psycopg.connect(dsn) as db:
        db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        watermark = db.execute(
            "SELECT sequence_no FROM legacy.clock WHERE singleton=1"
        ).fetchone()[0]
        row = db.execute(
            "SELECT ledger_minor,revision FROM legacy.accounts WHERE account_no=%s",
            (account_no,)
        ).fetchone()
        if not row:
            return {"status": "MISSING_ACCOUNT"}
        return {"status": ("AUTHORITATIVE" if watermark >= minimum_version
                           else "BELOW_MINIMUM_VERSION"),
                "balanceMinor": row[0], "accountVersion": row[1],
                "watermark": watermark}


def main() -> int:
    try:
        legacy, target = require_fixture()
        if len(sys.argv) == 3 and sys.argv[1] == "balance":
            print(json.dumps(balance(legacy, int(sys.argv[2]), 0)))
            return 0
        if len(sys.argv) in (7, 8) and sys.argv[1] == "transfer":
            _, _, request_id, src, dst, amount, epoch, *fault = sys.argv
            print(json.dumps(transfer(legacy, target, request_id, int(src),
                                      int(dst), int(amount), int(epoch),
                                      fault[0] if fault else "none")))
            return 0
        raise ValueError("Usage: balance <account> | transfer <id> <src> <dst> <amount> <epoch> [fault]")
    except Exception as ex:
        print(f"{type(ex).__name__}: {ex}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
