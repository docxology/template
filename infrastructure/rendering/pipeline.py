"""Rendering pipeline orchestrator module.

This module coordinates the PDF rendering stage by:
1. Validating LaTeX packages
2. Verifying figures
3. Rendering individual manuscript files to multiple formats
4. Generating a combined PDF and HTML
5. Verifying output quality
"""

import subprocess
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError, ValidationError
from infrastructure.core.logging.constants import BANNER_WIDTH
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
from infrastructure.project.discovery import resolve_project_root
from infrastructure.publishing.transmission_bookends import is_transmission_bookend

# Re-exports for backwards compatibility
from infrastructure.rendering._pipeline_summary import (  # noqa: F401
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)

logger = get_logger(__name__)


def _has_generated_manuscript_ordering(config_path: Path) -> bool:
    """Return True when an injected config owns generated manuscript ordering."""
    if not config_path.is_file():
        return False
    return "# Generated manuscript ordering" in config_path.read_text(encoding="utf-8")


def _resolve_manuscript_dir(project_root: Path) -> Path:
    """Return the manuscript directory to render from.

    Prefers the injected output/manuscript/ directory when it exists and
    contains markdown files; falls back to the source manuscript/ directory.

    When the injected dir is selected, this function also refreshes the
    rendering-critical auxiliary files (``config.yaml`` and ``*.bib``) from
    the source ``manuscript/`` directory. Without a fresh ``config.yaml``,
    title-page and TOC injection can render from stale metadata.
    """
    import shutil as _shutil

    source_dir = project_root / "manuscript"
    injected_dir = project_root / "output" / "manuscript"
    if injected_dir.exists() and any(injected_dir.glob("*.md")):
        if source_dir.is_dir():
            cfg_src = source_dir / "config.yaml"
            cfg_dst = injected_dir / "config.yaml"
            if cfg_src.is_file():
                if _has_generated_manuscript_ordering(cfg_dst):
                    logger.info(
                        "Preserved generated config.yaml ordering in injected manuscript: %s",
                        cfg_dst,
                    )
                else:
                    _shutil.copy2(cfg_src, cfg_dst)
                    logger.info(f"Refreshed config.yaml in injected manuscript: {cfg_dst}")
            for bib in sorted(source_dir.glob("*.bib")):
                bib_dst = injected_dir / bib.name
                _shutil.copy2(bib, bib_dst)
                logger.info(f"Refreshed {bib.name} in injected manuscript: {bib_dst}")
        logger.info(f"Rendering from injected manuscript directory: {injected_dir}")
        return injected_dir
    return source_dir


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


def _run_manuscript_variable_script(
    project_root: Path,
    template_repo_root: Path | None = None,
) -> int:
    """Hydrate project manuscript variables before rendering, when available."""
    import os

    from infrastructure.core.runtime.environment import get_python_command

    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    if not script.is_file():
        return 0

    logger.info("Hydrating manuscript variables before render: %s", script.name)
    cmd = get_python_command() + [str(script)]
    env = os.environ.copy()
    if template_repo_root is not None:
        env.setdefault("TEMPLATE_REPO_ROOT", str(template_repo_root))
    try:
        result = subprocess.run(  # nosec B603
            cmd,
            cwd=str(project_root),
            env=env,
            check=False,
            timeout=300,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        logger.error("Manuscript variable hydration failed to execute: %s", exc)
        return 1

    if result.returncode != 0:
        logger.error("Manuscript variable hydration failed (exit code %s)", result.returncode)
        return 1
    log_success("Manuscript variables hydrated", logger)
    return 0


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
    logger.info("\n" + "=" * BANNER_WIDTH)
    logger.info(f"MANUSCRIPT COMPOSITION ({len(source_files)} files)")
    logger.info("=" * BANNER_WIDTH)
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
    logger.info("=" * BANNER_WIDTH + "\n")


def _load_project_config_yaml(manuscript_dir: Path) -> dict[str, Any] | None:
    """Load the manuscript ``config.yaml`` as a plain dict for render-format toggles.

    Returns None when the file is missing, unparseable, or PyYAML is unavailable —
    callers must fall back to defaults in that case. Best-effort by design.
    """
    cfg = manuscript_dir / "config.yaml"
    if not cfg.is_file():
        return None
    try:
        import yaml
    except ImportError:
        logger.debug("PyYAML not available; cannot read render.formats from config.yaml")
        return None
    try:
        with cfg.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError) as exc:
        logger.debug(f"Could not parse {cfg.name} for render formats: {exc}")
        return None


