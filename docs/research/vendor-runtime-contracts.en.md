# Vendor runtime contracts: what survives a brownfield replacement?

[Español](vendor-runtime-contracts.es.md) · [Source catalog](../../research/vendor-runtime-contracts/catalog.json) · [Chapters 1](../../book/en/part-1-before-translating/01-the-mainframe-is-not-a-fast-box.md) and [13](../../book/en/part-4-patterns/13-before-choosing-a-pattern-identify-the-contract.md).

**Research cut: 4 November 2026 · #17/#18/#28 · NOT native-platform execution or bank acceptance.** This is a bounded **11-record/10-reference increment**, not the full manufacturer matrix, full 236-entry plan or universal IBM-to-cloud equivalence. Exact hardware model, OS and data engine installed at the customer are unknown. Source dates and retrieval limits are explicit. IBM Docs links were indexed but returned HTTP 403 for direct reading; Unisys technical pages and the archived Fujitsu announcement were readable. Consequently source scope is attached to individual claims, never extrapolated.

## A source-first interview, not "how many vCPUs per MIPS?"

Ask operations and architecture jointly for the inventory: manufacturer/model/year and actual firmware, CPC/LPAR or partition topology, OS and version, monitor and UOW boundaries, transaction/data stores, security IDs, batch/JCL/job scheduler, external effects, logging and recovery, storage channel/queue paths, WAN channel and terminal behavior, service classes/CPU delay, source record encodings, and support/licensing evidence. For each subsystem request an **authorized incident/restart trace**, representative normal and peak windows, measured p50/p95/p99 for **complete business operations**, I/O queue and log durability, RPO/RTO, source retention and handoff position, and owner of every writer. Don't put bank data or secrets in the public laboratory.

### Platform attribution matrix

| Platform / documented source | The real observable boundary | Candidate pattern (not equivalence) | Blocking observation |
| --- | --- | --- | --- |
| IBM Z CSS, PR/SM and z/OS WLM; indexed [CSS](https://www.ibm.com/docs/en/zos-basic-skills?topic=mainframe-channel-subsystem-css) and [WLM](https://www.ibm.com/docs/en/zos/3.2.0?topic=tabs-service-classes) documentation | Central CPU, partition dispatch, service goals and asynchronous channel I/O are **separate** facilities | Bounded admission queues, storage/failure-path measurement, horizontal scaling only after load attribution | Under CPU pressure or log-path failure, individual online-class p99 remains unproven |
| Db2 for z/OS 13; indexed [ISOLATION bind option](https://www.ibm.com/docs/en/db2-for-zos/13.0.0?topic=services-isolation) | UR/CS/RS/RR isolation, SQL locks and transaction commit; package bind options affect behavior | SQL unit of work + explicit retries, same-boundary ledger, independent concurrent oracle | A candidate reads uncommitted or changes balances under a prohibited schedule |
| IBM i 7.6; indexed [commitment control](https://www.ibm.com/docs/en/i/7.6.0?topic=database-commitment-control) | Job/activation group and journaled resource boundaries; not Db2 z/OS or CICS | Source-authoritative projection, application transaction and journal-position reconciliation | A job crashes but incomplete entries survive on destination |
| Unisys MCP 21.0; [EDB Access](https://www.support.unisys.com/aseries/docs/ClearPath-MCP-21.0/38508198-005/section-000081944.html) | Access defines ordering and retrieval over physical record sets | Typed ACL, ordered key semantics, replacement DB with differential selection | SQL index yields different record order, duplicates or recovery results |
| Unisys OS 2200 ePortal TIP 10.0; [configuration](https://www.support.unisys.com/ePortalIC-10.0/topic/82073594_clearpath_eportal_developerhelp/html/section-000039403.htm) | Optional reconnect/resend on send error can be unsafe for *stateful* host processing | Operation-ID idempotency + durable status lookup; channel retry policy | Host COMMIT succeeds, ACK is lost, retry creates a second posting |
| Fujitsu GS21 3600/3400; [2018 archived vendor announcement](https://info.archives.global.fujitsu/global/about/resources/news/press-releases/2018/0417-01.html) | Historical models were announced; installed MSP/XSP, data engine, batch format and support **unknown** | RETAIN + verify model/OS/manual and approved coexistence options | Proposed CICS/Db2 or generic CDC mapping without customer inventory |
| NEC ACOS / Bull GCOS (unspecified installation) | **NOT_VERIFIED**, not necessarily absent | RETAIN, establish exact release and primary manual first | Any feature assertion or “unsupported” label without evidence |

**Do not combine IBM Z, IBM i and Unisys into one generic "mainframe platform" row.** MCP and OS 2200 are distinct OS/runtime/data families; even the same vendor can impose different restart, data and messaging semantics. The Fujitsu press release is **historical product evidence**, not a technical manual or proof of present availability.

## End-to-end financial request trace (to pre-register with the client)

```text
Remote branch / ATM / mobile
    -> WAN / channel or card switch / authentication
    -> host ingress, admission and priority
    -> transaction monitor / durable operation identity
    -> Db2/EDB/IMS/VSAM or other actual data engine
    -> lock / access path / index / buffer pool
    -> log + durable COMMIT (ownership boundary)
    -> MQ/external payment/cash effects and reconciliation
    -> response, acknowledgement, client retry/status inquiry
```

For each trace record at least operation ID, source epoch, subsystem/version, start/end timestamps (synchronized and monotonic caveats), commit decision, retry attempt, log position, delayed side effects and known/unknown outcome. The complete request p99 must be measured from correlated **requests**, not manufactured by adding disparate per-hop percentiles. The chain is an illustrative *questionnaire*, not a measured trace or a universal banking topology.

## Three positive designs with equally important refusal paths

**Read-heavy:** source balance/booked-balance read, scoped cache and projection. Quantify read/write ratio, miss share, read age, snapshot/log lag and fallback. Refuse a projected balance as spendable or a clock sample as linearizable. Existing W01 PostgreSQL PASS is synthetic, not Db2/IBM i throughput.

**Write-heavy:** internal transfer with two postings, outbox and one durable writer authority. Measure hot-account contention, lock/commit latency, log flush and parallel retries. Refuse a two-actor saga that posts one side before the other if the business contract requires immediate atomicity.

**Channel/recovery:** OS 2200 TIP or CICS/IMS application with response lost after host COMMIT. Track stateful connection, operation ID, source journal and duplicate effect controls; do not treat a transport retry or 202 Accepted as proof of a financial decision.

A system may rationally **remain** on the original platform if its necessary UOW semantics, physical dependencies or recovery evidence cannot yet be replaced safely. A smaller hybrid ACL and read-only integration may deliver value without claiming full cutover.

## Reproducible metadata gate

`python3 scripts/check_vendor_runtime_contracts.py --self-test` executes **25 catalog integrity/negative cases**. The validator refuses missing vendor/version/source, cross-vendor source refs, invented publication dates, blank failure/oracle, self-approval, fabricated native experiments, unsupported “no” and promotion of the Fujitsu 2018 press announcement to a feature parity claim. It does not run COBOL, perform source archaeology, test vendor CDC, estimate hardware or approve migration. See the English-only [catalog README](../../research/vendor-runtime-contracts/README.md).

**Follow-up owners:** #17 deeper CPU/memory/I/O and measured trace + paired architecture figures; #18 more documented vendor families and red flags; #28 complete functional/capability coverage, batch/offline/interoperability and 236-category target only after evidence; #58 real bank source/fencing proof. #53 remains frozen. TODM **G2 INCONCLUSIVE / G6 BLOCK** for all synthetic/original-customer claims in this dossier; no new release.
