# W01 restricted source reader — PostgreSQL original evidence (4 November 2026)

[Español](W01-READER.es.md) · [Original W01 16-test checkpoint](W01-PROJECTION.md) · [PR #93 merged](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/93)

## Exact bounded outcome

**`PASS_BOUNDED_SYNTHETIC_TESTS`: 20/20 tests on real PostgreSQL 16.13, two independent database clusters on ONE GitHub-hosted runner.** Four new tests improve on the original 16-case experiment without rewriting its original evidence or changing its SHA.

- Original [W01 source-reader Actions run #41855993179](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41855993179), job `126664633712`.
- Original PR-head source/checkout SHA `fc248c0ba72f40ac797b407dac818d2e1ad7219e`, merge SHA `0894478ddbc2733e1fcffbd44c4b5b1137ed06db`.
- GitHub artifact ID `13336738360`, `w01-postgresql-synthetic-original-not-bank-approved`, 2,838 bytes, published archive digest `sha256:8a8b036c2ac47d73a4a065e73bf1b7484a41be0fa39a77b71f37d75c25b1831f`, expires 2 February 2027. The checksum is GitHub artifact **metadata**, not a statement that this report independently recomputed ZIP bytes.
- Permanent [selected verbatim original CI lines](W01-READER-PR93-ORIGINAL-CI-EXCERPT.log) and [machine-readable log-transcribed result/artifact metadata](w01-reader-pr93-original-ci-summary.json). These are **not** the full CI job logs or an immutable copy of the ZIP original.

## Independent negative controls observed

| Case | Observation |
| --- | --- |
| SQL DML denial | `w01_reader` UPDATE of `legacy.accounts` fails at PostgreSQL with `42501 InsufficientPrivilege`, even after `SET TRANSACTION READ WRITE`; UPDATE of the source clock and SELECT on withheld transaction history are also denied |
| Privileged credential refusal | Projection refuses a `postgres` superuser as the source role; connection identity and effective database privileges are checked, not just a DSN string |
| Isolated reader CLI | A separate subprocess executes with `W01_LEGACY_DSN` for `w01_reader` and no test-admin DSN in its environment; receives an explicitly nonspendable source fallback |
| Destructive fixture safety | Both exact loopback/admin database targets are verified *before* either disposable schema can be dropped; malicious/nonloopback DSNs are rejected with source unchanged |
| Historical behavior | Previous 16 tests still pass: snapshot watermark, stale projection fallback, corruption, same-clock privileged source mutation detected at **refresh**, regression, failures, ledger oracle and topology |

**Strict claim:** The *reader's PostgreSQL privileges* prevent writing to the two protected financial tables in this synthetic fixture. The **test process** itself still has superuser credentials so it can reset data and generate synthetic financial writes; production isolation of admin secrets is **not** proven.

## What is not proven

No real COBOL/CICS/IMS/Db2 role mapping, no enforcement against a privileged bank source writer, no unbypassable clock/cutover fence, no linearizable balance, no CDC, physical HA, production load, customer-authorized Golden Master or business policy. A clock-only read can still miss an unversioned source edit and a post-clock-sample COMMIT; the original [W01 source audit](W01-PROJECTION.md) retains those limitations. This test is **not** a banking acceptance.

**TODM G2 `INCONCLUSIVE` / G6 `BLOCK`**; #32 and #58 remain OPEN, E2 #8 administratively CLOSED, #53 frozen. No deployment approval or book release. See [EN implementation note](../../docs/research/w01-reader-identity.en.md) and [ES](../../docs/research/w01-reader-identity.es.md).

## Complementary PR-head workflows

Premerge, Brand artwork, Lab (offline/native/Podman) and the W01 run are all PASS on the exact PR-head SHA. [Book #41855993301](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41855993301) **fully completed SUCCESS** on the exact PR-head SHA: diagrams, Markdown and ES/EN links/sync all passed. This was independently observed after the original partial checkpoint. This follow-up did not modify diagram sources.
