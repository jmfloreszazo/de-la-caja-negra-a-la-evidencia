#!/usr/bin/env python3
"""Fail closed on M1 snapshots: tested transport only, never E3 or ledger evidence."""
import json
from pathlib import Path
import re
import os
import sys
from urllib.request import Request, urlopen

base=Path(__file__).resolve().parents[1]/"evidence/runs"
records=[]
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
    records.append(r)
    print("M1 c"+str(parallel)+": PASS, immutable observations from workflow",p["runId"])

if "--online" in sys.argv:
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN required for --online")
    repo="jmfloreszazo/de-la-caja-negra-a-la-evidencia"
    def fetch(path):
        url=f"https://api.github.com/repos/{repo}/{path}"
        req=Request(url,headers={
          "Authorization":"Bearer "+token,
          "Accept":"application/vnd.github+json",
          "X-GitHub-Api-Version":"2022-11-28",
          "User-Agent":"M1-Provenance-Validator"
        })
        with urlopen(req,timeout=30) as response:
            return json.load(response)
    run=fetch("actions/runs/40943584513")
    assert run["status"]=="completed" and run["conclusion"]=="success"
    assert run["event"]=="pull_request"
    jobs=fetch("actions/runs/40943584513/jobs?per_page=100")["jobs"]
    assert len({r["provenance"]["runId"] for r in records})==1
    for record in records:
        p=record["provenance"]
        assert run["head_sha"]==p["workflowHeadSha"]
        assert any(j["id"]==p["jobId"] and j["name"]=="transport"
                   and j["conclusion"]=="success" for j in jobs)
        assert p["source"]==run["html_url"]
    print("M1 LIVE GITHUB PROVENANCE: PASS, successful run and source SHA verified")

print("M1 SNAPSHOT VALIDATION: PASS (not ledger, WAN, TLS or mainframe)")
