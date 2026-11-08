"""Exercise guest orchestration with fake cloud/process tools, never Azure."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


@unittest.skipUnless(sys.platform == "linux", "Guest shell tests require Linux or WSL")
class GuestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="book-azure-shell-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = os.environ | {
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "FIXTURE": str(self.root),
            "TRACE": str(self.root / "trace.txt"),
        }

    def executable(self, name, content):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + content, encoding="utf-8")
        path.chmod(0o700)

    def prepare_workload(self):
        (self.root / "lab").mkdir()
        self.executable("dotnet", r"""
echo "dotnet $*" >> "$TRACE"
if test "${1:-}" = build && test "${FAIL_BUILD:-}" = "${2:-}"; then
    echo 'fixture build failure' >&2; exit 23
fi
case "${2:-}" in
    version) echo "${SQL_VERSION:-16.0.fixture}"; exit "${FAIL_READY:-0}" ;;
    snapshot) echo '{"fixture":true}'; exit 0 ;;
esac
echo 'test SDK, not a real measurement'
""")
        self.executable("python3", r"""
echo "$*" >> "$TRACE"
if test "${1:-}" = --version; then echo 'fixture Python'; exit 0; fi
if test "${1:-}" = -c; then echo 'disposable-fixture-password'; exit 0; fi
if test "${1:-} ${2:-}" = '-m venv'; then
    mkdir -p "$3/bin"; cp "$0" "$3/bin/python"; exit 0
fi
if test "${FAIL_CASE:-}" = "${1:-}"; then exit 19; fi
if test "${1:-}" = lab/e2_orleans/test_e2.py; then
    test -n "${E2_PG_NPGSQL:-}"
    test "$E2_PG_NPGSQL" = "$E1_PG_NPGSQL"
    [[ "$E2_PG_NPGSQL" == *"Database=e2lab;"* ]]
fi
if test "${1:-}" = lab/e2_orleans/test_multiprocess.py; then
    echo "provider=${E2_CLUSTER_PROVIDER:?}" >> "$TRACE"
fi
if test "${1:-}" = lab/e2_orleans/test_inflight.py; then
    test "${E2_CLUSTER_PROVIDER:-}" = adonet
fi
if test "${1:-}" = lab/e2_orleans/setup_adonet_membership.py; then
    [[ "${E2_POSTGRES_CONTAINER:-}" == book-lab-* ]]
    test -n "${CONTAINER_ENGINE:-}"
