# Fast reading path · seven chapters

**English** · [Español](READING_PATH.es.md) · [Full book](../book/en/README.md)

This is a **reading path**, not an abridged edition or a substitute summary. It moves from the risk of syntactic migration to an evidence-based modernization decision.

| Order | Reading | Question it answers |
|---|---|---|
| 1 | [Chapter 3 · Why one-to-one conversion is not modernization](../book/en/part-1-before-translating/03-why-one-to-one-conversion-is-not-modernization.md) | What problem does changing the language actually solve? |
| 2 | [Chapter 6 · REA and archaeology that leaves a trail](../book/en/part-2-archaeology-and-authority/06-rea-and-archaeology-that-leaves-a-trail.md) | How do interpretations of the legacy become traceable evidence? |
| 3 | [Chapter 10 · TODM and the problem of accepting what we build](../book/en/part-3-oracles/10-todm-and-the-problem-of-accepting-what-we-build.md) | Who determines whether an output is correct? |
| 4 | [Chapter 17 · From mainframe locks to explicit concurrency control](../book/en/part-4-patterns/17-from-mainframe-locks-to-explicit-concurrency-control.md) | Which transactional guarantee must survive? |
| 5 | [Chapter 24 · The benchmark that counts: load, contention, failure and cost](../book/en/part-5-capacity/24-the-benchmark-that-counts-load-contention-failure-and-cost.md) | Why is a single vCPU figure not a MIPS substitute? |
| 6 | [Chapter 28 · Transfers, locks and failures, locally](../book/en/part-6-lab/28-transfers-locks-and-failures-locally.md) | Which controls can be executed and contradicted today? |
| 7 | [Chapter 37 · The new modernization contract](../book/en/part-7-organization/37-the-new-modernization-contract.md) | What evidence is required before deciding to migrate? |

## Runnable companion

The [laboratory](../lab/README.md) demonstrates specific mechanisms with GnuCOBOL, .NET 10 and SQLite. To run the independent offline checks without compilers:

```bash
python3 lab/tools/verify_offline.py
```

To run the full walkthrough with Podman on a supported system:

```bash
cd lab
bash scripts/run-podman.sh --auto
```

**Do not extrapolate:** local tests establish mechanisms and invariants, not mainframe-equivalent capacity. E1–E4 remain designed, not executed. Read the [evidence and editorial review register](EDITORIAL_REVIEW.md) before quoting performance claims.

To go deeper: chapters 12 (equivalence), 19 (actors) and 35 (when not to migrate).
