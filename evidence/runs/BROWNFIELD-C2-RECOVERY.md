# C2 follow-up · SQL enrollment and interrupted authority recovery

**Bounded engineering evidence, 1 November 2026; not complete #64 acceptance.**
Original [CI #41352470918](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41352470918),
job `124985443092`, passed **19 controls** on exact checkout/source SHA
`3dd279c682ece00dfe62e68f68b1e4b967c4d333`.

- [Original ZIP](brownfield-c2-pr69-original.zip), retained byte-for-byte:
  artifact `13101916329`, 4088 bytes, SHA-256
  `f1ed8582f1e0bea5ef98fe723ec63d1748cb918b9f34c0f1cbb041bd7aa488c1`.
- [Original summary JSON](brownfield-c2-pr69-original-summary.json), extracted
  unchanged from that ZIP. The archive also contains build/provenance logs
  and all six concurrent same-ID responses.
- [First failure observation](brownfield-c2-pr69-first-failure.json): original
  [run #41352306908](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41352306908)
  failed its concurrent-response assertion. Its log did not print individual
  replies. Source inspection identified release of the operation lock before
  independent finalization; retaining that lock corrected the observed test.
  The failed run is preserved, not relabeled PASS.

The successful run includes controller-address guards, persistent enrollment
with environment opt-out refusal in both adapters, concurrent idempotency,
SQL recovery after lost ACK, journal corruption, actual external SIGKILL,
stale replay, missing outbox, epoch corruption and candidate rollback veto.

| Parent SIGKILL boundary | Persisted controller | Persisted candidate authority | Prepared intent |
| --- | --- | --- | --- |
| After preparation | legacy / 1 / SWITCHING | legacy / 1 | legacy/1 → candidate/2 |
| After candidate authority COMMIT | candidate / 2 / SWITCHING | legacy / 3 | candidate/2 → legacy/3 |

Both killed processes returned **-9**. The second transition rehearsed reversal
before any candidate-origin decision. Recovery reconciled the exact intent;
an unexpected epoch or removed outbox prevented thawing. The final epoch was 4.
A later candidate-origin decision then blocked rollback.

The final journal audit is deliberately **false**: `J-ADMIT-DEAD` and
`J-DISPATCH-DEAD` remain unresolved, and a balanced privileged raw-SQL posting
`J-RAW-SQL` is unjournaled. Both persisted-ledger oracles passed. The experiment
passes only if these unsafe cases are detected; it does not approve cutover.

Later test-only changes add a standalone enrolled-switch refusal control and
broader source hashes. They require their own exact-HEAD CI; these 19-control
bytes are never rewritten to claim later coverage. Original implementation
hashes remain inspectable in the summary and source commit.

**Limits:** three PostgreSQL containers on one runner; cooperative enrolled
adapters, not a real incumbent fence or atomic distributed COMMIT. In-flight
controller partitions, physical failure domains, external effects and owner
policy/mandates remain unverified. G2=INCONCLUSIVE, G6=BLOCK; #64/#58 remain
open, #53 frozen, and no release/tag changes.

[Earlier C2 evidence](BROWNFIELD-JOURNAL.md) · [Protocol and reproduction](../../lab/brownfield/journal/README.md) · [Español](BROWNFIELD-C2-RECOVERY.es.md)
