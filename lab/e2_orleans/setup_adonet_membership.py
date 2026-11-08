#!/usr/bin/env python3
"""Install EXACT vendor PostgreSQL 10.4.0 Orleans ADO.NET clustering scripts.

Only in disposable container e2lab: verify upstream Git blob hashes before
executing and record immutable provenance. No self-invented membership SQL.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen

COMMIT = "d114d7522a53b8cce4c6b97d44293e5c7273d766"
SCRIPTS = [
    ("src/AdoNet/Shared/PostgreSQL-Main.sql",
     "e4f78c86342297b7c7ffeb271b7be066e08f3508"),
    ("src/AdoNet/Orleans.Clustering.AdoNet/PostgreSQL-Clustering.sql",
     "e90af40c886a47ea9ea4e84f640c48b572cee494"),
]
HERE = Path(__file__).resolve().parent
RESULT = HERE.parent / "results" / "e2"
RESULT.mkdir(parents=True, exist_ok=True)


def verified_target(engine, target):
    if engine not in ("podman", "docker"):
        raise ValueError("Membership installation requires Podman or Docker")
    if target == "e2f10-pg":
        if os.environ.get("E2_NETWORK_TEST") != "1":
            raise ValueError("E2-F10 requires explicit network-fixture opt-in")
        return target
    if target == "e2-postgres":
        return target
    if not re.fullmatch(r"book-lab-\d+-\d+", target):
        raise ValueError("Membership schema requires an allowlisted disposable container")
    inspection = json.loads(subprocess.check_output([engine, "inspect", target], timeout=15))
    if len(inspection) != 1:
        raise ValueError("Expected exactly one owned experiment container")
    container = inspection[0]
    if (container["Config"].get("Labels", {}).get("org.jmfloreszazo.experiment") != "e2-cluster"
            or "POSTGRES_DB=e2lab" not in container["Config"].get("Env", [])
            or not container["State"]["Running"]):
        raise ValueError("Container is not a running, labelled disposable e2-cluster database")
    bindings = container["NetworkSettings"]["Ports"].get("5432/tcp", [])
    if not bindings or any(binding["HostIp"] != "127.0.0.1" for binding in bindings):
        raise ValueError("Disposable database must publish PostgreSQL only on loopback")
    identifier = container["Id"]
    if not re.fullmatch(r"[0-9a-f]{64}", identifier):
        raise ValueError("Container inspection did not return a full immutable ID")
    return identifier


def main():
    assert os.environ.get("E1_PG_DSN"), "Disposable E1_PG_DSN is required"
    engine = os.environ.get("CONTAINER_ENGINE", "podman")
    target = verified_target(engine, os.environ.get("E2_POSTGRES_CONTAINER", "e2-postgres"))
    manifest = []
    for path, expected in SCRIPTS:
        url = "https://raw.githubusercontent.com/dotnet/orleans/" + COMMIT + "/" + path
        with urlopen(Request(url, headers={"User-Agent": "E2-Orleans-CI/1.0"}),
                     timeout=35) as response:
            data = response.read()
        git_sha = hashlib.sha1(
            ("blob " + str(len(data)) + "\0").encode() + data
        ).hexdigest()
        assert git_sha == expected, ("Official source changed", path, git_sha)
        result = subprocess.run(
            [engine, "exec", "-i", target,
             "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres",
             "-d", "e2lab", "-q"],
            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=50
        )
        assert result.returncode == 0, (
            "Failed to apply vendor SQL", path,
            result.stderr.decode("utf-8", errors="replace")[-2600:]
        )
        manifest.append({
            "path": path,
            "upstreamCommit": COMMIT,
            "expectedGitBlobSha": expected,
            "observedGitBlobSha": git_sha,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "database": "e2lab",
            "target": f"disposable {engine} PostgreSQL",
            "container": target,
        })

    import psycopg
    with psycopg.connect(os.environ["E1_PG_DSN"], autocommit=True) as db:
        database_version = db.execute("SHOW server_version").fetchone()[0]
        installed = db.execute(
            "SELECT QueryKey FROM OrleansQuery ORDER BY QueryKey"
        ).fetchall()
        version_table = db.execute(
            "SELECT COUNT(*) FROM OrleansMembershipVersionTable"
        ).fetchone()[0]
        membership_table = db.execute(
            "SELECT COUNT(*) FROM OrleansMembershipTable"
        ).fetchone()[0]
    assert len(installed) >= 5, (
        "Official membership queries were not installed", installed
    )
    assert version_table == 0 and membership_table == 0
    manifest_path = RESULT / "e2-adonet-official-scripts.json"
    manifest_path.write_text(json.dumps({
        "experiment": "E2-ADO-NET-PostgreSQL-Official-Membership-Schema",
        "schemaVersion": 1,
        "status": "INSTALLED_NOT_YET_RECOVERY_PROVEN",
        "orleansVersion": "10.4.0",
        "databaseVersion": database_version,
        "membershipQueryCount": len(installed),
        "scripts": manifest,
        "limit": "Schema installation does not prove healthy silos, failover or physical-node recovery."
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "INSTALLED",
        "membershipQueryCount": len(installed),
        "scripts": manifest
    }, indent=2))


if __name__ == "__main__":
    main()
