#!/usr/bin/env python3
"""E1 PostgreSQL executable controls. Requires a DISPOSABLE local database.

Do not interpret these synthetic controls as mainframe capacity or operational SLA.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

import psycopg
from psycopg_pool import ConnectionPool, PoolTimeout

from ledger import connect, reset, transfer
from oracle import verify

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
OUT=LAB/"results"/"e1"
OUT.mkdir(parents=True,exist_ok=True)
controls={}


def assert_oracle(expected=True):
    observed=verify()
    assert all(observed.values()) is expected, observed
    return observed


def cli(*argv):
    return subprocess.run(
        [sys.executable,str(HERE/"ledger.py"),"transfer",*map(str,argv)],
        env=os.environ.copy(),capture_output=True,text=True,timeout=30
    )


def write_skew(isolation):
    # Deliberately teach the anomaly on an unrelated invariant:
    # at least one of the two on-call operators must remain active.
    with connect() as db:
        db.execute("UPDATE duty SET active=TRUE")
    barrier=threading.Barrier(2)
    sqlstates=[]
    lock=threading.Lock()

    def attempt_disable(uid):
        for trial in range(5):
            try:
                with connect() as db:
                    with db.transaction():
                        db.execute("SET TRANSACTION ISOLATION LEVEL "+isolation)
                        active=db.execute(
                            "SELECT COUNT(*) FROM duty WHERE active=TRUE"
                        ).fetchone()[0]
                        if trial==0:
                            barrier.wait(timeout=10)
                        if active==2:
                            db.execute("UPDATE duty SET active=FALSE WHERE id=%s",(uid,))
                            decision="DISABLED"
                        else:
                            decision="SKIPPED"
                return decision
            except psycopg.Error as exc:
                if exc.sqlstate!="40001":
                    raise
                with lock:
                    sqlstates.append(exc.sqlstate)
                time.sleep(.025*(trial+1))
        raise AssertionError("Serializable retry cap exceeded")
    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions=list(pool.map(attempt_disable,(1,2)))
    with connect() as db:
        remaining=db.execute("SELECT COUNT(*) FROM duty WHERE active=TRUE").fetchone()[0]
    return {"remainingActive":remaining,"decisions":decisions,"retries":sqlstates}


def run_checks():
    reset()
    with ThreadPoolExecutor(max_workers=2) as pool:
        race=list(pool.map(lambda i:transfer(f"race-{i}",1,2,70000),range(2)))
    assert sorted(x["status"] for x in race)==["COMMITTED","REJECTED"],race
    controls["rowLockOverdraft"]={"status":"PASS","observations":race}

    with ThreadPoolExecutor(max_workers=8) as pool:
        duplicates=list(pool.map(lambda _:transfer("same-op",2,1,100),range(8)))
    assert sum(x["status"]=="COMMITTED" for x in duplicates)==1,duplicates
    assert sum(x["status"]=="DUPLICATE_COMMITTED" for x in duplicates)==7,duplicates
    assert transfer("same-op",2,1,101)["status"]=="ID_CONFLICT"
    controls["idempotencyAndConflict"]={"status":"PASS","replies":[x["status"] for x in duplicates]}

    with connect() as db:
        prior=db.execute("SELECT balance FROM accounts WHERE id=2").fetchone()[0]
    thrown=cli("aborted",2,1,100,"--fault","throw-after-debit")
    assert thrown.returncode != 0,(thrown.stdout,thrown.stderr)
    with connect() as db:
        assert db.execute("SELECT balance FROM accounts WHERE id=2").fetchone()[0]==prior
        assert db.execute("SELECT COUNT(*) FROM operations WHERE id='aborted'").fetchone()[0]==0
    controls["exceptionRollback"]={"status":"PASS"}

    crash=cli("crash",2,1,100,"--fault","crash-after-debit")
    assert crash.returncode==91,(crash.returncode,crash.stdout,crash.stderr)
    with connect() as db:
        assert db.execute("SELECT balance FROM accounts WHERE id=2").fetchone()[0]==prior
        assert db.execute("SELECT COUNT(*) FROM operations WHERE id='crash'").fetchone()[0]==0
    controls["processCrashRollback"]={"status":"PASS"}

    lost=cli("lost",2,1,100,"--fault","lost-response")
    assert lost.returncode==92,(lost.returncode,lost.stdout,lost.stderr)
    assert transfer("lost",2,1,100)["status"]=="DUPLICATE_COMMITTED"
    controls["commitWithoutResponse"]={"status":"PASS"}

    # Hold the same account lock in two opposite-order transfers.
    # PostgreSQL detects a real SQLSTATE 40P01. A bounded, full
    # transaction retry resolves the deadlock without duplicate ledger rows.
    barrier=threading.Barrier(2)
    def crossing(which):
        return transfer(f"deadlock-{which}",3 if which==0 else 4,
                        4 if which==0 else 3,100,
                        lock_order="source-first",barrier=barrier,
                        lock_timeout_ms=5000,max_attempts=5)
    with ThreadPoolExecutor(max_workers=2) as pool:
        crossing_outcomes=list(pool.map(crossing,(0,1)))
    assert all(x["status"]=="COMMITTED" for x in crossing_outcomes),crossing_outcomes
    assert any("40P01" in x["retry_sqlstates"] for x in crossing_outcomes),crossing_outcomes
    controls["deadlockVictimRetried"]={"status":"PASS","observations":crossing_outcomes}

    # Lock bounded retry exhaustion must not be converted to a fake PASS.
    with connect() as holder:
        with holder.transaction():
            holder.execute("SELECT id FROM accounts WHERE id=5 FOR UPDATE")
            exhausted=transfer("exhausted",5,6,10,max_attempts=2,lock_timeout_ms=120)
            assert exhausted["status"]=="RETRY_EXHAUSTED",exhausted
            assert "55P03" in exhausted["retry_sqlstates"],exhausted
    with connect() as db:
        assert db.execute("SELECT COUNT(*) FROM operations WHERE id='exhausted'").fetchone()[0]==0
    controls["boundedLockTimeout"]={"status":"PASS","observation":exhausted}

    rc=write_skew("READ COMMITTED")
    assert rc["remainingActive"]==0,rc  # intentionally unsafe negative control
    sc=write_skew("SERIALIZABLE")
    assert sc["remainingActive"]>=1,sc
    assert "40001" in sc["retries"],sc
    controls["writeSkewPrevented"]={"status":"PASS","readCommittedNegative":rc,
                                    "serializable":sc}

    # Real psycopg connection pool: both slots are leased; a third lease
    # fails within the specified timeout, without silently waiting forever.
    with ConnectionPool(os.environ["E1_PG_DSN"],min_size=2,max_size=2,
                        timeout=.25,open=True) as pool:
        pool.wait(timeout=10)
        with pool.connection() as first, pool.connection() as second:
            try:
                with pool.connection(timeout=.25):
                    raise AssertionError("unexpected third connection")
            except PoolTimeout:
                pass
    controls["poolExhaustionBounded"]={"status":"PASS","maxConnections":2}

    checks=assert_oracle()
    controls["independentOracle"]={"status":"PASS","invariants":checks}

    # Negative control: independently corrupt a persisted posting,
    # verify that the external read-only oracle *rejects* it, then restore.
    with connect() as db:
        posting=db.execute(
            "SELECT op,account,delta FROM postings LIMIT 1"
        ).fetchone()
        assert posting, "No posting available for negative control"
        db.execute("DELETE FROM postings WHERE op=%s AND account=%s",posting[:2])
    corrupted=verify()
    assert corrupted["twoPostingsPerCommit"] is False,corrupted
    with connect() as db:
        db.execute("INSERT INTO postings(op,account,delta) VALUES(%s,%s,%s)",posting)
    assert_oracle()
    controls["oracleRejectsCorruptLedger"]={"status":"PASS",
                                              "detected":sorted(k for k,v in corrupted.items() if not v)}
    return controls


def main():
    begin=time.time()
    try:
        run_checks()
        status="PASS"
    except Exception as exc:
        status="FAIL"
        controls["exception"]={"type":type(exc).__name__,"message":str(exc)}
        raise
    finally:
        info={}
        try:
            with connect() as db:
                info={"postgresVersion":db.execute("SHOW server_version").fetchone()[0]}
        except Exception as exc:
            info={"databaseUnavailable":str(exc)}
        summary={
            "status":status if "status" in locals() else "FAIL",
            "environment":platform.platform(),
            "sourceSha256":{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                            for name in ("ledger.py","oracle.py","schema.sql","test_e1.py")},
            "experiment":"E1a synthetic PostgreSQL concurrency and independent-oracle slice",
            "limitations":"Not E1 complete; not .NET 10 port; no mainframe SLA or capacity claim.",
            "controls":controls,"elapsedSeconds":round(time.time()-begin,2),**info,
        }
        (OUT/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
        print(json.dumps(summary,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
