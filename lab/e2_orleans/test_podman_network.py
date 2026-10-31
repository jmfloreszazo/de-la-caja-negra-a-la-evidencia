#!/usr/bin/env python3
"""E2-F10-C01: independently network-namespaced Orleans silos in Podman.

Two Orleans 10.4.0 silos, one external client and PostgreSQL run in four
separate Podman network namespaces on ONE GitHub Linux host. This baseline
measures native routable bridge endpoints and ADO.NET SQL membership, not
a cross-machine failover, a partition or a production SLO.
"""
import hashlib
from datetime import datetime, timezone
import psycopg
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
APP_DIR = LAB / "results" / "e2f10" / "app"
OUT = LAB / "results" / "e2f10"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(LAB / "e1_pg"))
from ledger import connect, reset
from oracle import verify
from test_e2 import command, postgres_snapshot

NETWORK = "e2f10-net"
IMAGE = "mcr.microsoft.com/dotnet/aspnet:10.0"
POSTGRES = "docker.io/library/postgres:16.13"
NODES = {
    "e2f10-pg": "10.78.30.10",
    "e2f10-primary": "10.78.30.11",
    "e2f10-secondary": "10.78.30.12",
    "e2f10-client": "10.78.30.13",
}
CONN = ("Host=10.78.30.10;Port=5432;Database=e2lab;"
        "Username=postgres;Password=e2local;Pooling=true;Maximum Pool Size=32;"
        "GSS Encryption Mode=Disable")


def podman(*args, timeout=45, check=True, stdin=None):
    process = subprocess.run(
        ["podman", *map(str, args)], input=stdin,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
    )
    if check and process.returncode:
        raise RuntimeError(
            "podman " + " ".join(map(str, args[:6])) +
            " exited " + str(process.returncode) + ": " +
            "\\nSTDERR: " + process.stderr.decode(errors="replace")[-12000:] +
            "\\nSTDOUT: " + process.stdout.decode(errors="replace")[-2500:]
        )
    return process.stdout.decode(errors="replace").strip()


def env_args(silo_ip=None):
    variables = {
        "E2_CLUSTER_PROVIDER": "adonet", "E2_NETWORK_TEST": "1",
        "E2_CLUSTER_TEST": "1", "E2_PG_NPGSQL": CONN,
        "E2_MEMBERSHIP_NPGSQL": CONN
    }
    if silo_ip:
        variables["E2_ADVERTISED_IP"] = silo_ip
    result = []
    for key, val in variables.items():
        result.extend(["-e", key + "=" + val])
    return result


def start(name, *command, app=True, silo_ip=None):
    args = [
        "run", "-d", "--name", name, "--hostname", name,
        "--network", NETWORK + ":ip=" + NODES[name],
        "--security-opt", "no-new-privileges"
    ]
    if app:
        args += ["-v", str(APP_DIR.resolve()) + ":/app:ro"]
        args += ["-v", str(OUT.resolve()) + ":/fixtures:ro"]
        args += env_args(silo_ip)
    args += list(command)
    return podman(*args, timeout=90)


def wait_silo(name, role, seconds=85):
    marker = "E2_SILO_READY:" + role + ":"
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        logs = podman("logs", name, check=False)
        if marker in logs:
            return logs[-1400:]
        status = podman("inspect", "-f", "{{.State.Status}}", name)
        if status == "exited":
            raise AssertionError(name + " died during startup: " + logs[-3000:])
        time.sleep(0.35)
    raise TimeoutError("No Orleans silo ready: " + name + ": " + podman(
        "logs", name, check=False)[-2500:])


def client(mode, commands=None, timeout=65):
    assert mode in ("probe", "execute")
    args = ["exec", "e2f10-client", "dotnet",
            "/app/OrleansLab.dll", "cluster", "client", mode]
    path = None
    if mode == "execute":
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=OUT, prefix="f10-",
            suffix=".json", delete=False
        ) as stream:
            json.dump({"route": "orleans", "concurrent": False,
                       "commands": commands}, stream)
            path = Path(stream.name)
        args.append("/fixtures/" + path.name)
    try:
        try:
            return json.loads(podman(*args, timeout=timeout))
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            for node in ("e2f10-primary", "e2f10-secondary"):
                print("E2_F10_DIAGNOSTIC " + node + ": " +
                      podman("logs", node, check=False)[-9000:],
                      file=sys.stderr, flush=True)
            raise RuntimeError("E2-F10 external-client request failed") from error
    finally:
        if path:
            path.unlink(missing_ok=True)


