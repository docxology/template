"""Pandoc command construction and execution for combined PDF rendering."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pandoc_filters import formalism_filter_args
from infrastructure.rendering._pdf_pandoc_engine import build_pandoc_render_error
from infrastructure.rendering.combined_native_commands import pdf_combined_command

if TYPE_CHECKING:
    from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)


def build_pandoc_tex_command(
    config: "RenderingConfig",
    combined_md: Path,
    combined_tex: Path,
    manuscript_dir: Path,
) -> list[str]:
    """Build the Pandoc CLI command for markdown→LaTeX conversion."""
    configuration = None
    config_file = manuscript_dir / "config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as stream:
                decoded = yaml.safe_load(stream)
            if isinstance(decoded, dict):
                configuration = decoded
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("Failed to read typography settings from config.yaml: %s", exc)
    # Preserve Source's formalism-before-Crossref ordering.
    formalism = formalism_filter_args()

    crossref = shutil.which("pandoc-crossref")
    if crossref:
        logger.info("Using pandoc-crossref at %s", crossref)
    else:
        logger.warning(
            "pandoc-crossref not on PATH; @sec:/@tbl:/@fig:/@eq: will not resolve. "
            "Install: https://github.com/lierdakil/pandoc-crossref (e.g. brew install pandoc-crossref)"
        )

    return pdf_combined_command(
        config.pandoc_path,
        combined_md,
        combined_tex,
        manuscript_dir,
        Path(config.figures_dir),
        configuration,
        formalism,
        crossref,
    )


def run_pandoc_conversion(
    cmd: list[str],
    combined_md: Path,
    source_files: list[Path],
    md_content: str,
) -> None:
    """Execute the Pandoc subprocess, raising on failure."""
    from infrastructure.reporting.native_renderer_source_call import run_source_native_pandoc

    try:
        if run_source_native_pandoc(cmd, combined_md, source_files, writer="latex"):
            return
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )
    except subprocess.CalledProcessError as e:
        raise build_pandoc_render_error(e, combined_md, source_files, md_content, cmd) from e
