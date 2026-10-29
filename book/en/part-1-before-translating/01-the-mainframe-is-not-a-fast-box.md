**English** · [Español](../../es/parte-1-antes-de-traducir/01-el-mainframe-no-es-una-caja-rapida.md)

[← Part I · Before translating](README.md) · [Contents](../README.md) · [Chapter 2 · The system we are trying to preserve →](02-the-system-we-are-trying-to-preserve.md)

# Chapter 1 · The mainframe is not a fast box

> [!IMPORTANT]
> **Chapter thesis.** A mainframe is a platform for execution, data, operations and control. If we only measure its processor, we still do not know what we are trying to replace.

There is a conversation I have heard far too often in modernization projects: "we have X MIPS; how many virtual machines do we need in Azure?". At first sight it looks like a capacity question. In reality it usually reveals that we do not yet understand the system we want to replace. The mainframe is a platform for execution, data, operations and control. Reducing it to a processor figure is like measuring an airport by counting only the thrust of its engines.

COBOL is the visible language. Behind it there may be CICS for transaction processing, IMS or Db2 for data, VSAM for indexed files, JCL to organize jobs, JES for batch execution, RACF for security, WLM for priorities, and recovery, queuing, journaling and observability systems that have been evolving for decades. Not every system has all of these components. That is precisely why the first task is to inventory what exists, not to draw the cloud solution we would like to sell.

A CICS application is not a COBOL program with an HTTP endpoint in front of it. It may rely on units of work that jointly commit changes to recoverable resources. `SYNCPOINT` marks that commit or rollback boundary [16]. Db2 applications also depend on isolation levels, locks, access plans and the particulars of concurrent processing [37]. If an agent translates a `READ UPDATE` and forgets the guarantees that came with that access, the new program will compile. It may even pass the first hundred tests. What we will have lost is the property for which the bank trusted the old program.

The platform also includes how work is organized. A batch process is not necessarily "a big loop". It may be chained to closing windows, checkpoint states, sorts, reconciliations, dependencies and recovery mechanisms. Some jobs must finish before a branch opens and others must coexist with online operations. Moving them to a cron job in Kubernetes without mapping those dependencies is a conversion of commands, not a modernization.

The distinction matters because a program can be simple and its execution complex. Calculating interest may take a few lines. Doing it for millions of accounts, exactly once per period, with business calendars, restarts and reconciliation, is a complete system. Preserving it requires designing both the economic invariants and the operation that protects them.

## Four layers of equivalence

I propose separating four obligations: **functional equivalence** (the same decision and result under the same rules); **data equivalence** (the same meanings, amounts, encodings and persistent effects); **operational equivalence** (recovery, security, windows, observability and failures); and **capacity adequacy** (meeting latency, throughput, cost and resilience targets). They are different gates. Passing one does not pass the others.

The new solution may be functionally equivalent and perform worse. It may also process three times as many operations and lose a cent through a different rounding. In neither case are we done.

![Figure 1.1 · Four different obligations. Passing one does not pass the others.](../../figures/en/layers.png)

*Figure 1.1 · Four different obligations. Passing one does not pass the others.*

Translated into a status meeting: when someone says "it's already equivalent", the right question is *in which of the four layers, with what evidence and within what scope?*

> **Measuring a mainframe by its MIPS is like measuring an airport by the thrust of its engines.**

---

[← Part I · Before translating](README.md) · [Contents](../README.md) · [Chapter 2 · The system we are trying to preserve →](02-the-system-we-are-trying-to-preserve.md)
