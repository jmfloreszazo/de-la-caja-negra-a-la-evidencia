#!/usr/bin/env python3
"""W01 synthetic source-owned transactional change feed and bounded catch-up.

No external CDC, bank-grade change data capture, source fencing or linearizable
banking balance. No superuser source credentials are used by this application.
"""
from __future__ import annotations

import hashlib
import json
import os

import psycopg

GENESIS = "0" * 64
ALLOWED = {
    "W01_FEED_SOURCE_DSN": ("bf_legacy", "55438", "w01_feed_reader"),
    "W01_FEED_TARGET_DSN": ("bf_projection", "55442", "postgres"),
}
SOURCE_TABLES = ("legacy.accounts", "legacy.clock", "legacy.balance_feed",
                 "legacy.transactions", "legacy.entries", "legacy.notices")
READABLE = {"legacy.accounts", "legacy.clock", "legacy.balance_feed"}
DML = ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "TRIGGER", "REFERENCES")
EVENT_KEYS = ("sequence_no", "request_id", "debit_account", "credit_account",
              "amount_minor", "debit_before", "debit_after",
              "credit_before", "credit_after", "previous_hash", "event_hash")
MAX_HISTORY = 256  # Deliberately bounded synthetic ledger; no large-bank SLO.


class FeedBlocked(RuntimeError):
    """Refused or ambiguous state; do not publish a cursor or financial read."""


