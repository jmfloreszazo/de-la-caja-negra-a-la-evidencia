**English** · [Español](../../es/parte-7-organizacion/30-del-laboratorio-a-un-sistema-que-sigue-operando.md)

[← Part VII · From evidence to the organization](README.md) · [Contents](../README.md) · [Chapter 31 · The SDLC as part of the migration engine →](31-the-sdlc-as-part-of-the-migration-engine.md)

# Chapter 30 · From the lab to a system that keeps running

> [!IMPORTANT]
> **Chapter thesis.** During coexistence, each capability has a single write owner; going back may require transforming data; and any change of rules, compilers or models forces the acceptance evidence to be renewed.

## Coexistence has a write owner

A calculation without persistence is a good entry point to the problem. An enterprise application requires deciding how the two implementations coexist while the new one is verified.

In a shadow run, the reference system keeps operating and the new implementation receives comparable inputs to evaluate its response. That shadow must not duplicate external effects. A notification, a charge or an update must not be executed twice because we want to compare results.

The capture must define the observed state. If one implementation reads the data before an update and the other after, a difference may be due to the moment of reading. The evidence must allow us to distinguish a semantic defect from a divergence introduced by the experiment itself.

Write ownership must be explicit per capability and per phase. The strategy may include gradual routing, reconciliation and idempotency mechanisms, depending on the system. I would not introduce simultaneous writes to two data models as a minor integration detail.

![Figure 30.1 · Coexistence phases: in each one there is a single write owner, and going back may require transforming data.](../../figures/en/coexistence.png)

*Figure 30.1 · Coexistence phases: in each one there is a single write owner, and going back may require transforming data.*

## Going back can also transform data

A code rollback does not guarantee that the previous system understands the data written by the new version. Nor does it withdraw a message already consumed or undo an external interaction. The return plan must describe which consequences can be reverted and which require compensation or repair.

Before increasing traffic, I would check the cutover mechanism, reconciliation and recovery. If the return window depends on a maximum volume of changes, that limit is part of the delivery decision. An option that disappears after a few hours should not be described as available indefinitely.

Operational oracles extend the functional ones. We care about processing time, resource usage, recovery and data consistency. Their thresholds are set according to the service. I would not choose a universal equivalence percentage to approve any migration.

A small discrepancy in frequency can affect the most important operation. That is why risk classification and critical rules weigh more than a global average. Zero observed differences does not prove the absence of differences in the whole population either.

## Drift requires re-evaluating

After cutover, rules, data, compilers and dependencies change. The model that helps maintain the system can change too. G7 connects those changes with the acceptance evidence that must be renewed.

If a rate goes from two decimals to four, it is not enough to rerun the old set and celebrate that it is still green. The contract has changed. We need new boundaries, new expectations and possibly another representation.

The modernization will have truly improved the ability to evolve when we can make that change without losing the link between intent, implementation and acceptance. That continuity is one of the outcomes I want to pursue with TODM.

> **A code rollback does not withdraw a message already consumed or undo an external interaction.**

---

[← Part VII · From evidence to the organization](README.md) · [Contents](../README.md) · [Chapter 31 · The SDLC as part of the migration engine →](31-the-sdlc-as-part-of-the-migration-engine.md)
