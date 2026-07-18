"""Offline validation for private-project promotion attestations."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping

import yaml

_CHECK_FIELDS = (
    "identity_verified",
    "authorization_verified",
    "redaction_reviewed",
    "secrets_externalized",
    "routes_reviewed",
    "mcp_boundaries_reviewed",
    "export_tests_passed",
)


@dataclass(frozen=True)
class PromotionAttestation:
    """Validated, non-secret promotion evidence."""

    project: str
    source_commit: str
    reviewer: str
    checks: dict[str, bool]
    risk_acceptance: dict[str, str] | None

    @property
    def approved(self) -> bool:
        """Return whether promotion is complete or explicitly risk-accepted."""
        return all(self.checks.values()) or self.risk_acceptance is not None

    def to_dict(self) -> dict[str, object]:
        """Return a stable, secret-free representation for audit output."""
        return {
            "project": self.project,
            "source_commit": self.source_commit,
            "reviewer": self.reviewer,
            **self.checks,
            "risk_acceptance": self.risk_acceptance,
            "approved": self.approved,
        }


def validate_promotion_attestation(payload: Mapping[str, Any]) -> PromotionAttestation:
    """Validate a promotion mapping without authenticating or accessing a project."""
    raw = payload.get("promotion")
    if not isinstance(raw, Mapping):
        raise ValueError("attestation must contain a promotion mapping")

    project = _required_text(raw, "project")
    if project.startswith("/") or ".." in Path(project).parts:
        raise ValueError("promotion project must be a qualified, non-absolute name")
    source_commit = _required_text(raw, "source_commit")
    reviewer = _required_text(raw, "reviewer")

    checks: dict[str, bool] = {}
    for field in _CHECK_FIELDS:
        value = raw.get(field)
        if not isinstance(value, bool):
            raise ValueError(f"promotion.{field} must be a boolean")
        checks[field] = value

    risk_acceptance = _risk_acceptance(raw.get("risk_acceptance"))
    if not all(checks.values()) and risk_acceptance is None:
        missing = ", ".join(field for field, value in checks.items() if not value)
        raise ValueError(f"incomplete promotion attestation without risk acceptance: {missing}")

    return PromotionAttestation(project, source_commit, reviewer, checks, risk_acceptance)


def load_promotion_attestation(path: Path) -> PromotionAttestation:
    """Load and validate one YAML attestation from an offline fixture or project."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"could not read promotion attestation: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("promotion attestation YAML must contain a mapping")
    return validate_promotion_attestation(payload)


def main(argv: list[str] | None = None) -> int:
    """Validate an attestation and emit JSON suitable for an offline gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attestation", type=Path)
    args = parser.parse_args(argv)
    try:
        result = load_promotion_attestation(args.attestation)
    except ValueError as exc:
        print(json.dumps({"approved": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_dict(), sort_keys=True))
    return 0


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"promotion.{key} must be non-empty text")
    return value.strip()


def _risk_acceptance(value: Any) -> dict[str, str] | None:
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
    if expiry_date < date.today():
        raise ValueError("promotion.risk_acceptance.expiry must not be in the past")
    return {"owner": owner, "rationale": rationale, "expiry": expiry}


__all__ = ["PromotionAttestation", "load_promotion_attestation", "main", "validate_promotion_attestation"]