def _render_individual_files(
    manager: "RenderManager",
    source_files: list[Path],
    reporter: "DiagnosticReporter",
) -> tuple[int, list[str]]:
    """Render each source file; return (rendered_count, failed_file_names).

    Per-file chatter (each output path) is emitted at DEBUG; the stage-level
    progress bar carries the user-facing signal at INFO.
    """
    rendered_count = 0
    failed_files: list[str] = []
    progress = SubStageProgress(total=len(source_files), stage_name="Rendering Files")
    for i, source_file in enumerate(source_files, 1):
        progress.start_substage(i, source_file.name)
        try:
            if is_transmission_bookend(source_file):
                logger.debug(
                    "Skipping per-file render for transmission bookend (combined PDF only): %s",
                    source_file.name,
                )
                progress.complete_substage()
                continue
            outputs = manager.render_all(source_file)
            if outputs:
                for output_path in outputs:
                    logger.debug(f"  Generated: {output_path.name}")
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
    """Generate the combined PDF / HTML / DOCX / EPUB manuscripts.

    Each format is gated on the corresponding ``manager.config.enable_<fmt>``
    boolean. Defaults preserve current behavior (PDF + HTML on; DOCX + EPUB
    off — opt in via ``render.formats.{docx,epub}: true`` in
    ``manuscript/config.yaml``).
    """
    import traceback

    config = manager.config

    # ── Combined PDF ───────────────────────────────────────────────
    if config.enable_pdf:
        logger.debug("\n" + "=" * BANNER_WIDTH)
        logger.info("Generating combined PDF manuscript...")
        try:
            combined_pdf = manager.render_combined_pdf(_combined_source_files(md_files), manuscript_dir, project_name)
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
    else:
        logger.info("[skip] PDF rendering disabled in config (render.formats.pdf=false)")

    # ── Combined HTML ──────────────────────────────────────────────
    if config.enable_html:
        logger.debug("\n" + "=" * BANNER_WIDTH)
        logger.info("Generating combined HTML manuscript...")
        try:
            manager.render_combined_web(_combined_source_files(md_files), manuscript_dir, project_name)
        except RenderingError as re:
            logger.warning(f"⚠️  Rendering error generating combined HTML: {re.message}")
            reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            logger.warning(f"⚠️  Unexpected error generating combined HTML: {e}")
    else:
        logger.info("[skip] HTML rendering disabled in config (render.formats.html=false)")

    # ── Combined DOCX (opt-in) ─────────────────────────────────────
    if config.enable_docx:
        _render_combined_docx(manager, manuscript_dir, project_name, reporter)
    else:
        logger.debug("[skip] DOCX rendering disabled in config (default; render.formats.docx=true to enable)")

    # ── Combined EPUB (opt-in) ─────────────────────────────────────
    if config.enable_epub:
        _render_combined_epub(manager, manuscript_dir, project_name, reporter)
    else:
        logger.debug("[skip] EPUB rendering disabled in config (default; render.formats.epub=true to enable)")


def _combined_source_files(md_files: list[Path]) -> list[Path]:
    """Return combined-render inputs, ignoring missing generated transmission bookends."""
    combined_files: list[Path] = []
    for path in md_files:
        if path.exists() or not is_transmission_bookend(path):
            combined_files.append(path)
    return combined_files


_html_combined_source_files = _combined_source_files


