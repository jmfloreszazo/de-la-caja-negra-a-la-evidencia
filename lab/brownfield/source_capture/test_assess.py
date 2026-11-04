"""Adversarial structural validation for native CDC owner intake (NOT native tests)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from assess import CATALOG, assess

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "intake.example.json"


def example():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def pointer():
    # Syntactically shaped but NOT actual or independently validated evidence.
    return {"uri": "evidence/customer-only-not-present.json",
            "sha256": "a" * 64,
            "claim": "A declared file pointer, not verified evidence"}


def all_excluded():
    document = example()
    document["sourceSystem"] = "CUSTOMER-CLAIM-STRUCTURAL-ONLY"
    for k in ("ownerApproval", "baselineGoldenMaster", "snapshotCutoverPlan",
              "externalEffectOracle", "reconciliationSignoff"):
        document[k] = pointer()
    for item in document["paths"]:
        item["applicability"] = "OUT_OF_SCOPE"
        item["outOfScopeEvidence"] = pointer()
    return document


def in_scope(document, family):
    item = next(x for x in document["paths"] if x["family"] == family)
    item["applicability"] = "IN_SCOPE"
    item["captureProduct"] = "UNVERIFIED_PRODUCT_NAME"
    item["productVersion"] = "UNVERIFIED_VERSION"
    item["outOfScopeEvidence"] = None
    checks = CATALOG["genericChecks"] + CATALOG["families"][family]["checks"]
    item["controls"] = {k: pointer() for k in checks}
    return item


class NativeCaptureIntakeTests(unittest.TestCase):
    def test_01_sample_stays_not_ready_and_every_family_unknown(self):
        result = assess(example())
        self.assertEqual(result["status"], "NOT_READY")
        self.assertEqual(result["pathsUnknown"], 7)
        self.assertEqual(result["pathsDeclared"], 7)
        self.assertFalse(result["nativeCaptureTestExecuted"])
        self.assertEqual(result["todmG2"], "INCONCLUSIVE")
        self.assertEqual(result["todmG6"], "BLOCK")

    def test_02_all_excluded_self_assertions_do_not_approve_any_bank(self):
        result = assess(all_excluded())
        self.assertEqual(result["status"], "READY_FOR_INDEPENDENT_REVIEW")
        self.assertFalse(result["evidenceBytesVerified"])
        self.assertFalse(result["bankSourceWriterFenceProven"])
        self.assertFalse(result["productionApproved"])
        self.assertEqual(result["todmG6"], "BLOCK")

    def test_03_source_system_missing_is_not_ready(self):
        d = all_excluded()
        d["sourceSystem"] = "UNSPECIFIED-UNKNOWN"
        self.assertEqual(assess(d)["status"], "NOT_READY")

    def test_04_unknown_family_remains_not_ready(self):
        d = all_excluded()
        item = d["paths"][0]
        item["applicability"] = "UNKNOWN"
        item["outOfScopeEvidence"] = None
        self.assertEqual(assess(d)["status"], "NOT_READY")

    def test_05_unknown_family_cannot_smuggle_capture_config(self):
        d = example()
        d["paths"][0]["captureProduct"] = "claimed-cdc"
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_06_missing_family_is_refused(self):
        d = all_excluded()
        d["paths"].pop()
        result = assess(d)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertTrue(any("not inventoried" in s for s in result["missing"]))

    def test_07_duplicate_family_is_invalid(self):
        d = example()
        d["paths"].append(copy.deepcopy(d["paths"][0]))
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_08_unknown_vendor_not_magically_supported(self):
        d = all_excluded()
        in_scope(d, "FUJITSU_OR_OTHER")
        result = assess(d)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertTrue(any("vendor-specific primary documents" in x for x in result["missing"]))
        self.assertIn("FUJITSU_OR_OTHER", result["primarySourceFamiliesNotVerified"])

    def test_09_every_documented_family_can_be_structurally_intaked(self):
        for family, info in CATALOG["families"].items():
            if not info["documented"]:
                continue
            with self.subTest(family=family):
                d = all_excluded()
                in_scope(d, family)
                result = assess(d)
                self.assertEqual(result["status"], "READY_FOR_INDEPENDENT_REVIEW")
                self.assertEqual(result["todmG2"], "INCONCLUSIVE")
                self.assertFalse(result["evidenceBytesVerified"])
                self.assertFalse(result["nativeCaptureTestExecuted"])

    def test_10_in_scope_without_product_version_stays_not_ready(self):
        d = all_excluded()
        x = in_scope(d, "DB2_ZOS_LOG")
        x["productVersion"] = None
        self.assertEqual(assess(d)["status"], "NOT_READY")

    def test_11_required_cdc_control_missing_is_not_ready(self):
        d = all_excluded()
        x = in_scope(d, "VSAM_CICS")
        x["controls"]["IDCAMS_LOGREPLICATE_AND_LOGSTREAMID"] = None
        self.assertEqual(assess(d)["status"], "NOT_READY")

    def test_12_false_pass_root_is_rejected(self):
        for field in ("todmG6", "productionApproved", "nativeCdcVerified", "bankPass"):
            with self.subTest(field=field):
                d = all_excluded()
                d[field] = "PASS"
                self.assertEqual(assess(d)["status"], "INVALID")

    def test_13_fake_out_of_scope_proof_has_no_production_authority(self):
        d = all_excluded()
        r = assess(d)
        self.assertEqual(r["pathsOutOfScope"], 7)
        self.assertEqual(r["evidenceDisposition"],
                         "REFERENCES_ONLY_NEVER_NATIVE_OR_BANK_PASS")
        self.assertEqual(r["todmG6"], "BLOCK")

    def test_14_out_of_scope_requires_evidence(self):
        d = all_excluded()
        d["paths"][0]["outOfScopeEvidence"] = None
        self.assertEqual(assess(d)["status"], "NOT_READY")

    def test_15_excluded_path_cannot_supply_in_scope_claims(self):
        d = all_excluded()
        d["paths"][0]["controls"]["COMMIT_ORDER_AND_UOR"] = pointer()
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_16_in_scope_cannot_assert_exclusion(self):
        d = all_excluded()
        x = in_scope(d, "IMS_DLI_BATCH")
        x["outOfScopeEvidence"] = pointer()
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_17_undeclared_vendor_control_fails_closed(self):
        d = all_excluded()
        x = in_scope(d, "IBM_I_JOURNAL")
        x["controls"]["AUTOMATIC_BANK_PASS"] = pointer()
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_18_invalid_hash_or_uri_is_rejected(self):
        for part, value in (("sha256", "abc"), ("uri", "file:///tmp/hack")):
            with self.subTest(part=part):
                d = all_excluded()
                d["ownerApproval"][part] = value
                self.assertEqual(assess(d)["status"], "INVALID")

    def test_19_missing_owner_question_refused(self):
        d = example()
        d["paths"][0]["ownerQuestions"] = []
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_20_unidentified_or_extra_path_family_refused(self):
        d = example()
        d["paths"][0]["family"] = "DB2_ZOS_AUTOMATICALLY_SUPPORTED"
        self.assertEqual(assess(d)["status"], "INVALID")
        d = example()
        d["paths"][0]["done"] = True
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_21_invalid_schema_and_wrong_classification(self):
        d = example()
        d["schemaVersion"] = 2
        self.assertEqual(assess(d)["status"], "INVALID")
        d = example()
        d["classification"] = "BANK_APPROVED"
        self.assertEqual(assess(d)["status"], "INVALID")

    def test_22_cli_sample_returns_not_ready_and_block(self):
        proc = subprocess.run(
            [sys.executable, str(HERE / "assess.py"), str(SOURCE)],
            text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "NOT_READY")
        self.assertEqual(data["todmG6"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
