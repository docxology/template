"""Rendering pipeline orchestrator module.

This module coordinates the PDF rendering stage by:
1. Validating LaTeX packages
2. Verifying figures
3. Rendering individual manuscript files to multiple formats
4. Generating a combined PDF and HTML
5. Verifying output quality
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.exceptions import RenderingError, ValidationError
from infrastructure.core.logging.utils import get_logger, log_success, log_live_resource_usage
from infrastructure.core.progress import SubStageProgress
from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.core.logging.diagnostic import DiagnosticReporter, DiagnosticSeverity
from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)
from infrastructure.rendering.latex_package_validator import validate_preamble_packages
from infrastructure.rendering.latex_validation import ValidationReport

# Re-exports for backwards compatibility
from infrastructure.rendering._pipeline_summary import (  # noqa: F401
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
    _check_citations_used,
)

logger = get_logger(__name__)


def _resolve_manuscript_dir(project_root: Path) -> Path:
    """Return the manuscript directory to render from.

    Prefers the injected output/manuscript/ directory when it exists and
    contains markdown files; falls back to the source manuscript/ directory.
    """
    injected_dir = project_root / "output" / "manuscript"
    if injected_dir.exists() and any(injected_dir.glob("*.md")):
        logger.info(f"Rendering from injected manuscript directory: {injected_dir}")
        return injected_dir
    return project_root / "manuscript"


def _run_override_script(project_root: Path, override_script: Path) -> int:
    """Delegate rendering to a project-specific override script.

    Returns the exit code from the override script (0 = success).
    """
    from infrastructure.core.runtime.environment import get_python_command

    logger.info(f"⚡ Found custom render override: {override_script.name}")
    logger.info("Transferring control to project-specific renderer...")
    cmd = get_python_command() + [str(override_script)]
    try:
        result = subprocess.run(cmd, cwd=str(project_root), check=False, timeout=300)  # nosec B603
        if result.returncode == 0:
            log_success("Custom PDF rendering completed successfully", logger)
        else:
            logger.error(f"Custom PDF rendering failed (exit code {result.returncode})")
        return result.returncode
    except (subprocess.SubprocessError, OSError) as e:
        logger.error(f"Failed to execute custom renderer: {e}")
        return 1


def _validate_latex_packages(report: ValidationReport | None = None) -> int:
    """Run pre-flight LaTeX package validation.

    Args:
        report: Pre-built ValidationReport to evaluate.  If None the function
            calls validate_preamble_packages() to obtain one at runtime.
            Passing a report directly makes the function testable with real
            dataclass instances without requiring a LaTeX installation.

    Returns:
        0 if validation passed (or could not run), 1 if required packages
        are missing.
    """
    logger.info("Running pre-flight LaTeX package validation...")
    try:
        if report is None:
            report = validate_preamble_packages(strict=False)
        if not report.all_required_available:
            logger.error("❌ Missing required LaTeX packages!")
            logger.error(f"   Missing: {', '.join(report.missing_required)}")
            logger.error(f"   Install: sudo tlmgr install {' '.join(report.missing_required)}")
            return 1
        if report.missing_optional:
            logger.warning(f"⚠️  Missing {len(report.missing_optional)} optional package(s):")
            for pkg in report.missing_optional:
                logger.warning(f"   - {pkg}")
            logger.warning("   PDF will render with reduced functionality")
            logger.info(f"   To install: sudo tlmgr install {' '.join(report.missing_optional)}")
        else:
            logger.info("✓ All LaTeX packages available")
    except ValidationError as e:
        logger.error(f"❌ LaTeX package validation failed: {e}")
        for suggestion in e.suggestions:
            logger.error(f"   {suggestion}")
        return 1
    except (OSError, subprocess.SubprocessError) as e:
        logger.warning(f"⚠️  Could not validate LaTeX packages: {e}")
        logger.warning("   Proceeding anyway - compilation may fail if packages are missing")
    return 0


def _log_manuscript_composition(source_files: list[Path]) -> None:
    """Log the manuscript file composition summary with file sizes."""
    md_files = [f for f in source_files if f.suffix == ".md"]
    tex_files = [f for f in source_files if f.suffix == ".tex"]
    logger.info("\n" + "=" * 60)
    logger.info(f"MANUSCRIPT COMPOSITION ({len(source_files)} files)")
    logger.info("=" * 60)
    if md_files:
        logger.info(f"Markdown sections ({len(md_files)}):")
        for f in md_files:
            size_kb = f.stat().st_size / 1024
            logger.info(f"  • {f.name:<40} ({size_kb:>6.1f} KB)")
        total_size_kb = sum(f.stat().st_size for f in md_files) / 1024
        logger.info(f"  {'Total markdown:':<40} ({total_size_kb:>6.1f} KB)")
    if tex_files:
        logger.info(f"LaTeX files ({len(tex_files)}):")
        for f in tex_files:
            size_kb = f.stat().st_size / 1024
            logger.info(f"  • {f.name:<40} ({size_kb:>6.1f} KB)")
    logger.info("=" * 60 + "\n")


def _render_individual_files(
    manager: "RenderManager",
    source_files: list[Path],
    reporter: "DiagnosticReporter",
) -> tuple[int, list[str]]:
    """Render each source file; return (rendered_count, failed_file_names)."""
    rendered_count = 0
    failed_files: list[str] = []
    progress = SubStageProgress(total=len(source_files), stage_name="Rendering Files")
    for i, source_file in enumerate(source_files, 1):
        progress.start_substage(i, source_file.name)
        try:
            outputs = manager.render_all(source_file)
            if outputs:
                for output_path in outputs:
                    log_success(f"Generated: {output_path.name}", logger)
                rendered_count += 1
            else:
                logger.warning(f"  No output generated for {source_file.name}")
        except RenderingError as re:
            logger.warning(f"  ❌ Rendering error for {source_file.name}: {re.message}")
            reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.ERROR))
            failed_files.append(source_file.name)
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            logger.warning(f"  ❌ Unexpected error rendering {source_file.name}: {e}")
            reporter.record_error(
                category="UnexpectedError",
                message=f"Unexpected error rendering {source_file.name}: {e}",
                file_path=source_file.name,
            )
            failed_files.append(source_file.name)
        progress.complete_substage()
    return rendered_count, failed_files


def _render_combined_outputs(
    manager: "RenderManager",
    md_files: list[Path],
    manuscript_dir: Path,
    project_name: str,
    reporter: "DiagnosticReporter",
    rendered_count: int,
) -> None:
    """Generate the combined PDF and HTML manuscripts from all markdown files."""
    import traceback

    logger.info("\n" + "=" * 60)
    logger.info("Generating combined PDF manuscript...")
    try:
        combined_pdf = manager.render_combined_pdf(md_files, manuscript_dir, project_name)
        logger.info(f"✅ Generated combined PDF: {combined_pdf.name}")
    except RenderingError as re:
        logger.error(f"❌ Rendering error generating combined PDF: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.ERROR))
        if rendered_count > 0:
            logger.info(f"ℹ️  Note: {rendered_count} individual PDF(s) were generated despite combined PDF failure.")
    except (OSError, subprocess.SubprocessError, ValueError, TypeError) as e:
        logger.error(f"❌ Unexpected error generating combined PDF: {e}")
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Full traceback:\n{traceback.format_exc()}")
        if hasattr(e, "stderr") and e.stderr:
            logger.error(f"  Full stderr:\n{e.stderr}")
        if hasattr(e, "stdout") and e.stdout:
            logger.error(f"  Full stdout:\n{e.stdout}")
        try:
            combined_md_path = manuscript_dir.parent / "output" / "tex" / "_combined_manuscript.md"
            if combined_md_path.exists():
                logger.error(f"  Combined markdown: {combined_md_path} ({combined_md_path.stat().st_size} bytes)")
        except OSError as stat_err:
            logger.debug(f"  Could not stat combined markdown file: {stat_err}")
        logger.warning("  This is an unexpected error - please report this issue")

    logger.info("\n" + "=" * 60)
    logger.info("Generating combined HTML manuscript...")
    try:
        manager.render_combined_web(md_files, manuscript_dir, project_name)
    except RenderingError as re:
        logger.warning(f"⚠️  Rendering error generating combined HTML: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        logger.warning(f"⚠️  Unexpected error generating combined HTML: {e}")


def _render_pipeline_impl(project_name: str = "project") -> int:
    """Execute the PDF rendering pipeline using infrastructure rendering.

    This pipeline:
    1. Validates LaTeX packages (pre-flight check)
    2. Verifies figures from analysis stage
    3. Renders individual manuscript files to multiple formats
    4. Generates a combined PDF from all manuscript sections
    5. Reports on all generated outputs

    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    logger.info(f"Executing PDF rendering pipeline for project '{project_name}'...")
    repo_root = Path(__file__).parent.parent.parent
    project_root = repo_root / "projects" / project_name
    reporter = DiagnosticReporter(
        project_name=project_name,
        output_dir=project_root / "output",
    )

    manuscript_dir = _resolve_manuscript_dir(project_root)

    override_script = project_root / "scripts" / "_render_pdf_override.py"
    if override_script.exists():
        return _run_override_script(project_root, override_script)

    if _validate_latex_packages() != 0:
        return 1

    logger.info("Verifying figures from analysis stage...")
    fig_status = verify_figures_exist(project_root, manuscript_dir)
    if fig_status["found_figures"]:
        logger.info(f"  Found figures: {', '.join(fig_status['found_figures'][:3])}")
        if len(fig_status["found_figures"]) > 3:
            logger.info(f"  ... and {len(fig_status['found_figures']) - 3} more")
    else:
        logger.warning("  ⚠️  No figures found - will render PDF with missing figures")

    source_files = discover_manuscript_files(manuscript_dir)
    if not source_files:
        logger.warning("No manuscript files found")
        return 0

    _log_manuscript_composition(source_files)

    try:
        config = RenderingConfig(
            manuscript_dir=str(manuscript_dir),
            figures_dir=str(project_root / "output" / "figures"),
            output_dir=str(project_root / "output"),
            pdf_dir=str(project_root / "output" / "pdf"),
            web_dir=str(project_root / "output" / "web"),
            slides_dir=str(project_root / "output" / "slides"),
            poster_dir=str(project_root / "output" / "posters"),
        )
        manager = RenderManager(config, manuscript_dir=manuscript_dir, figures_dir=project_root / "output" / "figures")
        log_success("Initialized RenderManager from infrastructure.rendering", logger)
    except (OSError, ValueError, TypeError) as e:
        logger.error(f"Failed to initialize RenderManager: {e}")
        return 1

    md_files = [f for f in source_files if f.suffix == ".md"]
    rendered_count, failed_files = _render_individual_files(manager, source_files, reporter)

    if md_files:
        _render_combined_outputs(manager, md_files, manuscript_dir, project_name, reporter, rendered_count)

    if reporter.events:
        reporter.print_report()
        reporter.save_report()

    logger.info("\nRendering Summary:")
    logger.info(f"  Individual files processed: {rendered_count}")
    logger.info(f"  Markdown files: {len(md_files)}")
    if failed_files:
        logger.warning(f"  Failed: {len(failed_files)} file(s)")
        for fname in failed_files:
            logger.warning(f"    - {fname}")

    summary = generate_rendering_summary(project_name)
    log_rendering_summary(summary)
    log_success("PDF rendering pipeline completed", logger)
    return 0


def execute_render_pipeline(project_name: str = "project") -> int:
    """Execute PDF rendering orchestration.

    Returns:
        Exit code (0=success, 1=failure)
    """
    log_live_resource_usage("PDF rendering stage start", logger)
    try:
        exit_code = _render_pipeline_impl(project_name)
        if exit_code == 0:
            outputs_valid = verify_pdf_outputs(project_name)
            if outputs_valid:
                log_success("PDF rendering complete - ready for validation", logger)
            else:
                logger.warning("PDF rendering completed but output verification failed")
        else:
            logger.error("PDF rendering failed - check logs for details")

        log_live_resource_usage("PDF rendering stage end", logger)
        return exit_code
    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        log_live_resource_usage("PDF rendering stage end (error)", logger)
        return 1
