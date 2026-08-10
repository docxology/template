"""Typed, credential-free receipts for opt-in release rehearsals.

Receipts in this module describe evidence; they do not grant publication
authority. In particular, branch protection and private-sidecar promotion are
explicit authority fields and default to ``unavailable``. A local green test
run can therefore never silently become an administrator approval.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from infrastructure.core.subprocess_policy import (
    INTENTIONAL_SUBPROCESS_POLICIES,
    SubprocessPolicyRecord,
    validate_policy_inventory,
)

RELEASE_RECEIPT_SCHEMA = "template-release-receipt/v1"
ReceiptStatus = Literal["pass", "review_required", "blocked", "skipped"]
AuthorityStatus = Literal["confirmed", "unavailable", "blocked"]
_SECRET_PATTERN = re.compile(r"(?:token|secret|password|api[_-]?key|private[_-]?key)", re.IGNORECASE)


class ReleaseReceiptError(ValueError):
    """Raised when a receipt would make an unsafe or ambiguous claim."""


def _schema_errors(schema_version: str) -> list[str]:
    return [] if schema_version == RELEASE_RECEIPT_SCHEMA else [f"receipt schema must be {RELEASE_RECEIPT_SCHEMA}"]


def _status_errors(status: str, *, skip_reason: str) -> list[str]:
    errors: list[str] = []
    if status not in {"pass", "review_required", "blocked", "skipped"}:
        errors.append(f"invalid status: {status!r}")
    if status == "skipped" and not skip_reason.strip():
        errors.append("skipped receipts need an explicit skip_reason")
    if status == "pass" and skip_reason.strip():
        errors.append("passing receipts cannot carry a skip_reason")
    return errors


@dataclass(frozen=True)
class CommandReceipt:
    """Evidence for one command without recording secret environment values."""

    command: tuple[str, ...]
    status: ReceiptStatus
    exit_code: int | None
    duration_seconds: float
    skip_reason: str = ""
    output_sha256: str = ""

    def validate(self) -> list[str]:
        """Return actionable contract errors."""
        errors = _status_errors(self.status, skip_reason=self.skip_reason)
        if not self.command:
            errors.append("command must not be empty")
        if any(_SECRET_PATTERN.search(part) for part in self.command):
            errors.append("command contains a credential-like token or option")
        if self.duration_seconds < 0:
            errors.append("duration_seconds must be non-negative")
        if self.status == "pass" and self.exit_code != 0:
            errors.append("passing command receipts require exit_code=0")
        if self.status == "blocked" and self.exit_code == 0:
            errors.append("blocked command receipts cannot report exit_code=0")
        if self.output_sha256 and len(self.output_sha256) != 64:
            errors.append("output_sha256 must be a SHA-256 digest")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe representation."""
        return asdict(self) | {"command": list(self.command)}


@dataclass(frozen=True)
class ReleaseMetadataReceipt:
    """Release status plus explicit administrator-owned authority fields."""

    repository: str
    revision: str
    version: str
    status: ReceiptStatus
    branch_protection: AuthorityStatus = "unavailable"
    private_promotion: AuthorityStatus = "unavailable"
    authority_required: bool = True
    skip_reason: str = ""
    schema_version: str = RELEASE_RECEIPT_SCHEMA

    def validate(self) -> list[str]:
        """Return errors; authority is never inferred from local evidence."""
        errors = _schema_errors(self.schema_version)
        errors.extend(_status_errors(self.status, skip_reason=self.skip_reason))
        if not self.repository or not self.revision or not self.version:
            errors.append("repository, revision, and version are required")
        if self.branch_protection not in {"confirmed", "unavailable", "blocked"}:
            errors.append(f"invalid branch_protection status: {self.branch_protection!r}")
        if self.private_promotion not in {"confirmed", "unavailable", "blocked"}:
            errors.append(f"invalid private_promotion status: {self.private_promotion!r}")
        if self.status == "pass" and self.authority_required:
            if self.branch_protection != "confirmed":
                errors.append("passing release metadata requires administrator-confirmed branch protection")
            if self.private_promotion != "confirmed":
                errors.append("passing release metadata requires owner-confirmed private promotion status")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return deterministic receipt data."""
        return asdict(self)


@dataclass(frozen=True)
class CleanCheckoutReceipt:
    """Fresh-checkout rehearsal result with explicit unavailable-tool states."""

    revision: str
    platform: str
    status: ReceiptStatus
    runs: tuple[CommandReceipt, ...] = ()
    output_clean: bool = False
    skip_reason: str = ""
    schema_version: str = RELEASE_RECEIPT_SCHEMA

    def validate(self) -> list[str]:
        """Return errors, including the two-run determinism requirement."""
        errors = _schema_errors(self.schema_version)
        errors.extend(_status_errors(self.status, skip_reason=self.skip_reason))
        if not self.revision or not self.platform:
            errors.append("revision and platform are required")
        for run in self.runs:
            errors.extend(f"run: {error}" for error in run.validate())
        if self.status == "pass":
            if len(self.runs) < 2:
                errors.append("passing clean-checkout receipts require two deterministic runs")
            if any(run.status != "pass" for run in self.runs[:2]):
                errors.append("the first two clean-checkout runs must pass")
            if len(self.runs) >= 2 and self.runs[0].output_sha256 != self.runs[1].output_sha256:
                errors.append("the first two clean-checkout runs produced different deterministic output digests")
            if not self.output_clean:
                errors.append("passing clean-checkout receipts require clean outputs")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return deterministic receipt data."""
        return asdict(self) | {"runs": [run.to_dict() for run in self.runs]}


