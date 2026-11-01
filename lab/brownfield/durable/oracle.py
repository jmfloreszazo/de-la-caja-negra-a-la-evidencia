#!/usr/bin/env python3
"""Independent read-only SQL oracle for the disposable brownfield ledger."""
from collections import Counter, defaultdict
import os

import psycopg

EXPECTED_TOTAL_MINOR = 16 * 100_000


def observe(dsn: str | None = None) -> dict:
    """Read one repeatable snapshot without executing candidate business logic."""
    connection = dsn or os.environ["BROWNFIELD_PG_DSN"]
    with psycopg.connect(connection, autocommit=True) as db:
        with db.transaction():
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            name = db.execute("SELECT current_database()").fetchone()[0]
            if not name.startswith("bf_"):
                raise RuntimeError("Oracle refuses a database without the bf_ prefix")
            authority = db.execute(
                "SELECT writer,epoch FROM brownfield.authority WHERE id=1"
            ).fetchone()
            clock = db.execute(
                "SELECT watermark FROM brownfield.commit_clock WHERE id=1"
            ).fetchone()[0]
            accounts = dict(db.execute(
                "SELECT id,balance FROM brownfield.accounts ORDER BY id"
            ).fetchall())
            versions = dict(db.execute(
                "SELECT id,version FROM brownfield.accounts ORDER BY id"
            ).fetchall())
            operations = db.execute(
                "SELECT id,src,dst,amount,status,fingerprint,writer,epoch "
                "FROM brownfield.operations ORDER BY id"
            ).fetchall()
            postings = db.execute(
                "SELECT operation_id,account_id,delta "
                "FROM brownfield.postings ORDER BY operation_id,account_id"
            ).fetchall()
            outbox = db.execute(
                "SELECT operation_id,event_type FROM brownfield.outbox ORDER BY operation_id"
            ).fetchall()

    by_operation: dict[str, list[tuple[int, int]]] = defaultdict(list)
    by_account: Counter[int] = Counter()
    for op_id, account, delta in postings:
        by_operation[op_id].append((account, delta))
        by_account[account] += delta

    committed = {op[0]: op for op in operations if op[4] == "COMMITTED"}
    rejected = {op[0] for op in operations if op[4] == "REJECTED"}
    outbox_ids = [op_id for op_id, _ in outbox]
    post_cardinality = all(
        Counter((account, delta) for account, delta in by_operation[op_id])
        == Counter({(op[1], -op[3]): 1, (op[2], op[3]): 1})
        for op_id, op in committed.items()
    )
    guarantees = {
        "exactAccountFixture": sorted(accounts) == list(range(1, 17)),
        "nonnegativeBalances": all(balance >= 0 for balance in accounts.values()),
        "conservedMoney": sum(accounts.values()) == EXPECTED_TOTAL_MINOR,
        "balancesMatchPostings": all(
            accounts[account] == 100_000 + by_account[account]
            for account in range(1, 17)
        ),
        "pairedCommittedPostings": (
            post_cardinality and set(by_operation) == set(committed)
            and len(postings) == 2 * len(committed)
        ),
        "rejectedHaveNoEffects": not (rejected & (set(by_operation) | set(outbox_ids))),
        "exactOutbox": (
            Counter(outbox_ids) == Counter(committed)
            and all(event == "TransferCommitted" for _, event in outbox)
        ),
        "uniqueOperationIdsAndFingerprints": (
            len({o[0] for o in operations}) == len(operations)
            and all(len(o[5]) == 64 for o in operations)
        ),
        "watermarkEqualsRecordedDecisions": clock == len(operations),
        "accountVersionBounded": all(0 <= v <= clock for v in versions.values()),
        "writerEpochWellFormed": authority is not None
            and authority[0] in ("legacy", "candidate") and authority[1] >= 1,
    }
    return {
        "classification": "DISPOSABLE_SYNTHETIC_SQL_ORACLE_NOT_BUSINESS_APPROVAL",
        "checks": guarantees,
        "passed": all(guarantees.values()),
        "accountCount": len(accounts),
        "operationCount": len(operations),
        "committedCount": len(committed),
        "rejectedCount": len(rejected),
        "postingCount": len(postings),
        "outboxCount": len(outbox),
        "watermark": clock,
        "writer": authority[0] if authority else None,
        "epoch": authority[1] if authority else None,
        "todmG6": "BLOCK",
    }


if __name__ == "__main__":
    import json
    result = observe()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
