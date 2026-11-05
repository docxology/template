"""Pre-render validation helpers for combined PDF rendering."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_preflight import check_brace_balance
from infrastructure.validation.content.prerender import (
    prevalidate_for_render,
)

logger = get_logger(__name__)

__all__ = [
    "prevalidate_for_render",
    "prevalidate_markdown",
    "verify_figure_references",
]


def verify_figure_references(tex_content: str, figures_dir: Path) -> None:
    """Verify that all \\includegraphics references resolve to existing files."""
    fig_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
    referenced_figures = re.findall(fig_pattern, tex_content)

    if not referenced_figures:
        return

    logger.info(f"Verifying {len(referenced_figures)} figure reference(s)...")
    missing_figures: list[str] = []
    found_figures: list[str] = []

    def _figure_candidates(fig_ref: str) -> list[Path]:
        ref = fig_ref.strip()
        if ref.startswith(r"\detokenize{"):
            ref = ref.removeprefix(r"\detokenize{").rstrip("}")
        ref_path = Path(ref)
        candidates: list[Path] = []
        if ref_path.is_absolute():
            candidates.append(ref_path)
        parts = ref_path.parts
        if "figures" in parts:
            figure_index = parts.index("figures")
            candidates.append(figures_dir.joinpath(*parts[figure_index + 1 :]))
        candidates.extend([figures_dir / ref_path, figures_dir / ref_path.name])
        return [Path(unicodedata.normalize("NFC", str(candidate))) for candidate in candidates]

    for fig_ref in referenced_figures:
        display_name = fig_ref.split("/")[-1].rstrip("}")
        existing_path = next((candidate for candidate in _figure_candidates(fig_ref) if candidate.exists()), None)

        if existing_path is not None:
            found_figures.append(display_name)
            logger.debug(f"  ✓ Found: {display_name}")
        else:
            missing_figures.append(display_name)
            logger.warning(f"  ✗ Missing: {display_name}")
            if figures_dir.exists():
                similar = [
                    f.name
                    for f in figures_dir.rglob("*")
                    if f.name.lower().startswith(display_name.split(".")[0].lower())
                ]
                if similar:
                    logger.debug(f"    Similar files found: {', '.join(similar)}")

    logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
    if missing_figures:
        logger.warning(f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}")
        if len(missing_figures) > 5:
            logger.warning(f"  ... and {len(missing_figures) - 5} more missing figures")


def prevalidate_markdown(combined_md: Path) -> tuple[list[str], str]:
    """Pre-validate combined markdown for common issues.

    Returns:
        Tuple of (validation_errors, md_content)
    """
    validation_errors: list[str] = []
    md_content = ""
    if combined_md.exists():
        try:
            md_content = combined_md.read_text(encoding="utf-8")
            validation_errors = check_brace_balance(md_content)
            if validation_errors:
                logger.warning(f"Pre-validation found {len(validation_errors)} potential issue(s):")
                for err in validation_errors:
                    logger.warning(f"  • {err}")
                logger.info("  (These are warnings - PDF generation will proceed)")
        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
            logger.debug(f"Pre-validation check failed: {e}")
    return validation_errors, md_content
