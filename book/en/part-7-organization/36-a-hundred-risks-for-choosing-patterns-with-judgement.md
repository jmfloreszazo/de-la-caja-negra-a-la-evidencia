**English** · [Español](../../es/parte-7-organizacion/36-cien-riesgos-para-elegir-patrones-con-criterio.md)

[← Chapter 35 · When I would NOT migrate](35-when-i-would-not-migrate.md) · [Contents](../README.md) · [Chapter 37 · The new modernization contract →](37-the-new-modernization-contract.md)

# Chapter 36 · A hundred risks for choosing patterns with judgement

> [!IMPORTANT]
> **Chapter thesis.** There is no canonical, verifiable catalog of the hundred COBOL problems ranked by frequency. We can, however, keep a working register where each risk carries an application option, an infrastructure capability and the test that could refute them.

I looked for a canonical catalog of the hundred main COBOL problems and found no verifiable reference with that scope and a frequency classification. There are useful sources to build a rigorous chapter: IBM documents specific compiler migration problems, AWS gathers mainframe and decoupling patterns, and Azure offers catalogs of patterns and OLTP architectures [30–34]. They are not a common list of a hundred problems, nor do they promise to cover any system.

That is why I present my own catalog of a hundred modernization risks. The numbering identifies them and links them to evidence; it does not express frequency, severity or a universal priority. Part of the catalog deals with COBOL semantics, another part with mainframe services and the rest gathers enterprise system problems that also appear when modernizing other technologies.

Each entry proposes a candidate combination of application and infrastructure and a check that could refute it. It does not claim the solution is implemented, validated or suitable for every case. The assessment must record applicability, owner, original rule, target decision and acceptance evidence before closing an entry.

IBM's documentation is particularly instructive: even recompiling for a new version of COBOL can expose invalid numeric data, incompatible sizes or uninitialized values. We do not need to change language to discover a semantic dependency [30]. A new architecture does not automatically fix those conditions.

## How to use the catalog

I would start with three examples. Faced with a file with packed decimal, I would keep the bytes and the copybook, implement the codec and test limits before normalizing storage. Faced with two concurrent debits, I would fix the transactional unit and an overdraft test before deciding whether actors are involved. Faced with a missed batch window, I would analyse the critical path and the skew before adding workers. The pattern comes after the property we want to preserve.

Platform proposals express capabilities, not automatic equivalences between products. A local broker can implement per-key order; an Azure option can use sessions if its contract fits. A local database and a managed service can protect a transaction, but they must be compared against the real isolation, persistence and recovery policies.

Nor should an actor, CQRS or event sourcing become a mandatory destination. CQRS can separate a read projection from the write core; the projection needs a freshness and reconciliation policy. Event sourcing can provide a history of changes as the source of truth, but it requires event evolution, replay and validation. An append-only ledger is a more concrete domain decision: it can exist in SQL without adopting event sourcing for the whole application.

The lab includes the catalog in English, in JSON and Markdown (`risk-catalog/`), with the initial evaluation status and its relationship to the synthetic controls; Annex [E](../annexes/annex-e-catalog-of-one-hundred-risks.md) reproduces it. None of the hundred risks is marked as solved in production. That way we can use it as a working register and expand each entry when we have a real case.

Annex [E](../annexes/annex-e-catalog-of-one-hundred-risks.md) reproduces the full catalog, grouped into ten families: data and representations, money and time calculations, program flow and state, files and datasets, database access, transactions and financial messaging, batch and scheduling, integration and coexistence, performance and capacity, and SDLC, recovery and governance. Of the hundred, eleven are partially touched by a synthetic lab control; none is marked as solved in production.

## Closing an entry takes more than recognizing a pattern

To close R048 it is not enough to say the code acquires locks in order: the relevant histories must be run on the target engine, observing victims and retries and reconciling effects. To close R094 we must restore and recover under the conditions the service accepts. To close R099 we must show that the platform prevents delivering a different artifact, even if the builder tries.

This discipline turns the catalog into a practical link between archaeology, architecture and SDLC. We can start by keeping COBOL, replacing a capability or changing infrastructure. On every route the same question remains: what evidence shows that the new combination preserves the commitment we have decided to accept.

> **The pattern comes after the property we want to preserve.**

---

[← Chapter 35 · When I would NOT migrate](35-when-i-would-not-migrate.md) · [Contents](../README.md) · [Chapter 37 · The new modernization contract →](37-the-new-modernization-contract.md)
