"""Figure path normalization for LaTeX PDF compilation.

Fixes figure paths in generated LaTeX so that \\includegraphics commands
resolve correctly when the LaTeX compiler runs from output/pdf/.

Extracted from _pdf_tex_transforms.py for file-size health.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def _normalize_path(path_str: str) -> str:
    """Normalize path to handle Unicode and encoding issues."""
    return unicodedata.normalize("NFC", path_str)


def _extract_filename(path_str: str) -> str:
    """Extract filename from various path formats."""
    path_str = _normalize_path(path_str)

    path_variations = [
        "../output/figures/",
        "output/figures/",
        "../figures/",
        "./figures/",
    ]
    for prefix in path_variations:
        if prefix in path_str:
            return path_str.split(prefix)[-1]

    if "/" in path_str or "\\" in path_str:
        return re.split(r"[/\\]", path_str)[-1]
    return path_str


def fix_figure_paths(tex_content: str, manuscript_dir: Path, output_dir: Path) -> str:
    r"""Fix figure paths in LaTeX content for proper compilation.

    Converts relative paths like ../output/figures/ to paths relative to the
    LaTeX compilation directory, ensuring \includegraphics commands work correctly.

    The LaTeX compiler runs from output/pdf/, so figures in output/figures/
    should be referenced as ../figures/filename.png

    Args:
        tex_content: LaTeX content to process
        manuscript_dir: Directory containing manuscript files
        output_dir: Output directory where LaTeX is compiled (typically output/pdf/)

    Returns:
        LaTeX content with corrected figure paths
    """
    # Pattern to match \includegraphics with or without options
    # Handles both \includegraphics{path} and \includegraphics[options]{path}
    # Note: This basic pattern may miss \pandocbounded with nested braces in alt={}
    pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"

    # Additional pattern for \pandocbounded{\includegraphics[...]{path}}
    # This handles the complex case where options contain nested braces (alt={...})
    # We'll use a fallback string replacement after regex for any missed paths

    # figures_dir must be derived from output_dir (LaTeX compiles in output/pdf/),
    # NOT from manuscript_dir — which may be output/manuscript/ and would produce
    # the double-path bug: output/manuscript/../output/figures = output/output/figures.
    # output_dir is the pdf/ directory; figures/ is its sibling in output/.
    figures_dir = output_dir.parent / "figures"
    fixed_count = 0
    paths_fixed: list[str] = []

    def fix_path(match: re.Match[str]) -> str:
        r"""Fix a single includegraphics path to be relative to the compilation directory.

        Transforms figure paths from various formats (absolute, manuscript-relative,
        etc.) to paths relative to the LaTeX compilation directory (output/pdf/).
        Preserves any optional parameters like width or height specifications.

        Args:
            match: Regular expression match object containing:
                - group(0): The full \\includegraphics command
                - group(1): The figure path within braces

        Returns:
            The corrected \\includegraphics command with path relative to ../figures/.

        Note:
            - Logs a warning if the referenced figure file does not exist
            - Still returns the fixed path even for missing files to allow
              compilation to continue with other content
        """
        nonlocal fixed_count

        old_path = match.group(1)
        original_path = old_path

        # Check if already in correct format
        if old_path.startswith("../figures/"):
            return match.group(0)

        # Extract filename, handling encoding issues
        filename = _extract_filename(old_path)

        # Build new path relative to compilation directory
        # Since we're compiling in output_dir (output/pdf), figures are in ../figures/
        new_path = f"../figures/{filename}"

        # Verify the figure file exists (try both normalized and non-normalized)
        fig_full_path = figures_dir / filename
        fig_normalized = figures_dir / _normalize_path(filename)

        file_exists = fig_full_path.exists() or fig_normalized.exists()

        if file_exists:
            fixed_count += 1
            paths_fixed.append(f"{original_path} -> {new_path}")
            # Preserve options if present
            full_match = match.group(0)
            if "[" in full_match:
                # Extract options
                options_start = full_match.find("[")
                options_end = full_match.find("]")
                options = full_match[options_start : options_end + 1]
                return f"\\includegraphics{options}{{{new_path}}}"
            else:
                return f"\\includegraphics{{{new_path}}}"
        else:
            logger.warning(f"Figure file not found: {fig_full_path}")
            fixed_count += 1
            paths_fixed.append(f"{original_path} -> {new_path} (FILE NOT FOUND)")
            # Still return fixed path so compilation continues
            full_match = match.group(0)
            if "[" in full_match:
                options_start = full_match.find("[")
                options_end = full_match.find("]")
                options = full_match[options_start : options_end + 1]
                return f"\\includegraphics{options}{{{new_path}}}"
            else:
                return f"\\includegraphics{{{new_path}}}"

    # Primary pass: regex-based replacement handles well-formed \includegraphics commands
    tex_content = re.sub(pattern, fix_path, tex_content)

    # Fallback passes: catch paths the primary regex misses when \includegraphics options
    # contain nested braces (e.g., alt={...} with LaTeX math) that break [^\]]*].
    # Each pass targets a distinct prefix pattern that Pandoc/LaTeX can produce.
    _fallbacks: list[tuple[str, str, str]] = [
        ("../output/figures/", "../figures/", "fallback 1 (../output/figures/)"),
        ("]{figures/", "]{../figures/", "fallback 2 (bare figures/)"),
        ("]{output/figures/", "]{../figures/", "fallback 3 (output/figures/)"),
    ]
    for old, new, label in _fallbacks:
        count = tex_content.count(old)
        if count > 0:
            tex_content = tex_content.replace(old, new)
            fixed_count += count
            logger.info(f"Fixed {count} figure path(s) via {label}")

    if fixed_count > 0:
        logger.info(f"Fixed {fixed_count} figure path(s)")
        for path_info in paths_fixed[:10]:  # Show first 10
            logger.debug(f"  {path_info}")
        if len(paths_fixed) > 10:
            logger.debug(f"  ... and {len(paths_fixed) - 10} more")
    else:
        # No paths fixed - check if there are any figure references at all
        if pattern and re.search(pattern, tex_content):
            logger.debug("No figure paths needed fixing (already in correct format)")

    return tex_content
