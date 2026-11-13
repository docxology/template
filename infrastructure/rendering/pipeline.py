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
from dataclasses import dataclass, replace
import os
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError, ValidationError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.core.logging.utils import get_logger, log_live_resource_usage, log_success
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering import RenderManager
from infrastructure.rendering._combined_exports import (  # noqa: F401
    combined_source_files as combined_source_files,
)
from infrastructure.rendering._combined_exports import (
    html_combined_source_files as html_combined_source_files,
)
from infrastructure.rendering._combined_exports import (
    render_combined_docx as render_combined_docx,
)
from infrastructure.rendering._combined_exports import (
    render_combined_epub as render_combined_epub,
)
from infrastructure.rendering._combined_exports import (
    render_combined_outputs as render_combined_outputs,
)
from infrastructure.rendering._manuscript_source import (  # noqa: F401
    clean_stale_render_deliverables as clean_stale_render_deliverables,
)
from infrastructure.rendering._manuscript_source import (
    load_project_config_yaml as load_project_config_yaml,
)
from infrastructure.rendering._manuscript_source import (
    log_manuscript_composition as log_manuscript_composition,
)
from infrastructure.rendering._manuscript_source import (
    render_individual_files as render_individual_files,
)
from infrastructure.rendering._manuscript_source import (
    resolve_manuscript_dir as resolve_manuscript_dir,
)
from infrastructure.rendering._manuscript_source import (
    run_manuscript_variable_script as run_manuscript_variable_script,
)
from infrastructure.rendering._manuscript_source import (
    validate_latex_packages as validate_latex_packages,
)
from infrastructure.rendering._manuscript_source import (
    verify_config_tokens_resolved as verify_config_tokens_resolved,
)
from infrastructure.rendering._paper_frontmatter import declared_frontmatter, resolve_paper_layout
from infrastructure.rendering._pipeline_summary import (
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
    verify_render_outputs,
)
from infrastructure.rendering._untrusted_web import hold_untrusted_project, prepare_project_web
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files, verify_figures_exist
from infrastructure.rendering.native_render_custody import native_render_custody
from infrastructure.rendering.web_renderer import WebRenderer
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.validation.content.manuscript_config import (
    has_generated_manuscript_ordering as has_generated_manuscript_ordering,
)
from infrastructure.validation.content.manuscript_config import (
    is_project_resolved as is_project_resolved,
)
from infrastructure.validation.content.manuscript_config import (
    unresolved_config_tokens as unresolved_config_tokens,
)

logger = get_logger(__name__)


def _write_transmission_bookends(project_root: Path, project_name: str, *, repo_root: Path) -> None:
    from infrastructure.transmission.transmission_bookends import write_transmission_bookends

    write_transmission_bookends(project_root, project_name, repo_root=repo_root)


@dataclass(frozen=True)
class RenderPipelineDependencies:
    """Explicit collaborators for rendering orchestration and behavior tests."""

    resolve_project: Callable[[Path, str], Path] = resolve_project_root
    hydrate_manuscript: Callable[..., int] = run_manuscript_variable_script
    write_bookends: Callable[..., None] = _write_transmission_bookends
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


