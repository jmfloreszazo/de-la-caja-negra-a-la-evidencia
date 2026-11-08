#!/usr/bin/env python3
"""Bounded open-loop exploratory experiment; never an E3 capacity verdict."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PROJECT = HERE / "E3Fixture" / "E3Fixture.csproj"
DLL = HERE / "E3Fixture" / "bin" / "Release" / "net10.0" / "E3Fixture.dll"
DOTNET = os.environ.get("DOTNET", "dotnet")
CLASSIFICATION = "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE"
TOPOLOGY = "SINGLE_HOST_PROCESS_FAILURE_NOT_PHYSICAL_HA"


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def retain_runtime_artifacts(build_directory, output):
    """Retain the hashed runtime bytes as bounded, flat archive artifacts."""
    build_directory = build_directory.resolve(strict=True)
    output = output.resolve(strict=True)
    if not build_directory.is_relative_to(ROOT) or not output.is_relative_to(ROOT):
        raise ValueError("Runtime artifacts must stay within the repository")
    candidates = sorted(p for p in build_directory.iterdir() if p.suffix in (".dll", ".json"))
    if not candidates or len(candidates) > 128:
        raise ValueError("Invalid runtime artifact count")
    total = 0
    for source in candidates:
        if source.is_symlink() or not source.is_file() or source.resolve().parent != build_directory:
            raise ValueError("Runtime artifact must be a direct regular file")
        total += source.stat().st_size
        if total > 128 * 1024 * 1024:
            raise ValueError("Runtime artifacts exceed 128 MiB")
        if (output / source.name).exists():
            raise ValueError("Runtime artifact would overwrite an existing output")
    hashes = {}
    copied = 0
    for source in candidates:
        original_hash = digest(source)
        with source.open("rb") as reader, (output / source.name).open("xb") as writer:
            while chunk := reader.read(1024 * 1024):
                copied += len(chunk)
                if copied > 128 * 1024 * 1024:
                    raise ValueError("Runtime artifacts grew beyond 128 MiB")
                writer.write(chunk)
        if digest(output / source.name) != original_hash or digest(source) != original_hash:
            raise RuntimeError("Runtime artifact changed during retention")
        hashes[source.name] = original_hash
    return hashes


def validate_dsn(dsn, attested):
    parsed = conninfo_to_dict(dsn)
    if (os.environ.get("E3_DISPOSABLE_FIXTURE") != "YES"
            or parsed.get("host") != "127.0.0.1"
            or parsed.get("hostaddr", "127.0.0.1") != "127.0.0.1"
            or parsed.get("options") or parsed.get("service")
            or parsed.get("dbname") in (None, "", "postgres", "template0", "template1")):
        raise ValueError("Require E3_DISPOSABLE_FIXTURE=YES and explicit disposable loopback DSN without options/service")
    actual = {"host": parsed["host"], "port": int(parsed.get("port", 5432)),
              "database": parsed["dbname"], "username": parsed.get("user")}
    if actual != attested:
        raise ValueError("Python and .NET connections must name the same host, port, database and user")
    return actual


def source_provenance():
    names = ("SOURCE_HEAD_SHA", "SOURCE_ARCHIVE_SHA256", "SOURCE_WORKTREE_DIRTY")
    exported = {key: os.environ.get(key) for key in names}
    if any(exported.values()):
        head, archive, dirty = (exported[key] for key in names)
        if (not head or len(head) != 40 or not archive or len(archive) != 64
                or any(c not in "0123456789abcdefABCDEF" for c in head + archive)
                or dirty not in ("true", "false", "0", "1")):
            raise ValueError("Supply the complete valid launcher-attested source export trio")
    files = [*HERE.glob("*.py"), HERE / "workload.json", HERE / "README.md",
             *HERE.glob("E3Fixture/*.cs*"),
             ROOT / "lab" / "durable_rpc" / "DurableRpc" / "Program.cs",
             ROOT / "lab" / "durable_rpc" / "DurableRpc" / "DurableRpc.csproj",
             ROOT / "lab" / "durable_rpc" / "DurableRpc" / "Protos" / "ledger.proto",
             ROOT / "lab" / "e1_pg" / "oracle.py", ROOT / "lab" / "e1_pg" / "schema.sql",
             ROOT / "lab" / "performance-contract.json"]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)}
    def git(*args):
        try:
            result = subprocess.run(["git", "--no-pager", *args], cwd=ROOT,
                                    capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    return {"launcherAttestedExport": exported, "localGitHead": git("rev-parse", "HEAD"),
            "localGitStatus": git("status", "--short"), "fileSha256": hashes,
            "sourceSetSha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}


def validate_workload(config, profile):
    rates = profile["ratesPerSecond"]
    duration = len(rates) * profile["phaseSeconds"]
    if (not 1 <= len(rates) <= 3 or any(type(rate) is not int or not 1 <= rate <= 100 for rate in rates)
            or type(profile["phaseSeconds"]) is not int or not 1 <= profile["phaseSeconds"] <= 10
            or duration > 30 or sum(rates) * profile["phaseSeconds"] > 2000
            or not 0 < profile["killAtSeconds"] < profile["restartAtSeconds"] < duration - 1
            or config["replicas"] != 2 or config["maxInFlight"] != 32
            or config["requestTimeoutSeconds"] != 2 or config["maxDispatchLatenessSeconds"] != .1):
        raise ValueError("Workload exceeds the bounded preregistration envelope")


def make_offers(profile, run_id):
    records = []
    for phase, rate in enumerate(profile["ratesPerSecond"]):
        for offset in range(rate * profile["phaseSeconds"]):
            index = len(records)
            records.append({"index": index, "phase": phase, "ratePerSecond": rate,
                            "scheduledSeconds": phase * profile["phaseSeconds"] + offset / rate,
                            "replica": index % 2, "operationId": f"e3-{run_id}-{index}",
                            "src": 1 + index % 16, "dst": 1 + (index + 1) % 16,
                            "amountCents": 1 + index % 4, "outcome": "MISSED_RUN_ABORTED",
                            "dispatchSeconds": None, "completionSeconds": None,
                            "endToEndMs": None, "dispatchLatenessMs": None})
    return records


def dispatch_decision(lateness, active, config):
    if lateness > config["maxDispatchLatenessSeconds"]:
        return "MISSED_SCHEDULE"
    if active >= config["maxInFlight"]:
        return "MISSED_INFLIGHT_LIMIT"
    return None


def request_json(url, timeout, body=None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    payload = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=timeout) as response:
        return json.loads(response.read(16384))


def send_offer(record, port, origin, config):
    now = time.monotonic() - origin
    lateness = now - record["scheduledSeconds"]
    if lateness > config["maxDispatchLatenessSeconds"]:
        record["outcome"] = "MISSED_SCHEDULE"
        record["dispatchLatenessMs"] = lateness * 1000
        return
    record["dispatchSeconds"] = now
    record["dispatchLatenessMs"] = lateness * 1000
    command = {key: record[key] for key in ("operationId", "src", "dst", "amountCents")}
    try:
        result = request_json(f"http://127.0.0.1:{port}/transfer", config["requestTimeoutSeconds"], command)
        record["response"] = result
        if not isinstance(result, dict):
            raise ValueError("Expected an object response")
        if (result.get("operationId") == record["operationId"]
                and result.get("amountCents") == record["amountCents"]
                and result.get("status") == "COMMITTED"):
            record["outcome"] = "ACK_COMMITTED"
        elif (result.get("status") == "REJECTED" and result.get("operationId") == record["operationId"]
              and result.get("amountCents") == 0):
            record["outcome"] = "ACK_REJECTED"
        else:
            record["outcome"] = "AMBIGUOUS_RESPONSE"
    except urllib.error.HTTPError as exc:
        record["outcome"] = "AMBIGUOUS_HTTP_ERROR"
        record["httpStatus"] = exc.code
    except urllib.error.URLError as exc:
        record["outcome"] = ("FAILED_CONNECT" if isinstance(exc.reason, ConnectionRefusedError)
                             else "AMBIGUOUS_TRANSPORT")
        record["errorType"] = type(exc.reason).__name__
    except (OSError, ValueError, TimeoutError) as exc:
        record["outcome"] = "AMBIGUOUS_TRANSPORT"
        record["errorType"] = type(exc).__name__
    finally:
        record["completionSeconds"] = time.monotonic() - origin
        record["endToEndMs"] = (record["completionSeconds"] - record["scheduledSeconds"]) * 1000


class Services:
    def __init__(self, output, schema):
        self.output, self.schema = output, schema
        self.children, self.logs, self.events = [], [], []
        self.current = {}
        self.ports = []
        # Reserve both ports together so they cannot be selected twice.
        with socket.socket() as first, socket.socket() as second:
            for sock in (first, second):
                sock.bind(("127.0.0.1", 0))
                self.ports.append(sock.getsockname()[1])

    def start(self, replica):
        env = dict(os.environ, E3_PG_SCHEMA=self.schema)
        log = (self.output / f"service-{replica}-{len(self.children)}.log").open("w", encoding="utf-8")
        self.logs.append(log)
        child = subprocess.Popen([DOTNET, str(DLL), "server", str(self.ports[replica])],
                                 env=env, stdout=log, stderr=subprocess.STDOUT)
        self.children.append(child)
        self.current[replica] = child
        return child

    def ready(self, replica):
        child = self.current[replica]
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError("Owned E3 service exited before readiness; see service log")
            try:
                health = request_json(f"http://127.0.0.1:{self.ports[replica]}/health", 0.5)
                if health == {"pid": child.pid, "schema": self.schema}:
                    return
            except (OSError, ValueError):
                pass
            time.sleep(0.05)
        raise TimeoutError("Owned E3 service readiness timed out")

    def close(self):
        for child in self.children:
            if child.poll() is None:
                child.kill()
        for child in self.children:
            child.wait(timeout=8)
        for log in self.logs:
            log.close()


def run_load(services, offers, config, profile):
    origin = time.monotonic() + 0.1
    stop = threading.Event()
    failures = []

    def fault():
        try:
            if stop.wait(max(0, origin + profile["killAtSeconds"] - time.monotonic())):
                return
            child = services.current[0]
            if child.poll() is not None:
                raise RuntimeError("Target service already exited before injection")
            event = {"action": "KILL_PROCESS", "replica": 0, "pid": child.pid,
                     "scheduledSeconds": profile["killAtSeconds"],
                     "actualSeconds": time.monotonic() - origin}
            child.kill()
            child.wait(timeout=5)
            event["exitCode"] = child.returncode
            services.events.append(event)
            if stop.wait(max(0, origin + profile["restartAtSeconds"] - time.monotonic())):
                return
            child = services.start(0)
            services.events.append({"action": "RESTART_PROCESS", "replica": 0, "pid": child.pid,
                                    "scheduledSeconds": profile["restartAtSeconds"],
                                    "actualSeconds": time.monotonic() - origin})
            services.ready(0)
            services.events.append({"action": "RECOVERY_HEALTHY", "replica": 0, "pid": child.pid,
                                    "actualSeconds": time.monotonic() - origin})
        except Exception as exc:
            failures.append(type(exc).__name__)

    thread = threading.Thread(target=fault, name="e3-owned-process-fault")
    thread.start()
    active = set()
    try:
        with ThreadPoolExecutor(max_workers=config["maxInFlight"]) as executor:
            for record in offers:
                delay = origin + record["scheduledSeconds"] - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                done = {future for future in active if future.done()}
                for future in done:
                    future.result()
                active -= done
                missed = dispatch_decision(time.monotonic() - origin - record["scheduledSeconds"],
                                           len(active), config)
                if missed:
                    record["outcome"] = missed
                else:
                    active.add(executor.submit(send_offer, record, services.ports[record["replica"]],
                                               origin, config))
            for future in active:
                future.result()
        elapsed = time.monotonic() - origin
        thread.join(timeout=15)
        if thread.is_alive():
            raise TimeoutError("Fault lifecycle exceeded bound")
        if failures:
            raise RuntimeError("Fault lifecycle failed: " + ",".join(failures))
        return elapsed
    finally:
        stop.set()
        thread.join(timeout=20)


def reconcile(offers, rows):
    expected = {record["operationId"]: record for record in offers}
    persisted = {row[0]: row for row in rows}
    problems = []
    if len(persisted) != len(rows):
        problems.append("duplicatePersistedIdentity")
    for identity, row in persisted.items():
        record = expected.get(identity)
        if not record:
            problems.append("unexpectedPersistedIdentity:" + identity)
        elif tuple(row[1:4]) != (record["src"], record["dst"], record["amountCents"]):
            problems.append("payloadMismatch:" + identity)
    for record in offers:
        row = persisted.get(record["operationId"])
        record["persistedStatus"] = row[4] if row else "ABSENT"
        if record["outcome"] == "ACK_COMMITTED" and (not row or row[4] != "COMMITTED"):
            problems.append("acknowledgedCommitMissing:" + record["operationId"])
        if record["outcome"] == "ACK_REJECTED" and (not row or row[4] != "REJECTED"):
            problems.append("acknowledgedRejectionMissing:" + record["operationId"])
        if (record["outcome"].startswith("MISSED_") or record["outcome"] == "FAILED_CONNECT") and row:
            problems.append("unsubmittedOperationPersisted:" + record["operationId"])
    return {"consistent": not problems, "problems": problems,
            "persistedOperations": len(rows),
            "persistedCommits": sum(row[4] == "COMMITTED" for row in rows),
            "unacknowledgedPersistedCommits": sum(record["persistedStatus"] == "COMMITTED"
                and record["outcome"] != "ACK_COMMITTED" for record in offers)}


def percentile(values, q):
    return sorted(values)[max(0, math.ceil(len(values) * q) - 1)] if values else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("default", "smoke"), default="default")
    parser.add_argument("--output", type=Path, default=HERE / "results" / uuid.uuid4().hex)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args(argv)
    # No artifacts or database access before explicit opt-in and source validation.
    if os.environ.get("E3_DISPOSABLE_FIXTURE") != "YES":
        parser.error("Set E3_DISPOSABLE_FIXTURE=YES for an isolated schema in a disposable loopback E1 database")
    provenance = source_provenance()
    config = json.loads((HERE / "workload.json").read_text(encoding="utf-8"))
    profile = config["profiles"][args.profile]
    validate_workload(config, profile)
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        parser.error("Output must be a new directory within the repository")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "workload.json", config)
    summary = {"classification": CLASSIFICATION, "topology": TOPOLOGY,
               "capacityAcceptance": False, "status": "INCOMPLETE", "profile": args.profile,
               "utc": datetime.now(timezone.utc).isoformat(), "source": provenance,
               "limitations": config["limitations"], "errors": []}
    host = {"system": platform.system(), "release": platform.release(), "version": platform.version(),
            "machine": platform.machine(), "node": platform.node(), "python": platform.python_version(),
            "processors": os.cpu_count(), "uid": getattr(os, "getuid", lambda: None)(),
            "gid": getattr(os, "getgid", lambda: None)()}
    write_json(output / "host.json", host)
    summary["hostSha256"] = digest(output / "host.json")
    run_id = uuid.uuid4().hex
    schema = "e3_" + run_id
    offers = make_offers(profile, run_id)
    write_json(output / "offers-planned.json", offers)
    services = None
    admin = None
    created = False
    original_dsn = os.environ.get("E1_PG_DSN", "")
    try:
        with (output / "dotnet-info.txt").open("w", encoding="utf-8") as log:
            subprocess.run([DOTNET, "--info"], stdout=log, stderr=subprocess.STDOUT,
                           timeout=10, check=True)
        if not args.skip_build:
            with (output / "build.log").open("w", encoding="utf-8") as log:
                subprocess.run([DOTNET, "build", str(PROJECT), "-c", "Release", "-m:1",
                                "--disable-build-servers", "--nologo"], stdout=log,
                               stderr=subprocess.STDOUT, timeout=90, check=True)
        summary["runtimeArtifactSha256"] = retain_runtime_artifacts(DLL.parent, output)
        summary["binarySha256"] = summary["runtimeArtifactSha256"][DLL.name]
        descriptor = subprocess.run([DOTNET, str(DLL), "describe"], capture_output=True,
                                    text=True, check=True, timeout=10)
        summary["databaseEndpoint"] = validate_dsn(original_dsn, json.loads(descriptor.stdout))
        admin = psycopg.connect(original_dsn, autocommit=True, connect_timeout=3,
                               options="-c statement_timeout=5000 -c lock_timeout=2000")
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        created = True
        admin.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        with admin.transaction():
            admin.execute((ROOT / "lab" / "e1_pg" / "schema.sql").read_text(encoding="utf-8"))
        os.environ["E1_PG_DSN"] = make_conninfo(original_dsn, connect_timeout=3,
            options=f"-c search_path={schema} -c statement_timeout=5000 -c lock_timeout=2000")
        spec = importlib.util.spec_from_file_location("e3_independent_e1_oracle", ROOT / "lab" / "e1_pg" / "oracle.py")
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)
        summary["schema"] = schema
        summary["postgresVersion"] = admin.execute("SELECT version()").fetchone()[0]
        summary["postgresSettings"] = {name: admin.execute(sql.SQL("SHOW {}").format(sql.Identifier(name))).fetchone()[0]
                                       for name in ("fsync", "synchronous_commit", "full_page_writes",
                                                    "default_transaction_isolation", "max_connections")}
        summary["oracleBefore"] = oracle.verify()
        if not all(summary["oracleBefore"].values()):
            raise RuntimeError("Initial independent oracle rejected the E1 fixture")
        services = Services(output, schema)
        for replica in range(2):
            services.start(replica)
        for replica in range(2):
            services.ready(replica)
        summary["initialPids"] = {str(key): child.pid for key, child in services.current.items()}
        elapsed = run_load(services, offers, config, profile)
        summary["survivingServiceAliveAfterLoad"] = services.current[1].poll() is None
        if not summary["survivingServiceAliveAfterLoad"]:
            raise RuntimeError("The non-targeted service exited during the experiment")
        services.close()
        # Stop all writers, then bound the wait for backend rollback/disconnection.
        deadline = time.monotonic() + 8
        while admin.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE application_name=%s", (schema,)).fetchone()[0]:
            if time.monotonic() >= deadline:
                raise TimeoutError("Database writers did not quiesce")
            time.sleep(0.1)
        with admin.transaction():
            admin.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            snapshot = {table: admin.execute(sql.SQL("SELECT * FROM {} ORDER BY 1,2").format(sql.Identifier(table))).fetchall()
                        for table in ("accounts", "operations", "postings", "outbox", "duty")}
        write_json(output / "ledger-snapshot.json", snapshot)
        summary["reconciliation"] = reconcile(offers, snapshot["operations"])
        summary["oracleAfter"] = oracle.verify()
        posting = admin.execute("SELECT op,account,delta FROM postings ORDER BY op,account LIMIT 1").fetchone()
        if not posting:
            raise RuntimeError("No posting available for independent oracle negative control")
        try:
            admin.execute("DELETE FROM postings WHERE op=%s AND account=%s", posting[:2])
            bad = oracle.verify()
        finally:
            admin.execute("INSERT INTO postings(op,account,delta) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING", posting)
        restored = oracle.verify()
        summary["negativeControl"] = {"detected": sorted(k for k, v in bad.items() if not v),
                                      "restoredOracle": restored}
        healthy = next((event["actualSeconds"] for event in services.events if event["action"] == "RECOVERY_HEALTHY"), None)
        summary["recovery"] = {"healthySeconds": healthy,
            "recoveredServiceAcknowledgedCommit": healthy is not None and any(
                record["replica"] == 0 and record["outcome"] == "ACK_COMMITTED"
                and record["dispatchSeconds"] >= healthy for record in offers)}
        nominal = len(profile["ratesPerSecond"]) * profile["phaseSeconds"]
        summary["measurement"] = {"offered": len(offers), "outcomes": dict(Counter(r["outcome"] for r in offers)),
            "nominalOfferWindowSeconds": nominal, "elapsedThroughResponsesSeconds": elapsed,
            "clientDrainSeconds": max(0, elapsed - nominal),
            "persistedCommitsPerNominalSecond": summary["reconciliation"]["persistedCommits"] / nominal,
            "acknowledgedOnlyP99FromScheduledMs": percentile([r["endToEndMs"] for r in offers if r["outcome"] == "ACK_COMMITTED"], .99),
            "latencyCaveat": "ACK-only percentile excludes failed, missed and ambiguous offers; consult every recorded outcome. Persisted commits have no independent commit timestamp."}
        summary["measurement"]["phases"] = []
        for phase, rate in enumerate(profile["ratesPerSecond"]):
            subset = [record for record in offers if record["phase"] == phase]
            summary["measurement"]["phases"].append({
                "phase": phase, "ratePerSecond": rate, "offered": len(subset),
                "outcomes": dict(Counter(record["outcome"] for record in subset)),
                "persistedCommits": sum(record["persistedStatus"] == "COMMITTED" for record in subset),
                "acknowledgedOnlyP99FromScheduledMs": percentile([
                    record["endToEndMs"] for record in subset if record["outcome"] == "ACK_COMMITTED"], .99)})
        healthy_checks = (summary["reconciliation"]["consistent"] and all(summary["oracleAfter"].values())
            and not bad["twoPostingsPerCommit"] and not bad["projectionAgrees"] and all(restored.values())
            and summary["recovery"]["recoveredServiceAcknowledgedCommit"]
            and not any(r["outcome"] == "MISSED_RUN_ABORTED" for r in offers))
        summary["status"] = "EXPLORATORY_COMPLETED" if healthy_checks else "EXPLORATORY_CHECK_FAILED"
    except Exception as exc:
        # Never persist connection strings or exception messages containing credentials.
        summary["errors"].append(type(exc).__name__)
        summary["status"] = "EXPLORATORY_ERROR"
    finally:
        os.environ["E1_PG_DSN"] = original_dsn
        if services:
            try:
                services.close()
            except Exception as exc:
                summary["errors"].append("processCleanup:" + type(exc).__name__)
            summary["processEvents"] = services.events
            summary["ownedProcessExitCodes"] = {str(p.pid): p.poll() for p in services.children}
        if admin:
            try:
                if created:
                    admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
                summary["schemaCleanup"] = True
            except Exception as exc:
                summary["schemaCleanup"] = False
                summary["errors"].append("schemaCleanup:" + type(exc).__name__)
            finally:
                admin.close()
        write_json(output / "offers.json", offers)
        summary["artifactSha256"] = {p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "summary.json"}
        write_json(output / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "output": str(output), "capacityAcceptance": False}))
    return 0 if summary["status"] == "EXPLORATORY_COMPLETED" and not summary["errors"] else 1


if __name__ == "__main__":
    def interrupted(signum, frame):
        raise RuntimeError("Interrupted experiment")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    raise SystemExit(main())
