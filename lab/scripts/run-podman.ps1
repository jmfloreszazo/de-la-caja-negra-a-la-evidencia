# Build and run the lab with Podman on Windows (Podman Desktop / podman machine).
#   pwsh scripts/run-podman.ps1           guided, with pauses
#   pwsh scripts/run-podman.ps1 -Auto     everything, no pauses, including the bank module
param([switch]$Auto, [string]$Image = "cobol-modernization-lab")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "Podman is not installed: https://podman.io/docs/installation"; exit 3
}
New-Item -ItemType Directory -Force -Path results | Out-Null
$results = (Resolve-Path results).Path
podman build -t $Image -f Containerfile .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($Auto) {
    podman run --rm --network=none -v "${results}:/work/results" $Image python3 walkthrough.py --auto --bank
} else {
    podman run --rm -it --network=none -v "${results}:/work/results" $Image
}
exit $LASTEXITCODE
