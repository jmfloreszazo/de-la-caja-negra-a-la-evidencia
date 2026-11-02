# C2 · Controller TCP loss during a financial operation

**Bounded synthetic evidence; 2 November 2026. #64/#58 remain open.**

[Original run #41511782428](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41511782428),
job `125505163428`, executed protocol `C2_INFLIGHT_CONTROLLER_TCP_LOSS_V1`
on source/checkout `bfa0ed55e5097b6341ac4f9f01e6b4f712d0fb6c`.
The earlier 20-control C2 matrix passed before this separate new experiment.

- [Unmodified original ZIP](brownfield-c2-controller-loss-original.zip):
  artifact `13173950917`, 6494 bytes, SHA-256
  `89fb5b8ba2a2937829ec6f65527524158e321bdb26620e5f027573d51ddaa230`.
- [Unchanged JSON extracted from the original](brownfield-c2-controller-loss-original.json).
- Recomputed ZIP digest matches GitHub; all ten source hashes match the tested
  implementation. The ZIP preserves provenance, build and preceding results;
  it is not a reconstruction from logs.

## Observed results

| Observation | Python legacy | .NET 10 candidate |
| --- | --- | --- |
| Independent financial wait before cut | PID 543, Lock/advisory in INSERT | PID 685, Lock/advisory in INSERT |
| Lost controller session | PID 73 disappears | PID 109 disappears |
| Active TCP connections cut | 2 | 2 |
| Externally terminated gateway | SIGKILL, -9 | SIGKILL, -9 |
| Decision while financial operation remains uncommitted | UNKNOWN | UNKNOWN |
| Writer-switch attempt under uncertainty | BLOCK | BLOCK |
| SQL reconciliation after releasing barrier | COMMITTED | COMMITTED |
| Decisions / postings / outbox | 1 / 2 / 1 | 1 / 2 / 1 |
| Independent source/target oracles | 10/10 and 10/10 | 10/10 and 10/10 |

## Meaning and limits

The relay closes active TCP sockets and refuses reconnects; SQL confirms
previous sessions have disappeared. A test trigger pauses the transaction
after account updates and before INSERT/COMMIT: an independent session sees
the wait and no persisted decision yet. The financial operation can commit
after losing its controller session. **Losing a remote lock does not cancel
financial COMMIT.** The observed safety depends on persisted UNKNOWN,
cutover veto and reconciliation before replay, without duplicate effects.

These are two cases on one runner with a test barrier and relay. No silent
blackhole, asymmetric partition, all timing boundaries, real CICS/Db2 fence,
physical domains, external payment effects, capacity, RTO/RPO or bank-approved
policy is established. G2=INCONCLUSIVE; G6=BLOCK. Later SHAs require their own
CI; this original does not validate them.

[Español](BROWNFIELD-CONTROLLER-LOSS.es.md) · [Reproduction protocol](../../lab/brownfield/journal/README.md)
