"""Validation for deterministic AutoResearch readiness plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from infrastructure.autoresearch.models import (
    KNOWN_QUALITY_CHECKS,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
)
from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    ArtifactManifestEntry,
    validate_artifact_manifest,
)
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.drift.models import Report
from infrastructure.project.drift.orchestrator import check_project_scripts, check_repo_scripts
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan
from infrastructure.validation.evidence_registry import build_project_evidence_registry

ValidationPhase = Literal["all", "intrinsic", "extrinsic"]

INTRINSIC_QUALITY_CHECKS = frozenset({"domain_profile", "experiment_plan", "pipeline_contracts", "thin_orchestrators"})
EXTRINSIC_QUALITY_CHECKS = frozenset({"evidence_registry", "artifact_manifest"})


def validate_autoresearch_plan(
    plan: AutoResearchPlan,
    project_root: Path,
    *,
    phase: ValidationPhase = "all",
) -> AutoResearchReport:
    """Validate an AutoResearch plan against deterministic repository surfaces."""
    if not plan.config.enabled:
        return AutoResearchReport(project_name=plan.project_name, valid=True, plan=plan)

    issues: list[AutoResearchIssue] = []
    stage_names = {stage.name for stage in plan.stages}
    for stage_name in plan.stage_gates:
        if stage_name not in stage_names:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.STAGE_UNKNOWN",
                    f"stage_gates entry does not match a pipeline stage: {stage_name}",
                    plan.config.source_path or "autoresearch.yaml",
                    "Use an exact stage name from pipeline.yaml.",
                )
            )

    for check in plan.quality_checks:
        if check not in KNOWN_QUALITY_CHECKS:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.QUALITY_CHECK_UNKNOWN",
                    f"unknown quality check: {check}",
                    plan.config.source_path or "autoresearch.yaml",
                    f"Use one of: {', '.join(sorted(KNOWN_QUALITY_CHECKS))}.",
                )
            )

    active_checks = _checks_for_phase(plan.quality_checks, phase)
    if "domain_profile" in active_checks:
        _validate_domain_profile(project_root, issues)
    if "experiment_plan" in active_checks:
        _validate_experiment_plan(project_root, plan, issues)
    if "pipeline_contracts" in active_checks:
        _validate_pipeline_contracts(plan, issues)
    if "evidence_registry" in active_checks:
        _validate_evidence_registry(project_root, plan, issues)
    if "artifact_manifest" in active_checks:
        _validate_artifact_manifest(project_root, plan, issues)
    if "thin_orchestrators" in active_checks:
        _validate_thin_orchestrators(plan, issues)

    valid = not any(issue.severity == "error" for issue in issues)
    return AutoResearchReport(project_name=plan.project_name, valid=valid, issues=tuple(issues), plan=plan)


def _checks_for_phase(
    quality_checks: tuple[str, ...],
    phase: ValidationPhase,
) -> frozenset[str]:
    configured = frozenset(quality_checks)
    if phase == "all":
        return configured
    if phase == "intrinsic":
        return configured & INTRINSIC_QUALITY_CHECKS
    return configured & EXTRINSIC_QUALITY_CHECKS


def _validate_domain_profile(project_root: Path, issues: list[AutoResearchIssue]) -> None:
    try:
        load_domain_profile(project_root)
    except ValueError as exc:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.DOMAIN_PROFILE",
                str(exc),
                str(project_root / "domain_profile.yaml"),
                "Fix the domain profile schema.",
            )
        )


def _validate_experiment_plan(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    try:
        experiment_plan = load_experiment_plan(project_root)
        result = validate_experiment_plan(experiment_plan)
    except ValueError as exc:
        issues.append(
            _issue(
                "error",
                "AUTORESEARCH.EXPERIMENT_PLAN",
                str(exc),
                str(project_root / "experiment_plan.yaml"),
                "Fix the experiment plan schema.",
            )
        )
        return
    severity = _strict_severity(plan)
    for message in result.issues:
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.EXPERIMENT_PLAN",
                message,
                str(project_root / "experiment_plan.yaml"),
                "Declare a complete deterministic experiment design.",
            )
        )


def _validate_pipeline_contracts(plan: AutoResearchPlan, issues: list[AutoResearchIssue]) -> None:
    severity = _strict_severity(plan)
    for stage in plan.stages:
        if not stage.definition_of_done.strip():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.CONTRACT_MISSING_DONE",
                    f"pipeline stage lacks definition_of_done: {stage.name}",
                    "pipeline.yaml",
                    "Add a concrete definition_of_done to the stage contract.",
                )
            )
        if not stage.output_artifacts:
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.CONTRACT_MISSING_OUTPUTS",
                    f"pipeline stage lacks output_artifacts: {stage.name}",
                    "pipeline.yaml",
                    "Declare the stage output artifacts.",
                )
            )


def _validate_evidence_registry(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    registry = build_project_evidence_registry(project_root)
    if registry.facts():
        return
    issues.append(
        _issue(
            _strict_severity(plan),
            "AUTORESEARCH.EVIDENCE_REGISTRY_EMPTY",
            "evidence registry has no registered project facts",
            str(project_root / "output" / "reports" / "evidence_registry.json"),
            "Generate or register artifact-backed manuscript facts before publication.",
        )
    )


def _validate_artifact_manifest(
    project_root: Path,
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    severity = _strict_severity(plan)
    manifest_path = project_root / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.exists():
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.ARTIFACT_MANIFEST_MISSING",
                "artifact manifest is missing",
                str(manifest_path),
                "Run the pipeline or refresh output artifact manifests.",
            )
        )
    else:
        try:
            manifest = _read_artifact_manifest(manifest_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            issues.append(
                _issue(
                    "error",
                    "AUTORESEARCH.ARTIFACT_MANIFEST_INVALID",
                    f"artifact manifest cannot be parsed: {exc}",
                    str(manifest_path),
                    "Regenerate the artifact manifest.",
                )
            )
        else:
            report = validate_artifact_manifest(manifest, project_dir=project_root)
            for message in report.issues:
                issues.append(
                    _issue(
                        severity,
                        "AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE",
                        message,
                        str(manifest_path),
                        "Regenerate declared outputs or update the stage contract.",
                    )
                )

    for artifact in plan.required_artifacts:
        artifact_path = _artifact_path(project_root, artifact)
        if not artifact_path.exists():
            issues.append(
                _issue(
                    severity,
                    "AUTORESEARCH.ARTIFACT_MISSING",
                    f"required artifact is missing: {artifact}",
                    artifact,
                    "Run the producing pipeline stage or correct required_artifacts.",
                )
            )


def _validate_thin_orchestrators(
    plan: AutoResearchPlan,
    issues: list[AutoResearchIssue],
) -> None:
    drift_report = Report()
    check_project_scripts(plan.project_root, plan.repo_root, drift_report, plan.project_name)
    check_repo_scripts(plan.repo_root, drift_report)
    for finding in (*drift_report.errors(), *drift_report.warnings()):
        severity = "error" if finding.severity == "ERROR" and plan.config.strict else "warning"
        issues.append(
            _issue(
                severity,
                "AUTORESEARCH.THIN_ORCHESTRATOR",
                finding.message,
                finding.project,
                "Move reusable logic into infrastructure/ or project src/ modules.",
            )
        )


def _artifact_path(project_root: Path, artifact: str) -> Path:
    path = Path(artifact)
    if path.is_absolute():
        return path
    return project_root / path


def _read_artifact_manifest(path: Path) -> ArtifactManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a mapping")
    entries = tuple(_entry_from_payload(row) for row in payload.get("entries", []) if isinstance(row, dict))
    issues = tuple(str(issue) for issue in payload.get("issues", []))
    return ArtifactManifest(entries=entries, issues=issues)


def _entry_from_payload(row: dict[str, Any]) -> ArtifactManifestEntry:
    return ArtifactManifestEntry(
        path=str(row.get("path", "")),
        size_bytes=int(row.get("size_bytes", 0) or 0),
        sha256=str(row.get("sha256", "")),
        stage_num=int(row.get("stage_num", 0) or 0),
        stage_name=str(row.get("stage_name", "")),
        contract_match=bool(row.get("contract_match", False)),
        timestamp=str(row.get("timestamp", "")),
    )


def _strict_severity(plan: AutoResearchPlan) -> str:
    return "error" if plan.config.strict else "warning"


def _issue(
    severity: str,
    code: str,
    message: str,
    source_path: str,
    suggested_action: str,
) -> AutoResearchIssue:
    return AutoResearchIssue(
        severity=severity,
        code=code,
        message=message,
        source_path=source_path,
        suggested_action=suggested_action,
    )
