"""Manuscript metrics injection for template/.

Reads a ``metrics.json`` file produced by ``generate_manuscript_metrics.py``
and performs ``${variable}`` substitution in every numbered manuscript chapter,
writing the rendered versions to a specified output directory.

The pipeline hook in ``scripts/03_render_pdf.py`` automatically picks up the
rendered files from ``output/manuscript/`` if that directory is populated.

Public API:
    load_metrics      -- deserialise metrics.json
    render_chapter    -- process one chapter file with variable substitution
    render_all_chapters -- process all numbered chapters and copy ancillary files
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from string import Template

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Pattern for manuscript chapters: starts with one or more digits
_CHAPTER_PATTERN = re.compile(r"^\d")

# Non-chapter files to copy verbatim (preamble, bib, etc.)
_ANCILLARY_EXTENSIONS = {".bib", ".tex", ".yaml", ".yml"}


def load_metrics(metrics_path: Path) -> dict:
    """Load and validate a metrics JSON file.

    Args:
        metrics_path: Path to the ``metrics.json`` file.

    Returns:
        Dictionary of metric name → value, flat (nested keys are also flattened
        into dotted names for convenience, e.g. ``projects.code_project.test_count``).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON.
    """
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    try:
        with open(metrics_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {metrics_path}: {exc}") from exc

    # Build a flat dict for Template substitution
    flat: dict[str, str] = {}
    _flatten(raw, "", flat)

    logger.info(f"Loaded {len(flat)} metric variables from {metrics_path.name}")
    return flat


def _flatten(obj: object, prefix: str, out: dict[str, str]) -> None:
    """Recursively flatten a nested dict into ``prefix_key`` → str entries."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}_{k}" if prefix else k
            _flatten(v, new_key, out)
    elif isinstance(obj, (list, tuple)):
        out[prefix] = str(len(obj))  # lists → their length as a string
    else:
        out[prefix] = str(obj) if obj is not None else ""


def render_chapter(source_md: Path, metrics: dict, output_dir: Path) -> Path:
    """Substitute ``${variable}`` tokens in a chapter file using *metrics*.

    Uses :class:`string.Template` ``safe_substitute`` so that any unrecognised
    ``${...}`` tokens are left intact rather than raising an error.

    Args:
        source_md: Path to the source Markdown file (may contain ``${var}``).
        metrics:   Flat dict of variable name → string value.
        output_dir: Directory where the rendered file will be written.

    Returns:
        Path of the written rendered file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / source_md.name

    try:
        source_text = source_md.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error(f"Cannot read {source_md}: {exc}")
        raise

    rendered = Template(source_text).safe_substitute(metrics)

    # Warn about any unresolved tokens that remain
    remaining = re.findall(r"\$\{([^}]+)\}", rendered)
    if remaining:
        logger.warning(
            f"{source_md.name}: {len(remaining)} unresolved token(s): "
            + ", ".join(f"${{{t}}}" for t in sorted(set(remaining)))
        )

    dest.write_text(rendered, encoding="utf-8")
    logger.debug(f"Rendered {source_md.name} → {dest}")
    return dest


def render_all_chapters(
    manuscript_dir: Path, metrics: dict, output_dir: Path
) -> list[Path]:
    """Process all numbered chapter files and copy ancillary files.

    Numbered chapters (filenames starting with a digit) undergo variable
    substitution.  All other files (``references.bib``, ``preamble.md``,
    ``config.yaml``, etc.) are copied verbatim so that the output directory
    is a self-contained, fully renderable manuscript directory.

    Args:
        manuscript_dir: Source manuscript directory (contains ``NN_*.md`` files).
        metrics:        Flat dict of variable name → string value.
        output_dir:     Destination directory for rendered files.

    Returns:
        List of paths of all written files (rendered + copied).
    """
    if not manuscript_dir.is_dir():
        raise FileNotFoundError(f"Manuscript directory not found: {manuscript_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for item in sorted(manuscript_dir.iterdir()):
        if item.is_dir():
            continue  # skip subdirectories

        if _CHAPTER_PATTERN.match(item.name) and item.suffix == ".md":
            # Numbered chapter — apply substitution
            dest = render_chapter(item, metrics, output_dir)
            written.append(dest)
        else:
            # Ancillary file — copy verbatim
            dest = output_dir / item.name
            shutil.copy2(item, dest)
            written.append(dest)
            logger.debug(f"Copied ancillary file: {item.name}")

    logger.info(
        f"render_all_chapters: {len(written)} files written to {output_dir}"
    )
    return written
