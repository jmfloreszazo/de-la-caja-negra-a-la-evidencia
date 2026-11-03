# Editorial checkpoint — 3 November 2026

**English** · [Español](EDITORIAL_CHECKPOINT_2026-11-03.es.md)

This is a bounded technical/editorial review, not certification of native-level English or approval of a new release. Source baseline: main `3e0a949976391e0711795e8302afb63cb65bc045`. All source/language/book/evidence checks on that integrated checkpoint passed; Release was deliberately skipped.

## Corrections

1. Canonicalize 17 executable/configuration blocks to English in both editions and require exact ES/EN code equality in the existing language gate. Narrative diagrams/templates remain translatable. Structural fence counts alone previously missed translated comments and values.
2. Correct chapter 24's claim that the Foundry study isolated runtime. The primary source's “Qué comparo exactamente” and “Metodología” sections compare complete implementation stacks including SDK/serialization, with one request in flight and low offered rate. The revised book limits the inference accordingly.
3. Replace Annex A's ambiguous “Executed by design” label with reproduction commands and platform prerequisites. Add explicit A.2 and 25a.1 labels; inventory all 32 examples. Keep historical execution labels and original financial evidence unchanged.
4. Clarify conventions: syntax and helper checks do not certify the integration of a design fragment. Maintain explicit partial/untested scope.

## Primary-source revalidation

| Source | Book passage | Checked primary scope | Result |
| --- | --- | --- | --- |
| [45] [Foundry .NET/Python benchmark](https://jmfloreszazo.com/benchmark-dos-hosted-agents-mismo-foundry-net-10-lts-vs-python-3-12/) | Chapter 24, “From a useful benchmark to a misleading one” | Complete stacks; sequential light-load latency; no saturation measurement | Corrected runtime-only attribution in ES/EN |
| [44] [AHP article](https://jmfloreszazo.com/agent-host-protocol-ahp-por-que-el-host-y-no-tu-editor-es-el-dueno-del-estado-de-la-sesion/) | Chapter 8, session state versus modernization record | Host-owned session state and client views | Supports the session analogy; not independent evidence of banking approval authority |
| [1] [Leviathan/Autopilot](https://jmfloreszazo.com/de-leviatan-al-autopilot/) | Prologue and chapters 8/9 | Primary page was unavailable through the research reader in this review | Not revalidated; no unsupported correction or broken-link conclusion |
| [41] [Governed harness](https://jmfloreszazo.com/agentes-al-vuelo-frente-a-un-harness-gobernado/) | Prologue and chapter 29 | Primary page was unavailable through the research reader in this review | Not revalidated; remains pending |

## Targeted overlap matrix

| Passages reviewed | Shared theme | Distinct decision or evidence | Editorial action |
| --- | --- | --- | --- |
| Chapter 3 “The same example, in code”; chapter 17 “The transfer written for an engine with row locking”; chapter 28 “The contract is in the schema” | Transfers and locks | Lost reservation in a literal translation; proposed T-SQL transaction; actual SQLite lab and negative controls | Keep all three; do not confuse the proposed T-SQL fragment with executed SQL Server evidence |
| Chapter 10 “Three outcomes…”/“Testing the evaluator”; chapter 11 “A binding record”; chapter 27 “Equality can be misleading too” | Independent acceptance | Verdict semantics and evaluator attacks; pipeline responsibilities; actually executed equal-but-wrong mutation | Keep the separate criteria, not an automatic percentage cut |
| Chapter 9 “Correct is not the same as authorized”; chapter 31 “The evidence sheet…” | Authority | Business mandate versus review-time evidence binding | Keep; the sheet remains a template, not a real approval |
| Chapter 24 load methodology; chapter 28 diagnostic limits | Capacity caveats | Experimental design versus observed local admission results | Keep the scope warnings; correct the specific external-source inference |

This matrix reviews the named passages, not every sentence in the manuscript. Specialist English idiom review, complete bibliography revalidation and a book-wide overlap review remain pending. No broad passage deletion is justified by this sample.

## PDF baseline and final review boundary

The pre-edit PDFs are originals from run [41660337335](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41660337335), source `7a74a9f1cdc781b348d681fb7795202c064b68ad`. Book sources are unchanged between that source and the baseline main above. Artifact 13240919909 ZIP SHA256 `07cacdf66bb48d41767bdae86ae42cec747c049091bfbcb2d62c9619ba331d16` was independently downloaded and checked. ES: 144 pages, SHA256 `8fece6d9297fbbd97a9399032540138921cb44f78b7fb9e427baeb85d36df77e`; EN: 141 pages, SHA256 `7fc0477abdc4b63b6770552643500621433f81d4b7ba05e71e94e5607597d04c`.

Sample visual inspection covers EN contents page 2 and external-validation table continuation page 106, ES benchmark page 78 and external-validation table page 108. The inspected samples have legible text, repeated table headers and no observed clipping; they do not certify every page. ES page 78 makes the now-corrected runtime-only sentence visibly traceable. New PDFs must be built and sampled after the source corrections before this editorial cut can be considered visually reviewed. No baseline PDF is presented as the corrected output.

## Native execution and print adjustment

Original native run [41680741456](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41680741456), exact source `e8785e0a5c565e3b006c3d23feebc888130dce3b`, passed. The byte-identical ZIP and summary are committed under `evidence/editorial/`; ZIP SHA256 `9bff18d5ae6f44bcef890277d3afaa04bf98356f1eec04cb79b2e55b669f8cfa`. The independent `scripts/check_book_listing_observations.py` audit verifies all 43 original source hashes, 58 individual COBOL outputs and raw C# outcome. Tools: .NET SDK 10.0.403, GnuCOBOL 3.1.2.0 and Python 3.12.16 on hosted Linux.

The first corrected PDF sample still splits short code blocks at the page foot (for example the chapter 24 simulation begins with only two output lines). The print stylesheet now requests keeping a listing together when it fits on one page. A new render and visual check are pending before accepting that print change.
