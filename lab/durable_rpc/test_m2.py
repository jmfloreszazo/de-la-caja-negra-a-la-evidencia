#!/usr/bin/env python3
"""Execute M2 and independently verify persisted ledger on every run.

WARNING: reset() DROPS TABLES. Use a dedicated, disposable PostgreSQL database.
"""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"e1_pg"))
from ledger import reset,connect
from oracle import verify

OUTPUT=HERE.parent/"results"/"m2"
OUTPUT.mkdir(parents=True,exist_ok=True)
PROJ=HERE/"DurableRpc"/"DurableRpc.csproj"
DLL=HERE/"DurableRpc"/"bin"/"Release"/"net10.0"/"DurableRpc.dll"
DOTNET=os.environ.get("DOTNET","dotnet")
if not os.environ.get("E1_PG_NPGSQL") or not os.environ.get("E1_PG_DSN"):
    raise RuntimeError("E1_PG_NPGSQL and E1_PG_DSN must point to a dedicated disposable PostgreSQL instance")

build=subprocess.run([DOTNET,"build",str(PROJ),"-c","Release","-m:1",
                      "--disable-build-servers"],capture_output=True,text=True,timeout=240)
(OUTPUT/"build.log").write_text(build.stdout+build.stderr,encoding="utf-8")
if build.returncode:raise RuntimeError("Build failed; see lab/results/m2/build.log")

records=[]
for distro in ("uniform","hot"):
    for count in (1,2,4,8,16):
        for protocol in ("rest","grpc"):
            reset()
            label=f"{distro}-{count}-{protocol}"
            report=OUTPUT/(label+".json")
            started=time.monotonic()
            run=subprocess.run(
                [DOTNET,str(DLL),"benchmark",protocol,str(count),distro,"256","16",str(report)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=200)
            (OUTPUT/(label+".stderr.txt")).write_text(run.stderr,encoding="utf-8")
            if run.returncode:
                raise RuntimeError(f"{label}: exit {run.returncode}; stderr={run.stderr[-2500:]}")
            data=json.loads(report.read_text(encoding="utf-8"))
            x=data["experiment"]
            assert x["committed"]==256 and x["failures"]==0,x
            assert sum(x["perReplicaCommits"])==256,x
            assert all(x["perReplicaCommits"]),x
            independent=verify()
            assert all(independent.values()),(label,independent)
            with connect() as db:
                ops=db.execute("SELECT COUNT(*) FROM operations WHERE status='COMMITTED'").fetchone()[0]
                posts=db.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
                outbox=db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
                unique=db.execute("SELECT COUNT(DISTINCT id) FROM operations").fetchone()[0]
            assert (ops,posts,outbox,unique)==(256,512,256,256),(label,ops,posts,outbox,unique)
            record={"label":label,"protocol":protocol,"distribution":distro,"replicas":count,
                    "elapsedWallSeconds":round(time.monotonic()-started,2),
                    "verifiedBy":"independent read-only PostgreSQL ledger oracle",
                    "oracle":independent,
                    "ledger":{"commits":ops,"postings":posts,"outbox":outbox,"uniqueOperations":unique},
                    "client":x}
            records.append(record)
            print(json.dumps({"case":label,"commits":ops,"tps":x["durableCommittedPerSecond"],
                              "p99":x["p99Ms"],"oracle":"PASS"}),flush=True)

# Negative control. Corrupt data independently, demand oracle rejection, restore data.
with connect() as db:
    posting=db.execute("SELECT op,account,delta FROM postings LIMIT 1").fetchone()
    assert posting
    db.execute("DELETE FROM postings WHERE op=%s AND account=%s",posting[:2])
bad=verify()
assert not bad["twoPostingsPerCommit"] and not bad["projectionAgrees"],bad
with connect() as db:
    db.execute("INSERT INTO postings(op,account,delta) VALUES(%s,%s,%s)",posting)
assert all(verify().values())
summary={
  "schemaVersion":1,
  "classification":"M2_LOCAL_SINGLE_HOST_POSTGRES_DURABLE_SMOKE_NOT_CLOUD_OR_MAINFRAME",
  "utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
  "sourceCommit":os.environ.get("GITHUB_SHA","local"),
  "postgresVersion":None,
  "limitations":"One hosted runner, HTTP/2 h2c, closed loop, 256 requests each; no TLS/WAN/Azure/HA or mainframe parity.",
  "cases":records,
  "oracleNegativeControl":{"detected":sorted(k for k,v in bad.items() if not v),"restored":True}
}
with connect() as db:summary["postgresVersion"]=db.execute("SHOW server_version").fetchone()[0]
(OUTPUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print("M2 FINAL:",len(records),"cases PASS; no cloud capacity conclusions.")
