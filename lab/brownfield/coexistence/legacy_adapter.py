#!/usr/bin/env python3
"""Black-box simulated legacy command adapter. NO COBOL/parser or customer policy."""
import hashlib
import json
import os
import re
import sys
import time

import psycopg

def connection():
    if os.environ.get("BROWNFIELD_DISPOSABLE") != "YES":
        raise RuntimeError("Disposable opt-in required")
    dsn=os.environ["BROWNFIELD_LEGACY_DSN"]
    cfg=psycopg.conninfo.conninfo_to_dict(dsn)
    if cfg.get("dbname")!="bf_legacy" or cfg.get("host")!="127.0.0.1" or cfg.get("port")!="55438":
        raise RuntimeError("Only the isolated local bf_legacy:55438 fixture is allowed")
    return psycopg.connect(dsn)

def fingerprint(source, destination, amount):
    value=f"v1|source={source}|destination={destination}|amountMinor={amount}|currency=EUR|mandate=SYNTHETIC"
    return hashlib.sha256(value.encode()).hexdigest()

def transfer(op, src, dst, amount, expected_epoch):
    if not re.fullmatch(r"[A-Za-z0-9-]{1,80}",op):
        raise ValueError("Invalid operation ID")
    if not (1<=src<=16 and 1<=dst<=16 and src!=dst and 1<=amount<=1_000_000_000_000 and expected_epoch>=1):
        raise ValueError("Invalid transfer")
    request_hash=fingerprint(src,dst,amount)
    for attempt in range(6):
        try:
            with connection() as conn:
                with conn.transaction():
                    conn.execute("SET LOCAL lock_timeout='750ms'")
                    authority=conn.execute(
                        "SELECT mode,epoch FROM legacy.authority WHERE singleton=1 FOR SHARE"
                    ).fetchone()
                    if authority!=("ACTIVE",expected_epoch):
                        return {"status":"FENCED_LEGACY","epoch":authority[1]}
                    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",(op,))
                    previous=conn.execute(
                        "SELECT request_hash,decision FROM legacy.transactions WHERE request_id=%s",(op,)
                    ).fetchone()
                    if previous is not None:
                        return {"status":"DUPLICATE_"+previous[1] if previous[0]==request_hash else "ID_CONFLICT"}
                    for account in sorted((src,dst)):
                        row=conn.execute("SELECT account_no FROM legacy.accounts WHERE account_no=%s FOR UPDATE",(account,)).fetchone()
                        if row is None:
                            return {"status":"MISSING_ACCOUNT"}
                    debit=conn.execute(
                        "UPDATE legacy.accounts SET ledger_minor=ledger_minor-%s WHERE account_no=%s AND ledger_minor >= %s",
                        (amount,src,amount)
                    ).rowcount
                    decision="COMMITTED" if debit else "REJECTED"
                    if debit:
                        conn.execute("UPDATE legacy.accounts SET ledger_minor=ledger_minor+%s WHERE account_no=%s",(amount,dst))
                    conn.execute(
                        "INSERT INTO legacy.transactions(request_id,request_hash,source_no,destination_no,value_minor,decision,authority_epoch) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (op,request_hash,src,dst,amount,decision,expected_epoch)
                    )
                    sequence=conn.execute(
                        "UPDATE legacy.clock SET sequence_no=sequence_no+1 WHERE singleton=1 RETURNING sequence_no"
                    ).fetchone()[0]
                    if debit:
                        conn.execute("UPDATE legacy.accounts SET revision=%s WHERE account_no IN (%s,%s)",(sequence,src,dst))
                        conn.execute(
                            "INSERT INTO legacy.entries(request_id,account_no,amount_minor) VALUES (%s,%s,%s),(%s,%s,%s)",
                            (op,src,-amount,op,dst,amount)
                        )
                        conn.execute("INSERT INTO legacy.notices(request_id,kind) VALUES (%s,'TransferCommitted')",(op,))
                    return {"status":decision,"watermark":sequence}
        except psycopg.errors.DeadlockDetected:
            time.sleep(0.025*(attempt+1))
        except psycopg.errors.LockNotAvailable:
            time.sleep(0.025*(attempt+1))
    return {"status":"RETRY_EXHAUSTED"}

def balance(account, minimum):
    if not (1<=account<=16 and minimum>=0):
        raise ValueError("Invalid balance query")
    with connection() as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            version=conn.execute("SELECT sequence_no FROM legacy.clock WHERE singleton=1").fetchone()[0]
            bal,rev=conn.execute(
                "SELECT ledger_minor,revision FROM legacy.accounts WHERE account_no=%s",(account,)
            ).fetchone()
            return {"status":"AUTHORITATIVE" if version>=minimum else "BELOW_MINIMUM_VERSION",
                "balanceMinor":bal,"accountVersion":rev,"watermark":version,
                "source":"SYNTHETIC_LEGACY_BLACK_BOX"}

def main():
    if len(sys.argv)<2:
        return 4
    if sys.argv[1]=="transfer" and len(sys.argv)==7:
        result=transfer(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]))
    elif sys.argv[1]=="balance" and len(sys.argv)==4:
        result=balance(int(sys.argv[2]),int(sys.argv[3]))
    else:
        return 4
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"{type(error).__name__}: {error}",file=sys.stderr)
        sys.exit(5)
