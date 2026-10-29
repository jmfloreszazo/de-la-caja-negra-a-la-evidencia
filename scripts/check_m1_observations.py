#!/usr/bin/env python3
"""Fail closed on M1 snapshots: tested transport only, never E3 or ledger evidence."""
import json
from pathlib import Path
import re

base=Path(__file__).resolve().parents[1]/"evidence/runs"
for parallel in (8,32):
    file=base/f"m1-transport-c{parallel}.json"
    r=json.loads(file.read_text(encoding="utf-8"))
    p=r["provenance"]
    o=r["observation"]
    assert r["schemaVersion"]==1 and r["experiment"]=="M1"
    assert p["runId"]==40943584513 and p["jobId"]>0
    assert re.fullmatch(r"[0-9a-f]{40}",p["workflowHeadSha"])
    assert re.fullmatch(r"[0-9a-f]{40}",p["checkoutSha"])
    assert o["sourceCommit"]==p["checkoutSha"]
    assert o["classification"]=="EXECUTED_LOCALHOST_TRANSPORT_ONLY_NOT_LEDGER_OR_MAINFRAME"
    assert o["environment"]["tlsAndNetwork"].startswith("NOT TESTED")
    assert o["workload"]["closedLoop"] is True
    assert o["workload"]["concurrency"]==parallel
    assert o["workload"]["requestsPerRound"]==2500
    assert "No durable ledger" in o["workload"]["claims"]
    assert o["negativeOracleControl"]=="PASS"
    rounds=o["trials"]
    assert [x["Protocol"] for x in rounds]==["grpc","rest","rest","grpc"]
    assert all(x["Requests"]==2500 and x["Errors"]==0 for x in rounds)
    assert all(0<x["RepliesPerSecond"] and
            0<=x["P50Ms"]<=x["P95Ms"]<=x["P99Ms"] for x in rounds)
    print("M1 c"+str(parallel)+": PASS, immutable observations from workflow",p["runId"])
print("M1 SNAPSHOT VALIDATION: PASS (not ledger, WAN, TLS or mainframe)")
