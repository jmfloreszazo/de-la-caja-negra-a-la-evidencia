# Step-by-step walkthrough

This guide follows `walkthrough.py` and shows what you should see at each step, taken from the reference run of 29 October 2026. Your timings will differ; verdicts must not.

## 0. Before compiling anything

```bash
python3 tools/verify_offline.py
```

Expected last line: `VERIFY: PASS (offline checks only; ...)`. If the independent policy disagrees with a case, stop: either the contract or the reading of it is wrong, and no amount of C# will fix that.

## 1. Open the COBOL program

`legacy/fee.cob` reads one 14-character record:

```
01 raw-input pic x(14).
01 request-fields redefines raw-input.
   05 amount-cents     pic 9(8).
   05 rate-bps         pic 9(5).
   05 customer-active  pic x.
```

The same bytes are read as three fields. A translation that turns each name into an independent variable loses that relationship.

## 2. Run it locally

```bash
python3 cobol_local.py legacy/fee.cob --input 0000002500200Y
```

```
Compile: cobc -x -free -o /tmp/cobol-local-.../program .../legacy/fee.cob
Input: '0000002500200Y'
APPROVE|00000001
```

25 cents at 200 basis points is exactly half a cent. `ROUNDED` resolves the tie away from zero: one cent. Try `0000002400200Y` (rounds to 0) and `0000002600200Y` (rounds to 1).

## 3. Read the C# candidate

The decisive line in `Candidate/Program.cs`:

```csharp
var fee = decimal.Round(amount * (decimal)rate / 10000m, 0,
    mode == "round-even" ? MidpointRounding.ToEven : MidpointRounding.AwayFromZero);
```

`MidpointRounding.ToEven` is what `Math.Round` does when you do not specify a mode. It looks reasonable in a review. Case C003 (`0000002500200Y`) is the one that tells them apart.

## 4. Run the comparison and the gate controls

```bash
python3 run.py
```

Expected summary (`results/summary.json`):

```
none                     PASS          SIMULATED_ALLOW
round-even               FAIL          BLOCK
wrong-threshold          FAIL          BLOCK
approve-inactive         FAIL          BLOCK
missing-evidence         INCONCLUSIVE  BLOCK
missing-case             INCONCLUSIVE  BLOCK
duplicate-case           INCONCLUSIVE  BLOCK
invalid-anchor           INCONCLUSIVE  BLOCK
no-mandate               PASS          BLOCK
equal-but-wrong          FAIL          BLOCK
```

Open `results/round-even-gate.json`:

```json
{ "verdict": "FAIL", "authority": "DEMO_ONLY", "release": "BLOCK",
  "findings": [ "C003: candidate violates contract" ], "exitCode": 2 }
```

And `results/equal-but-wrong-gate.json`: both programs agree, and both are wrong.

```json
{ "verdict": "FAIL", "release": "BLOCK",
  "findings": [ "C003: legacy violates contract", "C003: candidate violates contract" ] }
```

## 5. Break it yourself

Ideas that should turn the gate red, and one that should not:

* change `1000000` to `999999` in `Candidate/Program.cs` → C008 fails (threshold);
* remove the `if (rate>10000)` line → C055 fails (invalid rate accepted);
* add a case to `contracts/cases.json` without updating `cases.sha256` → `run.py` refuses to start (anchor);
* rename a variable in the candidate → still PASS (behaviour unchanged).

## 6. From a calculation to transactions

```bash
python3 bank_test.py
```

Expected: `"status": "PASS"`, every control `PASS`, six invariants `true`, and `oracleRejectsCorruptLedger: PASS`. Then open the databases with any SQLite client:

```sql
SELECT o.id, o.status, p.account, p.delta
FROM operations o JOIN postings p ON p.op = o.id
ORDER BY o.id;
```

Each committed operation has exactly two postings that sum to zero and one outbox row.

## 7. The measurement trap

```bash
python3 tools/coordinated_omission_demo.py
```

```
mode                          req    req/s     p50     p95      p99      max  >100ms
closed-loop (1 client)       9500    950.0     1.0     1.0      1.0    501.0       1
open-loop (500/s)            5000    500.1     1.0   251.0    451.0    501.0     401
```

Same simulated server, same stall. The closed loop reports a p99 of 1 ms because its only client was waiting during the stall. Measure capacity with a controlled arrival rate, from the intended send time.