@dataclass(frozen=True)
class CoverageGapSnapshot:
    """Source-bound coverage-floor snapshot for release review."""

    revision: str
    infrastructure_percent: float | None
    infrastructure_floor: float
    projects: dict[str, float | None] = field(default_factory=dict)
    project_floors: dict[str, float] = field(default_factory=dict)
    status: ReceiptStatus = "review_required"
    skip_reason: str = ""
    schema_version: str = RELEASE_RECEIPT_SCHEMA

    def validate(self) -> list[str]:
        """Return errors without treating missing coverage as zero."""
        errors = _schema_errors(self.schema_version)
        errors.extend(_status_errors(self.status, skip_reason=self.skip_reason))
        if not self.revision:
            errors.append("revision is required")
        if self.infrastructure_percent is not None and self.infrastructure_percent < 0:
            errors.append("infrastructure coverage cannot be negative")
        for project, floor in self.project_floors.items():
            if project not in self.projects:
                errors.append(f"missing measured coverage for {project}")
            if floor < 0:
                errors.append(f"negative coverage floor for {project}")
        if self.status == "pass":
            if self.infrastructure_percent is None or self.infrastructure_percent < self.infrastructure_floor:
                errors.append("passing snapshot does not meet infrastructure coverage floor")
            for project, floor in self.project_floors.items():
                measured = self.projects.get(project)
                if measured is None or measured < floor:
                    errors.append(f"passing snapshot does not meet project floor for {project}")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return sorted project maps for deterministic serialization."""
        return asdict(self) | {
            "projects": dict(sorted(self.projects.items())),
            "project_floors": dict(sorted(self.project_floors.items())),
        }


@dataclass(frozen=True)
class SubprocessPolicyReceipt:
    """Versioned inventory of intentional subprocess wrappers."""

    policies: tuple[SubprocessPolicyRecord, ...]
    status: ReceiptStatus = "pass"
    skip_reason: str = ""
    schema_version: str = RELEASE_RECEIPT_SCHEMA

    def validate(self) -> list[str]:
        """Reject duplicate policy IDs and incomplete inventory rows."""
        errors = _schema_errors(self.schema_version)
        errors.extend(_status_errors(self.status, skip_reason=self.skip_reason))
        ids = [policy.policy_id for policy in self.policies]
        if len(ids) != len(set(ids)):
            errors.append("subprocess policy IDs must be unique")
        for policy in self.policies:
            if policy.timeout_seconds <= 0:
                errors.append(f"policy {policy.policy_id} has a non-positive timeout")
            if not policy.process_group:
                errors.append(f"policy {policy.policy_id} lacks a process-group boundary")
        return errors

    def to_dict(self) -> dict[str, object]:
        """Return deterministic policy records."""
        return asdict(self) | {
            "policies": [asdict(policy) for policy in sorted(self.policies, key=lambda item: item.policy_id)]
        }


def build_subprocess_policy_receipt(repo_root: Path | str | None = None) -> SubprocessPolicyReceipt:
    """Build a receipt from the source-owned intentional-wrapper inventory.

    A missing or invalid source declaration becomes ``blocked`` with its
    actionable diagnostics; it is never represented as a passing empty list.
    """
    root = Path(repo_root).resolve() if repo_root is not None else None
    errors = validate_policy_inventory(INTENTIONAL_SUBPROCESS_POLICIES, root)
    return SubprocessPolicyReceipt(
        policies=tuple(SubprocessPolicyRecord.from_policy(policy) for policy in INTENTIONAL_SUBPROCESS_POLICIES),
        status="pass" if not errors else "blocked",
        skip_reason="" if not errors else "; ".join(errors),
    )


def build_coverage_gap_snapshot(
    *,
    revision: str,
    infrastructure_percent: float | None,
    infrastructure_floor: float,
    projects: Mapping[str, float | None],
    project_floors: Mapping[str, float],
) -> CoverageGapSnapshot:
    """Build a coverage receipt without coercing unavailable values to zero."""
    snapshot = CoverageGapSnapshot(
        revision=revision,
        infrastructure_percent=infrastructure_percent,
        infrastructure_floor=infrastructure_floor,
        projects=dict(projects),
        project_floors=dict(project_floors),
    )
    errors = snapshot.validate()
    missing = []
    if infrastructure_percent is None:
        missing.append("infrastructure coverage unavailable")
    missing.extend(f"coverage unavailable for {project}" for project, value in projects.items() if value is None)
    if errors or missing:
        reasons = [*errors, *missing]
        return CoverageGapSnapshot(
            revision=revision,
            infrastructure_percent=infrastructure_percent,
            infrastructure_floor=infrastructure_floor,
            projects=dict(projects),
            project_floors=dict(project_floors),
            status="review_required",
            skip_reason="; ".join(reasons),
        )
    return snapshot


def write_receipt(path: Path | str, receipt: object) -> Path:
    """Write any receipt dataclass deterministically and return its path."""
    destination = Path(path)
    payload = receipt.to_dict() if hasattr(receipt, "to_dict") else receipt
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def receipt_digest(receipt: object) -> str:
    """Return a content digest for any serializable receipt."""
    payload = receipt.to_dict() if hasattr(receipt, "to_dict") else receipt
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


__all__ = [
    "AuthorityStatus",
    "CleanCheckoutReceipt",
    "CommandReceipt",
    "CoverageGapSnapshot",
    "RELEASE_RECEIPT_SCHEMA",
    "ReleaseMetadataReceipt",
    "ReleaseReceiptError",
    "ReceiptStatus",
    "SubprocessPolicyReceipt",
    "build_coverage_gap_snapshot",
    "build_subprocess_policy_receipt",
    "receipt_digest",
    "write_receipt",
]
