"""Technical qualification of the local adapter, not experiment acceptance."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
import uuid

from lab.todm_validation.bundle import seal
from lab.todm_validation.governance import PIN, demonstrate, upstream_functions
from lab.todm_validation.validate import FAIL, INCONCLUSIVE, PASS, INVARIANTS, adapt, aggregate, evaluate, safe_path, strict_json

HERE = Path(__file__).parent


def invariant_vector():
    return dict.fromkeys(INVARIANTS, True)


def e1_documents():
    clean = invariant_vector()
    bad = dict(clean, projectionAgrees=False, twoPostingsPerCommit=False)
    return {
        "report": {"experiment": "E1a synthetic PostgreSQL concurrency and independent-oracle slice", "status": "PASS",
                   "controls": {"independentOracle": {"invariants": clean, "status": "PASS"}}},
        "qualification": {"experiment": "E1b-independent-oracle-negative-control", "vectors": {"before": clean, "corrupted": bad, "restored": clean}},
    }


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.work = HERE / ".test-work" / uuid.uuid4().hex
        self.work.mkdir(parents=True)
        self.docs = e1_documents()
        for name, doc in self.docs.items():
            (self.work / (name + ".json")).write_text(json.dumps(doc), encoding="utf-8")
        for name in ("source.py", "contract.sql", "raw.txt"):
            (self.work / name).write_text("fixture " + name, encoding="utf-8")
        artifacts = [
            {"id": "report", "path": "report.json", "role": "report", "document": "report"},
            {"id": "qualification", "path": "qualification.json", "role": "qualification", "document": "qualification"},
            {"id": "source", "path": "source.py", "role": "source"},
            {"id": "contract", "path": "contract.sql", "role": "contract"},
            {"id": "raw", "path": "raw.txt", "role": "raw"},
        ]
        self.manifest = seal({"schemaVersion": 1, "kind": "TODM_EVIDENCE_BUNDLE", "upstreamCommit": PIN,
            "experiments": [{"experiment": "E1", "scope": "postgres-concurrency-slice", "risk": "Synthetic fixture only",
                             "limitations": ["No real experiment executed"], "artifacts": artifacts}]}, self.work)

    def tearDown(self):
        shutil.rmtree(self.work)
        try:
            self.work.parent.rmdir()
        except OSError:
            pass

    def replay(self):
        return evaluate(self.manifest, self.work)["experiments"][0]

    def update_report(self, doc):
        path = self.work / "report.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.manifest["experiments"][0]["artifacts"][0]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_positive_evaluation_is_never_release(self):
        result = self.replay()
        self.assertEqual(PASS, result["evaluationVerdict"])
        self.assertEqual(INCONCLUSIVE, result["methodologyVerdict"])
        self.assertEqual("BLOCK", result["releaseOutcome"])
        self.assertEqual([f"G{i}" for i in range(8)], [g["gate"] for g in result["gates"]])
        self.assertEqual(INCONCLUSIVE, result["gates"][2]["verdict"])
        self.assertEqual(INCONCLUSIVE, result["gates"][6]["verdict"])

    def test_genuine_byte_corruption_fails(self):
        with (self.work / "raw.txt").open("a", encoding="utf-8") as stream:
            stream.write("corruption")
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_missing_artifact_fails(self):
        (self.work / "source.py").unlink()
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_independent_invariant_false_overrides_pass_status(self):
        self.docs["report"]["controls"]["independentOracle"]["invariants"]["conserved"] = False
        self.update_report(self.docs["report"])
        self.assertEqual(FAIL, self.replay()["oracleVerdict"])

    def test_missing_oracle_report_is_inconclusive(self):
        self.update_report({"experiment": self.docs["report"]["experiment"], "status": "PASS", "controls": {}})
        self.assertEqual(INCONCLUSIVE, self.replay()["oracleVerdict"])

    def test_omitted_qualification_is_inconclusive(self):
        self.manifest["experiments"][0]["artifacts"].pop(1)
        self.assertEqual(INCONCLUSIVE, self.replay()["evaluationVerdict"])

    def test_forged_local_approval_denied(self):
        entry = self.manifest["experiments"][0]
        entry.update({"approved": True, "signature": "forged", "authority": "PASS", "baselineApproval": {"approved": True},
                      "releaseApproval": {"kind": "DEMO_SIMULATED", "approved": True, "approverRole": "release-owner"}})
        self.assertEqual("BLOCK", self.replay()["releaseOutcome"])
        self.assertEqual(INCONCLUSIVE, self.replay()["authorityVerdict"])

    def test_wrong_scope_cannot_pass(self):
        self.manifest["experiments"][0]["scope"] = "mainframe-production-capacity"
        self.assertEqual(INCONCLUSIVE, self.replay()["evaluationVerdict"])

    def test_duplicate_artifacts_rejected(self):
        self.manifest["experiments"][0]["artifacts"].append(copy.deepcopy(self.manifest["experiments"][0]["artifacts"][0]))
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_duplicate_document_rejected(self):
        item = self.manifest["experiments"][0]["artifacts"][1]
        item["document"] = "report"
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_duplicate_paths_under_alias_rejected(self):
        item = dict(self.manifest["experiments"][0]["artifacts"][0], id="alias", document="alias")
        self.manifest["experiments"][0]["artifacts"].append(item)
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_source_claims_must_bind_actual_bytes(self):
        self.docs["report"]["sourceSha256"] = {"source.py": "0" * 64}
        self.update_report(self.docs["report"])
        self.assertEqual(FAIL, self.replay()["evaluationVerdict"])

    def test_invalid_shapes_fail_closed(self):
        for malformed in ([], {}, None, "PASS", {"schemaVersion": 1}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                evaluate(malformed, self.work)
        for malformed in (None, [], "PASS", {"experiment": "unknown", "status": "PASS"}):
            with self.subTest(report=malformed):
                self.update_report(malformed)
                self.assertEqual(INCONCLUSIVE, self.replay()["oracleVerdict"])

    def test_unsafe_paths_rejected(self):
        for path in ("..\\outside", "../outside", "C:\\outside", "\\\\host\\share", "/root", "a:stream", "a/./b", "a//b", "a.\\b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(self.work.resolve(), path)

    def test_string_or_integer_invariants_do_not_pass(self):
        for value in ("true", 1, None):
            self.docs["report"]["controls"]["independentOracle"]["invariants"]["conserved"] = value
            self.update_report(self.docs["report"])
            self.assertEqual(INCONCLUSIVE, self.replay()["oracleVerdict"])

    def test_qualification_external_output_rejected_before_writes(self):
        from lab.todm_validation.qualify_bundle import qualify
        root = self.work / "bundle"
        root.mkdir()
        external = self.work / "external" / "qualification"
        with self.assertRaisesRegex(ValueError, "strictly inside --root"):
            qualify(root, external)
        self.assertFalse(external.parent.exists())
        self.assertEqual([], list(root.iterdir()))
        with self.assertRaisesRegex(ValueError, "strictly inside --root"):
            qualify(root, root)

    def test_resealing_changed_bytes_refused(self):
        (self.work / "source.py").write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            seal(self.manifest, self.work)

    def test_duplicate_json_and_nonfinite_numbers_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_negative_verdict_precedence(self):
        self.assertEqual(FAIL, aggregate([PASS, INCONCLUSIVE, FAIL]))
        self.assertEqual(INCONCLUSIVE, aggregate([PASS, INCONCLUSIVE]))
        self.assertEqual(INCONCLUSIVE, aggregate([]))

    def test_all_experiment_gates_even_without_evidence(self):
        from lab.todm_validation.validate import SCOPES
        entries = [{"experiment": name, "scope": scope, "risk": "Missing run", "limitations": ["No supplied run"], "artifacts": []} for name, scope in SCOPES.items()]
        self.manifest["experiments"] = entries
        result = evaluate(self.manifest, self.work)
        self.assertEqual(4, len(result["experiments"]))
        self.assertTrue(all(len(row["gates"]) == 8 and row["releaseOutcome"] == "BLOCK" for row in result["experiments"]))


class AdapterTests(unittest.TestCase):
    def test_upstream_governance_and_revocation(self):
        result = demonstrate()
        self.assertTrue(result["passed"])
        self.assertEqual(12, len(result["cases"]))
        self.assertEqual({"BLOCK", "SIMULATED_ALLOW"}, {case["release"]["outcome"] for case in result["cases"]})
        self.assertIn("authority_verdict", upstream_functions())

    def test_e4_recomputes_frozen_cases_instead_of_status(self):
        report = {"classification": "LIVE_MODEL_BUILDER_PILOT_NOT_E4_ACCEPTANCE", "cases": 1, "protectedUnchanged": True, "independentGate": {"verdict": "PASS"}}
        docs = {"cases": [{"id": "C001", "expected": "EXPECTED"}], "observations": [{"id": "C001", "legacy": "EXPECTED", "candidate": "WRONG"}]}
        self.assertEqual(FAIL, adapt("E4", report, docs)[0])
        docs["observations"][0]["candidate"] = "EXPECTED"
        self.assertEqual(PASS, adapt("E4", report, docs)[0])
        docs["observations"].append(dict(docs["observations"][0]))
        self.assertEqual(INCONCLUSIVE, adapt("E4", report, docs)[0])

    def test_e4_qualification_requires_actual_mutant_observations(self):
        report = {"classification": "LIVE_MODEL_BUILDER_PILOT_NOT_E4_ACCEPTANCE", "cases": 1, "protectedUnchanged": True, "independentGate": {"verdict": "PASS"}}
        docs = {"cases": [{"id": "C001", "expected": "EXPECTED"}],
                "observations": [{"id": "C001", "legacy": "EXPECTED", "candidate": "EXPECTED"}],
                "qualification": {"protectedUnchanged": True, "candidateGateReports": {}}}
        for name in ("none", "round-even", "wrong-threshold", "approve-inactive"):
            docs["qualification"]["candidateGateReports"][name] = {"verdict": "PASS" if name == "none" else "FAIL"}
            docs["qualification." + name] = [{"id": "C001", "legacy": "EXPECTED", "candidate": "EXPECTED" if name == "none" else "WRONG"}]
        self.assertEqual(PASS, adapt("E4", report, docs)[1])
        docs["qualification.round-even"][0]["candidate"] = "EXPECTED"
        self.assertEqual(FAIL, adapt("E4", report, docs)[1])
        del docs["qualification.round-even"]
        self.assertEqual(INCONCLUSIVE, adapt("E4", report, docs)[1])

    def test_explicit_failure_survives_missing_observations(self):
        report = {"classification": "LIVE_MODEL_BUILDER_PILOT_NOT_E4_ACCEPTANCE", "independentGate": {"verdict": "FAIL"}}
        self.assertEqual(FAIL, adapt("E4", report, {})[0])

    def test_e3_explicit_exploratory_shape(self):
        report = {"classification": "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE", "capacityAcceptance": False,
                  "oracleBefore": invariant_vector(), "oracleAfter": invariant_vector(), "errors": [],
                  "reconciliation": {"consistent": True}, "survivingServiceAliveAfterLoad": True,
                  "recovery": {"recoveredServiceAcknowledgedCommit": True},
                  "negativeControl": {"detected": ["twoPostingsPerCommit", "projectionAgrees"], "restoredOracle": invariant_vector()}}
        self.assertEqual(INCONCLUSIVE, adapt("E3", report, {})[0])
        report["oracleAfter"]["conserved"] = False
        self.assertEqual(FAIL, adapt("E3", report, {})[0])
        report["capacityAcceptance"] = True
        self.assertEqual(INCONCLUSIVE, adapt("E3", report, {})[0])

    def test_e3_actual_ledger_mutations_and_reconciliation(self):
        from lab.todm_validation.e3 import reconcile
        snapshot = {"accounts": [[i, 99999 if i == 1 else 100001 if i == 2 else 100000] for i in range(1, 17)],
                    "operations": [["op", 1, 2, 1, "COMMITTED"]], "postings": [["op", 1, -1], ["op", 2, 1]],
                    "outbox": [["op", "TransferCommitted"]]}
        offer = {"operationId": "op", "index": 0, "src": 1, "dst": 2, "amountCents": 1, "phase": 0, "ratePerSecond": 1,
                 "replica": 0, "scheduledSeconds": 3, "dispatchSeconds": 3, "outcome": "ACK_COMMITTED", "persistedStatus": "COMMITTED",
                 "response": {"operationId": "op", "amountCents": 1, "status": "COMMITTED"}}
        docs = {"ledger": snapshot, "offers": [offer], "planned": [copy.deepcopy(offer)]}
        report = {"measurement": {"offered": 1, "outcomes": {"ACK_COMMITTED": 1}},
                  "reconciliation": {"persistedCommits": 1, "persistedOperations": 1, "unacknowledgedPersistedCommits": 0},
                  "recovery": {"healthySeconds": 2.5}, "processEvents": [
                      {"action": "KILL_PROCESS", "actualSeconds": 1, "pid": 1, "replica": 0, "exitCode": -9},
                      {"action": "RESTART_PROCESS", "actualSeconds": 2, "pid": 2, "replica": 0},
                      {"action": "RECOVERY_HEALTHY", "actualSeconds": 2.5, "pid": 2, "replica": 0}]}
        checks, qualified = reconcile(report, docs)
        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(qualified)
        for kind in ("posting", "account", "request", "outbox", "ack", "planned", "count", "recovery"):
            changed_docs, changed_report = copy.deepcopy(docs), copy.deepcopy(report)
            if kind == "posting": changed_docs["ledger"]["postings"].pop()
            if kind == "account": changed_docs["ledger"]["accounts"][0][1] += 1
            if kind == "request": changed_docs["ledger"]["operations"][0][3] += 1
            if kind == "outbox": changed_docs["ledger"]["outbox"].clear()
            if kind == "ack": changed_docs["offers"][0]["response"]["operationId"] = "forged"
            if kind == "planned": changed_docs["planned"][0]["amountCents"] += 1
            if kind == "count": changed_report["reconciliation"]["persistedCommits"] += 1
            if kind == "recovery": changed_report["processEvents"][0]["exitCode"] = 0
            with self.subTest(mutation=kind):
                self.assertFalse(all(reconcile(changed_report, changed_docs)[0].values()))

    def test_e2_false_independent_vector(self):
        runs = [{"route": route, "fault": fault, "independentOracle": invariant_vector(),
                 "finalExactlyOneDurableEffect": True, "exitCode": -9,
                 "afterKill": {"operations": 0, "postings": 0, "outbox": 0} if fault == "kill-before-commit" else {"operations": 1, "postings": 2, "outbox": 1}}
                for route in ("direct", "orleans") for fault in ("kill-before-commit", "kill-after-commit")]
        report = {"experiment": "E2-Orleans-Actual-Cohost-Process-Kill", "killedRuns": runs}
        self.assertEqual(PASS, adapt("E2", report, {})[0])
        runs[0]["independentOracle"]["conserved"] = False
        self.assertEqual(FAIL, adapt("E2", report, {})[0])
        runs.pop()
        self.assertEqual(INCONCLUSIVE, adapt("E2", report, {})[0])


if __name__ == "__main__":
    unittest.main()
