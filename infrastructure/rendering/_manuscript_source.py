"""Manuscript source resolution and per-file rendering helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import TemplateError, ValidationError
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.diagnostic import DiagnosticReporter, DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.core.progress import SubStageProgress
from infrastructure.publishing.transmission_bookends import is_transmission_bookend
from infrastructure.rendering import RenderManager
from infrastructure.rendering.latex_package_validator import validate_preamble_packages
from infrastructure.rendering.latex_validation import ValidationReport

logger = get_logger(__name__)


def has_generated_manuscript_ordering(config_path: Path) -> bool:
    """Return True when an injected config owns generated manuscript ordering."""
    if not config_path.is_file():
        return False
    return "# Generated manuscript ordering" in config_path.read_text(encoding="utf-8")


def resolve_manuscript_dir(project_root: Path) -> Path:
    """Return the manuscript directory to render from."""
    import shutil as _shutil

    source_dir = resolve_source_manuscript_dir(project_root)
    injected_dir = project_root / "output" / "manuscript"
    if injected_dir.exists() and any(injected_dir.glob("*.md")):
        if source_dir.is_dir():
            cfg_src = source_dir / "config.yaml"
            cfg_dst = injected_dir / "config.yaml"
            if cfg_src.is_file():
                if has_generated_manuscript_ordering(cfg_dst):
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


def run_override_script(project_root: Path, override_script: Path) -> int:
    """Delegate rendering to a project-specific override script."""
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


def run_manuscript_variable_script(
    project_root: Path,
    template_repo_root: Path | None = None,
) -> int:
    """Hydrate project manuscript variables before rendering, when available."""
    import os

    from infrastructure.core.runtime.environment import resolve_test_python

    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    if not script.is_file():
        return 0

    logger.info("Hydrating manuscript variables before render: %s", script.name)
    cmd = resolve_test_python(project_root / ".venv") + [str(script)]
    logger.info("Using manuscript hydration interpreter: %s", cmd[0])
    env = os.environ.copy()
    if template_repo_root is not None:
        env["TEMPLATE_REPO_ROOT"] = str(template_repo_root)
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


def validate_latex_packages(report: ValidationReport | None = None) -> int:
    """Run pre-flight LaTeX package validation."""
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


def log_manuscript_composition(source_files: list[Path]) -> None:
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


def load_project_config_yaml(manuscript_dir: Path) -> dict[str, Any] | None:
    """Load the manuscript ``config.yaml`` as a plain dict for render-format toggles."""
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


def _clean_stale_web_artifacts(manager: RenderManager) -> None:
    """Remove generated web artifacts before a fresh per-file HTML render."""
    if not getattr(manager.config, "enable_html", False):
        return
    web_dir = Path(manager.config.web_dir)
    if not web_dir.exists():
        return
    stale_files = sorted(web_dir.glob("*.html"))
    combined_markdown = web_dir / "_combined_manuscript.md"
    if combined_markdown.exists():
        stale_files.append(combined_markdown)
    removed = 0
    for stale in stale_files:
        try:
            stale.unlink()
            removed += 1
        except OSError as exc:
            logger.debug("Could not remove stale web artifact %s: %s", stale, exc)
    if removed:
        logger.info("Removed %d stale web artifact(s) from %s", removed, web_dir)


def render_individual_files(
    manager: RenderManager,
    source_files: list[Path],
    reporter: DiagnosticReporter,
) -> tuple[int, list[str]]:
    """Render each source file; return (rendered_count, failed_file_names)."""
    _clean_stale_web_artifacts(manager)
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
        except TemplateError as render_error:
            # RenderingError and all other template-domain failures carry the
            # same diagnostic contract. Record a per-section failure instead
            # of aborting before the combined-render summary is written.
            logger.warning(f"  ❌ Rendering error for {source_file.name}: {render_error.message}")
            reporter.record(render_error.to_diagnostic_event(severity=DiagnosticSeverity.ERROR))
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
