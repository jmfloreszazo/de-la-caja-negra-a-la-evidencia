#!/usr/bin/env python3
"""Independent, read-only reconciliation across two disposable PostgreSQL servers.

This is a deterministic synthetic ledger comparison, not external bank approval.
"""
from collections import Counter, defaultdict
import hashlib
import json
import os
import sys
from pathlib import Path
import psycopg

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"durable"))
from oracle import observe as candidate_oracle

def legacy_dsn():
    dsn=os.environ["BROWNFIELD_LEGACY_DSN"]
    cfg=psycopg.conninfo.conninfo_to_dict(dsn)
    if (cfg.get("dbname"),cfg.get("host"),cfg.get("port"))!=("bf_legacy","127.0.0.1","55438"):
        raise ValueError("Legacy oracle requires exact isolated bf_legacy fixture")
    return dsn

def candidate_dsn():
    dsn=os.environ["BROWNFIELD_PG_DSN"]
    cfg=psycopg.conninfo.conninfo_to_dict(dsn)
    if (cfg.get("dbname"),cfg.get("host"),cfg.get("port"))!=("bf_lab","127.0.0.1","55437"):
        raise ValueError("Candidate oracle requires exact isolated bf_lab fixture")
    return dsn

def snapshot(which):
    if which not in ("legacy","candidate"):
        raise ValueError("Unknown side")
    dsn=legacy_dsn() if which=="legacy" else candidate_dsn()
    with psycopg.connect(dsn,autocommit=True) as db:
        with db.transaction():
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            if which=="legacy":
                accounts=db.execute("SELECT account_no,ledger_minor,revision FROM legacy.accounts ORDER BY account_no").fetchall()
                ops=db.execute("SELECT request_id,request_hash,source_no,destination_no,value_minor,decision FROM legacy.transactions ORDER BY request_id").fetchall()
                postings=db.execute("SELECT request_id,account_no,amount_minor FROM legacy.entries ORDER BY request_id,account_no").fetchall()
                events=db.execute("SELECT request_id,kind FROM legacy.notices ORDER BY request_id").fetchall()
                clock=db.execute("SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()[0]
                authority=db.execute("SELECT mode,epoch FROM legacy.authority WHERE singleton=1").fetchone()
            else:
                accounts=db.execute("SELECT id,balance,version FROM brownfield.accounts ORDER BY id").fetchall()
                ops=db.execute("SELECT id,fingerprint,src,dst,amount,status FROM brownfield.operations ORDER BY id").fetchall()
                postings=db.execute("SELECT operation_id,account_id,delta FROM brownfield.postings ORDER BY operation_id,account_id").fetchall()
                events=db.execute("SELECT operation_id,event_type FROM brownfield.outbox ORDER BY operation_id").fetchall()
                clock=db.execute("SELECT watermark FROM brownfield.commit_clock WHERE id=1").fetchone()[0]
                authority=db.execute("SELECT writer,epoch FROM brownfield.authority WHERE id=1").fetchone()
    return {"accounts":[list(row) for row in accounts],
            "operations":[list(row) for row in ops],
            "postings":[list(row) for row in postings],
            "outbox":[list(row) for row in events],
            "watermark":clock,"authority":list(authority)}

def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(",",":"),sort_keys=True,ensure_ascii=True).encode()).hexdigest()

def legacy_checks(s):
    accounts={a[0]:a[1] for a in s["accounts"]}
    operations={o[0]:o for o in s["operations"]}
    by_op=defaultdict(list)
    deltas=Counter()
    for op,acc,delta in s["postings"]:
        by_op[op].append((acc,delta))
        deltas[acc]+=delta
    committed={k:v for k,v in operations.items() if v[5]=="COMMITTED"}
    rejected=set(operations)-set(committed)
    events=dict(s["outbox"])
    exact=all(Counter(by_op[op])==Counter({(row[2],-row[4]):1,(row[3],row[4]):1})
              for op,row in committed.items())
    return {
        "accountFixture":sorted(accounts)==list(range(1,17)),
        "conservation":sum(accounts.values())==16*100_000,
        "nonnegative":all(v>=0 for v in accounts.values()),
        "balanceDerivedFromEntries":all(accounts[n]==100_000+deltas[n] for n in range(1,17)),
        "pairing":exact and set(by_op)==set(committed) and len(s["postings"])==2*len(committed),
        "noRejectedSideEffects":not (rejected & (set(by_op)|set(events))),
        "outboxCardinality":set(events)==set(committed) and all(v=="TransferCommitted" for v in events.values()),
        "watermarkMatchesDecisions":s["watermark"]==len(operations),
        "versionBounds":all(0<=a[2]<=s["watermark"] for a in s["accounts"]),
        "uniqueOperationIds":len(operations)==len(s["operations"]),
    }

def reconcile():
    source=snapshot("legacy")
    target=snapshot("candidate")
    source_checks=legacy_checks(source)
    target_checks=candidate_oracle(candidate_dsn())
    keys=("accounts","operations","postings","outbox","watermark")
    digests={k:{"legacy":digest(source[k]),"candidate":digest(target[k])} for k in keys}
    differences=[k for k in keys if digests[k]["legacy"]!=digests[k]["candidate"]]
    safe=all(source_checks.values()) and target_checks["passed"] and not differences
    return {"passed":safe,"classification":"SYNTHETIC_TWO_POSTGRES_SERVERS_NO_BUSINESS_APPROVAL",
            "sourceChecks":source_checks,"targetChecks":target_checks["checks"],
            "sourceWriter":source["authority"],"targetWriter":target["authority"],
            "sourceCount":len(source["operations"]),"targetCount":len(target["operations"]),
            "digests":digests,"differences":differences,"todmG6":"BLOCK"}

if __name__=="__main__":
    report=reconcile()
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report["passed"] else 1)
