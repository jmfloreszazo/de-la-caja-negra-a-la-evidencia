**English** · [Español](../../es/parte-7-organizacion/32-una-historia-de-migracion-la-cuenta-que-parecia-facil.md)

[← Chapter 31 · The SDLC as part of the migration engine](31-the-sdlc-as-part-of-the-migration-engine.md) · [Contents](../README.md) · [Chapter 33 · Modernization plan: first a capability test, then a bet →](33-modernization-plan-first-a-capability-test-then-a-bet.md)

# Chapter 32 · A migration story: the account that looked easy

> [!IMPORTANT]
> **Chapter thesis.** A program that compiles on .NET 10 is not a migrated account. Three tests —two simultaneous withdrawals, a transfer and a nightly close— are enough to discover three responsibilities that were not on the program map.

Imagine a fictional bank with a COBOL program called `ACCTUPD`. It processes debits and credits, queries a limits table, records movements and takes part in a nightly closing process. The first demo shows a small fragment: input, balance validation, new amount and write. An LLM produces readable C#. Management celebrates that the program already compiles on .NET 10. The technical team then asks for three more tests.

First test: two simultaneous withdrawals. The service without concurrency control approves both. The solution is not to add a `lock` in a web controller: that lock protects one process and the bank will have several nodes. We introduce a transaction and versioning or database-level locking, with an idempotent key. Actors can reduce conflicts by identity, but the commit is still the decisive boundary.

Second test: a transfer. There are two accounts and two writes. A failure between them shows that in-memory sequencing is not enough. We move to a ledger with an atomic operation within a database, or we formally define a compensation protocol when the movement crosses systems where local atomicity is not possible. The business decides which intermediate states are observable and which are not.

Third test: the nightly close. A distributed version tries to calculate a million accounts with one actor per account and too many small writes. Commit time dominates the profile. We reorganize the work into stable partitions, batched writes, idempotent controls and checkpoints. The final code looks less like the original COBOL. The behaviour and the invariants look more like the system we really need.

At this point we are no longer translating a routine. We have identified three different responsibilities: **online acceptance**, **accounting integrity** and **batch processing**. Separating them lets us deploy and measure each with its own criteria. This decomposition was not necessarily on the legacy program map. It is an architectural decision based on responsibilities, not on file names.

![Figure 32.1 · Three tests, three responsibilities that were not on the program map.](../../figures/en/story.png)

*Figure 32.1 · Three tests, three responsibilities that were not on the program map.*

> **The final code looks less like the original COBOL. The behaviour looks more like the system we really need.**

---

[← Chapter 31 · The SDLC as part of the migration engine](31-the-sdlc-as-part-of-the-migration-engine.md) · [Contents](../README.md) · [Chapter 33 · Modernization plan: first a capability test, then a bet →](33-modernization-plan-first-a-capability-test-then-a-bet.md)
