# Warm-up · three-way commission oracle

The first, smallest lab of the book. It computes a commission with an implied decimal point and checks it three ways:

1. approved baseline vs COBOL;
2. approved baseline vs .NET 10;
3. COBOL vs .NET 10.

Comparing only (3) would let both programs agree on the same mistake. The approved CSV is a separate test authority.

```bash
bash run.sh
```

The script compiles `cobol/commission.cbl`, builds `dotnet/`, runs `tests/oracle.py`, prints the in-process race example and then runs the rounding mutant, which **must** fail with exit code 2.

## The race example

```bash
dotnet dotnet/bin/Release/net10.0/Commission.dll --race
```

Two withdrawals of 600 start from a balance of 1,000. The naive version reads the same snapshot and approves both. `SemaphoreSlim` fixes it **inside one process only**. A service with several instances needs a database transaction or an equivalent, rigorously evaluated protocol: see the bank module in the main lab. Do not copy the in-memory model into a banking system.

## Status

Not part of the reference run of 29 October 2026. Windows users: run it in WSL or inside the Podman container (`podman run --rm cobol-modernization-lab bash examples/commission-three-way/run.sh`).

| Case | Amount | Rate % | Approved |
|---|---|---|---|
| rounding_midpoint | 25.00 | 2.50 | 0.63 |
| one_cent_midpoint | 1.00 | 0.50 | 0.01 |
| small_midpoint | 0.10 | 5.00 | 0.01 |

`0.625` rounds to `0.63` away from zero and to `0.62` with banker's rounding: that is what the mutant gets wrong.
