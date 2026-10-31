#!/usr/bin/env python3
"""Pure offline checks for the E2-B05 arrival contract, no networking."""
import unittest

from b05_arrival_contract import MAX_OFFERS, PHASES, PROFILES, generate


class ArrivalContractTests(unittest.TestCase):
    def make(self, profile, repetition=0):
        return generate(
            profile=profile, offered_tps=20,
            warmup_seconds=1, measurement_seconds=2, cooldown_seconds=1,
            seed=20261031, repetition=repetition
        )

    def test_exact_offered_clock_and_cardinality(self):
        for profile in PROFILES:
            with self.subTest(profile=profile):
                record = self.make(profile)
                self.assertEqual(record["status"], "GENERATED_NOT_EXECUTED")
                self.assertFalse(record["capacityEvidence"])
                offered = record["operations"]
                self.assertEqual(len(offered), 80)
                self.assertEqual(offered[0]["scheduledAtNs"], 0)
                self.assertEqual(offered[-1]["scheduledAtNs"], 3_950_000_000)
                self.assertEqual(len(set(x["operationId"] for x in offered)), 80)
                self.assertEqual([x["phase"] for x in offered].count("measurement"), 40)
                self.assertEqual(
                    [x["scheduledAtNs"] for x in offered],
                    sorted(x["scheduledAtNs"] for x in offered)
                )
                self.assertTrue(all(
                    x["sourceAccountId"] != x["targetAccountId"]
                    and 1 <= x["sourceAccountId"] <= 1000
                    and 1 <= x["targetAccountId"] <= 1000
                    and x["amountCents"] == 1
                    for x in offered
                ))

    def test_exact_fifty_eligible_hot_accounts_and_eighty_percent_share(self):
        record = self.make("five_percent_hot")
        self.assertEqual(record["eligibleHotAccounts"], list(range(1, 51)))
        for phase in PHASES:
            row = record["phases"][phase]
            self.assertEqual(row["hotSourceIntents"] * 5,
                             row["offeredRequests"] * 4)

    def test_single_hot_source_exact_half_each_phase(self):
        record = self.make("one_account_half_intents")
        for phase in PHASES:
            row = record["phases"][phase]
            self.assertEqual(row["accountOneSourceIntents"] * 2,
                             row["offeredRequests"])

    def test_crossed_pairs_remain_balanced(self):
        record = self.make("crossed")
        offered = record["operations"]
        self.assertEqual(sum(x["sourceAccountId"] == 1 for x in offered), 40)
        self.assertEqual(sum(x["sourceAccountId"] == 2 for x in offered), 40)
        self.assertEqual({
            (x["sourceAccountId"], x["targetAccountId"]) for x in offered
        }, {(1, 2), (2, 1)})

    def test_same_seed_replay_and_route_neutrality(self):
        before = self.make("uniform")
        after = self.make("uniform")
        self.assertEqual(before["offeredVectorSha256"],
                         after["offeredVectorSha256"])
        self.assertEqual(before["operations"], after["operations"])
        self.assertNotIn("orleans", before["route"].lower().replace(
            "orleans", ""))  # no executable route selected
        changed = self.make("uniform", repetition=1)
        self.assertNotEqual(before["offeredVectorSha256"],
                            changed["offeredVectorSha256"])

    def test_prespecified_invalid_rates_and_phase_samples_fail_closed(self):
        with self.assertRaises(ValueError):
            generate("five_percent_hot", 11, 1, 2, 1, 20261031, 0)
        with self.assertRaises(ValueError):
            generate("uniform", 0, 1, 2, 1, 20261031, 0)
        with self.assertRaises(ValueError):
            generate("uniform", 10000, 100, 100, 0, 20261031, 0)
        with self.assertRaises(ValueError):
            generate("uniform", 20, 0, 0, 0, 20261031, 0)

    def test_phase_isolation_and_empty_warmup_allowed(self):
        record = generate("one_account_half_intents", 20, 0, 1, 0, 7, 0)
        self.assertEqual(record["totalOfferedRequests"], 20)
        self.assertEqual(record["phases"]["warmup"]["offeredRequests"], 0)
        self.assertTrue(all(x["phase"] == "measurement"
                            for x in record["operations"]))


if __name__ == "__main__":
    unittest.main()
