#!/usr/bin/env bash
# Build and run the lab with Podman (Linux, macOS with podman machine, or WSL).
#   bash scripts/run-podman.sh            guided, with pauses
#   bash scripts/run-podman.sh --auto     everything, no pauses, including the bank module
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE="${IMAGE:-cobol-modernization-lab}"
command -v podman >/dev/null || { echo "Podman is not installed: https://podman.io/docs/installation" >&2; exit 3; }
mkdir -p results
podman build -t "$IMAGE" -f Containerfile .
# :Z relabels the volume for SELinux hosts (Fedora/RHEL); it is harmless elsewhere.
if [ "${1:-}" = "--auto" ]; then
  podman run --rm --network=none -v "$PWD/results:/work/results:Z" "$IMAGE" \
    python3 walkthrough.py --auto --bank
else
  podman run --rm -it --network=none -v "$PWD/results:/work/results:Z" "$IMAGE"
fi
echo "Results written to $PWD/results"
