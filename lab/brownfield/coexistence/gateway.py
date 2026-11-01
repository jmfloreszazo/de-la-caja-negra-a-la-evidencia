#!/usr/bin/env python3
"""Fail-closed capability router for the cooperative two-store synthetic fixture.

It calls the simulated legacy contract as a separate process, not a parser.
Never deploy this as a production IBM Z/CICS/Db2 gateway or distributed fence.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
from two_store import connections, shadow_prediction

HERE=Path(__file__).resolve().parent
DLL=HERE.parent/"durable"/"DurableBank"/"bin"/"Release"/"net10.0"/"DurableBank.dll"
DOTNET=os.environ.get("DOTNET","dotnet")

def authority():
    _old,new=connections()
    with psycopg.connect(new) as db:
        row=db.execute("SELECT writer,epoch FROM brownfield.authority WHERE id=1").fetchone()
        if row is None or row[0] not in ("legacy","candidate") or row[1]<1:
            raise RuntimeError("Missing/invalid SQL authority")
        return row[0],row[1]

def command(args):
    outcome=subprocess.run(args,text=True,capture_output=True,timeout=50,env=os.environ)
    if outcome.returncode!=0:
        raise RuntimeError("Black-box adapter failed closed: "+outcome.stderr.strip())
    try:
        result=json.loads(outcome.stdout)
    except json.JSONDecodeError as ex:
        raise RuntimeError("Non-JSON adapter response") from ex
    if not isinstance(result,dict) or "status" not in result:
        raise RuntimeError("Invalid adapter response")
    return result

def transfer(operation_id,source,destination,amount):
    writer,epoch=authority()
    if writer=="legacy":
        result=command([sys.executable,str(HERE/"legacy_api.py"),"transfer",
                        str(operation_id),str(source),str(destination),str(amount),str(epoch)])
    else:
        result=command([DOTNET,str(DLL),"transfer",str(operation_id),str(source),
                        str(destination),str(amount),"candidate",str(epoch)])
    return {"routedTo":writer,**result}

def balance(account,minimum_version=0):
    writer,_epoch=authority()
    if writer=="legacy":
        if minimum_version!=0:
            # The external legacy CLI does not yet expose a freshness argument.
            # Fail closed instead of ignoring the caller's consistency contract.
            raise RuntimeError("Legacy adapter cannot guarantee requested minimum version")
        result=command([sys.executable,str(HERE/"legacy_api.py"),"balance",str(account)])
    else:
        result=command([DOTNET,str(DLL),"balance",str(account),str(minimum_version)])
    return {"routedTo":writer,**result}

def shadow(source,destination,amount):
    if authority()[0]!="legacy":
        raise RuntimeError("Shadow prediction is only valid during legacy authority")
    result=shadow_prediction(int(source),int(destination),int(amount))
    return {"status":"READ_ONLY_SHADOW","isActualCandidateExecution":False,**result}

def main(argv):
    if not argv:
        raise ValueError("Usage: route | transfer ID SRC DST AMOUNT | balance ACCOUNT [MIN_VER] | shadow SRC DST AMOUNT")
    if argv==["route"]:
        writer,epoch=authority()
        return {"status":"ROUTE","writer":writer,"epoch":epoch}
    if len(argv)==5 and argv[0]=="transfer":
        return transfer(argv[1],int(argv[2]),int(argv[3]),int(argv[4]))
    if len(argv) in (2,3) and argv[0]=="balance":
        return balance(int(argv[1]),int(argv[2]) if len(argv)==3 else 0)
    if len(argv)==4 and argv[0]=="shadow":
        return shadow(int(argv[1]),int(argv[2]),int(argv[3]))
    raise ValueError("Invalid command")

if __name__=="__main__":
    try:
        print(json.dumps(main(sys.argv[1:]),sort_keys=True))
    except Exception as ex:
        print(json.dumps({"status":"BLOCKED","reason":str(ex)}))
        sys.exit(2)
