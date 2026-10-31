"""Run the .NET 10 functional prototype, then inspect it with an independent Python oracle."""
import json
import subprocess
import sys
from pathlib import Path

from contract_oracle import OracleFailure, load_contract, verify

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "contracts" / "cap007_cap005_synthetic.json"

def main() -> int:
    command = ["dotnet", "run", "--no-restore", "--project",
               str(HERE / "Greenfield.csproj"), "--", str(CONTRACT)]
    execution = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    if execution.returncode:
        print(execution.stdout, file=sys.stderr)
        print(execution.stderr, file=sys.stderr)
        return 2
    try:
        candidate = json.loads(execution.stdout)
        verify(load_contract(CONTRACT), candidate)
    except (json.JSONDecodeError, OracleFailure, KeyError, ValueError) as exc:
        print("GREENFIELD CONTRACT: REJECT", str(exc), file=sys.stderr)
        return 1
    print("GREENFIELD CONTRACT: PASS (synthetic, sequential, in-memory only)")
    print(f"Applied operations: {candidate['version']}; signed postings: {len(candidate['postings'])}; projection version: {candidate['projectionVersion']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