def _prepare_bookends_before_hydration(
    project_root: Path, project_name: str, root: Path, deps: RenderPipelineDependencies
) -> None:
    """Prepare native assets before a project seals their visualization evidence."""
    source = resolve_source_manuscript_dir(project_root)
    candidates = [source]
    consumed = project_root / "output" / "manuscript"
    if consumed.is_dir() and any(consumed.glob("*.md")):
        candidates.append(consumed)
    # An explicit consumed paper layout must never acquire legacy bookends,
    # even when the source config still describes a different layout.
    try:
        if any(declared_frontmatter(deps.load_project_config(directory)) for directory in candidates):
            return
    except RenderingError:
        # Hydration may resolve a provisional layout; the final consumed
        # manuscript still passes the existing strict admission below.
        return
    try:
        deps.write_bookends(project_root, project_name, repo_root=root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block rendering
        logger.warning("Transmission bookend preparation skipped: %s", exc)


def _render_untrusted_project(repo_root: Path, project_name: str, *, skip_manuscript_hydration: bool) -> int:
    """Render prepared HTML only from the admitted lexical project slot."""
    env = dict(os.environ)
    profile = RenderingConfig.from_env(env).security()
    if not skip_manuscript_hydration:
        raise RenderingError("untrusted Stage 3 requires --skip-manuscript-hydration and prepared inputs")
    if native_render_custody("untrusted Stage 3 cannot use a native render origin") is not None:
        raise RenderingError("untrusted Stage 3 cannot use native render launchers")

    with (
        hold_untrusted_project(repo_root, project_name) as (project_root, directory),
        project_output_lock(project_root),
    ):
        if not directory.matches_path():
            raise RenderingError("Untrusted Stage 3 project slot changed during admission")
        info = os.fstat(directory.descriptor)
        identity = (info.st_dev, info.st_ino)
        output_dir = project_root / "output"
        profile.validate_output_tree(output_dir)
        prepared = prepare_project_web(project_root, expected_root_identity=identity)
        settings = RenderingConfig.from_project_config(prepared.config, env=env)
        if not settings.enable_html or any(
            (settings.enable_pdf, settings.enable_slides, settings.enable_docx, settings.enable_epub)
        ):
            raise RenderingError("untrusted Stage 3 supports only the HTML format")

        config = replace(settings, output_dir=str(output_dir), web_dir=str(output_dir / "web"))
        WebRenderer(config)._render_untrusted_combined(prepared, project_anchor=(project_root, identity))
    return 0


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
    if os.environ.get("RENDER_SECURITY_PROFILE", "trusted-local") != "trusted-local":
        return _render_untrusted_project(root, project_name, skip_manuscript_hydration=skip_manuscript_hydration)
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
    else:
        _prepare_bookends_before_hydration(project_root, project_name, root, deps)
        hydration_exit = deps.hydrate_manuscript(project_root, template_repo_root=root)
        if hydration_exit != 0:
            return hydration_exit
    try:
        manuscript_dir = resolve_manuscript_dir(project_root)
    except ValidationError as exc:
        # config.yaml feeds the PDF title page; an unresolved {{TOKEN}} there
        # would print verbatim on the published cover. Fail closed instead.
        logger.error("❌ %s", exc.message)
        for suggestion in exc.suggestions:
            logger.error("   %s", suggestion)
        return 1
    # Paper-frontmatter admission excludes transmission semantics. Do not run
    # the legacy producer, which also consults source-project configuration,
    # against this explicit consumed paper layout.
    if not declared_frontmatter(deps.load_project_config(manuscript_dir)):
        try:
            deps.write_bookends(project_root, project_name, repo_root=root)
        except Exception as exc:  # noqa: BLE001 — bookends must not block rendering
            logger.warning("Transmission bookend generation skipped: %s", exc)
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
        settings = RenderingConfig.from_project_config(deps.load_project_config(manuscript_dir))
        output_dir = project_root / "output"
        config = replace(
            settings,
            manuscript_dir=str(manuscript_dir),
            figures_dir=str(output_dir / "figures"),
            output_dir=str(output_dir),
            pdf_dir=str(output_dir / "pdf"),
            web_dir=str(output_dir / "web"),
            slides_dir=str(output_dir / "slides"),
            docx_dir=str(output_dir / "docx"),
            epub_dir=str(output_dir / "epub"),
        )
        manager = deps.manager_factory(
            config,
            manuscript_dir=manuscript_dir,
            figures_dir=output_dir / "figures",
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
    paper_layout = resolve_paper_layout(manuscript_dir, tuple(md_files))
    try:
        clean_stale_render_deliverables(manager, source_files, project_name)
    except OSError as exc:
        logger.error("Could not remove stale render deliverable: %s", exc)
        return 1
    rendered_count, failed_files = deps.render_individual(manager, source_files, reporter)

    if md_files:
        if paper_layout.frontmatter:
            deps.render_combined(
                manager, md_files, manuscript_dir, project_name, reporter, rendered_count, paper_layout=paper_layout
            )
        else:
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
    # The authoritative verdict for the current outputs already exists; a run
    # that finished without per-file errors must still be refused when that
    # verdict is false. The verdict names its own failing clause above
    # (combined manuscript PDF absent or too small, no PDF files in the output
    # tree, a failing compilation, or an uncleared LaTeX warning policy), so
    # this refusal carries the decision instead of a second copy of it.
    if not deps.verify_outputs(project_name, repo_root=root):
        logger.error(
            "PDF rendering pipeline refused: the render verdict above names the failing clause "
            "(combined manuscript PDF absent or too small, no PDF files in the output tree, a failing "
            "compilation, or an uncleared LaTeX warning policy)"
        )
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
            log_success("PDF rendering complete - ready for validation", logger)
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
