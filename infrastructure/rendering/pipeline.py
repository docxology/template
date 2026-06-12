"""Rendering pipeline orchestrator module.

This module coordinates the PDF rendering stage by:
1. Validating LaTeX packages
2. Verifying figures
3. Rendering individual manuscript files to multiple formats
4. Generating a combined PDF and HTML
5. Verifying output quality
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_live_resource_usage, log_success
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering._combined_exports import (  # noqa: F401
    combined_source_files as _combined_source_files,
    html_combined_source_files as _html_combined_source_files,
    render_combined_docx as _render_combined_docx,
    render_combined_epub as _render_combined_epub,
    render_combined_outputs as _render_combined_outputs,
)
from infrastructure.rendering._manuscript_source import (  # noqa: F401
    has_generated_manuscript_ordering as _has_generated_manuscript_ordering,
    load_project_config_yaml as _load_project_config_yaml,
    log_manuscript_composition as _log_manuscript_composition,
    render_individual_files as _render_individual_files,
    resolve_manuscript_dir as _resolve_manuscript_dir,
    run_manuscript_variable_script as _run_manuscript_variable_script,
    run_override_script as _run_override_script,
    validate_latex_packages as _validate_latex_packages,
)
from infrastructure.rendering._pipeline_summary import (
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files, verify_figures_exist
from infrastructure.rendering import RenderManager
from infrastructure.core.logging.diagnostic import DiagnosticReporter

logger = get_logger(__name__)


def _render_pipeline_impl(project_name: str = "project", *, skip_manuscript_hydration: bool = False) -> int:
    """Execute the PDF rendering pipeline using infrastructure rendering."""
    logger.info(f"Executing PDF rendering pipeline for project '{project_name}'...")
    repo_root = Path(__file__).parent.parent.parent
    project_root = resolve_project_root(repo_root, project_name)
    if not project_root.is_dir():
        logger.error(f"Project directory not found: {project_root}")
        return 1
    reporter = DiagnosticReporter(
        project_name=project_name,
        output_dir=project_root / "output",
        load_existing=False,
    )
    reporter.clear_report()

    if skip_manuscript_hydration:
        logger.info("Skipping manuscript-variable hydration (--skip-manuscript-hydration)")
    elif _run_manuscript_variable_script(project_root, template_repo_root=repo_root) != 0:
        return 1

    manuscript_dir = _resolve_manuscript_dir(project_root)

    try:
        from infrastructure.publishing.transmission_bookends import write_transmission_bookends

        write_transmission_bookends(project_root, project_name, repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block rendering
        logger.warning("Transmission bookend generation skipped: %s", exc)

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
        project_yaml = _load_project_config_yaml(manuscript_dir)
        env_config = RenderingConfig.from_project_config(project_yaml)
        config = RenderingConfig(
            manuscript_dir=str(manuscript_dir),
            figures_dir=str(project_root / "output" / "figures"),
            output_dir=str(project_root / "output"),
            pdf_dir=str(project_root / "output" / "pdf"),
            web_dir=str(project_root / "output" / "web"),
            slides_dir=str(project_root / "output" / "slides"),
            docx_dir=str(project_root / "output" / "docx"),
            epub_dir=str(project_root / "output" / "epub"),
            enable_pdf=env_config.enable_pdf,
            enable_html=env_config.enable_html,
            enable_slides=env_config.enable_slides,
            enable_docx=env_config.enable_docx,
            enable_epub=env_config.enable_epub,
        )
        manager = RenderManager(config, manuscript_dir=manuscript_dir, figures_dir=project_root / "output" / "figures")
        log_success("Initialized RenderManager from infrastructure.rendering", logger)
        logger.info(
            f"Render formats: pdf={config.enable_pdf} html={config.enable_html} "
            f"slides={config.enable_slides} docx={config.enable_docx} epub={config.enable_epub}"
        )
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
    if failed_files:
        logger.error(f"PDF rendering pipeline failed: {len(failed_files)} manuscript file(s) had render errors")
        return 1
    log_success("PDF rendering pipeline completed", logger)
    return 0


def execute_render_pipeline(project_name: str = "project", *, skip_manuscript_hydration: bool = False) -> int:
    """Execute PDF rendering orchestration."""
    log_live_resource_usage("PDF rendering stage start", logger)
    try:
        exit_code = _render_pipeline_impl(project_name, skip_manuscript_hydration=skip_manuscript_hydration)
        if exit_code == 0:
            outputs_valid = verify_pdf_outputs(project_name)
            if outputs_valid:
                log_success("PDF rendering complete - ready for validation", logger)
            else:
                logger.error("PDF rendering completed but output verification failed")
                exit_code = 1
        else:
            logger.error("PDF rendering failed - check logs for details")

        log_live_resource_usage("PDF rendering stage end", logger)
        return exit_code
    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        log_live_resource_usage("PDF rendering stage end (error)", logger)
        return 1


__all__ = [
    "generate_rendering_summary",
    "log_rendering_summary",
    "verify_pdf_outputs",
    "execute_render_pipeline",
]
