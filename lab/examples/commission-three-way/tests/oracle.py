#!/usr/bin/env python3
"""Independent, synthetic three-way oracle: approved baseline / COBOL / .NET 10.

The mutation flag deliberately changes the .NET midpoint rounding policy.
"""
import argparse
import csv
from decimal import Decimal
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COBOL = ROOT / 'build' / 'commission'
DOTNET = ROOT / 'dotnet' / 'bin' / 'Release' / 'net10.0' / 'Commission.dll'


def invoke(command: list[str], value: str) -> Decimal:
    proc = subprocess.run(command, input=value + '\n', text=True,
                          capture_output=True, check=True, timeout=15)
    return Decimal(proc.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mutant', action='store_true', help='Introduce ToEven rounding bug')
    args = parser.parse_args()
    if not COBOL.is_file() or not DOTNET.is_file():
        print('Missing compiled binaries: run bash run.sh first.', file=sys.stderr)
        return 3
    cases = list(csv.DictReader((ROOT / 'tests' / 'approved_baseline.csv').open()))
    errors = 0
    for case in cases:
        entry = f"{case['amount']},{case['rate']}"
        expected = Decimal(case['expected'])
        try:
            cobol = invoke([str(COBOL)], entry)
            modern = invoke(['dotnet', str(DOTNET)] + (['--mutant'] if args.mutant else []), entry)
        except (subprocess.CalledProcessError, ValueError, OSError) as exc:
            print(f"ERROR {case['case']}: {exc}")
            errors += 1
            continue
        ok = cobol == expected and modern == expected and cobol == modern
        print(f"{'PASS' if ok else 'FAIL'} {case['case']:<20} approved={expected:.2f} COBOL={cobol:.2f} .NET={modern:.2f}")
        errors += not ok
    print(f"ORACLE: {'FAIL' if errors else 'PASS'} ({len(cases) - errors}/{len(cases)} cases), mutant={args.mutant}")
    return 2 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
