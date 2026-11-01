#!/usr/bin/env python3
"""Two-store, cooperative, synthetic brownfield migration orchestration.

Two PostgreSQL *containers* store different ledger schemas. A single control
authority lives in the candidate DB. This is NOT CICS fencing, 2PC, production
rollback or independent physical failure domains. All databases are disposable.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import psycopg

HERE = Path(__file__).resolve().parent
DURABLE = HERE.parent / "durable"
TABLES = ("accounts", "operations", "postings", "outbox", "clock")


class UnsafeCutover(ValueError):
    pass


def connections() -> tuple[str, str]:
    if os.environ.get("BROWNFIELD_DISPOSABLE") != "YES":
        raise UnsafeCutover("BROWNFIELD_DISPOSABLE=YES required")
    old = os.environ["BROWNFIELD_LEGACY_DSN"]
    new = os.environ["BROWNFIELD_PG_DSN"]
    for dsn, expected in ((old, "bf_legacy"), (new, "bf_lab")):
        with psycopg.connect(dsn) as db:
            actual = db.execute("SELECT current_database()").fetchone()[0]
            if actual != expected:
                raise UnsafeCutover("Unexpected database: " + actual)
    return old, new


def bootstrap() -> None:
    """Destructively resets ONLY two explicitly checked disposable DBs."""
    old, new = connections()
    with psycopg.connect(old) as db:
        db.execute("DROP SCHEMA IF EXISTS legacy CASCADE")
        db.execute((HERE / "legacy_schema.sql").read_text(encoding="utf-8"))
    with psycopg.connect(new) as db:
        db.execute("DROP SCHEMA IF EXISTS brownfield CASCADE")
        db.execute((DURABLE / "schema.sql").read_text(encoding="utf-8"))


def snapshot(dsn: str, side: str) -> dict[str, Any]:
    """Normalize distinct physical schemas under independent consistent snapshots."""
    assert side in ("legacy", "candidate")
    with psycopg.connect(dsn) as db:
        db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        def rows(sql: str) -> list[tuple]:
            return db.execute(sql).fetchall()
        if side == "legacy":
            accounts = rows("SELECT account_no,ledger_minor,revision "
                            "FROM legacy.accounts ORDER BY account_no")
            operations = rows(
                "SELECT request_id,request_hash,'legacy',authority_epoch,"
                "source_no,destination_no,value_minor,decision "
                "FROM legacy.transactions ORDER BY request_id"
            )
            postings = rows(
                "SELECT request_id,account_no,amount_minor "
                "FROM legacy.entries ORDER BY request_id,account_no"
            )
            outbox = rows(
                "SELECT request_id,kind FROM legacy.notices ORDER BY request_id"
            )
            clock = rows("SELECT sequence_no FROM legacy.clock WHERE singleton=1")[0][0]
        else:
            accounts = rows("SELECT id,balance,version FROM brownfield.accounts ORDER BY id")
            operations = rows(
                "SELECT id,fingerprint,writer,epoch,src,dst,amount,status "
                "FROM brownfield.operations ORDER BY id"
            )
            postings = rows(
                "SELECT operation_id,account_id,delta "
                "FROM brownfield.postings ORDER BY operation_id,account_id"
            )
            outbox = rows(
                "SELECT operation_id,event_type "
                "FROM brownfield.outbox ORDER BY operation_id"
            )
            clock = rows(
                "SELECT watermark FROM brownfield.commit_clock WHERE id=1"
            )[0][0]
    return {
        "accounts": [list(r) for r in accounts],
        "operations": [list(r) for r in operations],
        "postings": [list(r) for r in postings],
        "outbox": [list(r) for r in outbox],
        "clock": clock,
    }


def digest(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def independent_oracle(state: dict) -> dict[str, bool]:
    """Ledger invariants from persisted SQL; not candidate application logic."""
    accounts = {row[0]: row for row in state["accounts"]}
    operations = {row[0]: row for row in state["operations"]}
    by_op: dict[str, list[tuple[int, int]]] = {}
    effect: dict[int, int] = {}
    for op, acc, delta in state["postings"]:
        by_op.setdefault(op, []).append((acc, delta))
        effect[acc] = effect.get(acc, 0) + delta
    committed = {k: v for k, v in operations.items() if v[7] == "COMMITTED"}
    rejected = {k for k, v in operations.items() if v[7] == "REJECTED"}
    outbox = dict(state["outbox"])
    return {
        "fixtureAccounts": sorted(accounts) == list(range(1, 17)),
        "conservedBalances": sum(x[1] for x in accounts.values()) == 1_600_000,
        "balancesFromPostings": all(row[1] == 100000 + effect.get(i, 0)
                                    for i, row in accounts.items()),
        "atomicPairedPostings": (
            set(by_op) == set(committed)
            and len(state["postings"]) == 2 * len(committed)
            and all(sorted(by_op[op]) == sorted([
                (data[4], -data[6]), (data[5], data[6])
            ]) for op, data in committed.items())
        ),
        "exactOutbox": set(outbox) == set(committed)
            and all(event == "TransferCommitted" for event in outbox.values()),
        "rejectedNoEffects": not (rejected & (set(by_op) | set(outbox))),
        "clockMatchesDecisionCount": state["clock"] == len(operations),
        "versionsBounded": all(0 <= row[2] <= state["clock"]
                               for row in accounts.values()),
        "noUnknownDecisions": len(operations) == len(set(operations)),
        "wellFormedFingerprint": all(len(op[1]) == 64 for op in operations.values()),
    }


def reconcile() -> dict:
    """Independent, read-only comparison; a mismatch never silently promotes."""
    old, new = connections()
    source, destination = snapshot(old, "legacy"), snapshot(new, "candidate")
    hashes = {name: {"sourceSha256": digest(source[name]),
                     "targetSha256": digest(destination[name]),
                     "equal": source[name] == destination[name]}
              for name in TABLES}
    source_checks, target_checks = independent_oracle(source), independent_oracle(destination)
    return {
        "classification": "SYNTHETIC_TWO_STORE_NOT_REAL_MAINFRAME",
        "sourceOracle": source_checks, "targetOracle": target_checks,
        "digests": hashes,
        "sourceCount": len(source["operations"]),
        "targetCount": len(destination["operations"]),
        "allEqual": (all(x["equal"] for x in hashes.values())
                     and all(source_checks.values()) and all(target_checks.values())),
        "todmG6": "BLOCK",
    }


def _authority_for_update(control: psycopg.Connection) -> tuple[str, int]:
    row = control.execute(
        "SELECT writer,epoch FROM brownfield.authority WHERE id=1 FOR UPDATE"
    ).fetchone()
    if row is None:
        raise UnsafeCutover("Missing authoritative writer row")
    return row[0], row[1]


def stage() -> dict:
    """Copy legacy read-snapshot into non-authoritative target, never dual-post."""
    old, new = connections()
    with psycopg.connect(new) as ctrl:
        current = _authority_for_update(ctrl)
        if current[0] != "legacy":
            raise UnsafeCutover("Cannot overwrite a candidate-authoritative store")
        src = snapshot(old, "legacy")
        if not all(independent_oracle(src).values()):
            raise UnsafeCutover("Source SQL oracle failed")
        dst = snapshot(new, "candidate")
        if any(op[2] == "candidate" for op in dst["operations"]):
            raise UnsafeCutover("Cannot erase candidate-origin decisions")
        # Another connection and another transaction from the controller:
        # this is a *copy*, not 2PC. Legacy stays authoritative on crash.
        with psycopg.connect(new) as candidate:
            candidate.execute("DELETE FROM brownfield.outbox")
            candidate.execute("DELETE FROM brownfield.postings")
            candidate.execute("DELETE FROM brownfield.operations")
            candidate.execute("DELETE FROM brownfield.accounts")
            for acc, amount, rev in src["accounts"]:
                candidate.execute(
                    "INSERT INTO brownfield.accounts(id,balance,version) "
                    "VALUES (%s,%s,%s)", (acc, amount, rev))
            for (op, fp, writer, epoch, src_account, dst_account,
                 amount, status) in src["operations"]:
                candidate.execute(
                    "INSERT INTO brownfield.operations "
                    "(id,fingerprint,writer,epoch,src,dst,amount,status) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (op, fp, writer, epoch, src_account, dst_account, amount, status))
            for op, account, delta in src["postings"]:
                candidate.execute(
                    "INSERT INTO brownfield.postings(operation_id,account_id,delta) "
                    "VALUES (%s,%s,%s)", (op, account, delta))
            for op, event in src["outbox"]:
                candidate.execute(
                    "INSERT INTO brownfield.outbox(operation_id,event_type) "
                    "VALUES (%s,%s)", (op, event))
            candidate.execute(
                "UPDATE brownfield.commit_clock SET watermark=%s WHERE id=1",
                (src["clock"],))
        result = reconcile()
        if not result["allEqual"]:
            raise UnsafeCutover("Post-stage SQL reconciliation rejected snapshot")
        # ctrl lock is released only after stage is fully reconciled.
        return {"status": "STAGED_NON_AUTHORITATIVE", "reconciliation": result,
                "writer": current[0], "epoch": current[1], "todmG6": "BLOCK"}


def transition(target: str, epoch: int) -> dict:
    if target not in ("candidate", "legacy") or epoch < 1:
        raise UnsafeCutover("Invalid writer or epoch")
    old, new = connections()
    with psycopg.connect(new) as ctrl:
        actual_writer, actual_epoch = _authority_for_update(ctrl)
        if actual_epoch != epoch or actual_writer == target:
            raise UnsafeCutover("Stale writer/epoch or same writer")
        if (actual_writer, target) not in (
            ("legacy", "candidate"), ("candidate", "legacy")
        ):
            raise UnsafeCutover("Invalid transition")
        # Lock excludes compliant in-flight legacy & candidate API calls.
        # An external, non-cooperative IBM Z writer is NOT excluded.
        result = reconcile()
        if not result["allEqual"]:
            raise UnsafeCutover("FORWARD_FIX_REQUIRED: stores differ; rollback unsafe")
        ctrl.execute("UPDATE brownfield.authority "
                     "SET writer=%s,epoch=epoch+1 WHERE id=1", (target,))
        return {"status": "SYNTHETIC_CUTOVER", "writer": target,
                "epoch": actual_epoch + 1, "reconciliation": result,
                "todmG6": "BLOCK"}


def shadow_prediction(source_account: int, dest_account: int, amount: int) -> dict:
    """Side-by-side predictions: NO target transfer is ever executed."""
    if source_account == dest_account or amount <= 0:
        raise ValueError("Bad synthetic request")
    old, new = connections()
    source = dict((i, balance) for i, balance, _ in snapshot(old, "legacy")["accounts"])
    dest = dict((i, balance) for i, balance, _ in snapshot(new, "candidate")["accounts"])
    def forecast(accounts: dict[int, int]) -> str:
        if source_account not in accounts or dest_account not in accounts:
            return "MISSING_ACCOUNT"
        return "COMMITTED" if accounts[source_account] >= amount else "REJECTED"
    return {
        "legacyPrediction": forecast(source),
        "candidatePrediction": forecast(dest),
        "equal": forecast(source) == forecast(dest),
        "targetFinancialWrites": 0,
        "note": "Hypothesis on read-only states; not a banking Golden Master."
    }
