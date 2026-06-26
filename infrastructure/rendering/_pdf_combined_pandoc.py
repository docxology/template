"""Pandoc command construction and execution for combined PDF rendering."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_pandoc_engine import build_pandoc_render_error

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
    figures_dir = Path(config.figures_dir)
    cmd = [
        config.pandoc_path,
        str(combined_md),
        "-o",
        str(combined_tex),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=latex",
        "--standalone",
        "--number-sections",
        "--natbib",
        "--metadata=linkReferences:true",
        "--resource-path=" + str(manuscript_dir),
        "--resource-path=" + str(figures_dir),
    ]

    # Attempt to extract geometry from config.yaml and pass to pandoc
    config_file = manuscript_dir / "config.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            if yaml_data and isinstance(yaml_data, dict):
                metadata = yaml_data.get("metadata", {})
                geometry = metadata.get("geometry")
                if geometry:
                    cmd.extend(["-V", f"geometry:{geometry}"])
                    logger.debug(f"Added geometry to pandoc args: {geometry}")
                # Opt-in typography overrides (mirror the geometry pattern). Unset =>
                # pandoc defaults, so existing projects are unaffected. ``documentclass``
                # (e.g. ``extarticle``) is required for sub-10pt ``fontsize`` values.
                documentclass = metadata.get("documentclass")
                if documentclass:
                    cmd.extend(["-V", f"documentclass:{documentclass}"])
                    logger.debug(f"Added documentclass to pandoc args: {documentclass}")
                fontsize = metadata.get("fontsize")
                if fontsize:
                    cmd.extend(["-V", f"fontsize:{fontsize}"])
                    logger.debug(f"Added fontsize to pandoc args: {fontsize}")
        except (OSError, yaml.YAMLError) as e:
            logger.warning(f"Failed to read typography settings from config.yaml: {e}")

    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd.extend(["--filter", crossref])
        logger.info("Using pandoc-crossref at %s", crossref)
    else:
        logger.warning(
            "pandoc-crossref not on PATH; @sec:/@tbl:/@fig:/@eq: will not resolve. "
            "Install: https://github.com/lierdakil/pandoc-crossref (e.g. brew install pandoc-crossref)"
        )

    return cmd


def run_pandoc_conversion(
    cmd: list[str],
    combined_md: Path,
    source_files: list[Path],
    md_content: str,
) -> None:
    """Execute the Pandoc subprocess, raising on failure."""
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )
    except subprocess.CalledProcessError as e:
        raise build_pandoc_render_error(e, combined_md, source_files, md_content, cmd) from e
