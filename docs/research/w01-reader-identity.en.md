# W01 — Access control must be enforced by PostgreSQL, not by a Python convention

**Research/engineering note · 4 November 2026 · Issue #32.** [Español](w01-reader-identity.es.md) · [W01 original 16-case checkpoint](../../evidence/runs/W01-PROJECTION.md).

## Gap identified after W01

The first W01 run proved that `projection.py` uses `SET TRANSACTION ... READ ONLY` against the legacy PostgreSQL fixture. **It did not prove the application's connection identity was unable to write.** The source DSN used the `postgres` superuser in the original 16-test experiment, so an unintended write path, future code change or leaked credential could mutate source balances. A read-only SQL transaction is a *session property*, not a least-privilege security policy.

This follow-up strengthens only the **synthetic PostgreSQL** fixture. It does **not** demonstrate the real source environment is fenced, protect against privileged operators, or transfer this role model automatically to CICS/IMS/Db2/VSAM.

## Concrete design and tests

- Maintain the **source-owned** `legacy.accounts` and `legacy.clock` with their original financial ledger, operations, postings and outbox in `bf_legacy` on loopback port 55438. The reader must remain nonauthoritative; the candidate projection stays in a separate database `bf_projection` on port 55442.
- In the *test harness only*, bootstrap an unprivileged PostgreSQL login `w01_reader`. Grant `USAGE` on the `legacy` schema and `SELECT` exclusively on `legacy.accounts` and `legacy.clock`. Do not grant access to transfers, entries or outbox; do not grant `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `TRIGGER`, `REFERENCES` or schema `CREATE`.
- The application now refuses source DSNs without the exact `w01_reader` identity, or where the effective SQL login is superuser, can create roles/databases, bypasses RLS or holds any of the above financial modification permissions. This is a **runtime privilege inspection** plus an actual database denial, not merely a documentation requirement.
- Separate the disposable **test writer/admin** from the read application: a test-only `W01_LEGACY_ADMIN_DSN` creates schemas, posts a synthetic transfer and performs independent oracle queries. The application `projection.py` never imports or reads that environment variable; the isolated CLI test launches with an explicit *reader-only* environment. The test runner still possesses administrative credentials; that is **not** equivalent to production secret isolation.
- Negative controls attempt `UPDATE legacy.accounts` after `SET TRANSACTION READ WRITE`, `UPDATE legacy.clock`, and reads of withheld `legacy.transactions`; PostgreSQL must refuse these operations with `42501 InsufficientPrivilege`. Also reject an application source DSN configured as `postgres` superuser. The earlier 16 functional cases remain intact.
- Guard **both** disposable reset endpoints before any destructive `DROP SCHEMA`; a matching database name alone is not a sufficient safeguard. The end-to-end test only operates on exact database names, fixed loopback addresses and ports with explicit opt-in.
- Record negative outcomes, source/checkout SHA, original logs and result JSON via the dedicated W01 GitHub Actions job. Treat CI success as **bounded PostgreSQL least-privilege proof**, not a real bank cutover authorization.

## What this does not solve

A legitimate or malicious **privileged source writer** can still alter balances without incrementing the clock. The existing W01 tests show that the *next refresh* detects a same-clock mutation, whereas a clock-only query cannot detect it immediately. A source COMMIT can occur between clock sampling and reading projection data: the response remains **not linearizable**. The projection does not support streaming CDC, EOD semantics, independent physical failure domains, banking authorization, approved Golden Master, key management or SLO acceptance.

For a real mainframe migration, the client must prove that **all** online, batch, offline, privileged and asynchronous writing paths obey a source-owned accounting/version/fence contract, and that an independent reviewer can reconcile external effects. See [source-fence acceptance](../BROWNFIELD_SOURCE_FENCE.md) and [original W01 limitations](w01-projection.en.md). A role called `w01_reader` is a disposable laboratory stand-in and should never be used as a production identity or password.

**TODM G2 remains `INCONCLUSIVE`, G6 `BLOCK`; no global W01/banking PASS.** After the new head-specific CI is observed, link its job and original artifact here, without changing the historic 16/16 SHA or its proof.
