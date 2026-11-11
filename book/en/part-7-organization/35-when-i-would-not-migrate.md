**English** · [Español](../../es/parte-7-organizacion/35-cuando-no-migraria.md)

[← Chapter 34 · Measuring what we do not yet know](34-measuring-what-we-do-not-yet-know.md) · [Contents](../README.md) · [Chapter 36 · A hundred risks for choosing patterns with judgement →](36-a-hundred-risks-for-choosing-patterns-with-judgement.md)

# Chapter 35 · When I would NOT migrate

> [!IMPORTANT]
> **Chapter thesis.** Keeping the mainframe, improving it or combining it with new systems are legitimate decisions if the data justifies them. A well-governed hybrid architecture can be more modern than a reckless full rewrite.

Modernization does not mean everything must leave the mainframe. Some systems have stable workloads, reasonable support and well-understood guarantees that do not justify a move. In those cases I would invest first in observability, automation, documentation and governed exposure of capabilities. An assessment must be allowed to conclude **“do not migrate”** and explain why that better protects the business.

I would not migrate a critical ledger without access to operational profiles and without an environment where equivalence and recovery tests can be run. I would not make an irreversible cutover while unidentified writers coexist. I would not accept an SLA because a synthetic benchmark achieved a striking TPS. I would not split into microservices a process whose atomicity we cannot recover. I would not use actors to simulate a cross-domain transaction and call it safe. And I would not entrust the acceptance of a baseline to the same AI that generated the candidate.

It is not technological conservatism. It is a discipline of reversible decisions. Good modernization is the kind that lets us learn without taking hostage the system that pays salaries, settles operations or protects policies.

## Without dogma

| It makes sense to migrate a capability when | It does not when |
|---|---|
| There is a measurable business goal the current system prevents | The only argument is the age of the language |
| A behaviour and capacity oracle can be built | "Correct" cannot be defined verifiably |
| There is access to operational profiles and a test environment | There is no workload footprint or way to rehearse recovery |
| Data ownership can be transferred with a protocol | Unidentified writers coexist |
| The required atomicity is preserved in the target | A transaction the business needs to be atomic would have to be split |
| The cost of verifying is affordable compared with the benefit | Verification costs more than the problem it solves |

> **Not migrating must also be a documented, measurable and revisable decision.**

---

[← Chapter 34 · Measuring what we do not yet know](34-measuring-what-we-do-not-yet-know.md) · [Contents](../README.md) · [Chapter 36 · A hundred risks for choosing patterns with judgement →](36-a-hundred-risks-for-choosing-patterns-with-judgement.md)
