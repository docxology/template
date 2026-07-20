"""Fail-closed candidate security gate for private-project promotion."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import yaml

from infrastructure.project.promotion.models import PromotionGateReport, SecurityTodoFinding

PROMOTION_CHECKS: tuple[str, ...] = (
    "authentication",
    "authorization",
    "redaction",
    "secret_store",
    "route_handlers",
    "mcp",
    "export_tests",
)

_ALLOWED_CHECK_STATUSES = frozenset({"closed", "not-applicable", "risk-accepted"})
_SCANNED_SUFFIXES = frozenset(
    {".go", ".java", ".js", ".jsx", ".lean", ".md", ".py", ".rs", ".sh", ".toml", ".ts", ".tsx", ".yaml", ".yml"}
)
_SKIP_PARTS = frozenset({".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "node_modules", "output"})
_MAX_TEXT_BYTES = 2_000_000
_TODO_MARKER = re.compile(r"\b(?:TODO|FIXME|XXX)\b", flags=re.IGNORECASE)
_SECURITY_TERM = re.compile(
    r"\b(?:auth(?:entication|orization)?|credential|export[ _-]?test|mcp|permission|redact(?:ion)?|"
    r"route[ _-]?handler|secret|security|access[ _-]?control)\b",
    flags=re.IGNORECASE,
)


def _candidate_files(project_root: Path, attestation_path: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for path in sorted(project_root.rglob("*")):
        relative = path.relative_to(project_root)
        if any(part in _SKIP_PARTS for part in relative.parts):
            continue
        if path == attestation_path:
            continue
        if path.is_symlink():
            errors.append(f"candidate contains a symlink that cannot cross the public boundary: {relative.as_posix()}")
            continue
        if not path.is_file() or path.suffix.lower() not in _SCANNED_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            errors.append(f"candidate file cannot be inspected: {relative.as_posix()}")
            continue
        if size > _MAX_TEXT_BYTES:
            errors.append(f"candidate text file exceeds the promotion scan limit: {relative.as_posix()}")
            continue
        files.append(path)
    return files, errors


def scan_security_todos(
    project_root: Path,
    *,
    attestation_path: Path | None = None,
) -> tuple[tuple[SecurityTodoFinding, ...], tuple[str, ...]]:
    """Find unresolved security TODO markers without returning source content."""
    root = project_root.resolve()
    attestation = (attestation_path or root / "promotion-security.yaml").resolve()
    files, errors = _candidate_files(root, attestation)
    findings: list[SecurityTodoFinding] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            errors.append(f"candidate text file cannot be decoded as UTF-8: {relative}")
            continue
        for line_number, line in enumerate(lines, start=1):
            if _TODO_MARKER.search(line) and _SECURITY_TERM.search(line):
                finding_id = f"{relative}:{line_number}"
                findings.append(SecurityTodoFinding(finding_id=finding_id, path=relative, line=line_number))
    return tuple(findings), tuple(errors)


def check_private_project_promotion(
    project_root: Path,
    *,
    attestation_path: Path | None = None,
    as_of: date | None = None,
) -> PromotionGateReport:
    """Evaluate a private candidate against the complete security contract."""
    requested_root = project_root.expanduser()
    root = requested_root.resolve()
    attestation = (attestation_path or root / "promotion-security.yaml").expanduser().resolve()
    today = as_of or date.today()
    errors: list[str] = []
    if not root.is_dir():
        return PromotionGateReport(
            project=requested_root.name,
            attestation=str(attestation),
            findings=(),
            errors=("candidate project directory does not exist",),
        )
    try:
        attestation.relative_to(root)
    except ValueError:
        errors.append("promotion attestation must live inside the candidate project")

    payload = _load_attestation(attestation, errors)
    if payload.get("schema_version") != 1:
        errors.append("promotion attestation schema_version must equal 1")
    if payload.get("project") != root.name:
        errors.append("promotion attestation project must match the candidate directory name")

    review = payload.get("review")
    if not isinstance(review, Mapping):
        errors.append("promotion attestation review must be a mapping")
    else:
        if _text(review.get("reviewed_by")) is None:
            errors.append("promotion attestation review.reviewed_by must be non-empty")
        reviewed_at = _parse_date(review.get("reviewed_at"), field="review.reviewed_at", errors=errors)
        if reviewed_at is not None and reviewed_at > today:
            errors.append("promotion attestation review.reviewed_at cannot be in the future")

    checks = payload.get("checks")
    if not isinstance(checks, Mapping):
        errors.append("promotion attestation checks must be a mapping")
        checks = {}
    missing_checks = sorted(set(PROMOTION_CHECKS) - set(checks))
    unknown_checks = sorted(set(checks) - set(PROMOTION_CHECKS))
    if missing_checks:
        errors.append(f"promotion attestation is missing checks: {', '.join(missing_checks)}")
    if unknown_checks:
        errors.append(f"promotion attestation has unknown checks: {', '.join(unknown_checks)}")
    for check in PROMOTION_CHECKS:
        if check in checks:
            _validate_resolution(
                checks[check],
                field=f"checks.{check}",
                as_of=today,
                allowed_statuses=_ALLOWED_CHECK_STATUSES,
                errors=errors,
            )

    findings, scan_errors = scan_security_todos(root, attestation_path=attestation)
    errors.extend(scan_errors)
    accepted_findings = payload.get("security_findings", {})
    if not isinstance(accepted_findings, Mapping):
        errors.append("promotion attestation security_findings must be a mapping")
        accepted_findings = {}
    live_ids = {finding.finding_id for finding in findings}
    stale_ids = sorted(set(accepted_findings) - live_ids)
    if stale_ids:
        errors.append(f"promotion attestation contains stale security findings: {', '.join(stale_ids)}")
    for finding in findings:
        resolution = accepted_findings.get(finding.finding_id)
        if resolution is None:
            errors.append(f"unresolved security TODO requires risk acceptance: {finding.finding_id}")
            continue
        _validate_resolution(
            resolution,
            field=f"security_findings.{finding.finding_id}",
            as_of=today,
            allowed_statuses=frozenset({"risk-accepted"}),
            errors=errors,
        )

    return PromotionGateReport(
        project=root.name,
        attestation=str(attestation),
        findings=findings,
        errors=tuple(errors),
    )


def render_promotion_report(report: PromotionGateReport) -> str:
    """Render a concise report that never includes candidate source content."""
    status = "PASS" if report.eligible else "FAIL"
    lines = [
        f"{status} private-project promotion gate: {report.project}",
        f"Security TODO findings: {len(report.findings)}",
    ]
    lines.extend(f"- {error}" for error in report.errors)
    return "\n".join(lines)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _parse_date(value: object, *, field: str, errors: list[str]) -> date | None:
    text = _text(value)
    if text is None:
        errors.append(f"{field} must be an ISO date")
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        errors.append(f"{field} must be an ISO date")
        return None


def _validate_resolution(
    value: object,
    *,
    field: str,
    as_of: date,
    allowed_statuses: frozenset[str],
    errors: list[str],
) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{field} must be a mapping")
        return
    status = _text(value.get("status"))
    if status not in allowed_statuses:
        errors.append(f"{field}.status must be one of: {', '.join(sorted(allowed_statuses))}")
        return
    if _text(value.get("evidence")) is None:
        errors.append(f"{field}.evidence must be non-empty")
    if status != "risk-accepted":
        return
    if _text(value.get("rationale")) is None:
        errors.append(f"{field}.rationale is required for risk acceptance")
    if _text(value.get("accepted_by")) is None:
        errors.append(f"{field}.accepted_by is required for risk acceptance")
    expires = _parse_date(value.get("expires"), field=f"{field}.expires", errors=errors)
    if expires is not None and expires < as_of:
        errors.append(f"{field}.expires is stale as of {as_of.isoformat()}")


def _load_attestation(path: Path, errors: list[str]) -> Mapping[str, object]:
    if not path.is_file():
        errors.append(f"promotion attestation does not exist: {path.name}")
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        errors.append(f"promotion attestation is not valid UTF-8 YAML: {path.name}")
        return {}
    if not isinstance(payload, Mapping):
        errors.append("promotion attestation root must be a mapping")
        return {}
    return payload


__all__ = [
    "PROMOTION_CHECKS",
    "check_private_project_promotion",
    "render_promotion_report",
    "scan_security_todos",
]
