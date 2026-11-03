# E2 · Live positive calibration of the activation observer

**Calibration only; ordinary AccountGrain partition concurrency remains open.**

[Original run #41630777280](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41630777280),
job 125899472499, exact source/checkout `75dfccb8513d38f7fa70386be47c64014a981996`.
This adds a separate diagnostic grain with `StatelessWorker(maxLocalWorkers: 2)`
and a bounded pre-ledger two-party barrier. Multiple activations are deliberately
allowed by this test type. The accepted AccountGrain and ledger are unchanged.

| Original case | Actual observation | Durable SQL effect |
| --- | --- | --- |
| Single request, fresh process/database | Expected barrier timeout; one BEGIN/ERROR; zero overlap | 0 operations / 0 postings / 0 outbox; 7/7 invariants |
| Two requests, fresh process/database | Two distinct actual activation IDs, same diagnostic grain key; 197.293967 ms envelope overlap | 1 operation / 2 postings / 1 outbox; 7/7 invariants |
| Replay / conflicting payload | DUPLICATE_COMMITTED / ID_CONFLICT | No additional effect |

The contested ID committed amount 37; amount 31 received ID_CONFLICT. Complete
accounts/postings/outbox snapshots independently match the winner. The original
returned results are also reconciled with SQL by the offline checker. The
negative is a sensitivity control, not an accidental infrastructure failure.

The [versioned summary](e2-activation-calibration-original.json) is reproduced
from the exact JSON payload written by the original driver to stdout and
`summary.json`. Git blob identity: `0c65ed626a5edbf211116235ef3b673b10819751`.
The [offline audit](../../scripts/check_e2_activation_calibration.py) freezes
those bytes, verifies all 39 source hashes against the original Git commit,
recomputes log envelopes and independently checks every persisted row and ACK.
The complete CI artifact 13228386871 is 15771 bytes; GitHub reports ZIP SHA-256
`a0a52f20d7a417a677a8a8b8b39daea75c2688c30bf9a9d85bf9c82e58a9e6c8`.
ZIP metadata is recorded; a byte-level audit of that ZIP is not claimed here.

This is one silo/process on one physical host, with an in-process Orleans
client and disposable PostgreSQL. The positive overlap is an invocation
envelope, not simultaneous SQL COMMIT or a benchmark. It calibrates detection
of real, intentionally multiple diagnostic activations. It does not show
concurrent ordinary AccountGrain activations during C05/F10 partition, natural
split brain, actor exclusivity, physical HA or bank acceptance. E2 stays partial.

[Español](E2-ACTIVATION-CALIBRATION.es.md) · [Protocol](../../lab/e2_activation_calibration/README.md)
