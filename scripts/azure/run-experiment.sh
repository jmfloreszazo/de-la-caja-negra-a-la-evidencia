#!/usr/bin/env bash
set -euo pipefail
experiment=${1:?Specify core, e1, e1-sqlserver, e2, e2-cluster, e3, e4-replay, m1 or m2}
evidence=${2:?Specify an evidence directory}
case "$experiment" in core|e1|e1-sqlserver|e2|e2-cluster|e3|e4-replay|m1|m2) ;; *) echo "Unsupported experiment: $experiment" >&2; exit 2 ;; esac
if test "$experiment" = e1-sqlserver; then
    if test "${ACCEPT_EULA:-}" != Y; then
        echo 'SQL Server Developer requires explicit license acceptance: ACCEPT_EULA=Y. No database was started.' >&2
        exit 2
    fi
    sql_image=${SQLSERVER_IMAGE:-mcr.microsoft.com/mssql/server:2022-latest}
    if ! [[ "$sql_image" =~ ^mcr\.microsoft\.com/mssql/server(:2022[A-Za-z0-9_.-]*|@sha256:[a-f0-9]{64})$ ]]; then
        echo 'Use an explicit official SQL Server 2022 tag or digest.' >&2
        exit 2
    fi
fi
test -d lab
mkdir -p "$evidence"
evidence=$(realpath "$evidence")
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
dotnet --info > "$evidence/dotnet-info.txt"
python3 --version > "$evidence/python-version.txt"
uname -a > "$evidence/kernel.txt"
date -u +%FT%TZ > "$evidence/started-utc.txt"
if test "$experiment" = core; then
    (cd lab && python3 walkthrough.py --auto --bank)
    exit 0
fi
if test "$experiment" = e4-replay; then
    bash scripts/azure/run-e4-replay.sh "$evidence"
    exit 0
fi
if test "$experiment" = m1; then
    dotnet build lab/transport/TransportLab/TransportLab.csproj -c Release -m:1 --disable-build-servers \
        > "$evidence/build-TransportLab.log" 2>&1
    mkdir -p lab/results/transport
    for concurrency in 8 32; do
        report="lab/results/transport/report-c$concurrency.json"
        dotnet lab/transport/TransportLab/bin/Release/net10.0/TransportLab.dll \
            benchmark 5088 2500 "$concurrency" "$report"
        python3 lab/transport/check_report.py "$report"
    done
    exit 0
fi
engine=${CONTAINER_ENGINE:-podman}
case "$engine" in podman|docker) ;; *) echo "Unsupported container engine: $engine" >&2; exit 2 ;; esac
"$engine" version > "$evidence/container-engine-version.txt"

