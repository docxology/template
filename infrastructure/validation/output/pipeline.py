"""Validation output pipeline orchestrator module.

This module coordinates the validation stage by:
1. Validating generated PDFs
2. Checking markdown formatting
3. Verifying file integrity
4. Generating validation reports
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.determinism import resolve_build_timestamp
from infrastructure.core.pipeline.artifacts import (
    ArtifactManifest,
    aggregate_artifact_manifests,
    validate_artifact_manifest,
)
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.discovery import resolve_project_root
from infrastructure.validation.content.figure_validator import validate_figure_registry
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    missing_evidence_source_paths,
    validate_text_against_registry,
    write_evidence_registry_report,
)
from infrastructure.validation.output.artifacts import (
    current_project_manifest_if_valid as _current_manifest_if_valid,
    read_artifact_manifest as _read_manifest,
)
from infrastructure.validation.output.design import validate_project_design as _validate_project_design
from infrastructure.validation.output.markdown_checks import (
    validate_manuscript_output_markdown as _validate_markdown,
)
from infrastructure.validation.output.pdf_checks import (
    validate_pdfs as _validate_pdfs,
    validate_transmission_bookends as _validate_transmission_bookends,
)
from infrastructure.validation.output.prose_quality import (
    load_project_config_yaml as _load_config_yaml,
    prose_quality_enabled as _is_prose_quality_enabled,
    validate_prose_quality as _validate_prose_quality,
)
from infrastructure.validation.output.claim_verification import (
    claim_verification_enabled as _is_claim_verification_enabled,
    verify_project_claims as _verify_project_claims,
)
from infrastructure.validation.output.validator import ValidationResultDict, collect_detailed_validation_results

logger = get_logger(__name__)

# Resolve repository root once at module load.
# This file lives at infrastructure/validation/output/pipeline.py → 4 parents up = repo root.
_REPO_ROOT = Path(__file__).parent.parent.parent.parent


@dataclass(frozen=True)
class PipelineCheck:
    """Data container for PipelineCheck."""

    name: str
    run: Callable[[], bool]


def _build_core_checks(
    project_name: str,
    *,
    repo_root: Path = _REPO_ROOT,
    prose_validator: Callable[[str], bool] | None = None,
) -> list[PipelineCheck]:
    checks = [
        PipelineCheck("PDF validation", lambda: validate_pdfs(project_name, repo_root=repo_root)),
        PipelineCheck(
            "Transmission bookends",
            lambda: validate_transmission_bookends(project_name, repo_root=repo_root),
        ),
        PipelineCheck(
            "Markdown validation",
            lambda: validate_manuscript_output_markdown(project_name, repo_root=repo_root),
        ),
    ]
    if _prose_quality_enabled(project_name, repo_root=repo_root):
        validate = prose_validator or (lambda name: validate_prose_quality(name, repo_root=repo_root))
        checks.append(PipelineCheck("Prose quality", lambda: validate(project_name)))
    return checks


def _run_registered_checks(checks: list[PipelineCheck]) -> list[tuple[str, bool]]:
    results: list[tuple[str, bool]] = []
    for i, check in enumerate(checks, 1):
        try:
            logger.info("  [%d/%d] Running %s...", i, len(checks), check.name)
            passed = check.run()
            status = "✅ PASSED" if passed else "⚠️  ISSUES"
            logger.info("  [%d/%d] %s: %s", i, len(checks), check.name, status)
            results.append((check.name, passed))
        except Exception as exc:
            logger.error("  [%d/%d] %s: ❌ FAILED - %s", i, len(checks), check.name, exc, exc_info=True)
            results.append((check.name, False))
    return results


def _project_root(project_name: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Resolve active or WIP project roots for validation stages."""
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


def validate_pdfs(project_name: str = "project", *, repo_root: Path = _REPO_ROOT) -> bool:
    """Validate generated PDF files.

    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    return _validate_pdfs(_project_root(project_name, repo_root=repo_root))


def validate_transmission_bookends(
    project_name: str = "project",
    *,
    repo_root: Path = _REPO_ROOT,
    page_validator: Callable[[Path], bool] | None = None,
) -> bool:
    """Validate transmission bookend single-page contract when enabled."""
    return _validate_transmission_bookends(
        _project_root(project_name, repo_root=repo_root),
        project_name,
        page_validator=page_validator,
    )


def validate_manuscript_output_markdown(project_name: str = "project", *, repo_root: Path = _REPO_ROOT) -> bool:
    """Validate markdown files in manuscript using infrastructure validation module.

    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    return _validate_markdown(_project_root(project_name, repo_root=repo_root), repo_root, project_name)


