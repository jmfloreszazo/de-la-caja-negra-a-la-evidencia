#!/usr/bin/env python3
"""E1 PostgreSQL candidate. All monetary values are integer cents.

Separate from the protected SQLite baseline. Experimental implementation:
a successful run is NOT evidence of equivalence to the production mainframe.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time

import psycopg

DSN = os.environ.get("E1_PG_DSN", "")
RETRYABLE = {"40P01", "40001", "55P03", "23505"}


def connect():
    if not DSN:
        raise RuntimeError("Set E1_PG_DSN for the disposable experiment database")
    return psycopg.connect(DSN, autocommit=True, connect_timeout=8)


def reset():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with connect() as db:
        with db.transaction():
            db.execute(schema)


def transfer(
    operation: str, src: int, dst: int, amount: int, *,
    fault: str = "none", lock_order: str = "canonical",
    barrier=None, max_attempts: int = 6, lock_timeout_ms: int = 750
):
    """Retry entire local SQL transaction, never a statement inside a failed txn."""
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}", operation):
        raise ValueError("Invalid operation identity")
    if not 1 <= src <= 16 or not 1 <= dst <= 16 or src == dst or not 0 < amount <= 10**12:
        raise ValueError("Invalid transfer arguments")
    if fault not in ("none", "throw-after-debit", "crash-after-debit", "lost-response"):
        raise ValueError("Unsupported injected fault")
    if lock_order not in ("canonical", "source-first"):
        raise ValueError("Unsupported lock order")
    retries, last_error, retried_states = 0, None, []
    start = time.perf_counter()
    for attempt in range(max_attempts):
        try:
            with connect() as db:
                with db.transaction():
                    db.execute("SELECT set_config('lock_timeout', %s, true)",
                               (str(lock_timeout_ms) + "ms",))
                    # Serialize commands with the same request id. A retry after
                    # an ambiguous response must not post twice.
                    db.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                               (operation,))
                    prior = db.execute(
                        "SELECT src,dst,amount,status FROM operations WHERE id=%s",
                        (operation,)
                    ).fetchone()
                    if prior is not None:
                        same = prior[:3] == (src, dst, amount)
                        verdict = "DUPLICATE_" + prior[3] if same else "ID_CONFLICT"
                    else:
                        order = sorted((src, dst)) if lock_order == "canonical" else (src, dst)
                        for i, account in enumerate(order):
                            exists = db.execute(
                                "SELECT id FROM accounts WHERE id=%s FOR UPDATE",
                                (account,)
                            ).fetchone()
                            if not exists:
                                raise ValueError("Missing account")
                            if i == 0 and barrier is not None and attempt == 0:
                                barrier.wait(timeout=10)
                        affected = db.execute(
                            "UPDATE accounts SET balance=balance-%s "
                            "WHERE id=%s AND balance >= %s",
                            (amount, src, amount)
                        ).rowcount
                        if affected:
                            if fault == "throw-after-debit":
                                raise RuntimeError("Injected exception after debit")
                            if fault == "crash-after-debit":
                                os._exit(91)
                            db.execute("UPDATE accounts SET balance=balance+%s WHERE id=%s",
                                       (amount, dst))
                        verdict = "COMMITTED" if affected else "REJECTED"
                        db.execute(
                            "INSERT INTO operations(id,src,dst,amount,status)"
                            " VALUES(%s,%s,%s,%s,%s)",
                            (operation, src, dst, amount, verdict)
                        )
                        if affected:
                            db.execute(
                                "INSERT INTO postings(op,account,delta)"
                                " VALUES(%s,%s,%s),(%s,%s,%s)",
                                (operation, src, -amount, operation, dst, amount)
                            )
                            db.execute("INSERT INTO outbox(op,event) VALUES(%s,%s)",
                                       (operation, "TransferCommitted"))
                # COMMIT is complete before simulating lost acknowledgment.
                if fault == "lost-response" and verdict == "COMMITTED":
                    os._exit(92)
                return {"status": verdict, "retries": retries, "retry_sqlstates": retried_states,
                        "elapsedMs": round((time.perf_counter()-start)*1000, 3)}
        except psycopg.Error as exc:
            last_error = exc.sqlstate
            if exc.sqlstate not in RETRYABLE:
                raise
            retries += 1
            retried_states.append(exc.sqlstate)
            if attempt + 1 < max_attempts:
                time.sleep(.025 * (attempt+1))
    return {"status": "RETRY_EXHAUSTED", "retries": retries,
            "last_sqlstate": last_error, "retry_sqlstates": retried_states,
            "elapsedMs": round((time.perf_counter()-start)*1000, 3)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action", choices=("reset", "transfer", "version"))
    parser.add_argument("args", nargs="*")
    parser.add_argument("--fault", default="none")
    args=parser.parse_args()
    if args.action=="reset":
        reset()
        print("initialized")
    elif args.action=="version":
        with connect() as db:
            print(db.execute("SHOW server_version").fetchone()[0])
    else:
        if len(args.args)!=4:
            parser.error("transfer requires OP SRC DST AMOUNT")
        r=transfer(args.args[0],int(args.args[1]),int(args.args[2]),
                   int(args.args[3]),fault=args.fault)
        print(json.dumps(r))
        if r["status"]=="RETRY_EXHAUSTED":
            raise SystemExit(7)


if __name__=="__main__":
    main()
