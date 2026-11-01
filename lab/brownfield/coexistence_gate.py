"""Synthetic brownfield cutover rehearsal; NOT a distributed lock or release approval.

The gate models routing decisions and fail-closed predicates. It cannot fence a
real legacy transaction processor: that requires a shared durable authority,
reconciliation and an approved operational cutover protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


class CutoverBlocked(ValueError):
    """A synthetic state transition lacks a required safety precondition."""


@dataclass(frozen=True)
class CutoverEvidence:
    """Fixture-level declarations, NOT independently signed or verified data."""

    source_epoch: int
    source_watermark: int
    target_watermark: int
    source_balances_sha256: str
    target_balances_sha256: str
    source_operations_sha256: str
    target_operations_sha256: str
    source_postings_sha256: str
    target_postings_sha256: str
    source_outbox_sha256: str
    target_outbox_sha256: str
    observed_source_count: int
    observed_target_count: int
    source_inflight_count: int
    target_inflight_count: int
    provenance: str


@dataclass
class Operation:
    fingerprint: str
    writer: str
    epoch: int
    status: str = "IN_FLIGHT"


class RehearsalGate:
    """Single-process simulation of a proposed capability-level writer boundary.

    Never use this in a deployed transaction path. Actual fencing must be
    enforced atomically by a shared authoritative system, not by Python memory.
    """

    scope = "SYNTHETIC_REHEARSAL_NOT_PRODUCTION"
    todm_g6 = "BLOCK"
    business_owner_approved = False

    def __init__(self) -> None:
        self.writer = "legacy"
        self.epoch = 1
        self.operations: dict[str, Operation] = {}
        self.ledger_watermark = 0
        self.projection_watermark = 0

    def route_transfer(self, operation_id: str, fingerprint: str, epoch: int) -> str:
        if not isinstance(operation_id, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", operation_id):
            raise ValueError("Invalid stable operation ID")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
            raise ValueError("Fingerprint must be the complete lowercase SHA-256 digest")
        if not isinstance(epoch, int) or isinstance(epoch, bool):
            raise ValueError("Invalid expected writer epoch")
        old = self.operations.get(operation_id)
        if old is not None:
            if old.fingerprint != fingerprint:
                return "ID_CONFLICT"
            if old.status == "UNKNOWN":
                return "UNKNOWN_REQUIRES_RECONCILIATION"
            if old.status == "IN_FLIGHT":
                return "IN_FLIGHT_RETRY_BLOCKED"
            return "DUPLICATE_" + old.status
        if epoch != self.epoch:
            return "FENCED_STALE_EPOCH"
        self.operations[operation_id] = Operation(fingerprint, self.writer, self.epoch)
        return "ROUTE_" + self.writer.upper()

    def record_outcome(self, operation_id: str, outcome: str) -> None:
        item = self.operations.get(operation_id)
        if item is None or item.status != "IN_FLIGHT":
            raise CutoverBlocked("Outcome requires a tracked in-flight operation")
        if outcome not in {"COMMITTED", "REJECTED", "UNKNOWN"}:
            raise CutoverBlocked("Unrecognized outcome")
        item.status = outcome
        if outcome == "COMMITTED":
            self.ledger_watermark += 1

    def reconcile_unknown(self, operation_id: str, durable_outcome: str, *, evidence_id: str) -> None:
        item = self.operations.get(operation_id)
        if item is None or item.status != "UNKNOWN":
            raise CutoverBlocked("Only uncertain operations can be reconciled")
        if durable_outcome not in {"COMMITTED", "REJECTED"}:
            raise CutoverBlocked("Unknown must resolve to a durable decision")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise CutoverBlocked("An explicit synthetic reconciliation observation is required")
        # This evidence_id is a test fixture reference, not a verified SQL audit.
        item.status = durable_outcome
        if durable_outcome == "COMMITTED":
            self.ledger_watermark += 1

    def read_projection(self, minimum_version: int) -> str:
        if not isinstance(minimum_version, int) or isinstance(minimum_version, bool) or minimum_version < 0:
            raise ValueError("Invalid minimum version")
        return "PROJECTED" if self.projection_watermark >= minimum_version else "STALE_PROJECTION"

    def catch_up_projection(self, version: int) -> None:
        if not isinstance(version, int) or isinstance(version, bool) or version < self.projection_watermark or version > self.ledger_watermark:
            raise CutoverBlocked("Projection version cannot regress or exceed the ledger")
        self.projection_watermark = version

    def assess_cutover(self, target: str, evidence: CutoverEvidence) -> tuple[str, ...]:
        """Return blocking reasons, not approval and not a real database observation."""
        reasons = []
        if target not in {"legacy", "candidate"} or target == self.writer:
            reasons.append("INVALID_TARGET")
        if any(op.status == "IN_FLIGHT" for op in self.operations.values()):
            reasons.append("IN_FLIGHT_COMMANDS")
        if any(op.status == "UNKNOWN" for op in self.operations.values()):
            reasons.append("UNRESOLVED_UNKNOWN_COMMANDS")
        if not isinstance(evidence, CutoverEvidence):
            reasons.append("MISSING_RECONCILIATION")
            return tuple(reasons)
        if evidence.source_epoch != self.epoch:
            reasons.append("STALE_AUTHORITY_EPOCH")
        for count in (evidence.observed_source_count, evidence.observed_target_count,
                      evidence.source_inflight_count, evidence.target_inflight_count):
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                reasons.append("INVALID_COUNTS")
                break
        if (evidence.source_inflight_count != 0 or evidence.target_inflight_count != 0):
            reasons.append("UNRECONCILED_INFLIGHT")
        if evidence.observed_source_count != evidence.observed_target_count:
            reasons.append("OPERATION_COUNT_MISMATCH")
        if (not isinstance(evidence.source_watermark, int) or
            not isinstance(evidence.target_watermark, int) or
            isinstance(evidence.source_watermark, bool) or
            isinstance(evidence.target_watermark, bool) or
            evidence.source_watermark < 0 or
            evidence.source_watermark != evidence.target_watermark or
            evidence.source_watermark != self.ledger_watermark):
            reasons.append("WATERMARK_MISMATCH")
        for field in ("balances", "operations", "postings", "outbox"):
            a = getattr(evidence, f"source_{field}_sha256")
            b = getattr(evidence, f"target_{field}_sha256")
            if (not isinstance(a, str) or not isinstance(b, str) or
                not re.fullmatch(r"[a-f0-9]{64}", a) or a != b):
                reasons.append(field.upper() + "_MISMATCH")
        if not isinstance(evidence.provenance, str) or not evidence.provenance.startswith("synthetic-fixture:"):
            reasons.append("MISSING_SYNTHETIC_PROVENANCE")
        return tuple(reasons)

    def rehearse_cutover(self, target: str, evidence: CutoverEvidence) -> int:
        blockers = self.assess_cutover(target, evidence)
        if blockers:
            raise CutoverBlocked(",".join(blockers))
        self.writer = target
        self.epoch += 1
        # Not a production promotion: G6 is permanently BLOCK in this rehearsal.
        return self.epoch