def _resolve_combined_markdown(manuscript_dir: Path) -> Path | None:
    """Find the combined-manuscript markdown produced by the combined-PDF pipeline.

    The combined renderer writes to ``<project>/output/pdf/_combined_manuscript.md``
    or ``<project>/output/tex/_combined_manuscript.md`` depending on layout.
    DOCX + EPUB rendering reuses this preprocessed source.

    ``manuscript_dir`` may be either the source ``<project>/manuscript/`` or the
    injected ``<project>/output/manuscript/``. We canonicalise to ``<project>/``
    and then probe ``output/{pdf,tex}/_combined_manuscript.md``.
    """
    if manuscript_dir.name == "manuscript" and manuscript_dir.parent.name == "output":
        project_root = manuscript_dir.parent.parent
    else:
        project_root = manuscript_dir.parent
    candidates = [
        project_root / "output" / "pdf" / "_combined_manuscript.md",
        project_root / "output" / "tex" / "_combined_manuscript.md",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def _resolve_bibliography(manuscript_dir: Path) -> Path | None:
    """Return the first .bib in the manuscript dir, or None if not found."""
    bibs = sorted(manuscript_dir.glob("*.bib"))
    return bibs[0] if bibs else None


def _render_combined_docx(
    manager: "RenderManager",
    manuscript_dir: Path,
    project_name: str,
    reporter: "DiagnosticReporter",
) -> None:
    """Render the combined DOCX from the preprocessed combined markdown."""
    from infrastructure.rendering.docx_renderer import render_docx

    combined_md = _resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] DOCX rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    docx_dir = Path(manager.config.docx_dir)
    docx_dir.mkdir(parents=True, exist_ok=True)
    out_path = docx_dir / f"{project_name}_combined.docx"
    bibliography = _resolve_bibliography(manuscript_dir)

    logger.debug("\n" + "=" * BANNER_WIDTH)
    logger.info("Generating combined DOCX manuscript...")
    try:
        result = render_docx(
            combined_md,
            out_path,
            bibliography=bibliography,
            pandoc_path=manager.config.pandoc_path,
        )
        logger.info(f"✅ Generated combined DOCX: {result.output_path.name} ({result.size_bytes / 1024:.1f} KB)")
    except RenderingError as re:
        logger.warning(f"⚠️  Rendering error generating combined DOCX: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
    except (OSError, subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
        logger.warning(f"⚠️  Unexpected error generating combined DOCX: {e}")


def _render_combined_epub(
    manager: "RenderManager",
    manuscript_dir: Path,
    project_name: str,
    reporter: "DiagnosticReporter",
) -> None:
    """Render the combined EPUB from the preprocessed combined markdown."""
    from infrastructure.rendering.epub_renderer import render_epub

    combined_md = _resolve_combined_markdown(manuscript_dir)
    if combined_md is None:
        logger.warning(
            "[skip] EPUB rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)"
        )
        return

    epub_dir = Path(manager.config.epub_dir)
    epub_dir.mkdir(parents=True, exist_ok=True)
    out_path = epub_dir / f"{project_name}_combined.epub"
    bibliography = _resolve_bibliography(manuscript_dir)

    logger.debug("\n" + "=" * BANNER_WIDTH)
    logger.info("Generating combined EPUB manuscript...")
    try:
        result = render_epub(
            combined_md,
            out_path,
            bibliography=bibliography,
            pandoc_path=manager.config.pandoc_path,
        )
        logger.info(f"✅ Generated combined EPUB: {result.output_path.name} ({result.size_bytes / 1024:.1f} KB)")
    except RenderingError as re:
        logger.warning(f"⚠️  Rendering error generating combined EPUB: {re.message}")
        reporter.record(re.to_diagnostic_event(severity=DiagnosticSeverity.WARNING))
    except (OSError, subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
        logger.warning(f"⚠️  Unexpected error generating combined EPUB: {e}")


def _render_pipeline_impl(project_name: str = "project", *, skip_manuscript_hydration: bool = False) -> int:
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
            poster_dir=str(project_root / "output" / "posters"),
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
    """Execute PDF rendering orchestration.

    Args:
        project_name: Name of project in projects/ directory.
        skip_manuscript_hydration: when True, skip the (slow) manuscript-variable
            hydration step before rendering — for fast title-page/metadata
            re-renders that do not need an analysis rebuild.

    Returns:
        Exit code (0=success, 1=failure)
    """
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
    # Re-exports from _pipeline_summary
    "generate_rendering_summary",
    "log_rendering_summary",
    "verify_pdf_outputs",
    # Public entry point
    "execute_render_pipeline",
]