def verify_outputs_exist(
    project_name: str = "project", *, repo_root: Path = _REPO_ROOT
) -> tuple[bool, ValidationResultDict]:
    """Verify all expected output files exist.

    Args:
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        Tuple of (validation_passed, detailed_validation_results)
    """
    log_substep("Verifying output structure...", logger)

    output_dir = _project_output_dir(project_name, repo_root=repo_root)

    detailed_validation = collect_detailed_validation_results(output_dir)
    structure_valid = detailed_validation["structure"]["valid"]

    if structure_valid:
        log_success("Output structure is valid", logger)
        for dir_name, dir_info in detailed_validation["directories"].items():
            if dir_info["exists"] and dir_info["file_count"] > 0:
                logger.info(f"  • {dir_name}/: {dir_info['file_count']} files ({dir_info['size_mb']} MB)")
    else:
        logger.warning("Output structure validation has issues:")
        for severity, issues in (
            ("critical", detailed_validation["issues_by_severity"]["critical"]),
            ("warning", detailed_validation["issues_by_severity"]["warning"]),
        ):
            if issues:
                logger.warning(f"  {severity.upper()} issues:")
                for issue in issues[:3]:
                    logger.warning(f"    • {issue}")
                if len(issues) > 3:
                    logger.warning(f"    ... and {len(issues) - 3} more")

    return structure_valid, detailed_validation


def validate_evidence_registry(project_root: Path, manuscript_dir: Path) -> tuple[bool, list[str]]:
    """Validate manuscript evidence tokens against project artifact provenance."""
    log_substep("Validating evidence registry...", logger)

    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found at expected location: {manuscript_dir}")
        return True, []

    markdown_files = sorted(path for path in manuscript_dir.rglob("*.md") if path.is_file())
    if not markdown_files:
        logger.warning("No manuscript markdown files found for evidence registry validation")
        return True, []

    registry = build_project_evidence_registry(project_root)
    write_evidence_registry_report(project_root / "output", registry)
    error_issues: list[str] = []
    warning_issues: list[str] = []
    for source_path in missing_evidence_source_paths(project_root, registry):
        error_issues.append(f"missing evidence source path: {source_path}")
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        strict_file = any(token in path.name.lower() for token in ("claim", "ledger", "results", "table", "caption"))
        report = validate_text_against_registry(text, registry, strict=strict_file)
        for issue in report.errors:
            error_issues.append(f"{path.name}:{issue.line_number}: unsupported {issue.kind} {issue.value}")
        for issue in report.warnings:
            warning_issues.append(f"{path.name}:{issue.line_number}: unsupported {issue.kind} {issue.value}")

    issues = [*error_issues, *warning_issues]

    if issues:
        for issue_text in issues:
            logger.warning(issue_text)
        return not error_issues, issues

    log_success("Evidence registry validation passed", logger)
    return True, []


def validate_project_design(project_root: Path, *, repo_root: Path = _REPO_ROOT) -> tuple[bool, list[str]]:
    """Validate advisory domain profile, experiment plan, and opt-in readiness overlays."""
    from infrastructure.autoresearch import validate_autoresearch_overlay

    return _validate_project_design(
        project_root,
        repo_root,
        overlay_validators=(validate_autoresearch_overlay,),
    )


def _read_artifact_manifest(path: Path) -> ArtifactManifest:
    return _read_manifest(path)


def _current_project_manifest_if_valid(output_dir: Path, project_root: Path) -> ArtifactManifest | None:
    """Return the project-authored manifest when it is current."""
    return _current_manifest_if_valid(output_dir, project_root)


