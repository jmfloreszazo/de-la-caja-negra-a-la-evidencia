**English** · [Español](../../es/parte-4-patrones/15-anti-corruption-layer-traducir-significados-no-tipos.md)

[← Chapter 14 · Strangler Fig: change the edge before the heart](14-strangler-fig-change-the-edge-before-the-heart.md) · [Contents](../README.md) · [Chapter 16 · Data ownership →](16-data-ownership.md)

# Chapter 15 · Anti-Corruption Layer: translate meanings, not types

> [!IMPORTANT]
> **Chapter thesis.** A `PIC S9(11)V99 COMP-3` is not a `decimal`: it is scale, representation, sign and constraints. The anti-corruption layer keeps those decisions from contaminating the new model and forces us to declare them.

A `PIC S9(11)V99 COMP-3` is not simply a `decimal`. The type expresses scale, representation, sign and constraints. An EBCDIC record may have collations, overpunch and redefined fields. A lexicographic comparison that worked with one collation may change when moving to Unicode. And a `REDEFINES` represents several interpretations of the same storage, often determined by an external discriminator.

The Anti-Corruption Layer (ACL) keeps those decisions from penetrating the modern model. Here I place encoding adapters, record parsers, scale validators, date converters, packed decimal decoding and error code mapping. On the other side appear explicit business concepts: `Money`, `AccountId`, `EffectiveDate`, `Posting`, `PolicyStatus`. The transformation must be bidirectional and verifiable while old and new coexist.

![Figure 15.1 · The anti-corruption layer as a class model: codecs translate bytes, quarantine collects what is invalid and the domain only sees business concepts.](../../figures/en/acl_class.png)

*Figure 15.1 · The anti-corruption layer as a class model: codecs translate bytes, quarantine collects what is invalid and the domain only sees business concepts.*

I would not call silently changing a historical behaviour "normalization". If the original system rounds each line before adding and the new one adds before rounding, the operations are not equivalent even though both use exact decimals. If the new rule is better, the right thing is to approve an **intentional business change** and document it as an authorized divergence. Equivalence oracles must not become a prison that preserves errors out of inertia, but nor should they be an excuse to fix them without control.

Agents can propose mappings from the copybook and from examples, but critical conversions must run with deterministic libraries and boundary tests. Each field needs a contract: original bytes, interpretation, range, nulls, sign, scale and policy for invalid data.

Microsoft documents this pattern as a facade or adaptation layer between subsystems that do not share semantics, and reminds us of two things worth keeping in mind during a migration: it can become a single point of failure, and we must decide from the start whether it will be permanent or retired when the transition ends [38].

## A codec that does not guess

The smallest ACL example worth writing is the packed decimal decoder. Each byte stores two digits, except the last, which stores one digit and the sign. There is no decimal point: the scale comes from the copybook.

**Listing 15.1 · Explicit COMP-3 decoding with the copybook scale** — *Illustrative · logic verified*

```csharp
public static decimal DecodePacked(ReadOnlySpan<byte> field, int scale)
{
    if (field.IsEmpty || scale < 0 || scale > 18)
        throw new ArgumentException("Invalid field or scale");

    long digits = 0;
    for (int i = 0; i < field.Length; i++)
    {
        digits = checked(digits * 10 + Digit(field[i] >> 4, i));
        if (i < field.Length - 1)
            digits = checked(digits * 10 + Digit(field[i] & 0x0F, i));
    }

    bool negative = (field[^1] & 0x0F) switch
    {
        0x0D or 0x0B => true,
        0x0C or 0x0F or 0x0A or 0x0E => false,
        _ => throw new FormatException("Invalid sign nibble")
    };

    decimal value = digits;
    for (int s = 0; s < scale; s++) value /= 10m;   // exact: decimal is base 10
    return negative ? -value : value;

    static int Digit(int nibble, int index) => nibble <= 9
        ? nibble
        : throw new FormatException($"Invalid digit nibble in byte {index}");
}
```

The logic of this codec is checked with an independent twin implementation over the vectors in the table; the C# code is illustrative.

| Bytes (hex) | Copybook | Expected result |
|---|---|---|
| `12 34 5C` | `PIC S9(3)V99 COMP-3` | 123.45 |
| `12 34 5D` | `PIC S9(3)V99 COMP-3` | −123.45 |
| `01 23 45 6D` | `PIC S9(5)V99 COMP-3` | −1234.56 |
| `99 9F` | `PIC 9(3) COMP-3` | 999 (sign F, unsigned) |
| `00 0C` | `PIC S9(3) COMP-3` | 0 |
| `1A 3C` | any | error: invalid digit nibble |
| `12 37` | any | error: invalid sign nibble |

The last two rows are the important ones. A codec that "tolerates" invalid bytes by turning them into zero has made a business decision nobody approved. IBM documents that even recompiling with a new version of Enterprise COBOL can expose invalid numeric data that had been there for years [30]. The ACL is where that data is detected, quarantined and counted, not where it is hidden.

> **I would not call silently changing a historical behaviour "normalization".**

---

[← Chapter 14 · Strangler Fig: change the edge before the heart](14-strangler-fig-change-the-edge-before-the-heart.md) · [Contents](../README.md) · [Chapter 16 · Data ownership →](16-data-ownership.md)
