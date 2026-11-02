"""TODM-inspired G0-G7 synthetic assurance layer, with separate Golden Master.

This is NOT the TODM research engine, production identity enforcement,
cryptographic signoff, domain acceptance, or a release authorization.
See https://github.com/jmfloreszazo/TODM (v1.5.0 method).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from contract_oracle import OracleFailure, verify

GATES = ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7")

class AssuranceError(ValueError):
    pass

def digest(document: object) -> str:
    # Not a signature and cannot prove approval; simply an audit fingerprint.
    serialized = json.dumps(document, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

def characterize(contract: dict, golden_master: dict) -> dict:
    if not isinstance(golden_master, dict) or set(golden_master) != {
        "classification", "sourceId", "recordedAt", "provenance", "observations"
    }:
        raise AssuranceError("Missing or unexpected Golden Master metadata")
    if golden_master["classification"] != "SYNTHETIC_GOLDEN_MASTER_NOT_REAL_OBSERVATION":
        raise AssuranceError("Cannot promote unverified capture to real observation")
    for key in ("sourceId", "recordedAt", "provenance"):
        if not isinstance(golden_master[key], str) or not golden_master[key].strip():
            raise AssuranceError(f"Missing Golden Master provenance: {key}")
    observations = golden_master["observations"]
    if not isinstance(observations, list) or not observations:
        raise AssuranceError("Golden Master must explicitly describe test observations")
    expected = contract["expected"]["results"]
    mismatches = []
    matches = []
    seen = set()
    for item in observations:
        if not isinstance(item, dict) or set(item) != {"stepIndex", "observed"}:
            raise AssuranceError("Malformed Golden Master observation")
        idx = item["stepIndex"]
        if type(idx) is not int or idx in seen or not 0 <= idx < len(expected):
            raise AssuranceError("Duplicate or invalid observation index")
        seen.add(idx)
        output = item["observed"]
        if (not isinstance(output, dict) or
            not {"status", "version"} <= set(output) or
            not set(output) <= {"status", "version", "balance"} or
            not isinstance(output["status"], str) or
            type(output["version"]) is not int or
            ("balance" in output and type(output["balance"]) is not int)):
            raise AssuranceError("Golden Master result has invalid business observation schema")
        entry = {"stepIndex": idx, "expected": expected[idx],
                 "characterized": output}
        (matches if output == expected[idx] else mismatches).append(entry)
    return {
        "classification": "SYNTHETIC_CHARACTERIZATION_NOT_POLICY",
        "compared": len(observations), "matches": matches,
        "disagreements": mismatches, "captureFingerprintSha256": digest(golden_master),
    }

def evaluate(contract: dict, candidate: dict, golden_master: dict) -> dict:
    if contract.get("classification") != "SYNTHETIC_UNAPPROVED_CAPABILITY_CONTRACT":
        raise AssuranceError("Unapproved synthetic contract classification required")
    characterized = characterize(contract, golden_master)
    try:
        verify(contract, candidate)
        oracle = "PASS"
        reason = "Synthetic candidate matches independent reference outcomes and invariants"
    except (OracleFailure, KeyError, TypeError, ValueError) as exc:
        oracle = "FAIL"
        reason = f"Synthetic independent oracle rejected output: {exc}"

    # G0..G7 are method-stage mapping, not evidence of complete TODM conformance.
    gates = {
        "G0": {"verdict": "PASS", "reason": "Explicitly bounded synthetic scope only"},
        "G1": {"verdict": "INCONCLUSIVE",
               "reason": "Golden Master is simulated, not actual authorized legacy observations"},
        "G2": {"verdict": "INCONCLUSIVE",
               "reason": "No independent accountable business-owner baseline approval or protected attestation"},
        "G3": {"verdict": "INCONCLUSIVE",
               "reason": "Oracle mutation tests require independently verified CI provenance; no signed qualification"},
        "G4": {"verdict": "INCONCLUSIVE",
               "reason": "Construction provenance and mandate are not independently attested"},
        "G5": {"verdict": oracle, "reason": reason},
        "G6": {"verdict": "BLOCK",
               "reason": "Release forbidden: G1/G2/G3/G4 and separate human authorization not satisfied"},
        "G7": {"verdict": "INCONCLUSIVE",
               "reason": "No deployment, production observation or drift-monitoring evidence"},
    }
    assert set(gates) == set(GATES)
    return {
        "method": "TODM_G0_G7_STAGE_MAPPING_NOT_TODM_ENGINE",
        "baselineClassification": contract["classification"],
        "referenceContractSha256": digest(contract),
        "candidateSha256": digest(candidate),
        "goldenMaster": characterized,
        "gates": gates,
        "independentOracleVerdict": oracle,
        "releaseAuthorization": "BLOCK",
        "productionApproved": False,
        "negativeEvidencePreserved": True,
        "warning": ("A passing synthetic G5 demonstrates only this local contract. "
                    "Golden Master is characterization, not independent business truth. "
                    "G6 remains BLOCK until independently attested approval and human release."),
    }
