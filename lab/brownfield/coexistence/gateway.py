#!/usr/bin/env python3
"""Synthetic capability-level ACL and conservative two-PostgreSQL cutover.

The adapter is an external CLI contract. This process does not import or
translate COBOL source. Legacy/Candidate databases are independent disposable
server processes on one host, not independent physical failure domains.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg

from reconcile import candidate_dsn, legacy_dsn, legacy_checks, reconcile, snapshot

HERE=Path(__file__).resolve().parent
DLL=HERE.parent/"durable"/"DurableBank"/"bin"/"Release"/"net10.0"/"DurableBank.dll"
DOTNET=os.environ.get("DOTNET","dotnet")

class CutoverBlocked(RuntimeError):
    pass

def legacy_db():
    return psycopg.connect(legacy_dsn())

def candidate_db():
    return psycopg.connect(candidate_dsn())

def run(command):
    p=subprocess.run(command,text=True,capture_output=True,timeout=45,env=os.environ)
    if p.returncode:
        raise CutoverBlocked(f"Adapter failed closed: rc={p.returncode}: {p.stderr.strip()}")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise CutoverBlocked("Adapter did not return canonical JSON") from exc

def legacy_call(*args):
    return run([sys.executable,str(HERE/"legacy_adapter.py"),*map(str,args)])

def candidate_call(*args):
    return run([DOTNET,str(DLL),*map(str,args)])

def authority():
    with legacy_db() as db:
        source=db.execute("SELECT mode,epoch FROM legacy.authority WHERE singleton=1").fetchone()
    with candidate_db() as db:
        target=db.execute("SELECT writer,epoch FROM brownfield.authority WHERE id=1").fetchone()
    return source,target

def route():
    source,target=authority()
    if source[0]=="ACTIVE" and target[0]=="legacy":
        # Candidate SQL contains seeded shadow state, never a target business writer.
        return "legacy",source[1]
    if source[0]=="FENCED" and target[0]=="candidate":
        return "candidate",target[1]
    return "BLOCK",0

def transfer(op,src,dst,amount):
    writer,epoch=route()
    if writer=="legacy":
        return {"routedTo":"legacy",**legacy_call("transfer",op,src,dst,amount,epoch)}
    if writer=="candidate":
        return {"routedTo":"candidate",**candidate_call("transfer",op,src,dst,amount,"candidate",epoch)}
    return {"routedTo":"none","status":"BLOCKED_NO_SINGLE_WRITER"}

def balance(account,minimum=0):
    writer,epoch=route()
    if writer=="legacy":
        return {"routedTo":"legacy",**legacy_call("balance",account,minimum)}
    if writer=="candidate":
        return {"routedTo":"candidate",**candidate_call("balance",account,minimum)}
    return {"routedTo":"none","status":"BLOCKED_NO_SINGLE_WRITER"}

def shadow_preview(source,dest,amount):
    """No SQL target write. Advisory prediction only; never acceptance evidence."""
    if route()[0]!="legacy" or not (1<=source<=16 and 1<=dest<=16 and source!=dest and amount>0):
        return {"status":"SHADOW_BLOCKED"}
    src=snapshot("legacy")
    balances={a[0]:a[1] for a in src["accounts"]}
    return {"status":"READ_ONLY_PREDICTION","wouldDecide":"COMMITTED" if balances[source]>=amount else "REJECTED",
        "watermark":src["watermark"],"targetPostingCount":len(snapshot("candidate")["postings"]),
        "isActualCandidateExecution":False}

def seal_legacy():
    if route()[0]!="legacy":
        raise CutoverBlocked("Cutover requires legacy-only routing")
    with legacy_db() as db:
        with db.transaction():
            row=db.execute("SELECT mode,epoch FROM legacy.authority WHERE singleton=1 FOR UPDATE").fetchone()
            if row[0]!="ACTIVE":
                raise CutoverBlocked("Legacy is not active")
            db.execute("UPDATE legacy.authority SET mode='FENCED' WHERE singleton=1")
    # After commit the independent adapter holds no authority to add new data.
    if route()[0]!="BLOCK":
        raise CutoverBlocked("Legacy seal did not create a no-writer interval")

def copy_fenced_snapshot():
    source=snapshot("legacy")
    if source["authority"][0]!="FENCED":
        raise CutoverBlocked("Cannot copy from an unfenced source")
    checks=legacy_checks(source)
    if not all(checks.values()):
        raise CutoverBlocked("Source failed independent accounting checks")
    if route()[0]!="BLOCK":
        raise CutoverBlocked("Import must occur while both routes are disabled")
    with candidate_db() as db:
        with db.transaction():
            state=db.execute(
                "SELECT writer,epoch FROM brownfield.authority WHERE id=1 FOR UPDATE"
            ).fetchone()
            if state!=("legacy",1):
                raise CutoverBlocked("Target must be unpromoted baseline")
            target_count=db.execute("SELECT count(*) FROM brownfield.operations").fetchone()[0]
            target_clock=db.execute("SELECT watermark FROM brownfield.commit_clock WHERE id=1").fetchone()[0]
            if target_count!=0 or target_clock!=0:
                raise CutoverBlocked("Target not pristine; cannot silently overwrite decisions")
            if db.execute("SELECT count(*) FROM brownfield.postings").fetchone()[0]!=0:
                raise CutoverBlocked("Target already has postings")
            if db.execute("SELECT count(*) FROM brownfield.outbox").fetchone()[0]!=0:
                raise CutoverBlocked("Target already has outbox records")
            for account,balance,revision in source["accounts"]:
                db.execute("UPDATE brownfield.accounts SET balance=%s,version=%s WHERE id=%s",
                           (balance,revision,account))
            for op,request_hash,src,dst,value,decision in source["operations"]:
                db.execute(
                    "INSERT INTO brownfield.operations(id,fingerprint,writer,epoch,src,dst,amount,status) "
                    "VALUES (%s,%s,'legacy',1,%s,%s,%s,%s)",
                    (op,request_hash,src,dst,value,decision))
            for op,account,delta in source["postings"]:
                db.execute("INSERT INTO brownfield.postings(operation_id,account_id,delta) VALUES (%s,%s,%s)",
                           (op,account,delta))
            for op,kind in source["outbox"]:
                db.execute("INSERT INTO brownfield.outbox(operation_id,event_type) VALUES (%s,%s)",(op,kind))
            db.execute("UPDATE brownfield.commit_clock SET watermark=%s WHERE id=1",
                       (source["watermark"],))
    return {"status":"COPIED_NOT_PROMOTED","watermark":source["watermark"]}

def promote():
    if route()[0]!="BLOCK":
        raise CutoverBlocked("Promotion requires no writer during reconciliation")
    source,target=authority()
    if source[0]!="FENCED" or target!=("legacy",1):
        raise CutoverBlocked("Wrong authority state for first promotion")
    report=reconcile()
    if not report["passed"]:
        raise CutoverBlocked("CUTOVER_BLOCKED_SQL_MISMATCH:"+",".join(report["differences"]))
    outcome=candidate_call("switch","legacy",1,"candidate",
                           report["sourceCount"],report["sourceCount"])
    if outcome["status"]!="SYNTHETIC_SWITCH" or outcome["todmG6"]!="BLOCK":
        raise CutoverBlocked("Candidate promotion was rejected")
    if route()[0]!="candidate":
        raise CutoverBlocked("Routing did not converge")
    return {"status":"SYNTHETIC_CUTOVER","writer":"candidate","epoch":outcome["epoch"],
            "baselineDecisions":report["sourceCount"],"todmG6":"BLOCK"}

def rollback():
    source,target=authority()
    if source[0]!="FENCED" or target[0]!="candidate":
        raise CutoverBlocked("Rollback requires one fenced legacy source")
    report=reconcile()
    if not report["passed"]:
        raise CutoverBlocked("ROLLBACK_BLOCKED_FORWARD_RECONCILIATION_REQUIRED")
    # Strictly forbid rollback after ANY new candidate decision, even one
    # whose net balance is zero or whose operation ID looks familiar.
    if report["sourceCount"]!=report["targetCount"]:
        raise CutoverBlocked("ROLLBACK_BLOCKED_NEW_CANDIDATE_DECISIONS")
    outcome=candidate_call("switch","candidate",target[1],"legacy",
                           report["targetCount"],report["targetCount"])
    if outcome["status"]!="SYNTHETIC_SWITCH":
        raise CutoverBlocked("Target deactivation failed")
    # Crash between deactivation and legacy reactivation => zero writers,
    # never two. Caller can inspect evidence; no auto-retry to prod.
    with legacy_db() as db:
        with db.transaction():
            row=db.execute("SELECT mode,epoch FROM legacy.authority WHERE singleton=1 FOR UPDATE").fetchone()
            if row!=source:
                raise CutoverBlocked("Legacy authority changed during rollback")
            db.execute("UPDATE legacy.authority SET mode='ACTIVE',epoch=epoch+1 WHERE singleton=1")
    if route()[0]!="legacy":
        raise CutoverBlocked("Legacy reactivation did not converge")
    return {"status":"SYNTHETIC_ROLLBACK","writer":"legacy","todmG6":"BLOCK"}

def main(argv):
    if not argv:
        raise ValueError("Usage: route|transfer|balance|shadow|seal|copy|promote|rollback")
    if argv[0]=="route" and len(argv)==1:
        return {"route":route()[0],"sourceAndTarget":authority()}
    if argv[0]=="transfer" and len(argv)==5:
        return transfer(argv[1],int(argv[2]),int(argv[3]),int(argv[4]))
    if argv[0]=="balance" and len(argv)==3:
        return balance(int(argv[1]),int(argv[2]))
    if argv[0]=="shadow" and len(argv)==4:
        return shadow_preview(int(argv[1]),int(argv[2]),int(argv[3]))
    if argv[0]=="seal" and len(argv)==1:
        seal_legacy()
        return {"status":"LEGACY_FENCED","route":route()[0]}
    if argv[0]=="copy" and len(argv)==1:
        return copy_fenced_snapshot()
    if argv[0]=="promote" and len(argv)==1:
        return promote()
    if argv[0]=="rollback" and len(argv)==1:
        return rollback()
    raise ValueError("Unsupported or malformed command")

if __name__=="__main__":
    try:
        print(json.dumps(main(sys.argv[1:]),sort_keys=True))
    except (CutoverBlocked,ValueError) as ex:
        print(json.dumps({"status":"BLOCKED","reason":str(ex)}))
        sys.exit(2)
