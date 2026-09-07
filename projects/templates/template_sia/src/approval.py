"""Fail-closed sandbox, diff, rollback, and approval contract for SIA forks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal, Mapping

APPROVAL_SCHEMA = "template-sia/approval-contract/1"
ApprovalMode = Literal["fixture_replay", "live_proposal", "live_apply"]
ApprovalStatus = Literal["not_required", "pending", "approved", "rejected"]
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ApprovalContract:
    """Typed evidence required before a fork can apply generated mutations."""

    mode: ApprovalMode
    sandbox_root: str = ""
    diff_sha256: str = ""
    rollback_sha256: str = ""
    approval_status: ApprovalStatus = "not_required"
    approval_receipt_id: str = ""
    schema_version: str = APPROVAL_SCHEMA

    def validate(self) -> tuple[str, ...]:
        """Return actionable failures without granting approval implicitly."""
        issues: list[str] = []
        if self.schema_version != APPROVAL_SCHEMA:
            issues.append(f"schema_version must be {APPROVAL_SCHEMA}")
        if self.mode not in {"fixture_replay", "live_proposal", "live_apply"}:
            issues.append(f"unknown approval mode: {self.mode!r}")
        if self.approval_status not in {"not_required", "pending", "approved", "rejected"}:
            issues.append(f"unknown approval status: {self.approval_status!r}")
        if self.mode == "fixture_replay":
            if self.approval_status != "not_required":
                issues.append("fixture replay must not claim a human approval")
            return tuple(issues)

        if not self.sandbox_root.strip():
            issues.append("live proposal/apply requires a sandbox_root")
        if not _DIGEST.fullmatch(self.diff_sha256):
            issues.append("live proposal/apply requires a SHA-256 diff digest")
        if not _DIGEST.fullmatch(self.rollback_sha256):
            issues.append("live proposal/apply requires a SHA-256 rollback digest")
        if self.mode == "live_apply":
            if self.approval_status != "approved":
                issues.append("live_apply requires approval_status='approved'")
            if not self.approval_receipt_id.strip():
                issues.append("live_apply requires an approval_receipt_id")
        elif self.approval_status == "approved" and not self.approval_receipt_id.strip():
            issues.append("approved live proposals require an approval_receipt_id")
        return tuple(issues)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, credential-free approval payload."""
        return asdict(self)


def validate_approval_contract(payload: Mapping[str, object]) -> tuple[str, ...]:
    """Validate a JSON-shaped approval payload without executing mutations."""
    try:
        contract = ApprovalContract(
            mode=str(payload.get("mode", "")),  # type: ignore[arg-type]
            sandbox_root=str(payload.get("sandbox_root", "")),
            diff_sha256=str(payload.get("diff_sha256", "")),
            rollback_sha256=str(payload.get("rollback_sha256", "")),
            approval_status=str(payload.get("approval_status", "not_required")),  # type: ignore[arg-type]
            approval_receipt_id=str(payload.get("approval_receipt_id", "")),
            schema_version=str(payload.get("schema_version", "")),
        )
    except (TypeError, ValueError) as exc:
        return (f"invalid approval payload: {exc}",)
    return contract.validate()


__all__ = ["APPROVAL_SCHEMA", "ApprovalContract", "validate_approval_contract"]
