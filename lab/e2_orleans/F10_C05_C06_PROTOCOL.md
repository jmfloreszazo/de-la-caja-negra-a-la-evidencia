# C05/C06 — Directional silo packets, contested operation and recovery

Status: **bounded original CI verified**, run #41528812921 on source
`958961906de0ca5d3945d410c64d465ba7d34a3e`; see the
[audited paired report](../../evidence/runs/E2-C05-C06-DIRECTIONAL.md). Issue #24 stays open
for remaining activation/recovery acceptance. This does not accept overall E2.
Keep E2 partially_verified, G2 INCONCLUSIVE/G6 BLOCK, #53 frozen and release
identifiers unchanged. Do not infer activation exclusivity from this test.

## Fixed experiment and acceptance

Two fresh Ubuntu jobs independently block primary-to-secondary and
secondary-to-primary packets. Each job contains PostgreSQL 16.13, two Orleans
10.4.0 ADO.NET silos and one external client, in four distinct network
namespaces on **one physical host**. Record container IDs, actual host PIDs,
namespace IDs, runner identity, source/checkout SHA, all source hashes, image
IDs/digests and raw PASS or FAIL observations.

1. On the fixed private `10.78.30.0/24` fixture only, require two independent
   successful host-side SQL connections before reset. Require two Active SQL
   membership generations. Use the already verified C01 identity-only seeding
   to establish exact 8/8 account placement on IDs 1..16. Normal later financial
   calls use **no placement hints**. Commit baseline `c05-baseline` (1 to 2,
   11 cents), require 1 operation/2 postings/1 outbox and seven SQL oracles.
2. Capture management membership and detailed account-grain catalog observations
   through clients with a single fixed primary or secondary gateway. These
   APIs are from pinned Orleans 10.4.0 upstream
   `d114d7522a53b8cce4c6b97d44293e5c7273d766`:
   [IManagementGrain](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/src/Orleans.Core/SystemTargetInterfaces/IManagementGrain.cs)
   and [DetailedGrainStatistic](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/src/Orleans.Core/Statistics/SiloRuntimeStatistics.cs).
   Before and after the fault, require successful observation. During the fault,
   record unavailability explicitly. A catalog response is **not atomic**;
   missing/absent duplicate rows cannot establish exclusive or simultaneous
   activation. Keep the activation-exclusivity acceptance gate open.
3. In the designated silo namespace only, append an OUTPUT DROP for TCP
   packets to the peer with source **or** destination port 11150/11151. Leave
   both client gateway ports and PostgreSQL untouched. Save exact firewall
   rules and require the selected rule's packet counter to increase.
4. Start native, 45-second auto-stopping dumpcap observers sharing each silo namespace after injection;
   generate TCP SYNs in both directions. Preserve both original PCAPs and
   their decoded bytes/hash. Require packets from the unblocked host to reach
   the blocked host, and no selected-port packets from the blocked host to
   reach the unblocked host. **One-way packet loss can break TCP initiated
   from either side**, because TCP needs return traffic. Never call a pair
   of TCP timeouts proof of symmetric packet loss. SQL and gateways must
   remain independently reachable from both silos and the client.
5. Launch two external client processes concurrently, pinned to different
   gateways, offering `c05-contested-id` (2 to 1), with 31 and 37 cents.
   Observe acknowledgements or uncertainty. Each client allows 15s startup
   and 8s per RPC, then terminates; a parent timeout, crash, invalid JSON or
   failed injection is a test failure. Preserve ACKs immediately, without
   making a later identity request a condition for recording them. A
   dispatched timeout/exception is ambiguous; it **does not mean rollback**.
   SQL may contain zero or one contested operation during the cut. Every
   acknowledged COMMITTED/DUPLICATE/ID_CONFLICT must agree with SQL. Require
   exact posting/outbox cardinality and all seven independent oracles.
