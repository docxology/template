"""Validation-report construction, recommendations, and persistence.

Split from :mod:`infrastructure.validation.output.pipeline` (line-count gate);
the parent module imports :func:`generate_validation_report` from here so the
public import path is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.determinism import resolve_build_timestamp
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.core.logging.utils import get_logger, log_substep
from infrastructure.project.discovery import resolve_project_root

logger = get_logger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent.parent


def _project_root(project_name: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Resolve active or WIP project roots for validation reports."""
    return resolve_project_root(repo_root, project_name)


def _project_output_dir(project_name: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Return the resolved project output directory."""
    return _project_root(project_name, repo_root=repo_root) / "output"


def _project_relative_path(project_name: str, child: str = "", *, repo_root: Path = _REPO_ROOT) -> str:
    """Return a repo-relative project path for reports and recommendations."""
    path = _project_root(project_name, repo_root=repo_root)
    if child:
        path = path / child
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def generate_validation_report(
    check_results: list[tuple[str, bool]],
    figure_issues: list[str],
    output_statistics: dict[str, Any],
    project_name: str = "project",
    *,
    repo_root: Path = _REPO_ROOT,
    bind_rendered_inputs: bool = False,
) -> dict[str, Any]:
    """Generate validation report with structured output."""
    log_substep("Generating validation report...", logger)

    output_dir = _project_output_dir(project_name, repo_root=repo_root) / "reports"

    validation_results: dict[str, Any] = {
        "timestamp": resolve_build_timestamp(
            deterministic=True if bind_rendered_inputs else None,
            repo_root=repo_root,
        ),
        "checks": {name: result for name, result in check_results},
        "figure_issues": figure_issues,
        "output_statistics": output_statistics,
        "summary": {
            "total_checks": len(check_results),
            "passed": sum(1 for _, result in check_results if result),
            "failed": sum(1 for _, result in check_results if not result),
            "figure_issues_count": len(figure_issues),
            "all_passed": all(result for _, result in check_results) and len(figure_issues) == 0,
        },
    }

    recommendations: list[dict[str, str]] = []
    for check_name, result in check_results:
        if not result:
            if check_name == "PDF validation":
                recommendations.append(
                    {
                        "priority": "high",
                        "issue": "PDF validation failed",
                        "action": "Check PDF generation logs and LaTeX compilation errors",
                        "file": "output/pdf/*_compile.log",
                    }
                )
            elif check_name == "Transmission bookends":
                recommendations.append(
                    {
                        "priority": "high",
                        "issue": "Transmission bookend page-span validation failed",
                        "action": "Compact bookend content or reduce QR strip so BEGIN/END each fit one page",
                        "file": _project_relative_path(
                            project_name, f"output/pdf/{project_name}_combined.pdf", repo_root=repo_root
                        ),
                    }
                )
            elif check_name == "Markdown validation":
                recommendations.append(
                    {
                        "priority": "medium",
                        "issue": "Markdown validation issues found",
                        "action": "Review markdown validation output for formatting issues",
                        "file": _project_relative_path(project_name, "manuscript", repo_root=repo_root),
                    }
                )
            elif check_name == "Output structure":
                recommendations.append(
                    {
                        "priority": "high",
                        "issue": "Missing output directories",
                        "action": "Ensure all analysis scripts completed successfully",
                        "file": _project_relative_path(project_name, "output", repo_root=repo_root),
                    }
                )
            elif check_name == "Figure registry":
                recommendations.append(
                    {
                        "priority": "high",
                        "issue": "Figure registry validation failed",
                        "action": "Regenerate the figure registry and repair missing or unbound figures",
                        "file": _project_relative_path(
                            project_name, "output/figures/figure_registry.json", repo_root=repo_root
                        ),
                    }
                )
            elif check_name == "Evidence registry":
                recommendations.append(
                    {
                        "priority": "medium",
                        "issue": "Evidence registry reported unsupported manuscript facts",
                        "action": "Register generated facts or replace unsupported hard-coded claims",
                        "file": _project_relative_path(
                            project_name, "output/reports/evidence_registry.json", repo_root=repo_root
                        ),
                    }
                )
            elif check_name == "Artifact manifest":
                recommendations.append(
                    {
                        "priority": "medium",
                        "issue": "Artifact manifest reported drift or missing declared outputs",
                        "action": "Regenerate declared outputs or update the stage contract",
                        "file": _project_relative_path(
                            project_name, "output/reports/artifact_manifest.json", repo_root=repo_root
                        ),
                    }
                )
            elif check_name == "Project design overlays":
                recommendations.append(
                    {
                        "priority": "high",
                        "issue": "Domain profile or experiment plan validation failed",
                        "action": "Fix domain_profile.yaml or experiment_plan.yaml schema and design declarations",
                        "file": _project_relative_path(project_name, repo_root=repo_root),
                    }
                )

    if figure_issues:
        recommendations.append(
            {
                "priority": "medium",
                "issue": f"{len(figure_issues)} figure reference issue(s)",
                "action": "Register missing figures or remove unused references",
                "file": _project_relative_path(
                    project_name, "output/figures/figure_registry.json", repo_root=repo_root
                ),
            }
        )

    validation_results["recommendations"] = recommendations
    if bind_rendered_inputs:
        from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot

        snapshot = build_current_rendered_snapshot(repo_root, project_name)
        validation_results["validated_inputs"] = snapshot.validated_inputs_dict()

    if bind_rendered_inputs:
        from infrastructure.reporting.pipeline_io import generate_validation_markdown

        project_root = _project_root(project_name, repo_root=repo_root)
        json_path = output_dir / "validation_report.json"
        markdown_path = output_dir / "validation_report.md"
        atomic_write_text_confined(
            project_root,
            json_path,
            json.dumps(validation_results, indent=2, sort_keys=True) + "\n",
        )
        atomic_write_text_confined(
            project_root,
            markdown_path,
            generate_validation_markdown(validation_results),
        )
        logger.info(f"Validation reports saved: {json_path}, {markdown_path}")
    else:
        try:
            from infrastructure.reporting import save_validation_report as gen_validation_report

            saved_files = gen_validation_report(validation_results, output_dir)
            logger.info(f"Validation reports saved: {', '.join(str(p) for p in saved_files.values())}")
        except (ImportError, OSError, TypeError, AttributeError) as e:
            logger.warning(f"Failed to generate structured validation report: {e}")
            report_file = output_dir / "validation_report.json"
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(report_file, "w") as f:
                json.dump(validation_results, f, indent=2)
            logger.info(f"Validation report saved: {report_file}")

    # Print final diagnostic telemetry report (end of pipeline run)
    reporter = DiagnosticReporter(project_name=project_name, output_dir=output_dir.parent)
    if reporter.events:
        reporter.print_report()

    return validation_results
