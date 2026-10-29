**English** · [Español](../../es/parte-1-antes-de-traducir/03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md)

[← Chapter 2 · The system we are trying to preserve](02-the-system-we-are-trying-to-preserve.md) · [Contents](../README.md) · [Chapter 4 · What I share with other authors and where I disagree →](04-what-i-share-with-other-authors-and-where-i-disagree.md)

# Chapter 3 · Why one-to-one conversion is not modernization

> [!IMPORTANT]
> **Chapter thesis.** We should not copy the inherited design: we should preserve its obligations and redesign the mechanisms that satisfy them. A literal translation can be a legitimate bridge, never the destination.

Translating instructions can be a useful activity. The criticism starts when we confuse that activity with the final goal. If we keep the same program boundaries, the same coupling to data, the same global state model and the same imperative order of operations, but swap COBOL for C#, we will have manufactured a legacy monolith in another language. What some call "JOBOL" in Java can also exist in .NET. The problem is not the target language: it is the design we drag along.

The literal copy fails for six reasons. First, **it inherits accidental partitions**: modules reflected the memory, team and compilation limits of another era, not necessarily business capabilities. Second, **it preserves couplings** that now cross networks and databases. A read from a common area that cost nanoseconds can become a remote call. Third, **it replicates implicit state** that is no longer safe when scaling horizontally. Fourth, **it carries over storage semantics** —EBCDIC, `COMP-3`, `REDEFINES`, overlaid fields, sign formats— into representations that do not share their assumptions. Fifth, **it keeps delivery problems**: massive deployments, inseparable changes and rigid windows. Sixth, **it prevents us from exploiting the new environment**, because it forces modern technology to imitate the decisions of a different architecture.

But saying we should "never" do a 1:1 conversion would be as dogmatic as saying we always should. There is a legitimate role for a mechanical, conservative translation: it can create a transition platform, reduce dependence on a compiler, keep a temporary contract or enable differential testing before redesigning. In that case I would not sell it as the end state. I would declare it a **compatibility phase**, with a date, exit criteria and identified technical debt. I would also consider keeping COBOL in production while we extract new services. Modernization is not measured by the percentage of code rewritten.

The sentence that guides this book is this: **we should not copy the inherited design; we should preserve its obligations and redesign the mechanisms that satisfy them**. That requires asking what each old block really guarantees. The report produced by a nightly program can become a partitioned pipeline. The lock on a record can become a short SQL transaction, optimistic control or a per-key queue. The conversational session can become an explicit state machine. But never without first identifying which property it protected.

## What is said and what there is

The public conversation about automatic translation mixes claims that are worth separating. I put them side by side because it is the fastest way to know what we are buying.

| What is said | What there is |
|---|---|
| "AI converts COBOL to C# in hours" | It can generate plausible C# in hours. Functional, data, operational and capacity equivalence are not included |
| "If it compiles and passes the tests, it's migrated" | That depends on who wrote the tests and where the expected result came from. If the same agent wrote them from the same code, they verify its interpretation |
| "We use decimal, so the money adds up" | The type is the beginning. Scale, when rounding happens and how ties are broken decide the cent |
| "No more mainframe, now it's cloud native" | If we keep program boundaries, global state and data coupling, we have the same monolith with more network hops |
| "We'll do 1:1 and refactor later" | It can be a good strategy if the compatibility phase has a date, exit criteria and identified debt. Without them, "later" never comes |

## A deceptively simple example

Suppose a COBOL program that reads an account, checks the balance, decrements it and writes the record. An AI produces a `WithdrawAsync` method, uses `decimal` and gets the right result for one case. It sounds reasonable. If two instances of the service read the balance before either confirms its write, both may approve the withdrawal. The data is correct in each isolated execution; the system is wrong when it works as a system. You do not necessarily get to that failure by enlarging the LLM's context window. You get there by analysing the concurrency contract.

Modernization, therefore, is not one agent transforming syntax while another invents tests from the same code. It is building an independent specification, identifying guarantees and choosing patterns whose effects we can demonstrate.

## The same example, in code