def persisted_membership():
    with connect() as db:
        rows = db.execute(
            "SELECT DeploymentId,Address,Port,Status,ProxyPort "
            "FROM OrleansMembershipTable "
            "WHERE DeploymentId='e2-f10-podman-bridge' ORDER BY Port"
        ).fetchall()
        version = db.execute(
            "SELECT Version FROM OrleansMembershipVersionTable "
            "WHERE DeploymentId='e2-f10-podman-bridge'"
        ).fetchone()
    return {
        "rows": [list(row) for row in rows],
        "version": version[0] if version else None
    }


def business_counts():
    with connect() as db:
        return {
            "committedOperations": db.execute(
                "SELECT COUNT(*) FROM operations WHERE status='COMMITTED'"
            ).fetchone()[0],
            "postings": db.execute(
                "SELECT COUNT(*) FROM postings"
            ).fetchone()[0],
            "outboxEvents": db.execute(
                "SELECT COUNT(*) FROM outbox"
            ).fetchone()[0]
        }


def probe_hosts(secondary_alive, timeout=155):
    started = time.monotonic()
    previous = ""
    while time.monotonic() - started < timeout:
        try:
            report = client("probe", timeout=35)
            names = {
                int(k): str(value).split(":", 1)[0]
                for k, value in report["accountHostNodes"].items()
            }
            required = ({"e2f10-primary", "e2f10-secondary"}
                        if secondary_alive else {"e2f10-primary"})
            if set(names.values()) == required:
                return report, names
            previous = str(names)
        except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            previous = str(exc)[-350:]
        time.sleep(3)
    raise AssertionError("Grain placement not achieved: " + previous)


def namespace_id(container):
    return podman("exec", container, "readlink", "/proc/self/ns/net")


