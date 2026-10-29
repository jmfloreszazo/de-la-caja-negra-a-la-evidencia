#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v cobc >/dev/null || { echo 'Install GnuCOBOL (cobc) first' >&2; exit 3; }
command -v dotnet >/dev/null || { echo 'Install .NET 10 SDK first' >&2; exit 3; }
command -v python3 >/dev/null || { echo 'Install Python 3 first' >&2; exit 3; }
mkdir -p build
cobc -x -free -o build/commission cobol/commission.cbl
dotnet build dotnet/Commission.csproj --configuration Release --nologo
python3 tests/oracle.py
printf '\nConcurrent withdrawal teaching example:\n'
dotnet dotnet/bin/Release/net10.0/Commission.dll --race
printf '\nMutation control (expected oracle exit code 2):\n'
set +e
python3 tests/oracle.py --mutant
status=$?
set -e
if [ "$status" -ne 2 ]; then
  echo "Unexpected mutant outcome: $status (expected 2)" >&2
  exit 4
fi
echo 'The mutant was correctly rejected.'