Let's look at the old program. The fragment is illustrative, but the pattern appears in a great many CICS transactions over VSAM files.

**Listing 3.1 · COBOL withdrawal under CICS: the read reserves the record** — *Illustrative*

```cobol
           EXEC CICS READ FILE('ACCOUNTS')
                     INTO(WS-ACCOUNT)
                     RIDFLD(WS-ACCOUNT-ID)
                     UPDATE
                     RESP(WS-RESP)
           END-EXEC
           IF WS-RESP = DFHRESP(NORMAL)
              IF WS-BALANCE >= WS-AMOUNT
                 SUBTRACT WS-AMOUNT FROM WS-BALANCE
                 EXEC CICS REWRITE FILE('ACCOUNTS')
                           FROM(WS-ACCOUNT)
                           RESP(WS-RESP)
                 END-EXEC
              ELSE
                 EXEC CICS UNLOCK FILE('ACCOUNTS') END-EXEC
                 MOVE 'NSF' TO WS-RESULT
              END-IF
           END-IF
```

The important word is `UPDATE`. It is not a decorative label: the read obtains exclusive control of the record, and on a recoverable file the change takes part in the unit of work that is committed or backed out at the syncpoint [16]. The guarantee is not written in the COBOL; it is provided by the environment in which the COBOL runs.

Now the translation anyone —person or agent— produces in five minutes:

**Listing 3.2 · Literal C# translation: it compiles, passes the happy path and loses the guarantee** — *Illustrative*

```csharp
public async Task<string> WithdrawAsync(string accountId, decimal amount)
{
    var account = await _repository.GetAsync(accountId); // no reservation
    if (account.Balance < amount) return "NSF";
    account.Balance -= amount;                           // decided on a snapshot
    await _repository.SaveAsync(account);                // unconditional write
    return "OK";
}
```

With a single instance and a single client, it works. With two instances and two simultaneous withdrawals, both read the same balance, both approve and the second write overwrites the first. No unit test detects it, because no unit test runs two histories at once.

![Figure 3.1 · The literal translation under concurrency: two instances decide on the same snapshot and 1,300 is paid out of an account holding 1,000.](../../figures/en/race_naive.png)

*Figure 3.1 · The literal translation under concurrency: two instances decide on the same snapshot and 1,300 is paid out of an account holding 1,000.*

The fix is not to put a `lock` in the controller: it would protect one process, and the service will have several. It is to move the rule to the place where it is committed. This is the real fragment from the lab, which runs against a SQLite database from independent processes:

**Listing 3.3 · Conditional debit inside the transaction (Bank/Program.cs)** — *Executed*

```csharp
db.Exec("BEGIN IMMEDIATE"); begun = true;
// ... idempotency check on the operation identity ...
db.Exec($"UPDATE accounts SET balance=balance-{amount} WHERE id={src} AND balance>={amount}");
var approved = db.Changes == 1;   // 1 row: approved; 0: insufficient funds
if (approved) {
    db.Exec($"UPDATE accounts SET balance=balance+{amount} WHERE id={dst}");
}
// ... operation, two postings and outbox row in the SAME transaction ...
db.Exec("COMMIT");
```

![Figure 3.2 · The rule lives where it is committed: the engine serializes writes on the row and only one withdrawal meets the condition.](../../figures/en/race_fixed.png)

*Figure 3.2 · The rule lives where it is committed: the engine serializes writes on the row and only one withdrawal meets the condition.*

The resulting code looks less like the original COBOL. The behaviour looks more like what we need. That, in miniature, is the thesis of this book. Chapter [28](../part-6-lab/28-transfers-locks-and-failures-locally.md) shows what happens when two processes really compete for that balance.

> **A 1:1 modernization can be a bridge, but we should never mistake the bridge for the city we want to reach.**

---

[← Chapter 2 · The system we are trying to preserve](02-the-system-we-are-trying-to-preserve.md) · [Contents](../README.md) · [Chapter 4 · What I share with other authors and where I disagree →](04-what-i-share-with-other-authors-and-where-i-disagree.md)
