#!/usr/bin/env python3
"""W01: nonauthoritative PostgreSQL balance projection for a synthetic legacy.

A snapshot reader, NOT CDC, a live mainframe integration, a bank balance API,
a cash-authorization path or a production-ready consistency/HA guarantee.
The source is only read with READ ONLY transactions AND a separately
validated PostgreSQL role with SELECT-only grants. Fixture resets/writes
belong exclusively to the test harness, not this application.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import psycopg

HERE = Path(__file__).resolve().parent
ALLOWED = {
    "W01_LEGACY_DSN": ("bf_legacy", "55438"),
    "W01_PROJECTION_DSN": ("bf_projection", "55442"),
}
FORBIDDEN_ENV = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE",
                 "PGPORT", "PGDATABASE", "PGUSER", "PGOPTIONS")


class UnsafeFixture(ValueError):
    pass


class InvalidSource(RuntimeError):
    pass


def validated_dsns() -> tuple[str, str]:
    """Do not let a synthetic database-reset or reader touch an arbitrary host."""
    if os.environ.get("W01_DISPOSABLE") != "YES":
        raise UnsafeFixture("Explicit W01_DISPOSABLE=YES opt-in required")
    if any(os.environ.get(name) for name in FORBIDDEN_ENV):
        raise UnsafeFixture("Implicit PostgreSQL environment overrides prohibited")
    out = []
    for key, (name, port) in ALLOWED.items():
        dsn = os.environ.get(key)
        if not dsn:
            raise UnsafeFixture("Missing required " + key)
        params = psycopg.conninfo.conninfo_to_dict(dsn)
        expected_role = "w01_reader" if key == "W01_LEGACY_DSN" else "postgres"
        if (any(params.get(option) for option in
                ("hostaddr", "service", "servicefile", "target_session_attrs", "options"))
                or (params.get("host"), params.get("port"), params.get("dbname"),
                    params.get("user"))
                != ("127.0.0.1", port, name, expected_role)):
            raise UnsafeFixture("Only exact loopback disposable endpoints and roles allowed")
        with psycopg.connect(dsn) as conn:
            actual = conn.execute("SELECT current_database(), current_user").fetchone()
            if actual != (name, expected_role):
                raise UnsafeFixture("Unexpected database or effective role identity")
            if key == "W01_LEGACY_DSN":
                # A READ ONLY transaction is a session choice, not an access
                # control boundary. Independently assert the DB role cannot
                # mutate financial tables even after SET TRANSACTION READ WRITE.
                permissions = conn.execute(
                    "SELECT rolsuper,rolcreaterole,rolcreatedb,rolreplication,"
                    "rolbypassrls FROM pg_roles WHERE rolname=current_user"
                ).fetchone()
                if permissions is None or any(permissions):
                    raise UnsafeFixture("Source reader cannot be privileged")
                if conn.execute(
                    "SELECT has_schema_privilege(current_user,'legacy','CREATE')"
                ).fetchone()[0]:
                    raise UnsafeFixture("Source reader must not create legacy objects")
                for table in ("legacy.accounts", "legacy.clock",
                              "legacy.transactions", "legacy.entries",
                              "legacy.notices"):
                    for action in ("INSERT", "UPDATE", "DELETE", "TRUNCATE",
                                   "REFERENCES", "TRIGGER"):
                        if conn.execute(
                            "SELECT has_table_privilege(current_user,%s,%s)",
                            (table, action)).fetchone()[0]:
                            raise UnsafeFixture("Source role can mutate: " + table)
                    # This synthetic projector may read only the balances and
                    # version clock, not operation details or external effects.
                    can_read = conn.execute(
                        "SELECT has_table_privilege(current_user,%s,'SELECT')",
                        (table,)).fetchone()[0]
                    if can_read != (table in ("legacy.accounts", "legacy.clock")):
                        raise UnsafeFixture("Unexpected source SELECT privileges")
        out.append(dsn)
    return out[0], out[1]


def _canonical_digest(watermark: int, rows: list[list[int]]) -> str:
    raw = json.dumps({"watermark": watermark, "accounts": rows},
                     sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def _rows(conn, sql: str) -> list[list[int]]:
    return [list(row) for row in conn.execute(sql).fetchall()]


def _validate_source(watermark: int, rows: list[list[int]]) -> None:
    if (not isinstance(watermark, int) or watermark < 0
            or len(rows) != 16 or [r[0] for r in rows] != list(range(1, 17))
            or sum(r[1] for r in rows) != 1_600_000
            or any(r[1] < 0 or not 0 <= r[2] <= watermark for r in rows)):
        raise InvalidSource("Authoritative source violates the declared disposable ledger fixture")


def authoritative_snapshot(dsn: str) -> dict:
    """One consistent, read-only PostgreSQL snapshot; no source mutation."""
    with psycopg.connect(dsn) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        watermark = conn.execute(
            "SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()
        if watermark is None:
            raise InvalidSource("Missing source watermark")
        rows = _rows(conn, "SELECT account_no,ledger_minor,revision "
                           "FROM legacy.accounts ORDER BY account_no")
    seq = watermark[0]
    _validate_source(seq, rows)
    return {"watermark": seq, "accounts": rows,
            "digest": _canonical_digest(seq, rows)}


def observed_source_clock(dsn: str) -> int:
    with psycopg.connect(dsn) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        row = conn.execute(
            "SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()
        if row is None or not isinstance(row[0], int) or row[0] < 0:
            raise InvalidSource("Missing or invalid source clock")
        return row[0]


def projection_snapshot(dsn: str) -> dict:
    with psycopg.connect(dsn) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        meta = conn.execute(
            "SELECT watermark,source_digest FROM projection.meta WHERE id=1").fetchone()
        rows = _rows(conn, "SELECT account_no,booked_minor,source_revision "
                           "FROM projection.accounts ORDER BY account_no")
    if meta is None:
        raise InvalidSource("Missing projection metadata")
    seq, digest = meta
    expected = _canonical_digest(seq, rows)
    return {"watermark": seq, "digest": digest, "computedDigest": expected,
            "accounts": rows, "integrity": expected == digest and len(rows) == 16}


def refresh() -> dict:
    """Idempotent *full snapshot* rebuild, never financial write or event replay.

    A historical source clock cannot move backward. A changed source at the
    SAME clock reveals an unversioned source update and blocks promotion.
    """
    source_dsn, target_dsn = validated_dsns()
    source = authoritative_snapshot(source_dsn)
    with psycopg.connect(target_dsn) as conn:
        old = conn.execute(
            "SELECT watermark,source_digest FROM projection.meta WHERE id=1 FOR UPDATE"
        ).fetchone()
        if old is None:
            raise InvalidSource("Missing projection control row")
        if source["watermark"] < old[0]:
            raise InvalidSource("SOURCE_WATERMARK_REGRESSION")
        if source["watermark"] == old[0] and old[1] is not None and old[1] != source["digest"]:
            raise InvalidSource("UNVERSIONED_SOURCE_MUTATION: same clock, different source")
        # Replace the entire *projection* within one SQL transaction. A crash
        # cannot publish the new clock with only half of the balances.
        conn.execute("DELETE FROM projection.accounts")
        for account, booked, revision in source["accounts"]:
            conn.execute(
                "INSERT INTO projection.accounts(account_no,booked_minor,source_revision) "
                "VALUES (%s,%s,%s)", (account, booked, revision))
        conn.execute(
            "UPDATE projection.meta SET watermark=%s,source_digest=%s,"
            "refreshed_at=clock_timestamp() WHERE id=1",
            (source["watermark"], source["digest"]))
    return {"status": "REBUILT_FROM_READ_ONLY_SOURCE", "watermark": source["watermark"],
            "digest": source["digest"], "financialWrites": 0,
            "classification": "SYNTHETIC_FULL_SNAPSHOT_NO_CDC"}


def balance(account: int, minimum_watermark: int = 0) -> dict:
    """No stale fallback: on unsafe projection, use a source snapshot or BLOCK.

    A source-clock read before the projection is a *sample*, NOT a linearizable
    cut. Another source transaction can COMMIT after sampling. Therefore W01
    never claims a bank-authoritative read or read-your-writes SLO.
    """
    if (not isinstance(account, int) or isinstance(account, bool)
            or not 1 <= account <= 16
            or not isinstance(minimum_watermark, int)
            or isinstance(minimum_watermark, bool) or minimum_watermark < 0):
        raise ValueError("Invalid synthetic account or minimum watermark")
    source_dsn, target_dsn = validated_dsns()
    try:
        observed = observed_source_clock(source_dsn)
    except (psycopg.Error, InvalidSource):
        return {"status": "BLOCKED_SOURCE_UNAVAILABLE", "sourceAuthority": "LEGACY",
                "todmG6": "BLOCK", "isSpendableFunds": False}
    if observed < minimum_watermark:
        return {"status": "BLOCKED_MINIMUM_WATERMARK", "sourceWatermark": observed,
                "requiredWatermark": minimum_watermark, "sourceAuthority": "LEGACY",
                "todmG6": "BLOCK", "isSpendableFunds": False}
    projection = None
    try:
        projection = projection_snapshot(target_dsn)
    except (psycopg.Error, InvalidSource):
        pass
    if (projection and projection["integrity"]
            and projection["watermark"] == observed
            and projection["watermark"] >= minimum_watermark):
        row = next((r for r in projection["accounts"] if r[0] == account), None)
        if row is not None:
            return {"status": "PROJECTION_OBSERVED_CURRENT", "sourceAuthority": "LEGACY",
                    "bookedMinor": row[1], "accountRevision": row[2],
                    "projectionWatermark": projection["watermark"],
                    "observedSourceWatermark": observed,
                    "isSpendableFunds": False, "todmG6": "BLOCK"}
    # NEVER serve a stale or tampered projection when authoritative read fails.
    try:
        source = authoritative_snapshot(source_dsn)
    except (psycopg.Error, InvalidSource):
        return {"status": "BLOCKED_FALLBACK_UNAVAILABLE", "sourceAuthority": "LEGACY",
                "todmG6": "BLOCK", "isSpendableFunds": False}
    if source["watermark"] < minimum_watermark:
        return {"status": "BLOCKED_MINIMUM_WATERMARK", "sourceAuthority": "LEGACY",
                "sourceWatermark": source["watermark"], "requiredWatermark": minimum_watermark,
                "todmG6": "BLOCK", "isSpendableFunds": False}
    row = next(r for r in source["accounts"] if r[0] == account)
    return {"status": "AUTHORITATIVE_FALLBACK", "sourceAuthority": "LEGACY",
            "bookedMinor": row[1], "accountRevision": row[2],
            "sourceWatermark": source["watermark"],
            "projectionWatermark": projection["watermark"] if projection else None,
            "isSpendableFunds": False, "todmG6": "BLOCK"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("refresh")
    read = subs.add_parser("balance")
    read.add_argument("account", type=int)
    read.add_argument("--minimum-watermark", type=int, default=0)
    args = parser.parse_args()
    if args.command == "refresh":
        output = refresh()
    else:
        output = balance(args.account, args.minimum_watermark)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