if test "$experiment" = e1-sqlserver; then
    for project in Bank/Bank e1_sqlserver/SqlBank/SqlBank e1_sqlserver/SqlOracle/SqlOracle e1_sqlserver/SqlFixtures/SqlFixtures; do
        dotnet build "lab/$project.csproj" -c Release -m:1 --disable-build-servers \
            > "$evidence/build-${project##*/}.log" 2>&1
    done
    export MSSQL_SA_PASSWORD
    MSSQL_SA_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24) + "aZ9!")')"
    export E1_SQL_PASSWORD="$MSSQL_SA_PASSWORD" SQLCMDPASSWORD="$MSSQL_SA_PASSWORD"
    sql_bank=lab/e1_sqlserver/SqlBank/bin/Release/net10.0/SqlBank.dll
    container="book-lab-$(date -u +%s)-$$"
    "$engine" create --name "$container" --memory=4g \
        --label org.jmfloreszazo.experiment=e1-sqlserver \
        -e ACCEPT_EULA=Y -e MSSQL_PID=Developer -e MSSQL_SA_PASSWORD \
        -p 127.0.0.1::1433 "$sql_image" > "$evidence/container-id.txt"
    identifier=$(cat "$evidence/container-id.txt")
    if ! [[ "$identifier" =~ ^[0-9a-f]{64}$ ]]; then
        echo 'Engine did not return a full owned SQL Server container ID.' >&2
        exit 1
    fi
    ready=false
    cleanup_sqlserver() {
        rc=$?
        trap - EXIT
        set +e
        "$engine" logs "$identifier" > "$evidence/sqlserver.log" 2>&1
        log_rc=$?
        snapshot_rc=null
        backup_rc=null
        copy_rc=null
        if test "$ready" = true; then
            dotnet "$sql_bank" snapshot > "$evidence/sqlserver-snapshot.json" 2> "$evidence/snapshot-errors.log"
            snapshot_rc=$?
            "$engine" exec -e SQLCMDPASSWORD "$identifier" sh -c '
                tool=/opt/mssql-tools18/bin/sqlcmd
                if test ! -x "$tool"; then tool=/opt/mssql-tools/bin/sqlcmd; fi
                "$tool" -S localhost -U sa -C -b -Q "BACKUP DATABASE [E1SqlLab] TO DISK = N'\''/var/opt/mssql/e1sql.bak'\'' WITH COPY_ONLY, INIT, CHECKSUM"
            ' > "$evidence/backup.log" 2>&1
            backup_rc=$?
            if test "$backup_rc" -eq 0; then
                "$engine" cp "$identifier:/var/opt/mssql/e1sql.bak" "$evidence/sqlserver.bak" \
                    > "$evidence/backup-copy.log" 2>&1
                copy_rc=$?
            fi
        fi
        "$engine" rm -f "$identifier" > "$evidence/container-cleanup.log" 2>&1
        cleanup_rc=$?
        printf '{"workloadExitCode":%s,"logExitCode":%s,"snapshotExitCode":%s,"backupExitCode":%s,"copyExitCode":%s,"cleanupExitCode":%s}\n' \
            "$rc" "$log_rc" "$snapshot_rc" "$backup_rc" "$copy_rc" "$cleanup_rc" > "$evidence/sqlserver-completion.json"
        for status in "$log_rc" "$snapshot_rc" "$backup_rc" "$copy_rc" "$cleanup_rc"; do
            if test "$status" != null && test "$rc" -eq 0 && test "$status" -ne 0; then rc=$status; fi
        done
        exit "$rc"
    }
    trap cleanup_sqlserver EXIT
    trap 'exit 143' TERM
    trap 'exit 130' INT
    "$engine" start "$identifier" > "$evidence/container-start.log"
    "$engine" image inspect "$sql_image" --format '{{.Id}} {{json .RepoDigests}}' > "$evidence/sqlserver-image.txt"
    port=$("$engine" port "$identifier" 1433/tcp | awk -F: '{print $NF}')
    export E1_SQL_HOST="127.0.0.1,$port"
    for attempt in $(seq 1 30); do
        if timeout --signal=TERM --kill-after=2s 5s dotnet "$sql_bank" version \
                > "$evidence/sqlserver-version.txt" 2>> "$evidence/readiness-errors.log"; then
            ready=true
            break
        fi
        sleep 2
    done
    if test "$ready" != true; then echo 'SQL Server readiness timed out.' >&2; exit 1; fi
    if ! grep -Eq '^16[.]' "$evidence/sqlserver-version.txt"; then
        echo 'The experiment requires SQL Server 2022 (major version 16).' >&2
        exit 1
    fi
    python3 lab/e1_sqlserver/test_e1c.py
    python3 lab/e1_sqlserver/test_worker_parity.py
    exit 0
fi

venv="$(dirname "$evidence")/venv"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install -r lab/e1_pg/requirements.txt
python="$venv/bin/python"
password=$("$python" -c 'import secrets; print(secrets.token_hex(24))')
export POSTGRES_PASSWORD="$password"
container="book-lab-$(date -u +%s)-$$"
image=${PG_IMAGE:-docker.io/library/postgres:16.13}
database=experiment
case "$experiment" in e2|e2-cluster) database=e2lab ;; esac
ready=false
cleanup() {
    rc=$?
    trap - EXIT
    set +e
    workload_rc=$rc
    # Keep bounded collection within the remote supervisor's 60-second TERM grace.
    timeout --signal=TERM --kill-after=2s 10s "$engine" logs "$identifier" > "$evidence/postgres.log" 2>&1
    log_rc=$?
    dump_rc=null
    if test "$ready" = true; then
        timeout --signal=TERM --kill-after=2s 30s "$engine" exec "$identifier" \
            pg_dump -U postgres -d "$database" -Fc \
            > "$evidence/postgres.dump" 2> "$evidence/postgres-dump-errors.log"
        dump_rc=$?
    fi
    timeout --signal=TERM --kill-after=2s 10s "$engine" rm -f "$identifier" > "$evidence/container-cleanup.log" 2>&1
    cleanup_rc=$?
    printf '{"workloadExitCode":%s,"logExitCode":%s,"dumpExitCode":%s,"cleanupExitCode":%s}\n' \
        "$workload_rc" "$log_rc" "$dump_rc" "$cleanup_rc" > "$evidence/postgres-completion.json"
    if test "$log_rc" -ne 0; then echo "PostgreSQL log collection failed (exit $log_rc)." >&2; fi
    if test "$dump_rc" != null && test "$dump_rc" -ne 0; then echo "PostgreSQL dump failed (exit $dump_rc); retained dump may be partial." >&2; fi
    if test "$cleanup_rc" -ne 0; then echo "PostgreSQL container cleanup failed (exit $cleanup_rc); inspect owned container $identifier." >&2; fi
    for status in "$log_rc" "$dump_rc" "$cleanup_rc"; do
        if test "$status" != null && test "$rc" -eq 0 && test "$status" -ne 0; then rc=$status; fi
    done
    exit "$rc"
}
"$engine" create --name "$container" -e POSTGRES_PASSWORD -e POSTGRES_DB="$database" \
  --label "org.jmfloreszazo.experiment=$experiment" \
  -p 127.0.0.1::5432 "$image" > "$evidence/container-id.txt"