fi
if [[ "${1:-}" == lab/e1_sqlserver/*.py ]]; then
    test "${E1_SQL_HOST:-}" = '127.0.0.1,55499'
    test -n "${E1_SQL_PASSWORD:-}"
fi
case "${1:-}" in
    -m|walkthrough.py|lab/e1_pg/*.py|lab/e1_sqlserver/*.py|lab/e2_orleans/*.py|lab/e3_capacity/test_e3.py|lab/durable_rpc/*.py|lab/transport/check_report.py) exit 0 ;;
    *) echo "Unexpected Python arguments: $*" >&2; exit 90 ;;
esac
""")
        self.executable("podman", r"""
echo "podman $*" >> "$TRACE"
case "$1" in
    version) echo 'fixture container runtime' ;;
    create) printf '%064d\n' 0 ;;
    start) exit "${FAIL_START:-0}" ;;
    run) echo 'fixture-container'; exit "${FAIL_START:-0}" ;;
    port) echo '127.0.0.1:55499' ;;
    image) echo 'fixture-image-id fixture-image-digest' ;;
    exec)
        if test "$2" = -e; then
            test "$3" = SQLCMDPASSWORD
            test -n "${SQLCMDPASSWORD:-}"
            echo 'fixture backup'
            exit "${FAIL_BACKUP:-0}"
        fi
        case "$3" in
            pg_isready) exit "${FAIL_PG_READY:-0}" ;;
            pg_dump) echo 'fixture persisted database'; exit "${FAIL_DUMP:-0}" ;;
            *) exit 91 ;;
        esac ;;
    logs) echo 'fixture database log'; exit "${FAIL_LOGS:-0}" ;;
    cp) echo 'fixture database backup' > "$3" ;;
    rm) test "$2" = -f; [[ "$3" == book-lab-* || "$3" =~ ^[0-9a-f]{64}$ ]]; exit "${FAIL_CLEANUP:-0}" ;;
    *) echo "Unexpected Podman arguments: $*" >&2; exit 92 ;;
esac
""")

    def run_workload(self, experiment):
        return subprocess.run(
            ["bash", str(HERE / "run-experiment.sh"), experiment, str(self.root / "run/evidence")],
            cwd=self.root, env=self.env, capture_output=True, text=True, timeout=20,
        )

    def test_all_supported_workloads_use_existing_entrypoints(self):
        self.prepare_workload()
        for experiment, entrypoint in (
            ("core", "walkthrough.py --auto --bank"),
            ("e1", "lab/e1_pg/test_multiprocess_parity.py"),
            ("e2", "lab/e2_orleans/test_e2.py"),
            ("e3", "lab/e3_capacity/test_e3.py --output lab/results/e3"),
            ("m2", "lab/durable_rpc/test_m2.py"),
        ):
            with self.subTest(experiment=experiment):
                result = self.run_workload(experiment)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(entrypoint, (self.root / "trace.txt").read_text())
        self.assertFalse((self.root / "run/evidence/venv").exists())
        self.assertTrue((self.root / "run/evidence/postgres.dump").is_file())

    def test_failed_oracle_stops_following_cases_and_retains_database(self):
        self.prepare_workload()
        self.env["FAIL_CASE"] = "lab/e1_pg/test_dotnet.py"
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 19, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertNotIn("lab/e1_pg/test_reference_parity.py", trace)
        self.assertIn("pg_dump", trace)
        self.assertIn("podman rm -f " + "0" * 64, trace)

    def test_m1_runs_both_profiles_without_starting_a_database(self):
        self.prepare_workload()
        result = self.run_workload("m1")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("benchmark 5088 2500 8", trace)
        self.assertIn("benchmark 5088 2500 32", trace)
        self.assertEqual(trace.count("lab/transport/check_report.py"), 2)
        self.assertNotIn("podman", trace)

    def test_postgres_failed_start_removes_owned_container_without_dump(self):
        self.prepare_workload()
        self.env["FAIL_START"] = "33"
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 33, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("podman rm -f " + "0" * 64, trace)
        self.assertNotIn("pg_dump", trace)
        self.assertNotIn("lab/e1_pg/test_e1.py", trace)
        completion = json.loads((self.root / "run/evidence/postgres-completion.json").read_text())
        self.assertIsNone(completion["dumpExitCode"])
        self.assertEqual(completion["workloadExitCode"], 33)

    def test_postgres_success_uses_owned_id_and_records_all_phases(self):
        self.prepare_workload()
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("-p 127.0.0.1::5432", trace)
        self.assertNotIn("disposable-fixture-password", trace)
        for operation in ("start", "port", "logs", "exec"):
            self.assertIn("podman " + operation + " " + "0" * 64, trace)
        completion = json.loads((self.root / "run/evidence/postgres-completion.json").read_text())
        self.assertTrue(all(value == 0 for value in completion.values()), completion)

    def test_postgres_readiness_failure_skips_dump_and_removes_container(self):
        self.prepare_workload()
        self.executable("sleep", "exit 0\n")
        self.env["FAIL_PG_READY"] = "27"
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PostgreSQL readiness timed out", result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertEqual(trace.count("pg_isready -t 2"), 60)
        self.assertNotIn("pg_dump", trace)
        self.assertNotIn("lab/e1_pg/test_e1.py", trace)
        self.assertIn("podman rm -f " + "0" * 64, trace)
        self.assertIn("pg_isready", trace)
        self.assertTrue((self.root / "run/evidence/postgres-readiness.log").exists())

    def test_postgres_dump_or_cleanup_failure_cannot_report_success(self):
        self.prepare_workload()
        for setting, field in (("FAIL_DUMP", "dumpExitCode"), ("FAIL_CLEANUP", "cleanupExitCode")):
            with self.subTest(setting=setting):
                self.env[setting] = "37"
                result = self.run_workload("e1")
                self.assertEqual(result.returncode, 37, result.stderr)
                self.env.pop(setting)
                completion = json.loads((self.root / "run/evidence/postgres-completion.json").read_text())
                self.assertEqual(completion["workloadExitCode"], 0)
                self.assertEqual(completion[field], 37)
                self.assertIn("podman rm -f " + "0" * 64, (self.root / "trace.txt").read_text())

    def test_postgres_collection_timeouts_still_attempt_cleanup(self):
        self.prepare_workload()
        self.executable("timeout", r"""
echo "timeout $*" >> "$TRACE"
if [[ "$*" == *" logs "* || "$*" == *" pg_dump "* ]]; then exit 124; fi
exec /usr/bin/timeout "$@"
""")
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 124, result.stderr)
        completion = json.loads((self.root / "run/evidence/postgres-completion.json").read_text())
        self.assertEqual(completion, {"workloadExitCode": 0, "logExitCode": 124,
                                     "dumpExitCode": 124, "cleanupExitCode": 0})
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("--kill-after=2s 10s", trace)
        self.assertIn("--kill-after=2s 30s", trace)
        self.assertIn("podman rm -f " + "0" * 64, trace)

    def test_postgres_log_failure_is_not_success(self):
        self.prepare_workload()
        self.env["FAIL_LOGS"] = "35"
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 35, result.stderr)
        self.assertIn("PostgreSQL log collection failed", result.stderr)

    def test_postgres_cleanup_preserves_workload_and_all_phase_exit_codes(self):
        self.prepare_workload()
        self.env.update(FAIL_CASE="lab/e1_pg/test_e1.py", FAIL_LOGS="35",
                        FAIL_DUMP="36", FAIL_CLEANUP="37")
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 19, result.stderr)
        completion = json.loads((self.root / "run/evidence/postgres-completion.json").read_text())
        self.assertEqual(completion, {"workloadExitCode": 19, "logExitCode": 35,
                                     "dumpExitCode": 36, "cleanupExitCode": 37})

    def test_m1_failed_oracle_stops_second_profile(self):
        self.prepare_workload()
        self.env["FAIL_CASE"] = "lab/transport/check_report.py"
        result = self.run_workload("m1")
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertNotIn("benchmark 5088 2500 32", (self.root / "trace.txt").read_text())

    def test_explicit_docker_engine_uses_the_same_workload(self):
        self.prepare_workload()
        (self.bin / "docker").symlink_to(self.bin / "podman")
        self.env["CONTAINER_ENGINE"] = "docker"
        result = self.run_workload("e2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "run/evidence/container-engine-version.txt").is_file())

    def test_unknown_engine_is_rejected_before_starting_a_database(self):
        self.prepare_workload()
        self.env["CONTAINER_ENGINE"] = "unexpected"
        result = self.run_workload("e1")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("Unsupported container engine", result.stderr)
        self.assertNotIn("podman run", (self.root / "trace.txt").read_text())

    def test_e2_builds_all_three_inputs_before_running_controls(self):
        self.prepare_workload()
        result = self.run_workload("e2")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("POSTGRES_DB=e2lab", trace)
        self.assertIn("pg_dump -U postgres -d e2lab", trace)
        for project in ("lab/Bank/Bank.csproj", "lab/e1_pg/PgBank/PgBank.csproj",
                        "lab/e2_orleans/OrleansLab/OrleansLab.csproj"):
            self.assertLess(trace.index(f"dotnet build {project}"),
                            trace.index("lab/e2_orleans/test_e2.py"))

    def test_e2_build_failure_stops_controls_and_retains_logs(self):
        self.prepare_workload()
        self.env["FAIL_BUILD"] = "lab/e2_orleans/OrleansLab/OrleansLab.csproj"
        result = self.run_workload("e2")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertNotIn("lab/e2_orleans/test_e2.py", (self.root / "trace.txt").read_text())
        self.assertIn("fixture build failure",
                      (self.root / "run/evidence/e2-build-orleans.log").read_text())
        self.assertTrue((self.root / "run/evidence/postgres.dump").is_file())

    def test_cluster_mode_runs_both_providers_before_inflight_controls(self):
        self.prepare_workload()
        result = self.run_workload("e2-cluster")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("org.jmfloreszazo.experiment=e2-cluster", trace)
        positions = [trace.index(item) for item in (
            "lab/e2_orleans/test_e2.py", "lab/e2_orleans/test_deadlock.py",
            "lab/e2_orleans/test_workloads.py", "lab/e2_orleans/test_process_crash.py",
            "provider=development", "lab/e2_orleans/setup_adonet_membership.py",
            "provider=adonet", "lab/e2_orleans/test_inflight.py",
        )]
        self.assertEqual(positions, sorted(positions))

    def test_failed_cluster_control_stops_following_stages(self):
        self.prepare_workload()
        self.env["FAIL_CASE"] = "lab/e2_orleans/test_deadlock.py"
        result = self.run_workload("e2-cluster")
        self.assertEqual(result.returncode, 19, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertNotIn("lab/e2_orleans/test_workloads.py", trace)
        self.assertNotIn("lab/e2_orleans/setup_adonet_membership.py", trace)
        self.assertIn("pg_dump -U postgres -d e2lab", trace)

    def test_sqlserver_requires_consent_before_any_tool_runs(self):
        self.prepare_workload()
        self.env.pop("ACCEPT_EULA", None)
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("explicit license acceptance", result.stderr)
        self.assertFalse((self.root / "trace.txt").exists())

    def test_sqlserver_rejects_untrusted_image_before_any_tool_runs(self):
        self.prepare_workload()
        self.env.update(ACCEPT_EULA="Y", SQLSERVER_IMAGE="untrusted.invalid/server:2022")
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 2)
        self.assertIn("official SQL Server 2022", result.stderr)
        self.assertFalse((self.root / "trace.txt").exists())

    def test_sqlserver_uses_loopback_credentials_and_captures_backup(self):
        self.prepare_workload()
        self.env["ACCEPT_EULA"] = "Y"
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("-p 127.0.0.1::1433", trace)
        self.assertIn("--memory=4g", trace)
        self.assertNotIn("disposable-fixture-password", trace)
        self.assertLess(trace.index("build lab/e1_sqlserver/SqlFixtures/SqlFixtures.csproj"),
                        trace.index("podman create"))
        self.assertLess(trace.index("test_e1c.py"), trace.index("test_worker_parity.py"))
        self.assertNotIn("-m pip", trace)
        self.assertTrue((self.root / "run/evidence/sqlserver.bak").is_file())
        self.assertTrue((self.root / "run/evidence/sqlserver-snapshot.json").is_file())
        completion = json.loads((self.root / "run/evidence/sqlserver-completion.json").read_text())
        self.assertTrue(all(value == 0 for value in completion.values()), completion)

    def test_sqlserver_failure_stops_matrix_and_preserves_backup(self):
        self.prepare_workload()
        self.env.update(ACCEPT_EULA="Y", FAIL_CASE="lab/e1_sqlserver/test_e1c.py")
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 19, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertNotIn("test_worker_parity.py", trace)
        self.assertIn("podman rm -f " + "0" * 64, trace)
        self.assertTrue((self.root / "run/evidence/sqlserver.bak").is_file())

    def test_sqlserver_failed_start_still_removes_owned_container(self):
        self.prepare_workload()
        self.env.update(ACCEPT_EULA="Y", FAIL_START="33")
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 33, result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertIn("podman rm -f " + "0" * 64, trace)
        self.assertNotIn("test_e1c.py", trace)
        completion = json.loads((self.root / "run/evidence/sqlserver-completion.json").read_text())
        for field in ("snapshotExitCode", "backupExitCode", "copyExitCode"):
            self.assertIsNone(completion[field], "A skipped operation must not look successful")

    def test_sqlserver_readiness_exhaustion_cleans_up_without_running_controls(self):
        self.prepare_workload()
        self.executable("sleep", "exit 0\n")
        self.env.update(ACCEPT_EULA="Y", FAIL_READY="27")
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("SQL Server readiness timed out", result.stderr)
        trace = (self.root / "trace.txt").read_text()
        self.assertEqual(trace.count("SqlBank.dll version"), 30)
        self.assertNotIn("test_e1c.py", trace)
        self.assertIn("podman rm -f " + "0" * 64, trace)
        self.assertFalse((self.root / "run/evidence/sqlserver.bak").exists())

    def test_sqlserver_backup_or_cleanup_failure_cannot_report_success(self):
        self.prepare_workload()
        self.env["ACCEPT_EULA"] = "Y"
        for setting in ("FAIL_BACKUP", "FAIL_CLEANUP"):
            with self.subTest(setting=setting):
                self.env[setting] = "37"
                result = self.run_workload("e1-sqlserver")
                self.assertEqual(result.returncode, 37, result.stderr)
                self.env.pop(setting)

    def test_sqlserver_rejects_wrong_server_major_version(self):
        self.prepare_workload()
        self.env.update(ACCEPT_EULA="Y", SQL_VERSION="17.0.fixture")
        result = self.run_workload("e1-sqlserver")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("major version 16", result.stderr)
        self.assertNotIn("test_e1c.py", (self.root / "trace.txt").read_text())

    def prepare_remote(self, *, bad_hash=False, workload_exit=0, sqlserver=False):
        state = self.root / "state"
        state.mkdir()
        for name in ("bootstrap-complete", "dotnet-info.txt", "packages.txt", "bootstrap.sha256"):
            (state / name).write_text("fixture\n")
        source = self.root / "input"
        (source / "lab").mkdir(parents=True)
        with tarfile.open(self.root / "source.tar", "w") as archive:
            archive.add(source / "lab", arcname="lab")
        digest = hashlib.sha256((self.root / "source.tar").read_bytes()).hexdigest()
        launcher = f"#!/bin/bash\nmkdir -p lab/results\nprintf 'raw fixture' > lab/results/result.txt\nexit {workload_exit}\n"
        if sqlserver:
            launcher = ("#!/bin/bash\nset -eu\n"
                        "test \"$ACCEPT_EULA\" = Y\n"
                        "test \"$SQLSERVER_IMAGE\" = mcr.microsoft.com/mssql/server:2022-latest\n"
                        "mkdir -p lab/results\nprintf 'raw fixture' > lab/results/result.txt\n")
        script = (HERE / "remote-run.sh").read_text()
        values = {
            "STORAGE": "fixtureaccount", "CLIENT_ID": "fixture-client", "RUN_ID": "fixture-run",
            "SOURCE_SHA256": "0" * 64 if bad_hash else digest, "COMMIT": "a" * 40,
            "SOURCE_DIRTY": "false",
            "EXPERIMENT": "e1-sqlserver" if sqlserver else "e1",
            "LAUNCHER": base64.b64encode(launcher.encode()).decode(),
            "PG_IMAGE": "docker.io/library/postgres:16.13",
            "SQL_IMAGE": "mcr.microsoft.com/mssql/server:2022-latest",
            "ACCEPT_SQL_EULA": "Y" if sqlserver else "N",
        }
        for key, value in values.items():
            script = script.replace(f"__{key}__", value)
        script = script.replace("/var/lib/azure-lab", str(state))
        script = script.replace("/var/lock/book-experiment.lock", str(self.root / "lock"))
        (self.root / "remote.sh").write_text(script)
        self.executable("cloud-init", "test \"$*\" = 'status --wait'\n")
        self.executable("curl", "echo '{\"fixture\":true}'\n")
        self.executable("az", r"""
echo "az $*" >> "$TRACE"
if test "$1" = login; then exit 0; fi
test "$1 $2" = 'storage blob'
operation=$3
shift 3
file=''
while test "$#" -gt 0; do
    if test "$1" = --file; then file=$2; shift 2; else shift; fi
done
case "$operation" in
    download) cp "$FIXTURE/source.tar" "$file" ;;
    upload)
        if test "${FAIL_UPLOAD:-}" = 1; then echo 'fixture upload failure' >&2; exit 17; fi
        cp "$file" "$FIXTURE/uploaded.tar.gz" ;;
    *) exit 93 ;;
esac
""")

    def run_remote(self):
        return subprocess.run(["bash", str(self.root / "remote.sh")], env=self.env,
                              capture_output=True, text=True, timeout=20)

    def completion(self):
        with tarfile.open(self.root / "uploaded.tar.gz") as archive:
            return json.load(archive.extractfile("./completion.json"))

    def test_success_uploads_raw_results_and_completion(self):
        self.prepare_remote()
        result = self.run_remote()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AZURE_LAB_EXIT=0", result.stdout)
        self.assertEqual(self.completion()["workloadExitCode"], 0)
        with tarfile.open(self.root / "uploaded.tar.gz") as archive:
            self.assertEqual(archive.extractfile("./results/result.txt").read(), b"raw fixture")

    def test_sqlserver_explicit_license_and_image_reach_guest_launcher(self):
        self.prepare_remote(sqlserver=True)
        result = self.run_remote()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.completion()["workloadExitCode"], 0)

    def test_workload_failure_is_uploaded_without_success_marker(self):
        self.prepare_remote(workload_exit=19)
        result = self.run_remote()
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertIn("AZURE_LAB_EXIT=19", result.stdout)
        self.assertEqual(self.completion()["workloadExitCode"], 19)

    def test_bad_source_hash_prevents_workload_execution(self):
        self.prepare_remote(bad_hash=True)
        result = self.run_remote()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(self.completion()["workloadExitCode"], 0)
        self.assertFalse((self.root / "state/runs/fixture-run/source/lab/results").exists())

    def test_failed_upload_is_not_reported_as_success(self):
        self.prepare_remote()
        self.env["FAIL_UPLOAD"] = "1"
        result = self.run_remote()
        self.assertEqual(result.returncode, 17)
        self.assertIn("AZURE_LAB_EXIT=17", result.stdout)
        self.assertFalse((self.root / "uploaded.tar.gz").exists())

    def test_failed_artifact_collection_is_not_reported_as_success(self):
        self.prepare_remote()
        (self.root / "state/packages.txt").unlink()
        result = self.run_remote()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.completion()["workloadExitCode"], 0)
        self.assertEqual(self.completion()["artifactPreparationExitCode"], 1)


if __name__ == "__main__":
    unittest.main()
