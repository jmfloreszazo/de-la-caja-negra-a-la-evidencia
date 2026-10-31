# Intent — new banking capabilities from approved business meaning

Status: SYNTHETIC DESIGN EXERCISE ONLY. No real bank authority or production acceptance.

Implement two capability hypotheses from #32 and PR #51:
- CAP-007: internal transfer with stable operation ID, two balanced financial effects, insufficient-funds and authorization refusal, duplicate replay and conflict detection.
- CAP-005: distinguish authoritative booked balance from a potentially delayed statement projection, with an explicit minimum version.

This is clean-room implementation from **business contracts**, not COBOL syntax, COPYBOOK structure, program translation, or mainframe-specific data layout. No source parser is involved.

The reference contract is an intentionally tiny scenario file with a *manually specified* expected answer. A Python Oracle Gate independent of .NET checks the candidate's complete output and accounting invariants. Deliberately mutated outputs must be rejected.

Decision authority: business owner and approved institutional policy **missing**. The sample behavior is a plausible design hypothesis, not a requirement or a legacy behavior observation.

Boundary: the first .NET 10 prototype is **sequential and in-memory**. No durable COMMIT, ACID guarantee, real authentication, authorization provider, distributed idempotency, recovery after restart, actual projection bus, load/performance or production clearance is demonstrated. The lost-reply scenario is explicitly `UNKNOWN_AFTER_APPLY`, **not** `UNKNOWN_AFTER_COMMIT`.

Next safe implementation step after owner review: PostgreSQL transaction authority with operation-ID uniqueness, postings and outbox under one SQL transaction; add failure-injection after commit, independent SQL oracle, bounded open-loop load, and an actual read-model consumer with watermark. Do not reuse synthetic in-memory outcomes as evidence for those later claims.
