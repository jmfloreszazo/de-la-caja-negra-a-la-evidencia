#!/usr/bin/env bash
set -euo pipefail
umask 077
exec 9>/var/lock/book-experiment.lock
flock -n 9 || { echo 'Another experiment owns this runner.' >&2; exit 1; }
cloud-init status --wait
test -f /var/lib/azure-lab/bootstrap-complete
run='/var/lib/azure-lab/runs/__RUN_ID__'
test ! -e "$run"
mkdir -p "$run/evidence" "$run/source"
az login --identity --client-id '__CLIENT_ID__' --allow-no-subscriptions --output none

finish() {
    rc=$?
    trap - EXIT
    set +e
    workload_rc=$rc
    artifact_rc=0
    cp /var/lib/azure-lab/{dotnet-info.txt,packages.txt,bootstrap.sha256} "$run/evidence/" || artifact_rc=1
    if test -f "$run/launcher.sh"; then cp "$run/launcher.sh" "$run/evidence/" || artifact_rc=1; fi
    if test -d "$run/source/lab/results"; then
        cp -a "$run/source/lab/results" "$run/evidence/results" || artifact_rc=1
    fi
    printf '{"workloadExitCode":%s,"artifactPreparationExitCode":%s,"sourceCommit":"__COMMIT__","sourceSha256":"__SOURCE_SHA256__","worktreeDirty":__SOURCE_DIRTY__,"classification":"Azure-hosted single-VM synthetic smoke; not E3"}\n' "$workload_rc" "$artifact_rc" > "$run/evidence/completion.json"
    if test "$artifact_rc" -ne 0; then echo 'Evidence collection failed.' >&2; rc=$artifact_rc; fi
    tar -czf "$run/evidence.tar.gz" -C "$run/evidence" .
    archive_rc=$?
    if test "$archive_rc" -ne 0; then rc=$archive_rc; fi
    if test "$archive_rc" -eq 0; then
        az storage blob upload --auth-mode login --account-name '__STORAGE__' \
          --container-name evidence --name '__RUN_ID__/evidence.tar.gz' \
          --file "$run/evidence.tar.gz" --overwrite false --output none
        upload_rc=$?
        if test "$upload_rc" -ne 0; then rc=$upload_rc; fi
    fi
    printf '\nAZURE_LAB_EXIT=%s\n' "$rc"
    exit "$rc"
}
trap finish EXIT
az storage blob download --auth-mode login --account-name '__STORAGE__' \
  --container-name source --name '__RUN_ID__/source.tar' --file "$run/source.tar" --output none
echo '__SOURCE_SHA256__  '"$run/source.tar" | sha256sum --check
tar -xf "$run/source.tar" -C "$run/source"
if test '__EXPERIMENT__' = e4-replay; then
    az storage blob download --auth-mode login --account-name '__STORAGE__' \
      --container-name source --name '__RUN_ID__/e4-inputs.tar' --file "$run/e4-inputs.tar" --output none
    echo '__E4_INPUT_SHA256__  '"$run/e4-inputs.tar" | sha256sum --check
    python3 "$run/source/scripts/azure/e4-inputs.py" unpack --archive "$run/e4-inputs.tar" \
      --output "$run/source/lab/results/e4-inputs"
    export E4_ATTEMPT_DIRECTORY="$run/source/lab/results/e4-inputs/attempt"
    export E4_LEGACY_RESULTS="$run/source/lab/results/e4-inputs/legacy"
fi
printf '%s' '__LAUNCHER__' | base64 --decode > "$run/launcher.sh"
curl --fail --silent --show-error --noproxy '*' -H Metadata:true \
  'http://169.254.169.254/metadata/instance?api-version=2021-02-01' > "$run/evidence/azure-instance.json"
export PG_IMAGE='__PG_IMAGE__'
export SOURCE_HEAD_SHA='__COMMIT__' SOURCE_ARCHIVE_SHA256='__SOURCE_SHA256__' SOURCE_WORKTREE_DIRTY='__SOURCE_DIRTY__'
export EXPERIMENT_HOST=AZURE_VM
if test '__EXPERIMENT__' = e1-sqlserver; then
    export SQLSERVER_IMAGE='__SQL_IMAGE__' ACCEPT_EULA='__ACCEPT_SQL_EULA__'
fi
cd "$run/source"
timeout --signal=TERM --kill-after=60s 60m bash "$run/launcher.sh" '__EXPERIMENT__' "$run/evidence" > "$run/evidence/execution.log" 2>&1
