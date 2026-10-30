#!/usr/bin/env python3
"""Read-only, candidate-independent 1,000-account E2 ledger oracle.

Reuses the seven accounting principles from E1 while deriving the expected
total from the *synthetic fixture*, not from the implementation under test.
No imports of Orleans or application transfer code.
"""
import os
import psycopg

ACCOUNT_COUNT = 1000
OPENING_CENTS = 100000
EXPECTED_TOTAL = ACCOUNT_COUNT * OPENING_CENTS


def verify():
    with psycopg.connect(os.environ["E1_PG_DSN"], autocommit=True) as db:
        with db.transaction():
            db.execute("SET TRANSACTION READ ONLY, ISOLATION LEVEL REPEATABLE READ")
            def count(sql):
                return int(db.execute(sql).fetchone()[0])

            assert count("SELECT COUNT(*) FROM accounts") == ACCOUNT_COUNT
            return {
                "nonnegative": count("SELECT COUNT(*) FROM accounts WHERE balance<0") == 0,
                "conserved": count("SELECT COALESCE(SUM(balance),0) FROM accounts") == EXPECTED_TOTAL,
                "balancedPostings": count(
                    "SELECT COUNT(*) FROM (SELECT op FROM postings GROUP BY op "
                    "HAVING COUNT(*)<>2 OR SUM(delta)<>0) bad") == 0,
                "twoPostingsPerCommit": count(
                    "SELECT COUNT(*) FROM operations o WHERE o.status='COMMITTED' "
                    "AND (SELECT COUNT(*) FROM postings p WHERE p.op=o.id)<>2") == 0,
                "noPostingsForRejection": count(
                    "SELECT COUNT(*) FROM operations o WHERE o.status='REJECTED' "
                    "AND EXISTS (SELECT 1 FROM postings p WHERE p.op=o.id)") == 0,
                "outboxAtomic": count(
                    "SELECT COUNT(*) FROM operations o WHERE o.status='COMMITTED' "
                    "AND NOT EXISTS (SELECT 1 FROM outbox b WHERE b.op=o.id)") == 0
                    and count(
                    "SELECT COUNT(*) FROM outbox b JOIN operations o ON b.op=o.id "
                    "WHERE o.status<>'COMMITTED'") == 0,
                "projectionAgrees": count(
                    "SELECT COUNT(*) FROM accounts a WHERE a.balance<>100000+"
                    "COALESCE((SELECT SUM(delta) FROM postings p WHERE p.account=a.id),0)") == 0
            }


if __name__ == "__main__":
    result = verify()
    assert len(result) == 7 and all(result.values()), result
    print(result)
