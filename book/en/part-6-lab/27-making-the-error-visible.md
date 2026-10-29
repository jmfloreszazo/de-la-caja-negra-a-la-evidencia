**English** · [Español](../../es/parte-6-laboratorio/27-hacer-que-el-error-se-vea.md)

[← Chapter 26 · A local lab you can understand](26-a-local-lab-you-can-understand.md) · [Contents](../README.md) · [Chapter 28 · Transfers, locks and failures, locally →](28-transfers-locks-and-failures-locally.md)

# Chapter 27 · Making the error visible

> [!IMPORTANT]
> **Chapter thesis.** Three seeded defects, four kinds of incomplete evidence, a misleading match and a delivery without a mandate. Each produces a different verdict, and each verdict leaves a file someone else can open.

## A correct implementation within scope

First we run the COBOL program and the C# candidate on the same inputs. Each output is checked against the expected result pinned in the contract. This third element is important: two programs agreeing does not rule out both being wrong.

The gate does not just count matching rows. It checks that the expected cases exist and that observations have the corresponding identities. A missing case or output produces INCONCLUSIVE. An observed discrepancy produces FAIL. An incomplete set cannot win by having left out precisely the example that failed.

The baseline is checked against a digest. In the demo, that digest stays in a local file and serves to detect changes with respect to the reference used. It does not prove human approval or resistance against someone who can modify both pieces. Its teaching role is to show the link; the production architecture must protect the anchor.

The heart of the gate fits in a few lines. Each observation is compared with the approved expectation, never only with the other implementation; absence and contradiction produce different verdicts; and authorization is evaluated separately.

**Listing 27.1 · Gate/Program.cs: three verdicts and a separate authorization** — *Executed*

```csharp
foreach(var key in new[]{"legacy","candidate"})
{
    if(!row.TryGetProperty(key,out var value) || value.ValueKind!=JsonValueKind.String)
    {missing=true;findings.Add(id+": missing "+key);continue;}
    if(value.GetString()!=c.GetProperty("expected").GetString())
    {failed=true;findings.Add(id+": "+key+" violates contract");}
}
// ...
verdict=failed ? "FAIL" : missing ? "INCONCLUSIVE" : "PASS";
// ...
var release=verdict=="PASS" && authority ? "SIMULATED_ALLOW" : "BLOCK";
```

![Figure 27.1 · The decision logic of Gate/Program.cs: contradiction weighs more than absence, and authorization is evaluated separately.](../../figures/en/gate_flow.png)

*Figure 27.1 · The decision logic of Gate/Program.cs: contradiction weighs more than absence, and authorization is evaluated separately.*

## Three mutations of the candidate

The first mutation changes rounding to half-even. The 25-cent case detects the difference. The code may look reasonable at a quick review, because it uses a standard .NET operation. The contract makes visible why that operation does not match this rule.

The second raises the review threshold from 1,000,000 to 1,200,000 cents. The value immediately above the correct threshold and the case between both limits expose the defect. Testing only very small or very large amounts would let the change through.

The third omits the rejection of inactive customers. Here the order of decisions matters. We do not want the program to calculate a fee and approve an operation that should have been rejected earlier. The verifier compares the full output, including status and amount.

These controls are deliberately seeded and known to whoever built the lab. They serve to demonstrate the detection mechanism. They must not be described as defects discovered in a real product or as a blind productivity evaluation.

The three mutations live in the same candidate and are activated by argument. The rounding one is the most instructive, because at first sight it does not look like an error:

**Listing 27.2 · Candidate/Program.cs: where the defects are seeded** — *Executed*

```csharp
    if (line[13]=='N' && mode!="approve-inactive")
    { Console.WriteLine("REJECT|00000000"); continue; }
    var fee=decimal.Round(amount*(decimal)rate/10000m,0,
        mode=="round-even" ? MidpointRounding.ToEven : MidpointRounding.AwayFromZero);
    var threshold=mode=="wrong-threshold" ? 1200000 : 1000000;
```

## Equality can be misleading too

Another control modifies both observations so they agree on an incorrect result. A COBOL–C#-only comparison would accept it. Our gate rejects it because it checks both observations against the normative expectation of the case.

This control does not prove the capturer is incorruptible. On the contrary, it makes its importance visible. In production we need to know who obtained the observation, which executable it launched and which transformations it applied. If the builder can fabricate all the evidence, a correct baseline is not enough.

Finally we remove the synthetic mandate. The functional results are still correct, but delivery is blocked. The reader can observe two simultaneous statements: the candidate meets the checks and does not have permission to be delivered under that configuration.

These are two real gate outputs from the reference run. The first blocks half-even rounding in case C003. The second is the misleading match: both programs say the same thing, and both are wrong.

**Listing 27.3 · reference-results/round-even-gate.json and equal-but-wrong-gate.json** — *Executed*

```json
{ "verdict": "FAIL", "authority": "DEMO_ONLY", "release": "BLOCK",
  "findings": [ "C003: candidate violates contract" ], "exitCode": 2 }

{ "verdict": "FAIL", "authority": "DEMO_ONLY", "release": "BLOCK",
  "findings": [ "C003: legacy violates contract", "C003: candidate violates contract" ],
  "exitCode": 2 }
```

And this is the correct but unauthorized delivery: PASS behaviour, authority denied, delivery blocked, exit code 4.

**Listing 27.4 · reference-results/no-mandate-gate.json** — *Executed*

```json
{ "verdict": "PASS", "authority": "DENY", "release": "BLOCK", "findings": [], "exitCode": 4 }
```

## What we can conclude

The results show that the lab detects the defects and absences included, with the versions executed. They do not prove universal equivalence, the security of an enterprise pipeline or an autonomous modernization capability. Nor do they measure how much work AI saved.

It is a smaller conclusion than a promise of automatic migration. It is also a conclusion someone else can try to reproduce and refute.

## Break it yourself

The lab is made for you to contradict it. Four five-minute experiments, with their expected result:

| Change | Expected result | What it teaches |
|---|---|---|
| Change `1000000` to `999999` in the candidate | FAIL on C008 | The exact threshold is a case, not a detail |
| Remove the `rate>10000` check | FAIL on C055 | Validation is behaviour too |
| Add a case to `cases.json` without updating the anchor | `run.py` refuses to start | The baseline has an identity |
| Rename a variable in the candidate | PASS | The gate judges behaviour, not style |

> **It is a smaller conclusion than a promise of automatic migration. It is also one someone else can reproduce and refute.**

---

[← Chapter 26 · A local lab you can understand](26-a-local-lab-you-can-understand.md) · [Contents](../README.md) · [Chapter 28 · Transfers, locks and failures, locally →](28-transfers-locks-and-failures-locally.md)
