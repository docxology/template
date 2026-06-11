"""Project design-overlay validation for Stage 04 output checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan

logger = get_logger(__name__)


def project_name_from_root(project_root: Path, repo_root: Path) -> str:
    """Return the project discovery name for active or WIP project roots."""
    try:
        return str(project_root.resolve().relative_to((repo_root / "projects").resolve()))
    except ValueError:
        return project_root.name


def validate_project_design(project_root: Path, repo_root: Path) -> tuple[bool, list[str]]:
    """Validate advisory domain profile, experiment plan, and opt-in readiness overlays."""
    log_substep("Validating project design overlays...", logger)
    issues: list[str] = []
    try:
        load_domain_profile(project_root)
    except ValueError as exc:
        issues.append(str(exc))

    try:
        experiment_plan = load_experiment_plan(project_root)
        result = validate_experiment_plan(experiment_plan)
        issues.extend(result.issues)
    except ValueError as exc:
        issues.append(str(exc))

    autoresearch_path = project_root / "autoresearch.yaml"
    if autoresearch_path.exists():
        try:
            from infrastructure.autoresearch import (
                build_autoresearch_plan,
                validate_autoresearch_plan,
                write_autoresearch_report,
            )

            project_name = project_name_from_root(project_root, repo_root)
            autoresearch_plan = build_autoresearch_plan(repo_root, project_name)
            report = validate_autoresearch_plan(autoresearch_plan, project_root)
            write_autoresearch_report(project_root, report)
            issues.extend(f"{issue.code}: {issue.message}" for issue in report.issues if issue.severity == "error")
            if autoresearch_plan.config.strict:
                issues.extend(
                    f"{issue.code}: {issue.message}" for issue in report.issues if issue.severity == "warning"
                )
        except (OSError, ValueError, RuntimeError, AttributeError) as exc:
            issues.append(f"AutoResearch readiness validation failed: {exc}")

    if issues:
        for issue in issues:
            logger.warning(issue)
        return False, issues

    log_success("Project design overlays passed", logger)
    return True, []