identifier=$(cat "$evidence/container-id.txt")
if ! [[ "$identifier" =~ ^[0-9a-f]{64}$ ]]; then
    echo 'Engine did not return a full owned PostgreSQL container ID; inspect the retained creation response.' >&2
    exit 1
fi
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
timeout --signal=TERM --kill-after=2s 60s "$engine" start "$identifier" > "$evidence/container-start.log" 2>&1
"$engine" image inspect "$image" --format '{{.Id}} {{json .RepoDigests}}' > "$evidence/postgres-image.txt"
port=$("$engine" port "$identifier" 5432/tcp | awk -F: '{print $NF}')
for attempt in $(seq 1 60); do
    if timeout --signal=TERM --kill-after=2s 5s "$engine" exec "$identifier" \
            pg_isready -t 2 -U postgres -d "$database" >> "$evidence/postgres-readiness.log" 2>&1; then
        ready=true
        break
    fi
    sleep 2
done
if test "$ready" != true; then echo 'PostgreSQL readiness timed out.' >&2; exit 1; fi
export E1_PG_DSN="host=127.0.0.1 port=$port dbname=$database user=postgres password=$password"
export E1_PG_NPGSQL="Host=127.0.0.1;Port=$port;Database=$database;Username=postgres;Password=$password;Pooling=true;Maximum Pool Size=32"
case "$experiment" in
    e1)
        "$python" lab/e1_pg/test_e1.py
        "$python" lab/e1_pg/test_dotnet.py
        "$python" lab/e1_pg/test_reference_parity.py
        "$python" lab/e1_pg/test_oracle_vectors.py
        "$python" lab/e1_pg/test_multiprocess_parity.py
        ;;
    e2|e2-cluster)
        export E2_PG_NPGSQL="$E1_PG_NPGSQL"
        dotnet build lab/Bank/Bank.csproj -c Release -m:1 --disable-build-servers > "$evidence/e2-build-bank.log" 2>&1
        dotnet build lab/e1_pg/PgBank/PgBank.csproj -c Release -m:1 --disable-build-servers > "$evidence/e2-build-postgres.log" 2>&1
        dotnet build lab/e2_orleans/OrleansLab/OrleansLab.csproj -c Release -m:1 --disable-build-servers > "$evidence/e2-build-orleans.log" 2>&1
        "$python" lab/e2_orleans/test_e2.py
        if test "$experiment" = e2-cluster; then
            "$python" lab/e2_orleans/test_deadlock.py
            "$python" lab/e2_orleans/test_workloads.py
            "$python" lab/e2_orleans/test_process_crash.py
            E2_CLUSTER_PROVIDER=development "$python" lab/e2_orleans/test_multiprocess.py
            CONTAINER_ENGINE="$engine" E2_POSTGRES_CONTAINER="$container" \
                "$python" lab/e2_orleans/setup_adonet_membership.py
            E2_CLUSTER_PROVIDER=adonet "$python" lab/e2_orleans/test_multiprocess.py
            E2_CLUSTER_PROVIDER=adonet "$python" lab/e2_orleans/test_inflight.py
        fi
        ;;
    e3) E3_DISPOSABLE_FIXTURE=YES "$python" lab/e3_capacity/test_e3.py --output lab/results/e3 ;;
    m2) "$python" lab/durable_rpc/test_m2.py ;;
esac
"$python" -m pip freeze > "$evidence/python-packages.txt"
