#!/usr/bin/env python3
"""Check recorded M2 results, deterministic scope and live GitHub provenance."""
import json
import os
from pathlib import Path
import sys
from urllib.request import Request,urlopen

root=Path(__file__).resolve().parents[1]
record=json.loads((root/"evidence/runs/m2-local-observations.json").read_text(encoding="utf-8"))
p=record["provenance"]
w=record["workload"]
assert record["schemaVersion"]==1 and record["experiment"]=="M2"
assert record["classification"]=="EXECUTED_SINGLE_HOST_POSTGRES_LOCAL_SMOKE_NOT_CLOUD_OR_MAINFRAME"
assert p["runId"]==41016081107 and p["artifactId"]==12959965944
assert w["cases"]==20 and w["requestsPerCase"]==256 and w["concurrency"]==16
assert w["replicas"]==[1,2,4,8,16]
assert set(w["limits"])>={"no Azure/AKS/VMSS","no TLS/mTLS","no real WAN"}
assert record["independentOracle"]["perCaseCommitted"]==256
assert record["independentOracle"]["perCasePostings"]==512
assert record["independentOracle"]["perCaseOutbox"]==256
values=record["cases"]
expected={f"{d}-{n}-{p}" for d in ("uniform","hot")
          for n in (1,2,4,8,16) for p in ("rest","grpc")}
assert {x["case"] for x in values}==expected and len(values)==20
assert all(x["commits"]==256 and x["oracle"]=="PASS" and
           x["tps"]>0 and x["p99"]>0 for x in values)
assert "detected" in record["independentOracle"]["finalNegativeControl"]
print("M2 OFFLINE EVIDENCE: PASS, 20 correctly scoped PostgreSQL observations")

if "--online" in sys.argv:
    token=os.environ.get("GITHUB_TOKEN")
    if not token:raise ValueError("GITHUB_TOKEN needed for online check")
    repo="jmfloreszazo/de-la-caja-negra-a-la-evidencia"
    def fetch(path):
        request=Request("https://api.github.com/repos/"+repo+"/"+path,headers={
            "Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28","User-Agent":"M2-Evidence-Audit"})
        with urlopen(request,timeout=30) as res:return json.load(res)
    run=fetch("actions/runs/"+str(p["runId"]))
    assert run["status"]=="completed" and run["conclusion"]=="success"
    assert run["head_sha"]==p["headSha"]
    assert run["html_url"]==p["runUrl"]
    jobs=fetch("actions/runs/"+str(p["runId"])+"/jobs?per_page=100")["jobs"]
    assert any(j["id"]==p["jobId"] and j["name"]=="durable-evidence" and
               j["conclusion"]=="success" for j in jobs)
    artifact=fetch("actions/artifacts/"+str(p["artifactId"]))
    assert artifact["name"]==p["artifactName"]
    assert not artifact.get("expired",False)
    print("M2 LIVE SOURCE AND ARTIFACT PROVENANCE: PASS")
