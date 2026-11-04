# W01 source-owned synthetic change journal (PostgreSQL / Podman)

**ENGLISH-ONLY CODE + RUNBOOK · issue #58 · W01 CAP-005 · NOT ACTUAL MAINFRAME CDC.**

This follow-up uses two **different** PostgreSQL 16.13 server containers on **one** GitHub-hosted Linux runner. It builds on the previous W01 20-case nonauthoritative read model without replacing its implementation, original evidence, user-visible booked-balance behavior or historical SHA.

## Transactional source contract

A *test-only* PostgreSQL ledger writer inserts a row into `legacy.balance_feed` **inside the same SQL transaction** that updates the source accounts, both financial postings, outbox and `legacy.clock`. The journal row carries a contiguous source sequence, operation ID, debit/credit accounts, amount, both before/after images, previous-row hash and a SHA-256 content digest. Sequences come from the source's transactionally updated single clock row, **not `BIGSERIAL`**: PostgreSQL sequences can have gaps from aborted transactions, so treating SERIAL values as gap-free commits would be incorrect.

The change reader is **a distinct `w01_feed_reader` login**. PostgreSQL grants it SELECT only on source balances, clock and journal, and explicitly no write privileges and no access to payments/transactions/entries/outbox. The test harness owns a **separate disposable administrator DSN**; a reader-only subprocess proves it does not require that secret. This does not prove real production process/secret isolation or the privileges of CICS/IMS/Db2/VSAM users.

## Initial snapshot, cursor and bounded replay

1. In one `REPEATABLE READ READ ONLY` source transaction read the source clock, all 16 account balances/revisions and the source journal. Validate the **entire bounded** (at most 256 events) synthetic history and before/after images against its fixture genesis. This is a **synthetic bootstrap oracle**, not an efficient bank-scale CDC snapshot or owner-signed snapshot cut.
2. Publish the 16 rows, journal head hash, snapshot digest and cursor to a **separate** `projection.feed_*` namespace under **one target SQL COMMIT**. Any new source transaction after the snapshot belongs to later catch-up, not the installed historical cut.
3. Catch-up reads a bounded batch of entries and the observed source clock from **one source MVCC snapshot**; reject holes, reordered events, broken previous hashes, modified after-images or a cursor regression. Verify the target's existing snapshot digest and source before-images. Publish target financial read rows and committed cursor **in one target transaction**; an injected failure before cursor COMMIT rolls it all back. Duplicate tail consumption is a no-op; an external event ID does **not** authorize duplicate source posting.
4. Independently audit the *bounded full historical sequence* and current source balances under a new source snapshot, comparing the result against the target when both have the same cursor. An unversioned privileged source edit or deleted old history is detected **when this explicit audit runs**, not automatically at every feed poll.

**Limit:** no physical source-and-target atomic commit, no native WAL/CDC connector, no log retention management, no external event delivery guarantee, no change-feed authenticity signature or privileged-writer fencing. A source account edit without updating the clock/journal may go unnoticed by a *tail-only* consumer until a full audit. Hashes can be rewritten by a privileged writer; they are **integrity checks, not trusted origin attestations**.

## Test commands (destructive only for dedicated fixtures)

**WARNING:** The harness executes `DROP SCHEMA`. It refuses unapproved DB identities and requires exact loopback ports, database names and `W01_DISPOSABLE=YES`. Never run with a customer, shared or production database. Credentials below are fixed throwaway fixtures only.

```bash
python3 -m pip install -r lab/e1_pg/requirements.txt
podman run -d --name w01-feed-source \
  -e POSTGRES_DB=bf_legacy -e POSTGRES_PASSWORD=bflocal \
  -p 127.0.0.1:55438:5432 docker.io/library/postgres:16.13
podman run -d --name w01-feed-target \
  -e POSTGRES_DB=bf_projection -e POSTGRES_PASSWORD=bflocal \
  -p 127.0.0.1:55442:5432 docker.io/library/postgres:16.13

export W01_DISPOSABLE=YES
export W01_LEGACY_ADMIN_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=postgres password=bflocal'
export W01_LEGACY_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=w01_reader password=w01readerlocal'
export W01_PROJECTION_DSN='host=127.0.0.1 port=55442 dbname=bf_projection user=postgres password=bflocal'
export W01_FEED_SOURCE_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=w01_feed_reader password=w01feedlocal'
export W01_FEED_TARGET_DSN='host=127.0.0.1 port=55442 dbname=bf_projection user=postgres password=bflocal'

# After both servers are accepting connections:
python3 lab/brownfield/w01_feed/test_feed.py
cat lab/results/brownfield/w01-feed/feed-original.json
# The test suite resets the source and target between its 22 scenarios.
# Its last negative case intentionally leaves a tampered source feed.
# Therefore a separate 'feed.py audit' after the whole suite is NOT expected
# to PASS without resetting a clean fixture. Check each test's actual outcome.

podman rm -f w01-feed-source w01-feed-target
```

## Negative scenarios and evidence

The test suite additionally exercises **eight concurrent writers on disjoint account pairs**, using a shared transactional clock-row lock to serialize each source offset/hash choice. This is correct within the fixture but an acknowledged **global contention bottleneck**, not a proposal for mainframe-scale throughput. It also rejects a semantically wrong before-image even when a privileged actor recomputes a syntactically valid event hash.

The test suite covers: empty and nonzero snapshot cuts; a source COMMIT crossing snapshot/install; catch-up with fixed batch and restart/no-op; journal gaps and missing historical rows; event tamper and valid-hash broken predecessor; target corruption; target rollback between row mutations and cursor update; source rollback before COMMIT; a privileged source mutation without clock; changes to the clock without journal; independently denied source reader writes and privileged DSN; historical deletion missed by tail-only consumers but detected by full audit; exactly paired financial postings and outbox (through the independent prior W01 oracle).

The dedicated [GitHub Actions workflow](../../../.github/workflows/w01-source-journal.yml) records the exact checkout/source SHA, container and image identity, Python version, source hashes, original log and per-case JSON in an artifact uploaded **even when tests fail**. Its 20-case gate *must* preserve `realIncumbentFence=false`, `clockReadsLinearizable=false`, `scalesToBank=false`, `todmG2=INCONCLUSIVE`, `todmG6=BLOCK`. A green job verifies **only this synthetic PostgreSQL journal** and no banking deployment acceptance.

Paired research and pending customer campaign: [ES](../../../docs/research/w01-source-journal.es.md) · [EN](../../../docs/research/w01-source-journal.en.md) · [source-side fencing](../../../docs/BROWNFIELD_SOURCE_FENCE.md).
