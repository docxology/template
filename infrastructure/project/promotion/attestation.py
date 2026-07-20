"""Offline orchestration-attestation contract for private-project promotion."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from infrastructure.project.promotion.models import PromotionAttestation

ATTESTATION_CHECK_FIELDS: tuple[str, ...] = (
    "identity_verified",
    "authorization_verified",
    "redaction_reviewed",
    "secrets_externalized",
    "routes_reviewed",
    "mcp_boundaries_reviewed",
    "export_tests_passed",
)


def validate_promotion_attestation(
    payload: Mapping[str, Any],
    *,
    as_of: date | None = None,
) -> PromotionAttestation:
    """Validate a promotion mapping without authenticating or accessing a project."""
    raw = payload.get("promotion")
    if not isinstance(raw, Mapping):
        raise ValueError("attestation must contain a promotion mapping")

    project = _required_text(raw, "project")
    project_path = Path(project)
    if project_path.is_absolute() or ".." in project_path.parts or len(project_path.parts) < 2:
        raise ValueError("promotion project must be a qualified, non-absolute name")
    source_commit = _required_text(raw, "source_commit")
    reviewer = _required_text(raw, "reviewer")

    checks: dict[str, bool] = {}
    for field in ATTESTATION_CHECK_FIELDS:
        value = raw.get(field)
        if not isinstance(value, bool):
            raise ValueError(f"promotion.{field} must be a boolean")
        checks[field] = value

    risk_acceptance = _risk_acceptance(raw.get("risk_acceptance"), as_of=as_of or date.today())
    if not all(checks.values()) and risk_acceptance is None:
        missing = ", ".join(field for field, value in checks.items() if not value)
        raise ValueError(f"incomplete promotion attestation without risk acceptance: {missing}")

    return PromotionAttestation(project, source_commit, reviewer, checks, risk_acceptance)


def load_promotion_attestation(
    path: Path,
    *,
    as_of: date | None = None,
) -> PromotionAttestation:
    """Load and validate one YAML attestation from an offline fixture or project."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"could not read promotion attestation: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("promotion attestation YAML must contain a mapping")
    return validate_promotion_attestation(payload, as_of=as_of)


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"promotion.{key} must be non-empty text")
    return value.strip()


def _risk_acceptance(value: Any, *, as_of: date) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("promotion.risk_acceptance must be a mapping or null")
    owner = _required_text(value, "owner")
    rationale = _required_text(value, "rationale")
    expiry = _required_text(value, "expiry")
    try:
        expiry_date = date.fromisoformat(expiry)
    except ValueError as exc:
        raise ValueError("promotion.risk_acceptance.expiry must be ISO date YYYY-MM-DD") from exc
    if expiry_date < as_of:
        raise ValueError("promotion.risk_acceptance.expiry must not be in the past")
    return {"owner": owner, "rationale": rationale, "expiry": expiry}


__all__ = [
    "ATTESTATION_CHECK_FIELDS",
    "load_promotion_attestation",
    "validate_promotion_attestation",
]
