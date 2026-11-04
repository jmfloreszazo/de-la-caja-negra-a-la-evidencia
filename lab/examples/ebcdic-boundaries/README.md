# EBCDIC boundaries: a fixed-record exercise

Run from the repository root with Python 3.12 or later:

```bash
python3 lab/examples/ebcdic-boundaries/run_checks.py
```

No SDK, model, container or network is required. The report is written to `lab/results/ebcdic-boundaries/observations.json`, including failures, exact source hashes, Python/OS and CI source/checkout/run identities. This exercise does not change the bank adapters, protected reference snapshots or printed listing labels.

## Contract and authority

The record has exactly 13 bytes: an eight-byte SBCS text label, three opaque packed-decimal bytes and an unsigned two-byte big-endian counter. Only the label is decoded. Preserve its four trailing spaces and the binary suffix. Packed-decimal arithmetic is deliberately outside this exercise.

`expected.json` fixes input hex and expected values independently of the decoder. Seven code-point pairs are transcribed from [IBM CCSID Comparisons, swg21197185](https://www.ibm.com/support/pages/ccsid-comparisons), modified 20 June 2019 and consulted 4 November 2026. These distinguish 37 from 500; they are not an exhaustive CCSID mapping. Other records and acceptance rules are synthetic exercise choices, not observed or approved bank contracts. Python's [codec documentation](https://docs.python.org/3.12/library/codecs.html) defines the selected codecs and strict/replace behavior.

The cases demonstrate:

- All fourteen documented code-point expectations and three fixed mixed records.
- Wrong-CCSID decoding can succeed and round-trip while changing meaning. `strict` does not detect a valid character decoded under the wrong mapping.
- Eight source bytes for `CAFÉ` plus padding become nine UTF-8 bytes. Source byte offsets cannot be reused blindly after conversion.
- Missing/unsupported CCSID, wrong length and forbidden text controls are rejected. This example supports only integer CCSIDs 37 and 500; unsupported does not mean invalid on a real host.
- Encoding the euro sign under cp037 raises under `strict`; replacement yields a question mark and loses information. Do not silently replace or ignore errors in a financial interface.
- Converting the whole mixed record changes binary data. Preserve field boundaries before text conversion; never split fixed records by a byte that merely resembles a newline.

Four deliberately wrong result transformations are rejected against the fixed expectations: wrong CCSID, stripped padding, transcoded binary and little-endian counter. They qualify these specific predicates, not arbitrary conversion correctness. The 256-byte round-trip loops are codec self-consistency checks; the documented vectors supply the separate meaning check.

## Reproduction boundary

The dedicated CI runs this Python exercise on hosted Linux, macOS and Windows and retains one original artifact per job. A successful Python job does not establish Podman-machine/WSL2 reproduction, native z/OS/Db2/MQ behavior, dataset framing, DBCS, transport conversion or a customer's selected CCSID. For a real interface, obtain authorized raw records and metadata, specify per-field encodings/lengths/signs/scale and transfer mode, then compare independently expected outputs through the actual host/transfer/destination path. Record substitutions, truncation, ordering and replay behavior. Those external checks do not block this bounded exercise.
