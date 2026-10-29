**English** · [Español](../es/00b-prologo.md)

[← Conventions](00a-conventions.md) · [Contents](README.md) · [How to read this book →](00c-how-to-read-this-book.md)

# Prologue

> A translation can preserve the instructions. A modernization must preserve the guarantees that make the business possible, and change whatever prevents it from evolving.

There is a scene that sums up much of today's conversation about modernization. An agent receives an old program, produces a version in a modern language and runs a demo. The application starts. The screen responds. The examples come out right. Someone asks how long it would take to do the same with a company's system.

My first question would be a different one: what have we just demonstrated?

It is not a way of belittling the result. It is the question that lets us give it a value. We have shown that a tool can produce an implementation that passes certain examples under specific conditions. To move forward we need to identify those conditions, check what is left outside and decide who has the authority to accept the risk that remains.

I'll give away the conclusion without ceremony: **AI can investigate, propose and build; accepting the result requires contracts, independent oracles and explicit authority.** And there is a second conclusion, which took me longer to put into words: **a 1:1 modernization can be a bridge, but we should never mistake the bridge for the city we want to reach.**

This book was born from that distance between a technical possibility and an architectural decision. It brings together three lines of work I have been developing: application modernization, building with AI agents and governing software through independent evidence. My proposal, the Test Oracle-Driven Methodology, or TODM, tries to turn that relationship into a process that can be inspected, executed and discussed. I have been developing it in public: in the TODM repository [2], in "From Leviathan to Autopilot" [1], in "Agents on the fly versus a governed harness" [41] and in my analysis of REA, "Beyond the hype" [35].

COBOL is a particularly useful case for doing so. It forces us to talk about data, precision, contracts, operations and business knowledge. It does not let a migration hide behind a more attractive interface. If the balance is wrong, having calculated it with a recent framework is little consolation.

Reading several authors on COBOL modernization and AI helps frame the problem. Their defence of accumulated knowledge deserves attention. So does a discussion of the line some of them draw between what AI can understand and what it can transform. In these pages I take that discussion seriously and turn it into verifiable decisions.

Capacity is also part of this discussion. We must preserve transaction atomicity, understand locking and sustain the load with the agreed durability and recovery policy. A bigger server or more actors only help if they address the resource that constrains that commitment.

The journey ends in code. The lab follows a small COBOL service from local execution to comparison with a .NET 10 implementation. It includes deliberate errors, incomplete evidence and a delivery blocked even though the behaviour is correct. Its size makes the mechanism understandable. Its explicit scope prevents anyone from mistaking it for a finished enterprise migration.

I want readers to be able to reproduce the demonstration and then ask better questions of the next one. How easy it is to run the example should help us see the real difficulty more clearly.

---

[← Conventions](00a-conventions.md) · [Contents](README.md) · [How to read this book →](00c-how-to-read-this-book.md)
