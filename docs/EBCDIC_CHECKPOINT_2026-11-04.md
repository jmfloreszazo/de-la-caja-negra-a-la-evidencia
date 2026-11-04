# EBCDIC/CCSID: bounded evidence checkpoint

PR #88 delivers the bounded #11 exercise: 36 checks and four rejected result transformations on each of three operating systems. Original run [41801198131](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41801198131), source and checkout `3783f94249b3d3e3efd36096ec029b795eda2648`, passed all three jobs on its first attempt. The ZIPs remain unchanged; no earlier failures are invented.

| Runner | Python | Artifact | ZIP SHA-256 |
| --- | --- | --- | --- |
| ubuntu-24.04 | 3.12.15 | [13306629254](../evidence/editorial/ebcdic-original-ubuntu-24.04.zip) | `3b4e99e9909f3f0078fd957cfeabe2f4c0a190b644d4467a0a8cba032aa0839f` |
| macos-14 | 3.12.10 | [13307842169](../evidence/editorial/ebcdic-original-macos-14.zip) | `efb71552f14c7bdfa12d460a401b8026b247f86f955d1923c3d90cb579b8a362` |
| windows-2022 | 3.12.10 | [13307238043](../evidence/editorial/ebcdic-original-windows-2022.zip) | `474e11633fe7652d66157306c1ea28607441cb34805f6fd449fa0d2462220e0a` |

The [manifest](../evidence/editorial/ebcdic-original-manifest.json) preserves size, identity and observed platform. `python3 scripts/check_ebcdic_observations.py` verifies ZIPs, identities, the exact 36-case inventory, documented values, expected records, four altered results and three historical source hashes per job. A shallow checkout must fetch the original source first.

In Windows, the three observed source files have CRLF endings and backslash paths; their hashes differ from LF Git blobs. The audit verifies exactly LF→CRLF for that job and normalizes only the path separator when querying Git. It never rewrites original reports or labels these hashes as identical.

Chapter 12 and references [63]/[64] are paired ES/EN. The [exercise README](../lab/examples/ebcdic-boundaries/README.md) fixes synthetic authority, protocol, execution and limitations. Fourteen documented values supply an authority separate from the codecs; 256-byte round trips test only self-consistency. The four mutants are result transformations qualifying specific predicates, not tests of every possible converter.

This completes the bounded EBCDIC/CCSID kata substep. #11 remains open for other listings, full editorial review and full-lab macOS/Podman-machine and Windows/WSL2 reproduction. No native z/OS, Db2 or MQ conversion was executed; authorized real records, dataset framing, DBCS and the actual host/transfer/destination path remain unverified. The guide describes that validation without blocking this increment. No listing labels, protected financial sources, bank acceptance or release are changed.
