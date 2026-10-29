**English** · [Español](../../es/parte-3-oraculos/12-cobol-y-c-deben-acordar-el-significado.md)

[← Chapter 11 · The architecture of a verifiable modernization](11-the-architecture-of-a-verifiable-modernization.md) · [Contents](../README.md) · [Part IV · Patterns that replace responsibilities, not syntax →](../part-4-patterns/README.md)

# Chapter 12 · COBOL and C# must agree on meaning

> [!IMPORTANT]
> **Chapter thesis.** Using `decimal` is the beginning. Scale, when rounding happens, how ties are broken, range and shared memory are part of the contract, and a demo with round values does not test any of them.

## The right type is only the beginning

A migration can use `decimal` and still calculate wrongly. Scale, the moment of rounding, the range of the field and the handling of overflow are part of the behaviour. If we round each line and then add, we may get a different result from adding first and rounding at the end.

The .NET documentation states that `Math.Round` uses round-half-to-even by default in the overloads that do not specify another mode [8]. So writing `Round` and nothing else is not a neutral decision when we are trying to preserve existing behaviour.

In COBOL, the rounding and size-error clauses influence the stored result. IBM documents that, when ROUNDED is specified, rounding precedes the SIZE ERROR check, and that ON SIZE ERROR changes how an out-of-range result is handled [9]. The dialect and compiler options must be recorded; I would not extrapolate a GnuCOBOL test to every runtime.

In the lab we reduce the domain to non-negative amounts expressed in cents and integer rates in basis points. The result is also an integer number of cents. This choice makes rounding visible without requiring a full financial infrastructure.

## Half a cent of difference

Take an amount of 25 cents and a rate of 200 basis points, equivalent to two per cent. The exact fee before rounding is half a cent. Rounding half to even gives zero cents. Rounding to the nearest integer with ties away from zero gives one cent.

Both methods are deterministic. Both may be appropriate in some context. The question is which one our contract establishes. In this example we have fixed the second for non-negative values and we check it against the executed COBOL program.

The case is small, but it shows why a demo with round values can be misleading. For 100 euros with a rate that produces an exact amount, the two implementations agree. The defect only appears when we choose an input that distinguishes the criteria.

This is how the difference looks in both languages. In COBOL, the `ROUNDED` clause of the lab program:

**Listing 12.1 · The calculation in legacy/fee.cob** — *Executed*

```cobol
        compute fee-cents rounded = amount-cents * rate-bps / 10000
          on size error
            move 'INVALID' to result-code
          not on size error
            move fee-cents to fee-display
```

In .NET, the trap is the overload that says nothing:

**Listing 12.2 · Documented behaviour of Math.Round [8]** — *Illustrative*

```csharp
Math.Round(0.5m);                                  // 0 -> to even, by default
Math.Round(1.5m);                                  // 2 -> also to even
Math.Round(0.5m, MidpointRounding.AwayFromZero);   // 1
decimal.Round(25m * 200m / 10000m, 0,
              MidpointRounding.AwayFromZero);      // 1 -> lab case C003
```

Neither default line is a .NET bug. It is a different policy. The bug appears when nobody decides which one is ours.

## Memory is part of the contract too

REDEFINES lets us describe the same region of data with another structure. A translation that turns each name into an independent variable may lose that relationship. In our program, the input record is interpreted through a redefined group. The example is simple and visible: the same characters represent amount, rate and customer status.

![Figure 12.1 · REDEFINES: the same fourteen bytes read as three fields. A translation that creates three independent variables loses that relationship.](../../figures/en/fee_record.png)

*Figure 12.1 · REDEFINES: the same fourteen bytes read as three fields. A translation that creates three independent variables loses that relationship.*

I do not use that demonstration to claim we already handle arbitrary layouts. Variable structures, complex overlays, code page conversions and data persisted in specific formats are left out. The adapter of a real project must describe and test them with representative records.

We must also observe effects that do not appear in the returned value: writes, messages, state changes, return codes, order of operations and recovery after a failure. Two functions can return the same number and leave different systems behind.

The equivalence we care about belongs to an observation contract. The poorer that contract, the more relevant differences we can leave undetected.

> **The defect only appears when we choose an input that distinguishes the criteria.**

---

[← Chapter 11 · The architecture of a verifiable modernization](11-the-architecture-of-a-verifiable-modernization.md) · [Contents](../README.md) · [Part IV · Patterns that replace responsibilities, not syntax →](../part-4-patterns/README.md)
