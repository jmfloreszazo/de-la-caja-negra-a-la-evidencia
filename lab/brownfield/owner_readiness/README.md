# Incumbent source-authority intake (CAP-005 / CAP-007)

This directory is an **English-only, synthetic structural readiness gate**. It does not contact a bank or read live COBOL/CICS/IMS/Db2. See the technical guidance in [English](../../../docs/BROWNFIELD_SOURCE_FENCE.md) and [Spanish](../../../docs/BROWNFIELD_SOURCE_FENCE.es.md).

## What it does

`assess.py` checks a proposed dossier for seven potential source-writer families, each explicitly classified as `UNKNOWN`, `IN_SCOPE`, or `OUT_OF_SCOPE`. Unknown scope is incomplete; out-of-scope needs an explicit owner-evidence reference; in-scope needs evidence references for an actual source-enforced fence, in-flight UNKNOWN resolution, same-ID replay, independent SQL reconciliation and external effects. An applicant may only declare URIs and SHA-256 digests, **not** supply proof that the corresponding content is true.

Possible output statuses:

| Output | Exit | Meaning |
| --- | --- | --- |
| `INVALID` | 3 | Input schema or self-declared authority is invalid |
| `NOT_READY` | 2 | Structurally valid but evidence or scope is absent |
| `READY_FOR_INDEPENDENT_REVIEW` | 0 | Declarations are structurally complete **only**; **NOT approved** |

**Every output**, including `READY_FOR_INDEPENDENT_REVIEW`, has `todmG2=INCONCLUSIVE`, `todmG6=BLOCK`, `productionApproved=false`, `realIncumbentFence=NOT_DEMONSTRATED` and `evidenceVerification=NOT_PERFORMED_DECLARATIONS_ONLY`. An arbitrary URI/hash can be forged or point to irrelevant evidence; the tool **never** validates its contents or signatures. Therefore **never** use exit code 0 as a G2/G6 release or bank-cutover permission.

## Run

From the repository root:

```bash
python3 -m unittest discover -s lab/brownfield/owner_readiness -p "test_*.py" -v
python3 lab/brownfield/owner_readiness/assess.py \
  lab/brownfield/owner_readiness/intake.example.json
# Expected NOT_READY, exit 2 (not a CI failure: the specimen has no customer evidence)
```

The unit tests include an artificial structurally complete dossier and deliberately falsified `todmG6`, missing writer family, duplicate family, unknown-but-present proofs, absent source-side fencing reference, bad digest, and unsupported family. No live test, credential, bank trace, or real customer identifier belongs here.

## How an owner actually proceeds

1. **Create a private copy** with a unique, non-secret system reference. Record only source-authorized evidence or immutable references; no private customer values in this public repo.
2. Enumerate online, batch, channel, offline, asynchronous, privileged and external-effect paths. Mark absence `OUT_OF_SCOPE` only with source-owner exclusion evidence.
3. For each in-scope path obtain externally audited negative proofs from the **incumbent enforcement boundary**, in-flight/UNKNOWN and epoch handling, financial and external-effect reconciliation.
4. Collect separately an authorized Golden Master and a business-owner **intended policy** decision; they are not interchangeable. The form's `ownerApproval` means a **reference to be reviewed**, not validated signature authority.
5. Submit the resulting package for **independent** source, business, security, finance and TODM review. Technical adequacy and G2/G6 acceptance must be established outside this structural gate and traced to immutable artifacts.

Because the current fixture is cooperative on one runner, a full bank cutover and any production approval remain **not demonstrated**. Tracked under [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58); the frozen [#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53) is untouched.
