"""Validation for deterministic AutoResearch readiness plans."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from infrastructure.autoresearch.models import (
    KNOWN_QUALITY_CHECKS,
    AutoResearchIssue,
    AutoResearchPlan,
    AutoResearchReport,
)
from infrastructure.autoresearch.validation_checks import (
    _issue,
    _validate_ai_disclosure,
    _validate_artifact_manifest,
    _validate_benchmark_tasks,
    _validate_domain_profile,
    _validate_evidence_registry,
    _validate_experiment_plan,
    _validate_method_contracts,
    _validate_pipeline_contracts,
    _validate_review_gates,
    _validate_security_profile,
    _validate_thin_orchestrators,
)

ValidationPhase = Literal["all", "intrinsic", "extrinsic"]

INTRINSIC_QUALITY_CHECKS = frozenset(
    {
        "domain_profile",
        "experiment_plan",
        "pipeline_contracts",
        "thin_orchestrators",
        "ai_disclosure",
    }
)
EXTRINSIC_QUALITY_CHECKS = frozenset(
    {
        "evidence_registry",
        "artifact_manifest",
        "method_contracts",
        "review_gates",
        "benchmark_tasks",
        "security_profile",
    }
)


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
    if "method_contracts" in active_checks:
        _validate_method_contracts(project_root, plan, issues)
    if "review_gates" in active_checks:
        _validate_review_gates(project_root, plan, issues)
    if "benchmark_tasks" in active_checks:
        _validate_benchmark_tasks(project_root, plan, issues)
    if "ai_disclosure" in active_checks:
        _validate_ai_disclosure(project_root, plan, issues)
    if "security_profile" in active_checks:
        _validate_security_profile(project_root, plan, issues)

    valid = not any(issue.severity == "error" for issue in issues)
    return AutoResearchReport(project_name=plan.project_name, valid=valid, issues=tuple(issues), plan=plan)


def validate_autoresearch_overlay(project_root: Path, repo_root: Path) -> list[str]:
    """Validate the opt-in AutoResearch readiness overlay for a project.

    This is the AutoResearch module's own overlay-validator: the generic Stage 04
    design-validation layer invokes it as a domain hook rather than importing or
    special-casing AutoResearch internals. The overlay is detected by the presence
    of an ``autoresearch.yaml`` marker at the project root; absent that marker, no
    work is performed and an empty issue list is returned.

    Args:
        project_root: Filesystem root of the project being validated.
        repo_root: Repository root used to resolve the project discovery name.

    Returns:
        A list of human-readable issue strings (empty when the overlay is absent
        or passes). Errors are always surfaced; warnings are surfaced only when the
        plan is configured ``strict``.
    """
    marker_path = project_root / "autoresearch.yaml"
    if not marker_path.exists():
        return []

    from infrastructure.autoresearch.planner import build_autoresearch_plan
    from infrastructure.autoresearch.reports import write_autoresearch_report
    from infrastructure.project.discovery import project_name_from_root

    issues: list[str] = []
    try:
        project_name = project_name_from_root(project_root, repo_root)
        plan = build_autoresearch_plan(repo_root, project_name)
        report = validate_autoresearch_plan(plan, project_root)
        write_autoresearch_report(project_root, report)
        issues.extend(f"{issue.code}: {issue.message}" for issue in report.issues if issue.severity == "error")
        if plan.config.strict:
            issues.extend(f"{issue.code}: {issue.message}" for issue in report.issues if issue.severity == "warning")
    except (OSError, ValueError, RuntimeError, AttributeError) as exc:
        issues.append(f"AutoResearch readiness validation failed: {exc}")
    return issues


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
