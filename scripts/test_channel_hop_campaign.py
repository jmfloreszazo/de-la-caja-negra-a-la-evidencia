"""Adversarial intake checks. These are not a distributed execution campaign."""
import hashlib
import json
import pathlib
import tempfile
import unittest
from check_channel_hop_campaign import audit, REQUIRED_FILES


class IntakeRefusal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        hosts = {role: {"hostId": role, "failureDomain": "declared-" + role}
                 for role in ("client", "gateway", "core", "database", "oracle")}
        cases = []
        for ident in ("H01", "H02"):
            artifacts = {}
            for kind in REQUIRED_FILES:
                name = f"{ident}-{kind}.log"
                blob = f"synthetic test stub for {ident} {kind}".encode()
                (self.root / name).write_bytes(blob)
                artifacts[kind] = {"path": name, "sha256": hashlib.sha256(blob).hexdigest()}
            cases.append({"id": ident, "outcome": "INCONCLUSIVE", "operationId": ident,
                          "injectionWindow": "declared", "independentSqlOracle": True,
                          "unknownAutoAction": False, "duplicateFinancialEffects": False,
                          "artifacts": artifacts})
        self.data = {"schemaVersion": 1, "sourceSha": "a" * 40 + "b" * 24,
                     "syntheticDisposable": True, "productionApproved": False,
                     "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
                     "hosts": hosts, "cases": cases}
        self.file = self.root / "manifest.json"

    def check(self):
        self.file.write_text(json.dumps(self.data))
        return audit(self.file)

    def test_complete_fictional_bundle_is_review_only(self):
        result = self.check()
        self.assertEqual(result["verdict"], "READY_FOR_MANUAL_EVIDENCE_REVIEW")
        self.assertFalse(result["physicalIndependenceVerified"])
        self.assertFalse(result["bankApproved"])

    def test_no_fake_business_approval(self):
        self.data["todmG6"] = "PASS"
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_same_host_claim(self):
        self.data["hosts"]["gateway"]["hostId"] = "client"
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_missing_hop(self):
        self.data["cases"].pop()
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_missing_sql_oracle(self):
        self.data["cases"][0]["independentSqlOracle"] = False
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_unsafe_automation(self):
        self.data["cases"][0]["unknownAutoAction"] = True
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_modified_raw_artifact(self):
        (self.root / "H01-sql_snapshot.log").write_text("tampered")
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_path_escape(self):
        self.data["cases"][0]["artifacts"]["client_log"]["path"] = "../outside"
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_real_git_sha1_format_accepted(self):
        self.data["sourceSha"] = "f" * 40
        self.assertEqual(self.check()["verdict"], "READY_FOR_MANUAL_EVIDENCE_REVIEW")

    def test_invalid_sha_length_refused(self):
        self.data["sourceSha"] = "f" * 41
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_malformed_case_is_inconclusive_not_exception(self):
        self.data["cases"] = [{"id": None}, self.data["cases"][1]]
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_case_list_with_nonobject_refused(self):
        self.data["cases"] = [False, self.data["cases"][1]]
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_symlink_artifact_refused(self):
        original = self.root / "H01-client_log.log"
        other = self.root / "other-client.log"
        original.rename(other)
        original.symlink_to(other)
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_reused_artifact_refused(self):
        item = self.data["cases"][0]["artifacts"]
        item["client_log"] = dict(item["core_log"])
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_oversized_artifact_refused(self):
        p = self.root / "H01-fault_log.log"
        with p.open("wb") as out:
            out.truncate(32 * 1024 * 1024 + 1)
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_directory_traversal_refused(self):
        self.data["cases"][0]["artifacts"]["client_log"]["path"] = "sub/../H01-client_log.log"
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")

    def test_no_duplicated_financial_effects(self):
        self.data["cases"][1]["duplicateFinancialEffects"] = True
        self.assertEqual(self.check()["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