def generate_validation_report(
    check_results: list[tuple[str, bool]],
    figure_issues: list[str],
    output_statistics: dict[str, Any],
    project_name: str = "project",
    *,
    repo_root: Path = _REPO_ROOT,
) -> dict[str, Any]:
    """Generate validation report with structured output."""
    log_substep("Generating validation report...", logger)

    output_dir = _project_output_dir(project_name, repo_root=repo_root) / "reports"

    validation_results: dict[str, Any] = {
        "timestamp": resolve_build_timestamp(repo_root=repo_root),
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
                        "priority": "low",
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


def _load_project_config_yaml(manuscript_dir: Path) -> dict[str, Any] | None:
    """Load the manuscript ``config.yaml`` as a plain dict for validation toggles.

    Returns ``None`` when the file is missing, unparseable, or PyYAML is
    unavailable — callers fall back to defaults. Best-effort by design, mirroring
    the opt-in pattern used for DOCX/EPUB rendering in
    :mod:`infrastructure.rendering.pipeline`.
    """
    return _load_config_yaml(manuscript_dir)


def _prose_quality_enabled(project_name: str, *, repo_root: Path = _REPO_ROOT) -> bool:
    """Whether the opt-in AI-writing prose gate is enabled for *project_name*.

    Toggle lives in ``manuscript/config.yaml`` under
    ``validation.prose_quality.enabled`` and defaults to ``False`` so existing
    runs are unaffected.
    """
    return _is_prose_quality_enabled(_project_root(project_name, repo_root=repo_root))


def validate_prose_quality(project_name: str = "project", *, repo_root: Path = _REPO_ROOT) -> bool:
    """Report-only AI-writing fingerprint scan over manuscript Markdown.

    Flags prose patterns typical of unedited LLM output (stock-phrase density,
    em-dash overuse, uniform sentence length) via
    :func:`infrastructure.validation.content.ai_writing.analyze_prose`. This is a
    warning gate: it always returns ``True`` and never fails the pipeline. It is
    only invoked when ``validation.prose_quality.enabled`` is set in the project
    config, so disabled runs are byte-identical to the legacy behavior.
    """
    return _validate_prose_quality(_project_root(project_name, repo_root=repo_root))


def execute_validation_pipeline(
    project_name: str = "project",
    *,
    repo_root: Path = _REPO_ROOT,
    report_writer: Callable[..., dict[str, Any]] | None = None,
    claim_verifier: Callable[[Path], Any] | None = None,
    prose_validator: Callable[[str], bool] | None = None,
) -> int:
    """Execute validation orchestration.

    Returns:
        Exit code (0=success, 1=failure)
    """
    project_output_dir = _project_output_dir(project_name, repo_root=repo_root)
    DiagnosticReporter(
        project_name=project_name,
        output_dir=project_output_dir,
        load_existing=False,
    ).clear_report()

    checks = _build_core_checks(project_name, repo_root=repo_root, prose_validator=prose_validator)
    results = _run_registered_checks(checks)
    figure_issues: list[str] = []
    detailed_validation = None

    project_root = _project_root(project_name, repo_root=repo_root)
    manuscript_dir = resolve_source_manuscript_dir(project_root)

    claim_report = None
    if _is_claim_verification_enabled(project_root):
        try:
            verify_claims = claim_verifier or _verify_project_claims
            claim_report = verify_claims(project_root)
            results.append(("Claim verification", True))
        except Exception as e:
            logger.error(f"Error during claim verification: {e}", exc_info=True)
            results.append(("Claim verification", False))

    try:
        structure_result, detailed_validation = verify_outputs_exist(project_name, repo_root=repo_root)
        results.append(("Output structure", structure_result))
    except Exception as e:
        logger.error(f"Error during output structure validation: {e}", exc_info=True)
        results.append(("Output structure", False))

    try:
        registry_path = project_root / "output" / "figures" / "figure_registry.json"
        fig_result, figure_issues = validate_figure_registry(registry_path, manuscript_dir)
        results.append(("Figure registry", fig_result))
    except Exception as e:
        logger.error(f"Error during figure registry validation: {e}", exc_info=True)
        results.append(("Figure registry", False))
        figure_issues = []

    output_statistics: dict[str, Any]
    try:
        evidence_result, evidence_issues = validate_evidence_registry(project_root, manuscript_dir)
        results.append(("Evidence registry", evidence_result))
        if evidence_issues:
            output_statistics = {"evidence_issues": evidence_issues}
        else:
            output_statistics = {}
    except Exception as e:
        logger.error(f"Error during evidence registry validation: {e}", exc_info=True)
        results.append(("Evidence registry", False))
        output_statistics = {}

    if claim_report is not None:
        output_statistics["claim_verification"] = claim_report.summary()

    output_dir = project_root / "output"

    try:
        design_result, design_issues = validate_project_design(project_root, repo_root=repo_root)
        results.append(("Project design overlays", design_result))
        if design_issues:
            output_statistics["design_validation_issues"] = design_issues
    except Exception as e:
        logger.error(f"Error during project design validation: {e}", exc_info=True)
        results.append(("Project design overlays", False))

    try:
        artifact_manifest = _current_project_manifest_if_valid(output_dir, project_root)
        if artifact_manifest is None:
            artifact_manifest = aggregate_artifact_manifests(output_dir)
        artifact_report = validate_artifact_manifest(artifact_manifest, project_dir=project_root)
        results.append(("Artifact manifest", artifact_report.valid))
        if artifact_report.issues:
            output_statistics["artifact_manifest_issues"] = list(artifact_report.issues)
    except Exception as e:
        logger.error(f"Error during artifact manifest validation: {e}", exc_info=True)
        results.append(("Artifact manifest", False))

    if detailed_validation:
        output_statistics["detailed_validation"] = detailed_validation

    for subdir in ["pdf", "figures", "data"]:
        subdir_path = output_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*"))
            file_list = [f for f in files if f.is_file()]
            total_size = sum(f.stat().st_size for f in file_list)
            size_mb = total_size / (1024 * 1024)
            output_statistics[subdir] = {
                "files": len(file_list),
                "size_mb": size_mb,
            }

    write_report = report_writer or generate_validation_report
    write_report(results, figure_issues, output_statistics, project_name, repo_root=repo_root)

    logger.info("\n" + "=" * BANNER_WIDTH)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * BANNER_WIDTH)
    logger.info(f"Project: {project_name}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    all_passed = True
    warning_count = 0
    critical_count = 0

    logger.info("Individual Check Results:")
    for check_name, result in results:
        if result:
            status = "✅ PASS"
            logger.info(f"  {status}: {check_name}")
        else:
            if check_name == "PDF validation":
                status = "❌ FAIL"
                critical_count += 1
                all_passed = False
            elif check_name == "Transmission bookends":
                status = "❌ FAIL"
                critical_count += 1
                all_passed = False
            else:
                status = "⚠️  WARN"
                warning_count += 1
            logger.info(f"  {status}: {check_name}")

    if figure_issues:
        logger.info("")
        logger.info("Figure Reference Issues:")
        for issue in figure_issues:
            logger.warning(f"  • {issue}")

    if detailed_validation:
        structure = detailed_validation.get("structure", {})
        if structure.get("valid"):
            logger.info("")
            logger.info("Output Structure Status:")
            logger.info("  ✅ Output directory structure is valid")

            directories = detailed_validation.get("directories", {})
            for dir_name, dir_info in directories.items():
                if dir_info.get("exists") and dir_info.get("file_count", 0) > 0:
                    display_size_mb = dir_info.get("size_mb", "0.00")
                    logger.info(f"  📁 {dir_name}/: {dir_info['file_count']} files ({display_size_mb} MB)")
        else:
            logger.warning("")
            logger.warning("Output Structure Issues:")
            issues = structure.get("issues", [])
            for issue in issues[:5]:
                logger.warning(f"  • {issue}")

    logger.info("")
    logger.info("=" * BANNER_WIDTH)

    if all_passed and warning_count == 0 and critical_count == 0:
        log_success("✅ VALIDATION COMPLETE - All checks passed!", logger)
        logger.info("  → Pipeline can proceed to next stage")
        return 0
    elif all_passed and critical_count == 0:
        logger.info(f"⚠️  VALIDATION COMPLETE - {warning_count} warning(s), no critical issues")
        logger.info("  → Pipeline can continue - warnings are non-critical")
        return 0
    else:
        logger.error(f"❌ VALIDATION FAILED - {critical_count} critical issue(s)")
        logger.error("  → Pipeline halted - review issues above")
        logger.error("  → Check project output and manuscript for errors")
        return 1
