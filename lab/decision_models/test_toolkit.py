import copy
import io
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

from lab.decision_models import toolkit as t


ROOT = Path(__file__).resolve().parent


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.decision = t.load(ROOT / "examples" / "fee-decision.json")
        self.process = t.load(ROOT / "examples" / "fee-process.json")
        self.values = t.load(ROOT / "examples" / "fee-input.json")

    def test_manual_fee_expectations(self):
        for case in t.load(ROOT / "examples" / "fee-cases.json")["cases"]:
            with self.subTest(case=case["id"]):
                result = t.evaluate(self.decision, case["inputs"])
                self.assertEqual("PASS", result["status"])
                self.assertEqual(case["expected"], result["outputs"])
                self.assertIs(False, result["productionApproved"])

    def test_missing_inputs_and_no_match(self):
        self.assertEqual("INCONCLUSIVE", t.evaluate(self.decision, {})["status"])
        self.decision["rules"] = self.decision["rules"][:1]
        self.assertEqual("INCONCLUSIVE", t.evaluate(self.decision, self.values)["status"])

    def test_unknown_inputs_and_wrong_types(self):
        for values in ({**self.values, "approved": True}, {**self.values, "amountCents": True}, {**self.values, "amountCents": 1.5}, {**self.values, "amountCents": 10**18}):
            with self.subTest(values=values), self.assertRaises(t.Invalid):
                t.evaluate(self.decision, values)

    def test_unique_rejects_overlaps(self):
        self.decision["hitPolicy"] = "UNIQUE"
        result = t.evaluate(self.decision, {**self.values, "customerActive": "N"})
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(["inactive", "approve"], result["matchedRules"])

    def test_unique_single_match(self):
        self.decision["hitPolicy"] = "UNIQUE"
        self.assertEqual("PASS", t.evaluate(self.decision, self.values)["status"])

    def test_first_precedence(self):
        result = t.evaluate(self.decision, {**self.values, "rateBps": 10001, "customerActive": "N"})
        self.assertEqual("invalid-rate-high", result["selectedRule"])
        self.assertEqual(["invalid-rate-high", "inactive", "approve"], result["matchedRules"])

    def test_operators_variables_and_expression_validation(self):
        mutations = [
            lambda m: m["rules"][0]["when"][0].update(operator="eval"),
            lambda m: m["rules"][0]["when"][0].update(variable="missing"),
            lambda m: m["rules"][-1]["then"]["feeCents"].update(operation="eval"),
            lambda m: m["rules"][-1]["then"]["feeCents"].update(variables=["amountCents", "unknown"]),
            lambda m: m["rules"][-1]["then"]["feeCents"].update(rounding="IMPLICIT"),
            lambda m: m["rules"][-1]["then"]["feeCents"].update(divisor="0"),
            lambda m: m["rules"][-1]["then"]["feeCents"].update(scale=1),
        ]
        for mutate in mutations:
            model = copy.deepcopy(self.decision)
            mutate(model)
            with self.subTest(model=model), self.assertRaises(t.Invalid):
                t.validate_model(model)

    def decimal_model(self):
        model = copy.deepcopy(self.decision)
        model["inputs"] = {"x": {"type": "decimal"}, "y": {"type": "decimal"}}
        model["outputs"] = {"answer": {"type": "decimal"}}
        model["hitPolicy"] = "UNIQUE"
        model["rules"] = [{"id": "round", "when": [], "then": {"answer": {"operation": "multiplyDivide", "variables": ["x", "y"], "divisor": "1", "scale": 2, "rounding": "HALF_UP"}}}]
        return model

    def test_exact_decimal_rounding(self):
        model = self.decimal_model()
        for mode, operand, expected in [("HALF_UP", "1.005", "1.01"), ("HALF_UP", "-1.005", "-1.01"), ("HALF_EVEN", "1.005", "1.00"), ("HALF_EVEN", "1.015", "1.02"), ("DOWN", "-1.009", "-1.00")]:
            model["rules"][0]["then"]["answer"]["rounding"] = mode
            self.assertEqual(expected, t.evaluate(model, {"x": operand, "y": "1"})["outputs"]["answer"])

    def test_large_exact_product_and_nonterminating_division(self):
        model = self.decimal_model()
        expr = model["rules"][0]["then"]["answer"]
        expr.update(divisor="999999999999999999", scale=8)
        result = t.evaluate(model, {"x": "999999999999999999", "y": "1.00000001"})
        self.assertEqual("1.00000001", result["outputs"]["answer"])
        expr.update(divisor="3", scale=2)
        self.assertEqual("0.33", t.evaluate(model, {"x": "1", "y": "1"})["outputs"]["answer"])

    def test_decimal_comparisons_exact(self):
        model = self.decimal_model()
        for op, value, expected in [("eq", "1.00000000", "PASS"), ("ne", "1.00000001", "PASS"), ("lt", "1.00000001", "PASS"), ("le", "1", "PASS"), ("gt", "0.99999999", "PASS"), ("ge", "1.00000001", "INCONCLUSIVE")]:
            model["rules"][0]["when"] = [{"variable": "x", "operator": op, "value": value}]
            self.assertEqual(expected, t.evaluate(model, {"x": "1", "y": "1"})["status"])

    def test_invalid_decimal_encodings(self):
        for value in (1.0, "NaN", "Infinity", "1e2", "01", ".5", "1.123456789"):
            with self.subTest(value=value), self.assertRaises(t.Invalid):
                t.evaluate(self.decimal_model(), {"x": value, "y": "1"})

    def test_schema_rejects_unknown_missing_duplicate(self):
        for key, value in [("hitPolicy", "COLLECT"), ("profileVersion", True), ("productionApproved", True)]:
            model = {**self.decision, key: value}
            with self.assertRaises(t.Invalid):
                t.validate_model(model)
        del self.decision["version"]
        with self.assertRaises(t.Invalid):
            t.validate_model(self.decision)
        model = t.load(ROOT / "examples" / "fee-decision.json")
        model["rules"].append(copy.deepcopy(model["rules"][0]))
        with self.assertRaises(t.Invalid):
            t.validate_model(model)

    def test_trace_positive_and_incomplete(self):
        for name, expected in [("fee-trace", "PASS"), ("fee-trace-incomplete", "INCONCLUSIVE")]:
            trace = t.load(ROOT / "examples" / (name + ".json"))
            self.assertEqual(expected, t.check_trace(self.process, trace)["status"])
        trace["states"] = []
        self.assertEqual("INCONCLUSIVE", t.check_trace(self.process, trace)["status"])
        trace["states"] = ["Start", "Validate", "Rejected", "End"]
        self.assertEqual("PASS", t.check_trace(self.process, trace)["status"])

    def test_trace_negative(self):
        trace = t.load(ROOT / "examples" / "fee-trace.json")
        for states in (["Start", "Record", "End"], ["Validate", "Rejected", "End"], ["Start", "Unknown"], ["Start", "Validate", "Rejected", "End", "End"]):
            with self.subTest(states=states), self.assertRaises(t.Invalid):
                t.check_trace(self.process, {**trace, "states": states})
        with self.assertRaises(t.Invalid):
            t.check_trace(self.process, {**trace, "modelVersion": "v2"})

    def test_invalid_process_models(self):
        mutations = [lambda m: m["states"].append("Unreachable"), lambda m: m.update(ends=[]), lambda m: m["transitions"].append(["End", "Start"]), lambda m: m["transitions"].append(["Start", "Missing"]), lambda m: m["transitions"].append(["Start", "Validate"])]
        for mutate in mutations:
            model = copy.deepcopy(self.process)
            mutate(model)
            with self.assertRaises(t.Invalid):
                t.validate_model(model)

    def test_json_reader_rejects_ambiguous_numbers_and_keys(self):
        scratch = ROOT / ("test-scratch-" + uuid.uuid4().hex + ".json")
        try:
            for document in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":1.5}'):
                scratch.write_text(document, encoding="utf-8")
                with self.assertRaises(t.Invalid):
                    t.load(scratch)
        finally:
            scratch.unlink(missing_ok=True)

    def test_baseline_bytes_links_and_claims(self):
        manifest = t.load(ROOT / "examples" / "baseline.json")
        for approved in (False, True):
            manifest["approvalClaim"]["approved"] = approved
            result = t.check_baseline(manifest, ROOT)
            self.assertEqual("PASS", result["status"])
            self.assertFalse(result["productionApproved"])
            self.assertFalse(result["approvalClaimVerified"])
            self.assertEqual("INCONCLUSIVE", result["authorityStatus"])
        manifest["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaises(t.Invalid):
            t.check_baseline(manifest, ROOT)

    def test_baseline_missing_and_unbound(self):
        manifest = t.load(ROOT / "examples" / "baseline.json")
        manifest["artifacts"][0]["path"] = "missing-artifact.json"
        self.assertEqual("INCONCLUSIVE", t.check_baseline(manifest, ROOT)["status"])
        manifest = t.load(ROOT / "examples" / "baseline.json")
        manifest["artifacts"] = [a for a in manifest["artifacts"] if a["role"] != "adr"]
        with self.assertRaises(t.Invalid):
            t.check_baseline(manifest, ROOT)

    def test_confined_paths(self):
        for path in ("../file", "a/../file", "C:\\file", "\\\\host\\share", "/file", "file:stream", "a//b"):
            with self.subTest(path=path), self.assertRaises(t.Invalid):
                t.safe_path(ROOT, path)

    def test_cli_exit_codes_and_export_no_overwrite(self):
        model = str(ROOT / "examples" / "fee-decision.json")
        scratch = ROOT / ("test-scratch-" + uuid.uuid4().hex + ".json")
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, t.main(["validate", model]))
                self.assertEqual(2, t.main(["evaluate", model, "--input", str(ROOT / "examples" / "fee-input-incomplete.json")]))
                self.assertEqual(1, t.main(["check-trace", str(ROOT / "examples" / "fee-process.json"), "--input", str(ROOT / "examples" / "fee-trace-invalid.json")]))
                self.assertEqual(0, t.main(["export", model, "--output", str(scratch)]))
                before = scratch.read_bytes()
                self.assertEqual(1, t.main(["export", model, "--output", str(scratch)]))
                self.assertEqual(before, scratch.read_bytes())
                self.assertEqual(self.decision, t.load(scratch))
        finally:
            scratch.unlink(missing_ok=True)

    def test_candidate_mutants_disagree_with_manual_cases(self):
        cases = t.load(ROOT / "examples" / "fee-cases.json")["cases"]
        for mutation in ("rounding", "threshold", "inactive"):
            model = copy.deepcopy(self.decision)
            if mutation == "rounding":
                model["rules"][-1]["then"]["feeCents"]["rounding"] = "HALF_EVEN"
            elif mutation == "threshold":
                model["rules"][-2]["when"][0]["operator"] = "ge"
            else:
                model["rules"][5]["then"]["resultCode"]["constant"] = "APPROVE"
            self.assertTrue(any(t.evaluate(model, case["inputs"])["outputs"] != case["expected"] for case in cases), mutation)


if __name__ == "__main__":
    unittest.main()