def canonical_digest(sequence: int, accounts: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(
        {"watermark": sequence, "accounts": accounts},
        sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


def event_digest(event: dict) -> str:
    return hashlib.sha256(json.dumps(
        {key: event[key] for key in EVENT_KEYS if key != "event_hash"},
        sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()


def checked_dsns() -> tuple[str, str]:
    """Fail closed unless exact two disposable loopback identities are present."""
    if os.environ.get("W01_DISPOSABLE") != "YES":
        raise FeedBlocked("Disposable-only W01 opt-in is missing")
    if any(os.environ.get(k) for k in (
            "PGHOST", "PGHOSTADDR", "PGDATABASE", "PGPORT", "PGUSER",
            "PGOPTIONS", "PGSERVICE", "PGSERVICEFILE")):
        raise FeedBlocked("Implicit PostgreSQL connection overrides prohibited")
    found = []
    for key, expected in ALLOWED.items():
        dsn = os.environ.get(key)
        if not dsn:
            raise FeedBlocked("Missing " + key)
        params = psycopg.conninfo.conninfo_to_dict(dsn)
        if (any(params.get(k) for k in (
                "hostaddr", "service", "servicefile", "options",
                "target_session_attrs"))
                or (params.get("dbname"), params.get("port"), params.get("user"))
                != expected or params.get("host") != "127.0.0.1"):
            raise FeedBlocked("Non-disposable or privileged connection refused")
        with psycopg.connect(dsn) as conn:
            if conn.execute("SELECT current_database(),current_user").fetchone() != (
                    expected[0], expected[2]):
                raise FeedBlocked("Unexpected effective database/role")
            if key == "W01_FEED_SOURCE_DSN":
                privileged = conn.execute(
                    "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,"
                    "rolbypassrls FROM pg_roles WHERE rolname=current_user"
                ).fetchone()
                if privileged is None or any(privileged):
                    raise FeedBlocked("Source feed reader has privileged role flags")
                if conn.execute(
                        "SELECT has_schema_privilege(current_user,'legacy','CREATE')"
                ).fetchone()[0]:
                    raise FeedBlocked("Source feed reader can create legacy objects")
                for table in SOURCE_TABLES:
                    can_select = conn.execute(
                        "SELECT has_table_privilege(current_user,%s,'SELECT')",
                        (table,)).fetchone()[0]
                    if can_select != (table in READABLE):
                        raise FeedBlocked("Wrong source SELECT grants: " + table)
                    for permission in DML:
                        if conn.execute(
                            "SELECT has_table_privilege(current_user,%s,%s)",
                            (table, permission)).fetchone()[0]:
                            raise FeedBlocked("Source feed role can mutate: " + table)
        found.append(dsn)
    return found[0], found[1]


def _events(conn, lower=0, upper=None, limit=None) -> list[dict]:
    if upper is None:
        cur = conn.execute(
            "SELECT " + ",".join(EVENT_KEYS) + " FROM legacy.balance_feed "
            "WHERE sequence_no>%s ORDER BY sequence_no", (lower,))
    else:
        cur = conn.execute(
            "SELECT " + ",".join(EVENT_KEYS) + " FROM legacy.balance_feed "
            "WHERE sequence_no>%s AND sequence_no<=%s "
            "ORDER BY sequence_no LIMIT %s", (lower, upper, limit))
    return [dict(zip(EVENT_KEYS, row)) for row in cur.fetchall()]


def _check_event(event, seq: int, previous: str) -> None:
    if (event["sequence_no"] != seq or event["previous_hash"] != previous
            or event_digest(event) != event["event_hash"]
            or event["debit_account"] == event["credit_account"]
            or not 1 <= event["debit_account"] <= 16
            or not 1 <= event["credit_account"] <= 16
            or event["amount_minor"] <= 0
            or event["debit_before"] - event["debit_after"] != event["amount_minor"]
            or event["credit_after"] - event["credit_before"] != event["amount_minor"]):
        raise FeedBlocked("SOURCE_FEED_GAP_OR_CORRUPTION")


def _read_source(conn, verify_entire_history: bool) -> dict:
    conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    clock_row = conn.execute(
        "SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()
    if clock_row is None or not 0 <= clock_row[0] <= MAX_HISTORY:
        raise FeedBlocked("SOURCE_CLOCK_MISSING_OR_OUT_OF_BOUNDED_FIXTURE")
    seq = clock_row[0]
    accounts = [list(r) for r in conn.execute(
        "SELECT account_no,ledger_minor,revision FROM legacy.accounts "
        "ORDER BY account_no").fetchall()]
    if (len(accounts) != 16 or [r[0] for r in accounts] != list(range(1, 17))
            or sum(r[1] for r in accounts) != 1_600_000
            or any(r[1] < 0 or not 0 <= r[2] <= seq for r in accounts)):
        raise FeedBlocked("SOURCE_ACCOUNT_OR_LEDGER_CONTRACT_INVALID")
    if not verify_entire_history:
        return {"watermark": seq, "accounts": accounts}
    history = _events(conn)
    if len(history) != seq:
        raise FeedBlocked("SOURCE_HISTORY_GAP")
    # Historical replay from fixture genesis is a bounded independent oracle,
    # NOT a scalable production recovery or authenticity proof.
    expected = {i: [100000, 0] for i in range(1, 17)}
    previous = GENESIS
    for index, event in enumerate(history, 1):
        _check_event(event, index, previous)
        debit, credit = event["debit_account"], event["credit_account"]
        if (expected[debit][0] != event["debit_before"]
                or expected[credit][0] != event["credit_before"]):
            raise FeedBlocked("SOURCE_HISTORY_BEFORE_IMAGE_DIVERGENCE")
        expected[debit] = [event["debit_after"], index]
        expected[credit] = [event["credit_after"], index]
        previous = event["event_hash"]
    replayed = [[i, *expected[i]] for i in range(1, 17)]
    if replayed != accounts:
        raise FeedBlocked("SOURCE_HISTORY_STATE_DIVERGENCE")
    return {"watermark": seq, "lastHash": previous, "accounts": accounts,
            "digest": canonical_digest(seq, accounts)}


def source_snapshot(source_dsn: str) -> dict:
    """The cut position, all rows and full bounded journal use ONE SQL MVCC view."""
    with psycopg.connect(source_dsn) as conn:
        return _read_source(conn, verify_entire_history=True)


def target_state(target_dsn: str) -> dict | None:
    """Read target data and committed cursor in one consistent snapshot."""
    with psycopg.connect(target_dsn) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        return _read_target(conn, lock=False)


def _read_target(conn, lock: bool) -> dict | None:
    row = conn.execute(
        "SELECT source_watermark,last_hash,snapshot_digest "
        "FROM projection.feed_state WHERE singleton=1" +
        (" FOR UPDATE" if lock else "")).fetchone()
    if row is None:
        return None
    accounts = [list(r) for r in conn.execute(
        "SELECT account_no,booked_minor,source_revision "
        "FROM projection.feed_accounts ORDER BY account_no").fetchall()]
    seq, last_hash, digest = row
    if (len(accounts) != 16 or [r[0] for r in accounts] != list(range(1, 17))
            or sum(r[1] for r in accounts) != 1_600_000
            or any(r[1] < 0 or not 0 <= r[2] <= seq for r in accounts)
            or digest != canonical_digest(seq, accounts)):
        raise FeedBlocked("TARGET_STATE_DIGEST_OR_LEDGER_DIVERGENCE")
    return {"watermark": seq, "lastHash": last_hash, "digest": digest,
            "accounts": accounts}


def install_snapshot(target_dsn: str, snapshot: dict) -> dict:
    """Install a previously captured immutable source cut as one target COMMIT.

    Concurrent source writers after the snapshot are deliberately handled by
    later catch-up. This is not a distributed atomic source-target transaction.
    """
    seq, accounts = snapshot["watermark"], snapshot["accounts"]
    if (snapshot["digest"] != canonical_digest(seq, accounts)
            or len(accounts) != 16
            or [r[0] for r in accounts] != list(range(1, 17))):
        raise FeedBlocked("INVALID_BOOTSTRAP_SNAPSHOT")
    with psycopg.connect(target_dsn) as conn:
        if conn.execute(
            "SELECT 1 FROM projection.feed_state WHERE singleton=1 FOR UPDATE"
        ).fetchone() is not None:
            raise FeedBlocked("TARGET_ALREADY_BOOTSTRAPPED")
        conn.execute("DELETE FROM projection.feed_accounts")
        for i, balance, revision in accounts:
            conn.execute(
                "INSERT INTO projection.feed_accounts(account_no,booked_minor,"
                "source_revision) VALUES(%s,%s,%s)", (i, balance, revision))
        conn.execute(
            "INSERT INTO projection.feed_state(singleton,source_watermark,"
            "last_hash,snapshot_digest) VALUES(1,%s,%s,%s)",
            (seq, snapshot["lastHash"], snapshot["digest"]))
    return {"status": "SNAPSHOT_INSTALLED", "watermark": seq,
            "classification": "SYNTHETIC_SOURCE_SNAPSHOT_CUT"}


def bootstrap() -> dict:
    source_dsn, target_dsn = checked_dsns()
    return install_snapshot(target_dsn, source_snapshot(source_dsn))


def _read_increment(source_dsn: str, after: int, batch_size: int):
    with psycopg.connect(source_dsn) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        clock = conn.execute(
            "SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()
        if clock is None or clock[0] < after or clock[0] > MAX_HISTORY:
            raise FeedBlocked("SOURCE_CLOCK_REGRESSION_OR_UNBOUNDED")
        until = min(clock[0], after + batch_size)
        rows = _events(conn, after, until, batch_size) if until > after else []
        if len(rows) != until - after:
            raise FeedBlocked("SOURCE_FEED_MISSING_SEQUENCES")
        return clock[0], rows


def catchup(batch_size: int = 4, crash_after_rows=False) -> dict:
    """Incrementally replay strictly contiguous journal rows to a target COMMIT.

    Target cursor and balances commit together; source has already COMMITTED.
    An exception between row writes and cursor update rolls back the target.
    """
    if type(batch_size) is not int or not 1 <= batch_size <= 32:
        raise ValueError("Synthetic bounded batch_size must be 1..32")
    source_dsn, target_dsn = checked_dsns()
    old = target_state(target_dsn)
    if old is None:
        raise FeedBlocked("SNAPSHOT_REQUIRED")
    head, rows = _read_increment(source_dsn, old["watermark"], batch_size)
    with psycopg.connect(target_dsn) as conn:
        current = _read_target(conn, lock=True)
        if current is None or current["watermark"] != old["watermark"]:
            raise FeedBlocked("TARGET_CURSOR_CONCURRENTLY_CHANGED")
        if current != old:
            raise FeedBlocked("TARGET_CHANGED_SINCE_READ")
        accounts = {r[0]: [r[1], r[2]] for r in current["accounts"]}
        seq, previous = current["watermark"], current["lastHash"]
        for event in rows:
            _check_event(event, seq + 1, previous)
            debit, credit = event["debit_account"], event["credit_account"]
            if (accounts[debit][0] != event["debit_before"]
                    or accounts[credit][0] != event["credit_before"]):
                raise FeedBlocked("TARGET_BEFORE_IMAGE_MISMATCH")
            accounts[debit] = [event["debit_after"], seq + 1]
            accounts[credit] = [event["credit_after"], seq + 1]
            for account in (debit, credit):
                result = conn.execute(
                    "UPDATE projection.feed_accounts SET booked_minor=%s,"
                    "source_revision=%s WHERE account_no=%s",
                    (*accounts[account], account))
                if result.rowcount != 1:
                    raise FeedBlocked("TARGET_ACCOUNT_MISSING")
            previous = event["event_hash"]
            seq += 1
        if crash_after_rows:
            raise FeedBlocked("INJECTED_TARGET_CRASH_BEFORE_CURSOR_COMMIT")
        final = [[i, *accounts[i]] for i in sorted(accounts)]
        if len(final) != 16 or sum(r[1] for r in final) != 1_600_000:
            raise FeedBlocked("TARGET_FINANCIAL_INVARIANT_FAILED")
        conn.execute(
            "UPDATE projection.feed_state SET source_watermark=%s,"
            "last_hash=%s,snapshot_digest=%s WHERE singleton=1",
            (seq, previous, canonical_digest(seq, final)))
    return {"status": "APPLIED" if rows else "ALREADY_CURRENT",
            "eventsApplied": len(rows), "targetWatermark": seq,
            "sampledSourceHead": head,
            "sourceAuthority": "LEGACY", "todmG2": "INCONCLUSIVE",
            "todmG6": "BLOCK", "deploymentAuthorized": False}


def audit() -> dict:
    """Independent bounded full-history reconciliation; not an online read SLO."""
    source_dsn, target_dsn = checked_dsns()
    source = source_snapshot(source_dsn)
    target = target_state(target_dsn)
    if target is None:
        return {"status": "NOT_BOOTSTRAPPED", "todmG6": "BLOCK"}
    if target["watermark"] != source["watermark"]:
        return {"status": "WATERMARKS_DIFFER", "source": source["watermark"],
                "target": target["watermark"], "todmG6": "BLOCK"}
    valid = (target["digest"] == source["digest"]
             and target["lastHash"] == source["lastHash"]
             and target["accounts"] == source["accounts"])
    return {"status": "MATCHED_BOUNDED_SOURCE_SNAPSHOT" if valid else
            "BLOCKED_SOURCE_TARGET_DIVERGENCE",
            "watermark": source["watermark"], "sourceAuthority": "LEGACY",
            "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
            "deploymentAuthorized": False}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("bootstrap")
    catch = sub.add_parser("catchup")
    catch.add_argument("--batch-size", type=int, default=4)
    sub.add_parser("audit")
    args = parser.parse_args()
    try:
        result = (bootstrap() if args.command == "bootstrap" else
                  catchup(args.batch_size) if args.command == "catchup" else audit())
        print(json.dumps(result, sort_keys=True, indent=2))
    except (FeedBlocked, psycopg.Error) as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error),
                          "sourceAuthority": "LEGACY", "todmG6": "BLOCK",
                          "deploymentAuthorized": False}, sort_keys=True))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
