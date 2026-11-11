# Editorial record · Book narrative revision (10 November 2026)

**English** · [Español](EDITORIAL_RESTRUCTURE_2026-11-10.es.md) · [Book](../book/en/README.md)

## Editorial decision

The manuscript should read as José María Flores Zazo reasoning through an architecture problem, not as a sequence of GitHub delivery notes. The technical claims, adversarial observations and limitations remain. The narrative now follows **observed problem → architecture decision → evidence that could refute it → authority to accept**.

No executable versions or experimental records were altered. Synthetic banking stories remain labelled synthetic. Hosted CI does not certify mainframes, production bank networks or ATM devices.

## Reading arc

1. **Part I · Before translating:** understand the system and the guarantees the original runtime provides.
2. **Part II · Archaeology:** discover capabilities, hypotheses and source authority.
3. **Part III · TODM:** turn hypotheses into approved baselines, independent oracles and authorization.
4. **Part IV · Patterns:** replace responsibilities rather than source-program names.
5. **Part V · Capacity:** confront hardware, contention, network, recovery and total cost.
6. **Part VI · Laboratory:** run, break and verify bounded mechanisms.
7. **Part VII · Decision:** convert evidence into delivery practices, go/no-go, migration or coexistence.

The seven part openings now connect the argument in the first person. Chapter 32 keeps the fictional account story and distinguishes the demo, three design-changing tests and the resulting responsibilities.

## One canonical place for each idea

| Topic | Canonical chapter | Editorial change |
|---|---|---|
| Who owns writes | Ch. 16 · Data ownership | Clear writer authority, coexistence and rollback; no repeated Outbox tutorial |
| Outbox, compensation and financial boundaries | Ch. 18 · Distributing without breaking the books | Canonical implementation discussion; Chs. 16 and 21 link here |
| When Event Sourcing, CQRS and Sagas fit | Ch. 21 | Decision criteria, without repeating the mechanics of compensation |
| Orleans runtime versus service acceptance | Ch. 19 | Explicit distinction between runtime guarantee and required evidence |
| Investment and exit criteria | Ch. 33 | Starts with what could stop the migration |
| The right not to migrate | Ch. 35 | One home for the documented, revisable no-go decision |
| Capability-based mainframe decomposition | Part II companion chapter | Removes stale editorial-draft notice but keeps the synthetic scope |

### Experimental record moved without erasure

[Annex I](../book/en/annexes/annex-i-evidence-campaigns-and-limits.md) stores the details that used to interrupt the argument:

- **I:** banking channels: late advice, reversal, H01–H07, loopback TCP and a held ACK; previously channels sections 7–10.
- **II:** Orleans E2: C01, C04, C05/C06, long partitions, activations and directed probe; previously Chapter 28.
- **III:** brownfield C2: durable control, directional loss and reconciliation; previously Chapter 28.
- **IV:** B05 diagnosis, admission cohorts and external validation protocol; previously Chapter 28.

Original evidence links remain. **E1/E2 are not global PASS**; **E3/E4 remain bounded demonstrations without acceptance**; G2/G6 keep their conditional gates. Moving prose does not upgrade scientific claims.

## Voice and responsibility

This revision follows an architect presenting a concrete case, trying to disprove a claim and explaining a conditional decision. First-person judgement and runnable examples take precedence over formulaic summaries. It does not invent personal anecdotes, clients, metrics or production experiences for the author.

Laboratory code and original evidence were not changed. The only test modification is the reading-order assertion, updated to require Annex I after H; no validation has been disabled.

## Author review

This is an **editorial proposal in a pull request**, not an approved new edition. Priorities for review: Chapters 16/18, Chapter 21 versus channels, seven part openings, the Chapter 32 story and the size of Annex I. Temporary Actions PDFs should be inspected for continuity, layout, figures and tables. Merge and release publication require separate decisions.