6. Restore the OUTPUT rules exactly to their recorded baseline. Record UTC
   and monotonic times, membership generations and subsequent outcomes. Allow
   30s to observe two Active running silos; if this does not happen, explicitly
   recreate **both** silo containers (preserving SQL and old generations).
   Record this as assisted recovery, never transparent healing. Require
   acknowledged stable-ID attempts through both gateways within a **240s
   experiment bound** from firewall restoration. Publish measured duration and
   recovery mode; neither is an RTO/SLA promise. Preserve all intermediate
   errors and any old Dead membership generation.
7. Reconcile the actual winning payload from SQL. Require identical-payload
   DUPLICATE_COMMITTED and different-payload ID_CONFLICT with no extra effects.
   Commit one new `c06-recovery-new` (1 to 2, 5 cents). Require exactly the three
   declared operations, 6 postings, 3 outbox events and 7/7 SQL oracles. Recheck
   SQL/gateway reachability and collect catalog observations from both gateway
   choices. Preserve all original failures before considering any correction.

## Limits and remaining gates

Fixed gateway selection isolates the client's ingress, not the executing
activation. Management views and catalog samples can be incomplete during a
partition. This experiment does not prove exclusive grain activation, fencing,
absence of split brain, independent physical failure domains, PostgreSQL HA,
production RTO/RPO, sustained saturation, mainframe MIPS or global E2 acceptance.
Accepted `AccountGrain`, its non-reentrancy, `Contracts.cs` and the authoritative
`PgDurableLedger.cs` remain unchanged. Unsafe actor-local patterns are excluded
from these financial routes. Publish paired ES/EN book interpretation only after
actual original CI and independent artifact/source audit.

## First original execution — setup rejection, not a partition result

Run #41527647221 on source `5a260594c159c109cccf49f2f9f8287a37d18e10`
failed in both jobs at the shared SQL readiness helper's case-name allowlist:
`AssertionError('c05')`. Orleans and the network fault were not reached.
The corrected helper only adds `c05` to that existing allowlist; it preserves
the two independent successful SQL sessions and all older fault semantics.

Original failure ZIPs and byte-identical JSON extractions are retained under
`evidence/runs/e2-c05-first-preflight-{primary,secondary}.*`. Artifact
13181050437 (primary), SHA-256
`bba4c3af2b15b3b7d50ba88fb351c34ede8953c9d148fca406078ba48d61b13e`;
artifact 13180157790 (secondary), SHA-256
`8eabe4d141b8430f5d426bfbcf53bce87886b307c6b2a393f7c299d5430d7f17`.
Neither negative is a passing readiness or partition observation.

## Second original execution — capture shutdown failure

Run #41528077816 on source `72d93aee4cf148ade04c8e1979bc60d7439bdb75`
reached the actual fault and contested requests, but both jobs failed when
rootless crun denied host-side SIGINT delivery to tcpdump (`Permission denied`).
Each job recorded one COMMITTED and one dispatched timeout; SQL held 2/4/2
including baseline. Neither job reached completed recovery or is a PASS.
The complete original archives, including incomplete PCAPs, remain unchanged:
`evidence/runs/e2-c05-second-capture-{primary,secondary}.*`.
Primary artifact 13180038964, SHA-256
`f717bd165745bc4cd0d95485df559fc35bb15262ad6eff6562c1d63fb6fdfc41`;
secondary artifact 13180631863, SHA-256
`63e3778c681a73a08cd08330d441957e46d3e8d3d0f17fdee461e1b8b2848a55`.

The next capture implementation uses dumpcap's native `-a duration:45`
autostop, requires exit 0, retains the same private namespace and capabilities,
and decodes the resulting original PCAP using tcpdump. It needs no host signal
or elevated runtime permissions. Native autostop is documented by
[Wireshark](https://www.wireshark.org/docs/man-pages/dumpcap.html); dumpcap is
in the [pinned netshoot v0.13 source image](https://github.com/nicolaka/netshoot/blob/e1fbbfaf1a3f874a57103c4317f43444d8aae75d/Dockerfile).
The firewall/payload/oracle/recovery acceptance criteria remain unchanged.
