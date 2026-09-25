"""Rendering pipeline orchestrator module.

This module coordinates the PDF rendering stage by:
1. Validating LaTeX packages
2. Verifying figures
3. Rendering individual manuscript files to multiple formats
4. Generating a combined PDF and HTML
5. Verifying output quality
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging.utils import get_logger, log_live_resource_usage, log_success
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering._combined_exports import (  # noqa: F401
    combined_source_files as combined_source_files,
    html_combined_source_files as html_combined_source_files,
    render_combined_docx as render_combined_docx,
    render_combined_epub as render_combined_epub,
    render_combined_outputs as render_combined_outputs,
)
from infrastructure.rendering._manuscript_source import (  # noqa: F401
    clean_stale_render_deliverables as clean_stale_render_deliverables,
    has_generated_manuscript_ordering as has_generated_manuscript_ordering,
    is_project_resolved as is_project_resolved,
    load_project_config_yaml as load_project_config_yaml,
    log_manuscript_composition as log_manuscript_composition,
    render_individual_files as render_individual_files,
    resolve_manuscript_dir as resolve_manuscript_dir,
    run_manuscript_variable_script as run_manuscript_variable_script,
    run_override_script as run_override_script,
    unresolved_config_tokens as unresolved_config_tokens,
    validate_latex_packages as validate_latex_packages,
    verify_config_tokens_resolved as verify_config_tokens_resolved,
)
from infrastructure.rendering._pipeline_summary import (
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
    verify_render_outputs,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files, verify_figures_exist
from infrastructure.rendering import RenderManager
from infrastructure.core.logging.diagnostic import DiagnosticReporter

logger = get_logger(__name__)


def _write_override_composition(project_root: Path, project_name: str) -> None:
    """Bind a render-boundary composition receipt for custom-PDF lanes.

    The shared web/combined lanes emit ``manuscript_composition.json``
    (consumed by the rendered-provenance validation check); a project
    ``scripts/_render_pdf_override.py`` builds its combined PDF directly
    and would otherwise render without that receipt.  The override's
    token-substituted combined markdown (``output/pdf/temp_combined.md``)
    is promoted to the stable combined artifact and the receipt binds it
    to the discovered canonical manuscript inputs, mirroring
    :func:`~infrastructure.rendering.manuscript_composition.write_manuscript_composition`
    usage in the standard lanes.
    """
    from infrastructure.rendering._manuscript_source import resolve_source_manuscript_dir
    from infrastructure.rendering.manuscript_composition import write_manuscript_composition
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files

    try:
        source_dir = resolve_source_manuscript_dir(project_root)
        rendered_inputs = discover_manuscript_files(source_dir)
        if not rendered_inputs:
            logger.warning("Override composition skipped: no canonical manuscript inputs")
            return
        temp_combined = project_root / "output" / "pdf" / "temp_combined.md"
        if not temp_combined.is_file():
            logger.warning("Override composition skipped: no combined markdown from override render")
            return
        combined_md = project_root / "output" / "web" / "_combined_manuscript.md"
        combined_text = temp_combined.read_text(encoding="utf-8")
        if not combined_md.exists() or combined_md.read_text(encoding="utf-8") != combined_text:
            combined_md.parent.mkdir(parents=True, exist_ok=True)
            combined_md.write_text(combined_text, encoding="utf-8")
        write_manuscript_composition(
            project_root,
            project_name,
            rendered_inputs,
            combined_md,
            algorithm="shared-combined-markdown-v1",
        )
        logger.info("Override render composition receipt bound to: %s", combined_md)
    except Exception as exc:  # noqa: BLE001 — provenance must not fail the render
        logger.warning("Override composition receipt could not be written: %s", exc)


def _write_transmission_bookends(project_root: Path, project_name: str, *, repo_root: Path) -> None:
    from infrastructure.transmission.transmission_bookends import write_transmission_bookends

    write_transmission_bookends(project_root, project_name, repo_root=repo_root)


@dataclass(frozen=True)
class RenderPipelineDependencies:
    """Explicit collaborators for rendering orchestration and behavior tests."""

    resolve_project: Callable[[Path, str], Path] = resolve_project_root
    hydrate_manuscript: Callable[..., int] = run_manuscript_variable_script
    write_bookends: Callable[..., None] = _write_transmission_bookends
    run_override: Callable[[Path, Path], int] = run_override_script
    validate_latex: Callable[..., int] = validate_latex_packages
    verify_figures: Callable[[Path, Path], dict[str, Any]] = verify_figures_exist
    discover_manuscript: Callable[[Path], list[Path]] = discover_manuscript_files
    load_project_config: Callable[[Path], dict[str, Any] | None] = load_project_config_yaml
    manager_factory: Callable[..., RenderManager] = RenderManager
    render_individual: Callable[..., tuple[int, list[str]]] = render_individual_files
    render_combined: Callable[..., None] = render_combined_outputs
    generate_summary: Callable[..., dict[str, Any]] = generate_rendering_summary
    log_summary: Callable[[dict[str, Any]], None] = log_rendering_summary
    verify_outputs: Callable[..., bool] = verify_render_outputs


def _render_pipeline_impl(
    project_name: str = "project",
    *,
    skip_manuscript_hydration: bool = False,
    repo_root: Path | None = None,
    dependencies: RenderPipelineDependencies | None = None,
) -> int:
    """Execute the PDF rendering pipeline using infrastructure rendering."""
    deps = dependencies or RenderPipelineDependencies()
    logger.info(f"Executing PDF rendering pipeline for project '{project_name}'...")
    root = repo_root or Path(__file__).parent.parent.parent
    project_root = deps.resolve_project(root, project_name)
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
    elif deps.hydrate_manuscript(project_root, template_repo_root=root) != 0:
        return 1

    try:
        manuscript_dir = resolve_manuscript_dir(project_root)
    except ValidationError as exc:
        # config.yaml feeds the PDF title page; an unresolved {{TOKEN}} there
        # would print verbatim on the published cover. Fail closed instead.
        logger.error("❌ %s", exc.message)
        for suggestion in exc.suggestions:
            logger.error("   %s", suggestion)
        return 1

    try:
        deps.write_bookends(project_root, project_name, repo_root=root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block rendering
        logger.warning("Transmission bookend generation skipped: %s", exc)

    override_script = project_root / "scripts" / "_render_pdf_override.py"
    if override_script.exists():
        stale_override_pdf = project_root / "output" / "pdf" / f"{Path(project_name).name}_combined.pdf"
        try:
            stale_override_pdf.unlink(missing_ok=True)
        except OSError as exc:
            logger.error("Could not remove stale override PDF %s: %s", stale_override_pdf, exc)
            return 1
        exit_code = deps.run_override(project_root, override_script)
        if exit_code == 0:
            _write_override_composition(project_root, project_name)
        return exit_code

    if deps.validate_latex() != 0:
        return 1

    logger.info("Verifying figures from analysis stage...")
    fig_status = deps.verify_figures(project_root, manuscript_dir)
    if fig_status["found_figures"]:
        logger.info(f"  Found figures: {', '.join(fig_status['found_figures'][:3])}")
        if len(fig_status["found_figures"]) > 3:
            logger.info(f"  ... and {len(fig_status['found_figures']) - 3} more")
    else:
        logger.warning("  ⚠️  No figures found - will render PDF with missing figures")

    source_files = deps.discover_manuscript(manuscript_dir)
    if not source_files:
        logger.error("No manuscript files found; refusing to validate prior render outputs")
        return 1

    log_manuscript_composition(source_files)

    try:
        project_yaml = deps.load_project_config(manuscript_dir)
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
            slide_theme=env_config.slide_theme,
            slides_profile=env_config.slides_profile,
            slides_max_prose_words=env_config.slides_max_prose_words,
            slides_max_table_rows=env_config.slides_max_table_rows,
            slides_min_figure_area_percent=env_config.slides_min_figure_area_percent,
            slides_title_font_pt=env_config.slides_title_font_pt,
            slides_body_font_pt=env_config.slides_body_font_pt,
            slides_figure_label_font_pt=env_config.slides_figure_label_font_pt,
            slides_reader_href=env_config.slides_reader_href,
            enable_pdf=env_config.enable_pdf,
            enable_html=env_config.enable_html,
            enable_slides=env_config.enable_slides,
            enable_docx=env_config.enable_docx,
            enable_epub=env_config.enable_epub,
            latex_compiler=env_config.latex_compiler,
            pandoc_path=env_config.pandoc_path,
        )
        manager = deps.manager_factory(
            config,
            manuscript_dir=manuscript_dir,
            figures_dir=project_root / "output" / "figures",
        )
        log_success("Initialized RenderManager from infrastructure.rendering", logger)
        logger.info(
            f"Render formats: pdf={config.enable_pdf} html={config.enable_html} "
            f"slides={config.enable_slides} docx={config.enable_docx} epub={config.enable_epub}; "
            f"slides_profile={config.slides_profile}"
        )
    except (OSError, ValueError, TypeError) as e:
        logger.error(f"Failed to initialize RenderManager: {e}")
        return 1

    md_files = [f for f in source_files if f.suffix == ".md"]
    try:
        clean_stale_render_deliverables(manager, source_files, project_name)
    except OSError as exc:
        logger.error("Could not remove stale render deliverable: %s", exc)
        return 1
    rendered_count, failed_files = deps.render_individual(manager, source_files, reporter)

    if md_files:
        deps.render_combined(manager, md_files, manuscript_dir, project_name, reporter, rendered_count)

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

    summary = deps.generate_summary(project_name, repo_root=root)
    deps.log_summary(summary)
    if failed_files:
        logger.error(f"PDF rendering pipeline failed: {len(failed_files)} manuscript file(s) had render errors")
        return 1
    log_success("PDF rendering pipeline completed", logger)
    return 0


def execute_render_pipeline(
    project_name: str = "project",
    *,
    skip_manuscript_hydration: bool = False,
    repo_root: Path | None = None,
    dependencies: RenderPipelineDependencies | None = None,
) -> int:
    """Execute PDF rendering orchestration."""
    deps = dependencies or RenderPipelineDependencies()
    root = repo_root or Path(__file__).parent.parent.parent
    log_live_resource_usage("PDF rendering stage start", logger)
    try:
        exit_code = _render_pipeline_impl(
            project_name,
            skip_manuscript_hydration=skip_manuscript_hydration,
            repo_root=root,
            dependencies=deps,
        )
        if exit_code == 0:
            outputs_valid = deps.verify_outputs(project_name, repo_root=root)
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
    "verify_render_outputs",
    "RenderPipelineDependencies",
    "execute_render_pipeline",
]
