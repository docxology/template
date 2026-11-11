"""Structural validation for GitHub + Zenodo release pairing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from infrastructure.publishing.zenodo_urls import zenodo_record_url_from_doi


@dataclass(frozen=True)
class PairingCheck:
    """Single pairing validation check."""

    name: str
    label: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class PairingReport:
    """Aggregate pairing validation result."""

    valid: bool
    checks: tuple[PairingCheck, ...]


def _non_empty(value: Any) -> bool:
    return bool(str(value or "").strip())


def validate_release_pairing(current: Mapping[str, Any], *, require_doi: bool) -> PairingReport:
    """Validate cross-platform release linkage fields."""
    doi = str(current.get("doi") or "").strip()
    github_release_url = str(current.get("github_release_url") or "").strip()
    pdf_sha256 = str(current.get("pdf_sha256") or "").strip()
    zenodo_record_url = str(current.get("zenodo_record_url") or "").strip()
    expected_zenodo = zenodo_record_url_from_doi(doi) if doi else ""

    checks: list[PairingCheck] = [
        PairingCheck(
            name="doi",
            label="DOI minted",
            passed=_non_empty(doi),
            detail=doi or "pending",
        ),
        PairingCheck(
            name="github_release_url",
            label="GitHub release URL",
            passed=_non_empty(github_release_url),
            detail=github_release_url or "pending",
        ),
        PairingCheck(
            name="pdf_sha256",
            label="PDF SHA-256",
            passed=_non_empty(pdf_sha256),
            detail=pdf_sha256[:16] + "…" if len(pdf_sha256) > 16 else (pdf_sha256 or "pending"),
        ),
        PairingCheck(
            name="zenodo_record_url",
            label="Zenodo record URL",
            passed=not doi or (zenodo_record_url == expected_zenodo if zenodo_record_url else bool(expected_zenodo)),
            detail=zenodo_record_url or expected_zenodo or "pending",
        ),
    ]

    if not doi:
        valid = False
    else:
        valid = all(check.passed for check in checks)

    return PairingReport(valid=valid, checks=tuple(checks))


def format_pairing_checklist(report: PairingReport) -> str:
    """Render pairing checks as markdown bullet list."""
    lines = ["### Pairing validation", ""]
    for check in report.checks:
        marker = "✓" if check.passed else "✗"
        lines.append(f"- {marker} **{check.label}**: `{check.detail}`")
    status = "complete" if report.valid else "pending"
    lines.extend(["", f"**Status:** {status}"])
    return "\n".join(lines)


def format_pairing_checklist_compact(report: PairingReport) -> str:
    """Render pairing status for single-page bookends (failures only + one-line status)."""
    status = "complete" if report.valid else "pending"
    failed = [check for check in report.checks if not check.passed]
    if not failed:
        return f"**Pairing:** {status} (DOI, GitHub, SHA-256, Zenodo URL)"
    lines = [f"**Pairing:** {status} — unresolved:"]
    for check in failed:
        lines.append(f"- ✗ {check.label}: `{check.detail}`")
    return "\n".join(lines)
