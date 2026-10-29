#!/usr/bin/env python3
"""Differential .NET 10/Npgsql vs E1a Python ledger, same PostgreSQL database schema."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from ledger import connect, reset, transfer
from oracle import verify

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/"results"/"e1"
OUT.mkdir(parents=True,exist_ok=True)
DLL=HERE/"PgBank"/"bin"/"Release"/"net10.0"/"PgBank.dll"
DOTNET=os.environ.get("DOTNET","dotnet")


def invoke(*args, expected=0):
    p=subprocess.run([DOTNET,str(DLL),"transfer",*map(str,args)],
                     text=True,capture_output=True,timeout=35,env=os.environ)
    assert p.returncode==expected,(p.returncode,p.stdout,p.stderr)
    return json.loads(p.stdout) if expected==0 else None


def snapshot():
    with connect() as db:
        return {
            table:db.execute(
                "SELECT * FROM "+table+" ORDER BY 1"+(",2" if table=="postings" else "")
            ).fetchall()
            for table in ("accounts","operations","postings","outbox")
        }


def controls_python():
    sequence=[
        ("a",1,2,100),("b",1,2,200000),("a",1,2,100),
        ("a",1,2,200),("c",3,4,1000),("d",4,3,500)
    ]
    return [transfer(*row)["status"] for row in sequence]


def controls_dotnet():
    sequence=[
        ("a",1,2,100),("b",1,2,200000),("a",1,2,100),
        ("a",1,2,200),("c",3,4,1000),("d",4,3,500)
    ]
    return [invoke(*row)["status"] for row in sequence]


def main():
    start=time.perf_counter()
    build=subprocess.run([DOTNET,"build",str(HERE/"PgBank"),"-c","Release","-m:1",
                          "--disable-build-servers"],capture_output=True,text=True,
                         timeout=180)
    (OUT/"dotnet-build.txt").write_text(build.stdout+build.stderr,encoding="utf-8")
    assert build.returncode==0,build.stdout+build.stderr
    reset()
    python_states=controls_python()
    python_snapshot=snapshot()
    assert all(verify().values())
    reset()
    net_states=controls_dotnet()
    dotnet_snapshot=snapshot()
    assert all(verify().values())
    assert net_states==python_states,(net_states,python_states)
    assert dotnet_snapshot==python_snapshot,(dotnet_snapshot,python_snapshot)

    # Real independent processes: only one transfer succeeds on 100000 cents.
    reset()
    with ThreadPoolExecutor(max_workers=2) as ex:
        decisions=list(ex.map(lambda i:invoke(f"race-{i}",1,2,70000),range(2)))
    assert sorted(x["status"] for x in decisions)==["COMMITTED","REJECTED"],decisions

    # Concurrent duplicate submissions through Npgsql, one durable effect.
    with ThreadPoolExecutor(max_workers=4) as ex:
        rows=list(ex.map(lambda _:invoke("same-dotnet",2,1,100),range(4)))
    assert sum(x["status"]=="COMMITTED" for x in rows)==1
    assert sum(x["status"]=="DUPLICATE_COMMITTED" for x in rows)==3
    assert invoke("same-dotnet",2,1,101)["status"]=="ID_CONFLICT"

    with connect() as db:
        before=db.execute("SELECT balance FROM accounts WHERE id=2").fetchone()[0]
    invoke("throw",2,1,10,"--fault","throw-after-debit",expected=5)
    invoke("crash",2,1,10,"--fault","crash-after-debit",expected=91)
    with connect() as db:
        assert db.execute("SELECT balance FROM accounts WHERE id=2").fetchone()[0]==before
        assert db.execute("SELECT COUNT(*) FROM operations WHERE id IN ('throw','crash')").fetchone()[0]==0
    invoke("lost",2,1,10,"--fault","lost-response",expected=92)
    assert invoke("lost",2,1,10)["status"]=="DUPLICATE_COMMITTED"
    assert all(verify().values()),verify()

    summary={
        "status":"PASS",
        "module":"E1b PostgreSQL Npgsql 10.0.3 / .NET 10 differential slice",
        "sourceSha256":{
          "PgBank/Program.cs":hashlib.sha256((HERE/"PgBank/Program.cs").read_bytes()).hexdigest(),
          "PgBank/PgBank.csproj":hashlib.sha256((HERE/"PgBank/PgBank.csproj").read_bytes()).hexdigest(),
          "test_dotnet.py":hashlib.sha256((HERE/"test_dotnet.py").read_bytes()).hexdigest()
        },
        "parity":{"python":python_states,"dotnet":net_states,"persistedStateEqual":True},
        "concurrency":decisions,
        "controls":{
            "candidateParity":"PASS","rowLockOverdraft":"PASS",
            "idempotencyAndConflict":"PASS","exceptionRollback":"PASS",
            "processCrashRollback":"PASS","commitWithoutResponse":"PASS",
            "independentOracle":"PASS",
        },
        "elapsedSeconds":round(time.perf_counter()-start,3),
        "limits":"Synthetic controlled PostgreSQL; no real CICS/Db2 or mainframe performance equivalence."
    }
    (OUT/"summary-dotnet.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
