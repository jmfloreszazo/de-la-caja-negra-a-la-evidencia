**English** · [Español](../../es/parte-1-antes-de-traducir/04-lo-que-comparto-con-otros-autores-y-donde-discrepo.md)

[← Chapter 3 · Why one-to-one conversion is not modernization](03-why-one-to-one-conversion-is-not-modernization.md) · [Contents](../README.md) · [Chapter 5 · Modernizing means choosing which problem we solve →](05-modernizing-means-choosing-which-problem-we-solve.md)

# Chapter 4 · What I share with other authors and where I disagree

> [!IMPORTANT]
> **Chapter thesis.** The warning about lost knowledge is valuable. Turning it into a general impossibility is not: a probabilistic generator can feed a deterministic verification.

## A useful warning

After reading several authors, I find ideas I share. They propose protecting business knowledge, refactoring gradually and using AI to understand code that has become hard to maintain. They also question the promises of automatic replacement and stress the value of the specialists who know these systems. I share the need to examine those promises and to avoid a transformation destroying knowledge we still need.

The best of those texts also have a quality I want to keep: they state a thesis, connect it to stories and lead the reader towards a decision. A technical book can have a voice. It can argue. It can explain why a certain way of working worries its author. It does not need to become a sequence of slides.

My disagreement appears when a reasonable warning becomes a general impossibility. That uncontrolled automatic translation is dangerous does not prove that any AI-assisted construction is unviable. That a monolith depends on state does not make it incompatible with every cloud service. That many systems are poorly documented does not mean they lack analysable structure.

It pays to separate the problems in order to solve them. Language, runtime, architecture, data and operations introduce different constraints. If we treat them as a single incompatibility, we lose the ability to choose.

## The cloud does not force a single architecture

Microsoft's architecture documentation describes alternatives for running COBOL applications with compatible compilers and environments on Azure virtual machines or containers [5]. That documentation does not, on its own, validate a specific migration or its savings. It is enough, however, to question the general claim that COBOL and the cloud are incompatible.

Moving a workload may preserve couplings and constraints. It may also solve an infrastructure problem without rewriting the whole application. The decision must answer an explicit goal. If we want to reduce the time it takes to change a business rule, moving the same executable to another machine may not be enough. If we want to retire a specific environment, it may be a relevant piece.

Nor does a Java or C# target force us to distribute every transaction, eliminate batch or replace each function with a microservice. Those are architectural decisions. Mixing them with the language change adds variables to a transformation that is already hard to verify.

## A probabilistic generator can feed a deterministic verification

A model can produce incorrect code. So can a human. The engineering question is which mechanisms detect the error before the result is accepted, and what their limits are.

The probabilistic nature of the generator does not, by itself, determine the nature of the generated implementation. A compiled program can execute a deterministic rule. In turn, a deterministic test can be badly specified. That is why my proposal does not end at running tests: it requires examining who defined the expected result, where it comes from and which errors the evaluator can detect.

Here I extend the thesis of AI as a comprehension engine. Assisted comprehension is valuable, but it can also be wrong. An incorrect explanation of a rule can contaminate the specifications and every subsequent test. The useful line is not between letting AI explain and forbidding it to build. It is between proposing and accepting with adequate evidence.

## My position, in a table

For disagreement to be useful it has to be concrete. This is the comparison, point by point.

| Question | What is often argued | My position |
|---|---|---|
| AI to understand COBOL | Very favourable | Agreed, with evidence linked to each claim |
| AI to generate Java or C# | Very critical | Viable with constraints, a contract and independent validation |
| Keeping COBOL | Preferred option | Depends on the goal, the load and the cost of verifying |
| Incremental refactoring | Recommended | Agreed |
| Functional equivalence | Main risk | Must become a verifiable acceptance criterion |
| Private models | Recommended | Control of the data matters, not necessarily training your own model |

> **The useful line is not between letting AI explain and forbidding it to build. It is between proposing and accepting with evidence.**

---

[← Chapter 3 · Why one-to-one conversion is not modernization](03-why-one-to-one-conversion-is-not-modernization.md) · [Contents](../README.md) · [Chapter 5 · Modernizing means choosing which problem we solve →](05-modernizing-means-choosing-which-problem-we-solve.md)
