#!/usr/bin/env python3
"""Independent read-only persisted-ledger oracle. Never imports the SQL candidate."""
import os
import psycopg


def verify():
    dsn=os.environ["E1_PG_DSN"]
    with psycopg.connect(dsn, autocommit=True) as db:
        with db.transaction():
            db.execute("SET TRANSACTION READ ONLY")
            def number(query):
                return db.execute(query).fetchone()[0]
            checks = {
                "nonnegative": number("SELECT COUNT(*) FROM accounts WHERE balance < 0")==0,
                "conserved": number("SELECT SUM(balance) FROM accounts")==1600000,
                "balancedPostings": number(
                    "SELECT COUNT(*) FROM (SELECT op FROM postings GROUP BY op "
                    "HAVING SUM(delta) <> 0 OR COUNT(*) <> 2) AS bad"
                )==0,
                "twoPostingsPerCommit":number(
                    "SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' "
                    "AND (SELECT COUNT(*) FROM postings p WHERE p.op=o.id) <> 2"
                )==0,
                "noPostingsForRejection":number(
                    "SELECT COUNT(*) FROM operations o WHERE status='REJECTED' "
                    "AND EXISTS (SELECT 1 FROM postings p WHERE p.op=o.id)"
                )==0,
                "outboxAtomic":number(
                    "SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' "
                    "AND NOT EXISTS (SELECT 1 FROM outbox b WHERE b.op=o.id)"
                )==0 and number(
                    "SELECT COUNT(*) FROM outbox b JOIN operations o ON b.op=o.id "
                    "WHERE o.status <> 'COMMITTED'"
                )==0,
                "projectionAgrees":number(
                    "SELECT COUNT(*) FROM accounts a WHERE a.balance <> 100000 + "
                    "COALESCE((SELECT SUM(delta) FROM postings p WHERE p.account=a.id),0)"
                )==0
            }
            return checks