def wait_disposable_sql_ready(timeout=65):
    """Require two real host-side SQL sessions, not only pg_isready.

    This bounded preflight never retries a financial command. A transient
    PostgreSQL socket disconnect is a startup observation, NOT a passing
    database operation; persist each unsuccessful observation.
    """
    started = time.monotonic()
    attempts = []
    consecutive_sql_successes = 0
    while time.monotonic() - started < timeout:
        ready = podman(
            "exec", "e2f10-pg", "pg_isready",
            "-U", "postgres", "-d", "e2lab", check=False
        )
        observation = {
            "timestampUtc": datetime.now(timezone.utc).isoformat(),
            "pgIsReady": ready,
            "hostSql": "NOT_ATTEMPTED"
        }
        if "accepting connections" in ready:
            try:
                with connect() as db:
                    row = db.execute("SELECT 1, current_database()").fetchone()
                assert row == (1, "e2lab"), (
                    "Connected to unexpected disposable SQL database", row
                )
                consecutive_sql_successes += 1
                observation["hostSql"] = "SELECT_1_OK"
            except psycopg.OperationalError as exc:
                consecutive_sql_successes = 0
                observation["hostSql"] = "CONNECT_FAILED"
                observation["error"] = repr(exc)[-1200:]
        else:
            consecutive_sql_successes = 0
        attempts.append(observation)
        if consecutive_sql_successes >= 2:
            result = {
                "experiment": "E2-F10-C01-Disposable-PostgreSQL-Readiness",
                "status": "READY",
                "timestampUtc": datetime.now(timezone.utc).isoformat(),
                "requiredConsecutiveIndependentHostSqlSessions": 2,
                "observedAttempts": len(attempts),
                "elapsedSeconds": round(time.monotonic() - started, 3),
                "observations": attempts[-20:],
                "limits": (
                    "Preflight proves only disposable local SQL connectivity "
                    "at two sampled instants; not PostgreSQL high availability "
                    "or elimination of intermittent startup failure."
                )
            }
            (OUT / "e2-f10-c01-postgres-startup.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            return result
        time.sleep(0.5)
    raise AssertionError(
        "Disposable PostgreSQL did not demonstrate two consecutive "
        "independent host-side SELECT 1 sessions: " +
        json.dumps(attempts[-8:])
    )


def preserve_startup_failure(stage, error, containers):
    """Original failure evidence must survive the finally cleanup path."""
    record = {
        "experiment": "E2-F10-C01-Podman-Startup-Diagnostic",
        "status": "FAIL",
        "classification": "ORIGINAL_FAILED_RUN_NOT_ACCEPTED",
        "stage": stage,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "error": repr(error),
        "disposableSqlHostPort": "127.0.0.1:55435",
        "containers": {}
    }
    for name in containers:
        try:
            value = json.loads(podman("inspect", name))[0]
            record["containers"][name] = {
                "status": value["State"]["Status"],
                "exitCode": value["State"]["ExitCode"],
                "id": value["Id"],
                "networkAddresses": {
                    network: state["IPAddress"]
                    for network, state in
                    value["NetworkSettings"]["Networks"].items()
                },
                "logsTail": podman("logs", name, check=False)[-9000:]
            }
        except Exception as exc:
            record["containers"][name] = {"diagnosticError": repr(exc)}
    (OUT / "e2-f10-c01-failure-diagnostic.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1", (
        "Explicit E2_NETWORK_TEST=1 is required"
    )
    assert os.environ.get("E1_PG_DSN") and "55435" in os.environ["E1_PG_DSN"]
    assert (APP_DIR / "OrleansLab.dll").is_file()
    created = []
    network_created = False
    stage = "startup"
    try:
        podman("network", "create", "--subnet", "10.78.30.0/24", NETWORK)
        network_created = True
        start("e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
              "-e", "POSTGRES_DB=e2lab",
              "-p", "127.0.0.1:55435:5432",
              POSTGRES, app=False)
        created.append("e2f10-pg")
        stage = "disposable-sql-host-readiness"
        readiness_observation = wait_disposable_sql_ready()
        assert readiness_observation["status"] == "READY"
        stage = "disposable-sql-schema-reset"
        reset()
        stage = "adonet-membership-setup"
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as setup
        setup()
        initial = postgres_snapshot()

        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            start(name, "--entrypoint", "dotnet", IMAGE,
                  "/app/OrleansLab.dll", "cluster", "silo", role,
                  silo_ip=NODES[name])
            created.append(name)
            wait_silo(name, role)

        start("e2f10-client", "--entrypoint", "sleep", IMAGE, "600")
        created.append("e2f10-client")
        namespace_ids = {name: namespace_id(name) for name in created}
        assert len(set(namespace_ids.values())) == 4, (
            "Podman containers must use four DIFFERENT network namespaces",
            namespace_ids
        )
        inspections = {
            name: json.loads(podman("inspect", name))[0]
            for name in created
        }
        container_ips = {
            name: entry["NetworkSettings"]["Networks"][NETWORK]["IPAddress"]
            for name, entry in inspections.items()
        }
        assert container_ips == NODES, (container_ips, NODES)
        assert len({entry["Id"] for entry in inspections.values()}) == 4

        # Database and both gateways must be reachable from each separate
        # real namespace before performing a financial transaction.
        # This narrows failures from remote Npgsql exception serialization.
        preflight = {}
        for node in ("e2f10-primary", "e2f10-secondary", "e2f10-client"):
            probe = json.loads(podman(
                "exec", node, "dotnet", "/app/OrleansLab.dll",
                "cluster", "network-check", timeout=30
            ))
            assert probe["databaseHealthy"] is True, (node, probe)
            assert probe["primaryGatewayReachable"] is True, (node, probe)
            assert probe["secondaryGatewayReachable"] is True, (node, probe)
            preflight[node] = probe

        before_probe, node_hosts = probe_hosts(True)
        assert before_probe["clientNodeIdentity"].startswith("e2f10-client:")
        secondary_key = next(k for k, v in node_hosts.items()
                             if v == "e2f10-secondary")
        primary_key = next(k for k, v in node_hosts.items()
                           if v == "e2f10-primary")
        membership_before = persisted_membership()
        before_states = {int(row[2]): int(row[3])
                         for row in membership_before["rows"]}
        assert before_states == {11150: 3, 11151: 3}, membership_before
        assert {str(row[1]) for row in membership_before["rows"]} == {
            NODES["e2f10-primary"], NODES["e2f10-secondary"]
        }

        first = [
            command("e2-f10-before-secondary", secondary_key, primary_key, 10),
            command("e2-f10-before-primary", primary_key, secondary_key, 20)
        ]
        result = client("execute", first)
        assert [x["status"] for x in result["results"]] == [
            "COMMITTED", "COMMITTED"
        ], result
        assert [x["actualSiloNodeIdentity"].split(":")[0] for x in
                result["results"]] == ["e2f10-secondary", "e2f10-primary"]
        assert business_counts() == {
            "committedOperations": 2, "postings": 4, "outboxEvents": 2
        }
        assert all(verify().values())

        # Real container SIGKILL, not a simulated logical exception.
        podman("kill", "--signal", "SIGKILL", "e2f10-secondary")
        exit_code = int(podman(
            "inspect", "-f", "{{.State.ExitCode}}", "e2f10-secondary"
        ))
        assert exit_code == 137, ("Expected real SIGKILL exit 137", exit_code)
        survivor_probe, survivor_nodes = probe_hosts(False)
        assert survivor_nodes[secondary_key] == "e2f10-primary"
        membership_after = persisted_membership()
        after_states = {int(row[2]): int(row[3])
                        for row in membership_after["rows"]}
        assert after_states == {11150: 3, 11151: 6}, membership_after
        assert membership_after["version"] > membership_before["version"]

        replay = client("execute", [
            command("e2-f10-before-secondary", secondary_key, primary_key, 10),
            command("e2-f10-after-kill", secondary_key, primary_key, 5)
        ])
        assert [x["status"] for x in replay["results"]] == [
            "DUPLICATE_COMMITTED", "COMMITTED"
        ], replay
        assert all(x["actualSiloNodeIdentity"].startswith("e2f10-primary:")
                   for x in replay["results"])
        assert business_counts() == {
            "committedOperations": 3, "postings": 6, "outboxEvents": 3
        }
        oracle = verify()
        assert len(oracle) == 7 and all(oracle.values()), oracle
        after = postgres_snapshot()
        assert after != initial

        manifest = {
            "schemaVersion": 1,
            "experiment": "E2-F10-C01-Podman-Routable-Bridge-Network-Namespaces",
            "status": "PASS",
            "classification": "FOUR_INDEPENDENT_NETWORK_NAMESPACES_SINGLE_PHYSICAL_CI_HOST",
            "containerIds": {name: inspections[name]["Id"]
                             for name in created},
            "networkNamespaceIds": namespace_ids,
            "advertisedAndActualContainerIps": container_ips,
            "clientNodeIdentity": before_probe["clientNodeIdentity"],
            "accountInitialNodeNames": node_hosts,
            "sourceAccountPreviouslyOnSecondary": secondary_key,
            "sourceAccountOnPrimary": primary_key,
            "siloKill": {"container": "e2f10-secondary",
                         "signal": "SIGKILL", "actualExitCode": exit_code},
            "reactivatedOnPrimary": survivor_nodes[secondary_key]
                                     == "e2f10-primary",
            "membershipBefore": membership_before,
            "membershipAfter": membership_after,
            "idempotentReplay": replay["results"][0]["status"],
            "newTransaction": replay["results"][1]["status"],
            "businessEffects": business_counts(),
            "independentSqlOracle": oracle,
            "finalLedgerSha256": hashlib.sha256(
                json.dumps(after, separators=(",", ":"), ensure_ascii=True)
                .encode()).hexdigest(),
            "sourceSha256": {
                str(path.relative_to(LAB)): hashlib.sha256(
                    path.read_bytes()).hexdigest()
                for path in (
                    HERE / "test_podman_network.py",
                    HERE / "OrleansLab/ClusterModes.cs",
                    HERE / "OrleansLab/Contracts.cs",
                    HERE / "setup_adonet_membership.py",
                )
            },
            "limitations": (
                "All four independently network-namespaced Podman containers "
                "run on ONE physical Linux runner. One PostgreSQL container "
                "and one non-HA backing store. This is a healthy routable "
                "bridge setup and actual secondary container death AFTER "
                "client response, NOT an injected network partition, "
                "independent physical fault domains, database HA, an "
                "in-flight distributed COMMIT fault, sustained performance, "
                "or mainframe/MIPS equivalence."
            )
        }
        out = OUT / "e2-f10-podman-routable-bridge.json"
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "experiment": manifest["experiment"],
            "status": "PASS",
            "independentNamespaceCount": len(set(namespace_ids.values())),
            "actualSiloIps": container_ips,
            "membershipStatuses": after_states,
            "membershipVersionIncreased": True,
            "siloDeathExitCode": exit_code,
            "oracle": oracle,
            "limitations": manifest["limitations"],
        }, indent=2))
    except Exception as error:
        preserve_startup_failure(stage, error, created)
        raise
    finally:
        for name in reversed(created):
            podman("rm", "-f", name, check=False, timeout=50)
        if network_created:
            podman("network", "rm", NETWORK, check=False, timeout=50)


if __name__ == "__main__":
    main()
