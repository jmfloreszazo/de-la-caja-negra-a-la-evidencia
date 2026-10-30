#!/usr/bin/env python3
"""Capture reproducibility metadata for the disposable E1 lab without secrets.

Run after the PostgreSQL, .NET/SQLite reference parity and independent-oracle
jobs, while the Podman image and PostgreSQL test container are still present.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sqlite3
import subprocess

import psycopg

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OUT = LAB / "results" / "e1"
OUT.mkdir(parents=True, exist_ok=True)


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def optional(*args):
    try:
        return run(*args)
    except subprocess.CalledProcessError:
        return None


def main():
    image_id_file = HERE / "image-id.txt"
    assert image_id_file.is_file(), "Podman image ID was not captured"
    image_id = image_id_file.read_text(encoding="utf-8").strip()
    assert image_id, "Empty image ID"
    image_details = run(
        "podman", "image", "inspect", "docker.io/library/postgres:16.13",
        "--format", "{{json .RepoDigests}}"
    )
    digests = json.loads(image_details)
    assert isinstance(digests, list) and any("@sha256:" in v for v in digests), (
        "Missing content-addressed image digest", digests
    )

    with psycopg.connect(os.environ["E1_PG_DSN"], autocommit=True) as db:
        server = db.execute("SHOW server_version").fetchone()[0]
    project = (HERE / "PgBank/PgBank.csproj").read_text(encoding="utf-8")
    pkg = re.search(r'PackageReference Include="Npgsql" Version="([^"]+)"', project)
    assert pkg, "Cannot determine candidate Npgsql package version"

    sqlite_db = OUT / "reference-parity.db"
    assert sqlite_db.is_file(), "Run test_reference_parity.py first"
    sqlite_native_version = run(
        "dotnet", str(LAB / "Bank/bin/Release/net10.0/Bank.dll"),
        "version", str(sqlite_db)
    )
    assert sqlite_native_version, "Missing native SQLite version"

    run_id = os.environ.get("GITHUB_RUN_ID")
    checkout_commit = run("git", "rev-parse", "HEAD")
    source_parent = optional("git", "rev-parse", "HEAD^2")
    source_head = source_parent or checkout_commit
    assert re.fullmatch(r"[0-9a-f]{40}", checkout_commit)
    assert re.fullmatch(r"[0-9a-f]{40}", source_head)

    manifest = {
        "schemaVersion": 1,
        "experiment": "E1b-runtime-provenance",
        "status": "PASS",
        "classification": "REPRODUCIBILITY_MANIFEST_NOT_PERFORMANCE_PROOF",
        "github": {
            "runId": int(run_id) if run_id else None,
            "checkoutCommit": checkout_commit,
            "sourceHead": source_head,
            "event": os.environ.get("GITHUB_EVENT_NAME")
        },
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "dotnetSdk": run("dotnet", "--version"),
            "podman": run("podman", "--version")
        },
        "database": {
            "postgres": server,
            "sqliteNativeDotnet": sqlite_native_version,
            "sqlitePython": sqlite3.sqlite_version,
            "psycopg": psycopg.__version__,
            "npgsqlPackage": pkg.group(1)
        },
        "container": {
            "imageReference": "docker.io/library/postgres:16.13",
            "imageId": image_id,
            "repoDigests": digests
        },
        "sourceSha256": {
            str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                HERE / "capture_runtime.py", HERE / "test_reference_parity.py",
                HERE / "test_oracle_vectors.py", HERE / "oracle.py",
                LAB / "Bank/Program.cs", HERE / "PgBank/Program.cs"
            ]
        },
        "limits": (
            "An observed, disposable GitHub-hosted Linux execution. Registry "
            "digest plus versions aid reproduction but do not validate other "
            "operating systems, complete workload parity or power-loss durability."
        )
    }
    (OUT / "runtime-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
