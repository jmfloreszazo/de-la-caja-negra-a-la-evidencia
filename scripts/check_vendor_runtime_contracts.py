#!/usr/bin/env python3
"""Reject unsupported vendor-runtime equivalence in the #17/#18/#28 catalog.

Metadata and authored contract integrity only. Does NOT run vendor-native
COBOL, z/OS, MCP, OS 2200, IBM i, Fujitsu or customer banking workloads.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/vendor-runtime-contracts/catalog.json"
LAYERS = {"INFRA", "APP", "DATA", "SECURITY", "OPS", "CROSS_LAYER"}
KINDS = {"VENDOR_DOCUMENTED", "HISTORICAL_VENDOR_ANNOUNCEMENT", "DISCOVERY_ONLY"}
STRATEGIES = {"REHOST", "REPLATFORM", "REFACTOR", "REPLACE", "RETAIN", "HYBRID_COEXIST"}
ACCESS = {"FULL_TEXT", "SEARCH_INDEX", "SEARCH_INDEX_DIRECT_403"}
SOURCE_KINDS = {"DOCUMENTED", "HISTORICAL_ANNOUNCEMENT", "TRAINING_DESCRIPTION"}
CATALOG_KEYS = {"schema_version", "classification", "reviewed_on", "project_scope",
                "native_vendor_tests", "customer_evidence", "business_approval",
                "sources", "records", "notes"}
SOURCE_KEYS = {"id", "vendor", "title", "version_scope", "url", "published_on",
               "accessed_on", "access_mode", "kind"}
ROW_KEYS = {"id", "vendor", "platform", "kind", "layer", "original_contract",
            "migration_strategy", "candidate_patterns", "semantic_gap",
            "negative_control", "independent_oracle", "required_measurements",
            "source_ids", "risk_ids", "native_execution", "migration_verified",
            "bank_approved", "equivalence_claim", "installed_status", "service_level"}


def _text(value, minimum=5):
    return isinstance(value, str) and len(value.strip()) >= minimum


def _date(value):
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate(data) -> list[str]:
    problems = []
    if not isinstance(data, dict) or set(data) != CATALOG_KEYS:
        return ["Catalog must have exactly the versioned top-level fields"]
    if data["schema_version"] != 1:
        problems.append("Unexpected schema version")
    if data["classification"] != "PRIMARY_SOURCE_RESEARCH_AND_DESIGN_NOT_VENDOR_NATIVE_TEST":
        problems.append("False scope or execution classification")
    if data["native_vendor_tests"] != "NOT_EXECUTED":
        problems.append("Native vendor execution cannot be self-attested")
    if data["customer_evidence"] != "NOT_PROVIDED":
        problems.append("No customer source evidence was examined")
    if data["business_approval"] != "NOT_OBTAINED":
        problems.append("No bank sign-off can be self-attested")
    if not _date(data["reviewed_on"]):
        problems.append("Missing review date")
    if not _text(data["project_scope"]) or not isinstance(data["notes"], list):
        problems.append("Missing project scope and limitation notes")
    if not isinstance(data["sources"], list) or not isinstance(data["records"], list):
        return problems + ["Source/record arrays required"]
    seen_sources = {}
    for idx, src in enumerate(data["sources"]):
        if not isinstance(src, dict) or set(src) != SOURCE_KEYS:
            problems.append(f"Source {idx}: invalid field set")
            continue
        sid = src["id"]
        if sid in seen_sources:
            problems.append(f"Source {sid} duplicated")
        seen_sources[sid] = src
        if not _text(sid, 2) or not _text(src["vendor"]) or not _text(src["title"]):
            problems.append(f"Source {idx}: missing vendor/name")
        if not _text(src["version_scope"]) or not _text(src["url"]) or not (
            src["url"].startswith("https://www.ibm.com/") or
            src["url"].startswith("https://www.support.unisys.com/") or
            src["url"].startswith("https://www.unisys.com/") or
            src["url"].startswith("https://info.archives.global.fujitsu/")
        ):
            problems.append(f"Source {sid}: source/version/domain not scoped")
        if not _date(src["accessed_on"]) or (
            src["published_on"] is not None and not _date(src["published_on"])):
            problems.append(f"Source {sid}: unknown/invented date")
        if src["access_mode"] not in ACCESS or src["kind"] not in SOURCE_KINDS:
            problems.append(f"Source {sid}: retrieval/classification not recognized")
    seen_records = set()
    for idx, rec in enumerate(data["records"]):
        if not isinstance(rec, dict) or set(rec) != ROW_KEYS:
            problems.append(f"Record {idx}: invalid field set")
            continue
        rid = rec["id"]
        if rid in seen_records:
            problems.append(f"Record {rid}: duplicate ID")
        seen_records.add(rid)
        if not isinstance(rid, str) or not rid.startswith("VX"):
            problems.append(f"Record {idx}: wrong ID namespace")
        if rec["kind"] not in KINDS or rec["layer"] not in LAYERS or \
           rec["migration_strategy"] not in STRATEGIES:
            problems.append(f"Record {rid}: invalid taxonomy")
        for key in ("vendor", "platform", "original_contract", "semantic_gap",
                    "negative_control", "independent_oracle"):
            if not _text(rec[key], 12):
                problems.append(f"Record {rid}: missing {key}")
        for key in ("candidate_patterns", "required_measurements"):
            if not isinstance(rec[key], list) or len(rec[key]) == 0 or any(
                    not _text(p, 5) for p in rec[key]):
                problems.append(f"Record {rid}: missing {key}")
        if not isinstance(rec["risk_ids"], list) or any(
                not isinstance(x, str) or not x.startswith("R") or len(x) != 4
                for x in rec["risk_ids"]):
            problems.append(f"Record {rid}: invalid risk IDs")
        if rec["native_execution"] != "NOT_EXECUTED" or \
           rec["migration_verified"] is not False or rec["bank_approved"] is not False or \
           rec["equivalence_claim"] is not False or rec["installed_status"] != "UNKNOWN" or \
           rec["service_level"] != "NOT_MEASURED":
            problems.append(f"Record {rid}: inflated native, equivalence, installed or bank claim")
        refs = rec["source_ids"]
        if not isinstance(refs, list) or len(refs) != len(set(refs)):
            problems.append(f"Record {rid}: invalid source references")
            continue
        if rec["kind"] == "DISCOVERY_ONLY":
            if refs or rec["migration_strategy"] != "RETAIN":
                problems.append(f"Record {rid}: unknown product must remain source-less and retained")
        elif not refs:
            problems.append(f"Record {rid}: documented feature without primary source")
        for ref in refs:
            source = seen_sources.get(ref)
            if source is None or source["vendor"] != rec["vendor"]:
                problems.append(f"Record {rid}: vendor-source mismatch or unknown ref")
            elif rec["kind"] == "HISTORICAL_VENDOR_ANNOUNCEMENT" and \
                 source["kind"] != "HISTORICAL_ANNOUNCEMENT":
                problems.append(f"Record {rid}: misleading historical attribution")
            elif rec["kind"] == "VENDOR_DOCUMENTED" and \
                 source["kind"] == "HISTORICAL_ANNOUNCEMENT":
                problems.append(f"Record {rid}: announcement is not technical guarantee")
        if rec["kind"] == "HISTORICAL_VENDOR_ANNOUNCEMENT" and \
           rec["migration_strategy"] != "RETAIN":
            problems.append(f"Record {rid}: archived announcement cannot select replacement")
    if not any(r.get("kind") == "DISCOVERY_ONLY" for r in data["records"] if isinstance(r, dict)):
        problems.append("Unknown product register missing")
    if len(data["records"]) < 10:
        problems.append("Vendor/subsystem coverage regressed")
    return problems


class NegativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(CATALOG.read_text(encoding="utf-8"))

    def bad(self, edit):
        sample = copy.deepcopy(self.base)
        edit(sample)
        self.assertTrue(validate(sample), "Unsafe mutation was accepted")

    def test_01_reference_catalog(self):
        self.assertEqual(validate(self.base), [])

    def test_02_claim_native_execution(self):
        self.bad(lambda d: d.update(native_vendor_tests="PASS"))

    def test_03_claim_customer_data(self):
        self.bad(lambda d: d.update(customer_evidence="VERIFIED"))

    def test_04_claim_bank_signoff(self):
        self.bad(lambda d: d.update(business_approval="APPROVED"))

    def test_05_claim_equivalence(self):
        self.bad(lambda d: d["records"][0].update(equivalence_claim=True))

    def test_06_claim_native_row(self):
        self.bad(lambda d: d["records"][1].update(native_execution="PASS"))

    def test_07_claim_migration_complete(self):
        self.bad(lambda d: d["records"][2].update(migration_verified=True))

    def test_08_claim_installed(self):
        self.bad(lambda d: d["records"][3].update(installed_status="INSTALLED"))

    def test_09_claim_measured_slo(self):
        self.bad(lambda d: d["records"][4].update(service_level="99.99%"))

    def test_10_missing_oracle(self):
        self.bad(lambda d: d["records"][0].update(independent_oracle=""))

    def test_11_missing_negative_control(self):
        self.bad(lambda d: d["records"][3].update(negative_control=""))

    def test_12_vendor_mismatch(self):
        self.bad(lambda d: d["records"][6].update(source_ids=["P05"]))

    def test_13_false_source(self):
        self.bad(lambda d: d["records"][1].update(source_ids=["UNVERIFIED"]))

    def test_14_fabricated_publication_date(self):
        self.bad(lambda d: d["sources"][0].update(published_on="2026-02-30"))

    def test_15_missing_version_scope(self):
        self.bad(lambda d: d["sources"][0].update(version_scope=""))

    def test_16_fujitsu_marketing_promoted(self):
        self.bad(lambda d: d["records"][8].update(kind="VENDOR_DOCUMENTED"))

    def test_17_unknown_feature_marked_equivalent(self):
        self.bad(lambda d: d["records"][9].update(equivalence_claim=True))

    def test_18_unknown_product_given_feature_source(self):
        self.bad(lambda d: d["records"][9].update(source_ids=["P01"]))

    def test_19_remove_unknown_register(self):
        self.bad(lambda d: d.update(records=[x for x in d["records"]
                   if x["kind"] != "DISCOVERY_ONLY"]))

    def test_20_extra_approval_field(self):
        self.bad(lambda d: d["records"][0].update(productionAccepted=True))

    def test_21_untrusted_source_domain(self):
        self.bad(lambda d: d["sources"][0].update(url="https://example.org/claim"))

    def test_22_false_no_support_strategy(self):
        self.bad(lambda d: d["records"][9].update(migration_strategy="REPLACE"))

    def test_23_invalid_date_or_review(self):
        self.bad(lambda d: d.update(reviewed_on="yesterday"))

    def test_24_duplicate_record_id(self):
        self.bad(lambda d: d["records"][1].update(id=d["records"][0]["id"]))

    def test_25_discovery_absence_became_support_claim(self):
        self.bad(lambda d: d["records"][10].update(installed_status="UNSUPPORTED"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(NegativeControls)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() and result.testsRun == 25 else 1
    try:
        data = json.loads(args.catalog.read_text(encoding="utf-8"))
        errors = validate(data)
    except (ValueError, OSError) as error:
        errors = ["Unreadable catalog: " + str(error)]
    print(json.dumps({
        "status": "VALID_METADATA_ONLY" if not errors else "REJECT",
        "errors": errors, "nativePlatformTested": False,
        "bankApproved": False, "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
    }, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
