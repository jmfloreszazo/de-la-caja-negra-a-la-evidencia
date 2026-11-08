#!/usr/bin/env bash
set -euo pipefail
evidence=${1:?Specify evidence directory}
: "${E4_ATTEMPT_DIRECTORY:?Specify recorded model attempt}"
: "${E4_LEGACY_RESULTS:?Specify verified legacy results}"
: "${SOURCE_HEAD_SHA:?Verified source commit required}"
: "${SOURCE_ARCHIVE_SHA256:?Verified source digest required}"
: "${SOURCE_WORKTREE_DIRTY:?Verified dirty state required}"
test "$(id -u)" -eq 0
user=laboperator
uid=$(id -u "$user")
gid=$(id -g "$user")
home=$(getent passwd "$user" | cut -d: -f6)
test "$uid" -ne 0
test "$(stat -fc %T /sys/fs/cgroup)" = cgroup2fs
grep "^$user:" /etc/subuid > "$evidence/e4-subuid.txt"
grep "^$user:" /etc/subgid > "$evidence/e4-subgid.txt"
command -v newuidmap
command -v newgidmap
loginctl enable-linger "$user"
systemctl start "user@$uid.service"
test -S "/run/user/$uid/bus"
root=$(mktemp -d /var/tmp/book-e4-replay-XXXXXXXX)
finish_e4() {
    rc=$?
    trap - EXIT
    set +e
    if test -d "$root/source/lab/results"; then
        cp -a "$root/source/lab/results" "$evidence/e4-results"
        copy_rc=$?
        if test "$copy_rc" -ne 0; then
            echo "E4 result collection failed; original evidence retained at $root." >&2
            if test "$rc" -eq 0; then rc=$copy_rc; fi
            exit "$rc"
        fi
    fi
    rm -rf -- "$root"
    cleanup_rc=$?
    if test "$rc" -eq 0 && test "$cleanup_rc" -ne 0; then rc=$cleanup_rc; fi
    exit "$rc"
}
trap finish_e4 EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
mkdir -p "$root/source/lab" "$root/source/lab/results/inputs/attempt" "$root/source/lab/results/inputs/legacy"
for folder in e4_agents Candidate Gate contracts legacy; do cp -a "lab/$folder" "$root/source/lab/"; done
cp "$E4_ATTEMPT_DIRECTORY"/{candidate,request,response}.json "$root/source/lab/results/inputs/attempt/"
cp "$E4_LEGACY_RESULTS"/{summary,none-observations}.json "$root/source/lab/results/inputs/legacy/"
chmod -R a+rX "$root"
chown -R "$uid:$gid" "$root/source/lab/results"
labrun() {
    runuser -u "$user" -- env -i HOME="$home" USER="$user" LOGNAME="$user" \
        PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 \
        XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" \
        SOURCE_HEAD_SHA="$SOURCE_HEAD_SHA" SOURCE_ARCHIVE_SHA256="$SOURCE_ARCHIVE_SHA256" \
        SOURCE_WORKTREE_DIRTY="$SOURCE_WORKTREE_DIRTY" \
        systemd-run --user --scope --quiet -- "$@"
}
image=mcr.microsoft.com/dotnet/sdk@sha256:c7445f141c04f1a6b454181bd098dcfa606c61ba0bd213d0a702489e5bd4cd71
cd "$root/source"
labrun podman info --format json > "$evidence/e4-podman-info.json"
if ! labrun podman image inspect "$image" > "$evidence/e4-image.json" 2> "$evidence/e4-image-check.log"; then
    labrun podman pull "$image" > "$evidence/e4-image-pull.log" 2>&1
fi
cd "$root/source"
labrun python3 lab/e4_agents/qualify.py --engine podman \
    --legacy-results "$root/source/lab/results/inputs/legacy" \
    --output "$root/source/lab/results/qualification"
labrun python3 lab/e4_agents/live.py evaluate --engine podman \
    --attempt "$root/source/lab/results/inputs/attempt" \
    --legacy-results "$root/source/lab/results/inputs/legacy" \
    --output "$root/source/lab/results/evaluation"
