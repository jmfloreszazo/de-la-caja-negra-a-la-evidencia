**English** · [Español](../../es/parte-4-patrones/14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md)

[← Chapter 13 · Before choosing a pattern, identify the contract](13-before-choosing-a-pattern-identify-the-contract.md) · [Contents](../README.md) · [Chapter 15 · Anti-Corruption Layer: translate meanings, not types →](15-anti-corruption-layer-translate-meanings-not-types.md)

# Chapter 14 · Strangler Fig: change the edge before the heart

> [!IMPORTANT]
> **Chapter thesis.** Intercept a capability, route it gradually and retire the old path once the new one has proved it responds correctly. The simplicity of the drawing hides the two real challenges: choosing the seam and controlling shared data.

The Strangler Fig pattern [36] is the alternative that most often allows modernizing without requiring a big final cutover. Its idea is simple: intercept a capability, progressively route it to a new implementation and retire the old path when the new one has shown it responds correctly. But the simplicity of the drawing hides two challenges: setting boundaries and controlling shared data.

In COBOL, the boundary can be a CICS transaction, a program call, a file-based integration, an already exposed API or a step in the batch chain. My preference is a **business seam**: "quote a policy", "calculate interest", "post a charge", not "migrate program ABC123". Program names are a historical map of the implementation; they do not always represent domain capabilities.

The first deployment can be limited to *shadow mode*: the transaction keeps running in COBOL and the new implementation receives a safe copy of the request. We compare decisions and simulated effects, without duplicating production writes. Later we move to controlled reads or a small percentage of operations. There must be a reversibility plan, but we cannot promise an instant rollback once we have split data ownership and generated external effects. Rollback is a designed and rehearsed capability, not a sentence on a slide.

![Figure 14.1 · Life cycle of a Strangler Fig seam: every transition requires evidence, and the way back is rehearsed.](../../figures/en/strangler_states.png)

*Figure 14.1 · Life cycle of a Strangler Fig seam: every transition requires evidence, and the way back is rehearsed.*

A team can fall into the "eternal strangler" trap: the new system lives permanently off the old one through dozens of calls without bounded responsibilities. The remedy is to publish, for each seam, a retirement contract: data owner, observability, tests, rollback route, target date and the dependencies that will disappear. Modernizing also means **removing**.

## The facade that decides who answers

The piece that makes all of the above possible is a facade with a routing policy per capability. In shadow mode the reference system always answers and the candidate is evaluated off the critical path.

**Listing 14.1 · Coexistence facade with shadow mode for a capability without side effects** — *Illustrative*

```csharp
public enum Route { Legacy, Shadow, Modern }

public sealed class FeeFacade(ILegacyFee legacy, IModernFee modern,
                              IRoutingPolicy policy, IShadowComparer shadow)
{
    public async Task<FeeResult> CalculateAsync(FeeRequest request, CancellationToken ct)
    {
        switch (policy.RouteFor(request))
        {
            case Route.Modern:
                return await modern.CalculateAsync(request, ct);

            case Route.Shadow:
                var authoritative = await legacy.CalculateAsync(request, ct);
                shadow.Enqueue(request, authoritative);   // candidate evaluated separately
                return authoritative;                     // the reference answers

            default:
                return await legacy.CalculateAsync(request, ct);
        }
    }
}
```

![Figure 14.2 · Shadow mode for a capability without side effects: the reference always answers.](../../figures/en/shadow_seq.png)

*Figure 14.2 · Shadow mode for a capability without side effects: the reference always answers.*

This fragment is only safe because the fee is a pure calculation. If the capability writes, notifies or charges, the shadow cannot execute real effects: it needs a non-authoritative store, simulated effects and a capture that pins the state read by both sides. Chapter [30](../part-7-organization/30-from-the-lab-to-a-system-that-keeps-running.md) returns to that coexistence and to what going back means once data has been written.

> **Modernizing also means removing. A strangler without a retirement contract is an eternal strangler.**

---

[← Chapter 13 · Before choosing a pattern, identify the contract](13-before-choosing-a-pattern-identify-the-contract.md) · [Contents](../README.md) · [Chapter 15 · Anti-Corruption Layer: translate meanings, not types →](15-anti-corruption-layer-translate-meanings-not-types.md)
