#!/usr/bin/env python3
"""Generate a reproducible E2-B05 OFFER contract, not benchmark evidence.

The vectors can be consumed by independent load clients in a later experiment.
No Orleans/SQL request is issued here. The fixed-clock scheduled arrival is
distinct from actual dispatch, admission, acknowledgement and durable COMMIT.
All code, field names and software documentation are English-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ACCOUNT_COUNT = 1000
HOT_ACCOUNT_COUNT = 50
AMOUNT_CENTS = 1
INITIAL_BALANCE_CENTS = 100000
MAX_OFFERS = 200000
PROFILES = (
    "uniform",
    "five_percent_hot",
    "one_account_half_intents",
    "crossed",
)
PHASES = ("warmup", "measurement", "cooldown")
PROFILE_DESCRIPTIONS = {
    "uniform": "Independent seeded uniform selection of source account IDs 1..1000",
    "five_percent_hot": "Exactly 80% of source intents from eligible accounts 1..50 (5% of 1000); remaining 20% from 51..1000",
    "one_account_half_intents": "Exactly 50% of source intents from account 1; remaining 50% from accounts 2..1000",
    "crossed": "Exactly balanced opposite-direction source/target intents between accounts 1 and 2, shuffled deterministically; NOT strictly alternating; no claim of 5% hot distribution",
}


def _sources(profile: str, count: int, rng: random.Random) -> list[int]:
    if profile == "uniform":
        return [rng.randint(1, ACCOUNT_COUNT) for _ in range(count)]
    if count % 10:
        raise ValueError(
            "Hot and crossed workload phase counts must be multiples of 10 "
            "to retain exact prespecified proportions"
        )
    if profile == "five_percent_hot":
        n_hot = (count * 4) // 5
        # Visit all 50 eligible hot keys when at least 50 hot offers exist.
        values = [(index % HOT_ACCOUNT_COUNT) + 1 for index in range(n_hot)]
        values += [
            rng.randint(HOT_ACCOUNT_COUNT + 1, ACCOUNT_COUNT)
            for _ in range(count - n_hot)
        ]
    elif profile == "one_account_half_intents":
        values = [1] * (count // 2)
        values += [rng.randint(2, ACCOUNT_COUNT) for _ in range(count // 2)]
    elif profile == "crossed":
        values = [1, 2] * (count // 2)
    else:
        raise ValueError("Unknown profile: " + profile)
    rng.shuffle(values)
    return values


def generate(
    profile: str, offered_tps: int, warmup_seconds: int,
    measurement_seconds: int, cooldown_seconds: int,
    seed: int, repetition: int
) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown profile")
    if not 1 <= offered_tps <= 10000:
        raise ValueError("offered_tps must be in 1..10000")
    if not 0 <= warmup_seconds <= 600 or not 1 <= measurement_seconds <= 600 \
            or not 0 <= cooldown_seconds <= 600:
        raise ValueError("Invalid phase lengths")
    if not 0 <= seed <= 2**32 - 1 or not 0 <= repetition <= 99:
        raise ValueError("Invalid fixed seed or repetition")
    durations = (warmup_seconds, measurement_seconds, cooldown_seconds)
    total = offered_tps * sum(durations)
    if total > MAX_OFFERS:
        raise ValueError("Too many offered requests for one evidence vector")
    if profile != "uniform" and any(
        (offered_tps * seconds) % 10 for seconds in durations
    ):
        raise ValueError(
            "Each phase's number of intents must be a multiple of 10"
        )

    operations = []
    phase_metadata = {}
    elapsed_ns = 0
    for phase_index, (phase, seconds) in enumerate(zip(PHASES, durations)):
        phase_count = offered_tps * seconds
        rng = random.Random(
            seed * 65537 + repetition * 104729 + phase_index * 131071
            + PROFILES.index(profile) * 524287
        )
        sources = _sources(profile, phase_count, rng)
        hot = sum(source <= HOT_ACCOUNT_COUNT for source in sources)
        single = sum(source == 1 for source in sources)
        phase_metadata[phase] = {
            "durationSeconds": seconds,
            "offeredRequests": phase_count,
            "hotEligibleAccountCount": HOT_ACCOUNT_COUNT,
            "hotSourceIntents": hot,
            "accountOneSourceIntents": single
        }
        for i, src in enumerate(sources):
            if profile == "crossed":
                dst = 2 if src == 1 else 1
            else:
                dst = rng.randint(1, ACCOUNT_COUNT - 1)
                if dst >= src:
                    dst += 1
            operations.append({
                "operationId": f"e2-b05-{profile.replace('_', '-')}-r{repetition:02d}-{len(operations):07d}",
                "phase": phase,
                "scheduledAtNs": elapsed_ns + (i * 1_000_000_000 // offered_tps),
                "sourceAccountId": src,
                "targetAccountId": dst,
                "amountCents": AMOUNT_CENTS,
                "fault": "none"
            })
        elapsed_ns += seconds * 1_000_000_000

    if len(operations) != total or len({x["operationId"] for x in operations}) != total:
        raise AssertionError("Generator produced duplicate or missing offers")
    if any(
        not 1 <= x["sourceAccountId"] <= ACCOUNT_COUNT
        or not 1 <= x["targetAccountId"] <= ACCOUNT_COUNT
        or x["sourceAccountId"] == x["targetAccountId"]
        for x in operations
    ):
        raise AssertionError("Invalid candidate business command")
    if any(
        a["scheduledAtNs"] >= b["scheduledAtNs"]
        for a, b in zip(operations, operations[1:])
    ):
        raise AssertionError("Arrival schedule is not strictly increasing")
    if profile == "five_percent_hot":
        if any(
            row["hotSourceIntents"] * 5 != row["offeredRequests"] * 4
            for row in phase_metadata.values()
        ):
            raise AssertionError("Hot distribution violated")
    if profile == "one_account_half_intents":
        if any(
            row["accountOneSourceIntents"] * 2 != row["offeredRequests"]
            for row in phase_metadata.values()
        ):
            raise AssertionError("Single-account distribution violated")
    if profile == "crossed":
        counts = Counter(x["sourceAccountId"] for x in operations)
        if counts[1] != counts[2]:
            raise AssertionError("Crossed source requests unbalanced")

    encoded = json.dumps(
        operations, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return {
        "schemaVersion": 1,
        "experiment": "E2-B05-Fixed-Clock-Arrival-Contract",
        "status": "GENERATED_NOT_EXECUTED",
        "capacityEvidence": False,
        "generatorSourceSha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "offeredVectorSha256": hashlib.sha256(encoded).hexdigest(),
        "profile": profile,
        "distribution": PROFILE_DESCRIPTIONS[profile],
        "seed": seed,
        "repetition": repetition,
        "accountCount": ACCOUNT_COUNT,
        "eligibleHotAccounts": list(range(1, HOT_ACCOUNT_COUNT + 1)),
        "openingBalanceCentsPerAccount": INITIAL_BALANCE_CENTS,
        "totalOfferedRequests": total,
        "offeredRatePerSecond": offered_tps,
        "phases": phase_metadata,
        "arrivalClock": "scheduled_monotonic_offset_ns_from_run_start",
        "route": "UNBOUND_SAME_VECTOR_MUST_BE_USED_FOR_DIRECT_AND_ORLEANS",
        "noCoordinatedOmissionClaim": (
            "Schedules are precomputed independently of response completion; "
            "the subsequent external executor MUST record scheduled, dispatch, "
            "admitted, completion and missing/timeout samples without filtering."
        ),
        "limitations": (
            "This is an offline deterministic workload specification ONLY. "
            "No SQL, Orleans, client, VM or network was exercised. No observed "
            "latency, p50/p95/p99, sustained throughput, bottleneck, DB "
            "oracle verdict, capacity ceiling, physical HA or MIPS equivalence."
        ),
        "operations": operations
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--offered-tps", type=int, required=True)
    parser.add_argument("--warmup-seconds", type=int, default=10)
    parser.add_argument("--measurement-seconds", type=int, default=60)
    parser.add_argument("--cooldown-seconds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--repetition", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = generate(
        args.profile, args.offered_tps, args.warmup_seconds,
        args.measurement_seconds, args.cooldown_seconds,
        args.seed, args.repetition
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status": manifest["status"],
        "offeredVectorSha256": manifest["offeredVectorSha256"],
        "totalOfferedRequests": manifest["totalOfferedRequests"],
        "output": str(args.output),
        "limitation": "No workload execution or capacity evidence"
    }, indent=2))


if __name__ == "__main__":
    main()
