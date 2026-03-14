"""LaTeX content transformation functions for PDF rendering.

Handles rewriting/fixing of generated LaTeX content:
- Figure path normalization for compilation from output/pdf/
- Math delimiter repair from Pandoc conversion artifacts

Extracted from _pdf_latex_helpers.py for file-size health.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


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

    def normalize_path(path_str: str) -> str:
        """Normalize path to handle Unicode and encoding issues."""
        # Normalize Unicode characters using NFC (composition form)
        normalized = unicodedata.normalize("NFC", path_str)
        return normalized

    def extract_filename(path_str: str) -> str:
        """Extract filename from various path formats."""
        # Normalize first
        path_str = normalize_path(path_str)

        # Handle various path formats
        path_variations = [
            "../output/figures/",
            "output/figures/",
            "../figures/",
            "./figures/",
        ]

        for prefix in path_variations:
            if prefix in path_str:
                return path_str.split(prefix)[-1]

        # If no prefix matched, could be just a filename or absolute path
        if "/" in path_str or "\\" in path_str:
            # Split by last / or \
            return re.split(r"[/\\]", path_str)[-1]
        else:
            # Just a filename
            return path_str

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
        filename = extract_filename(old_path)

        # Build new path relative to compilation directory
        # Since we're compiling in output_dir (output/pdf), figures are in ../figures/
        new_path = f"../figures/{filename}"

        # Verify the figure file exists (try both normalized and non-normalized)
        fig_full_path = figures_dir / filename
        fig_normalized = figures_dir / normalize_path(filename)

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

    # Apply path fixes
    tex_content = re.sub(pattern, fix_path, tex_content)

    # Fallback: Simple string replacement for paths the regex missed
    # This handles \pandocbounded{\includegraphics[...,alt={...}]{../output/figures/xxx.png}}
    # where nested braces in options break the regex pattern
    remaining_old_paths = tex_content.count("../output/figures/")
    if remaining_old_paths > 0:
        tex_content = tex_content.replace("../output/figures/", "../figures/")
        fixed_count += remaining_old_paths
        logger.info(f"Fixed {remaining_old_paths} additional figure path(s) via fallback")

    # Second fallback: Handle bare "figures/" paths (no ../ prefix)
    # These come from markdown ![...](figures/xxx.png) references that Pandoc
    # converts to \includegraphics{figures/xxx.png}. Since LaTeX compiles
    # from output/pdf/, these need to become ../figures/xxx.png.
    # We match the pattern "]{figures/" inside \includegraphics commands
    # to avoid false positives in regular text.
    bare_figure_count = tex_content.count("]{figures/")
    if bare_figure_count > 0:
        tex_content = tex_content.replace("]{figures/", "]{../figures/")
        fixed_count += bare_figure_count
        logger.info(f"Fixed {bare_figure_count} bare figure path(s) via second fallback")

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


def fix_math_delimiters(tex_content: str) -> str:
    r"""Fix broken math delimiters from Pandoc conversion.

    Pandoc incorrectly converts \[ and \] to {[} and {]}, breaking math mode.
    This function fixes these issues and restores proper LaTeX math formatting.

    Args:
        tex_content: LaTeX content with broken math delimiters

    Returns:
        LaTeX content with fixed math delimiters
    """
    fixed_count = 0

    # Helper function to fix math content
    def fix_math_content(content: str) -> str:
        """Fix broken patterns within math content."""
        # 1. Remove all nested {[} and {]} that Pandoc incorrectly inserted
        content = re.sub(r"\{\[\}", "", content)
        content = re.sub(r"\{\]\}", "", content)

        # 2. Fix \mathbb{E}\emph{\{q(s}\tau)\} -> \mathbb{E}_{q(s_\tau)}
        # Pattern: \mathbb{E}\emph{\{q(s}\tau)\} or \mathbb{E}\emph{\{o}\tau)\}
        content = re.sub(
            r"\\mathbb\{E\}\\emph\{\\\{([^}]+)\}([a-zA-Z_]+)\\\}\)",
            r"\\mathbb{E}_{\1_\2}",
            content,
        )

        # 3. Fix broken subscripts: s\_\tau -> s_\tau, o\_\tau -> o_\tau
        content = re.sub(r"([a-zA-Z])\\_([a-zA-Z_]+)", r"\1_\2", content)

        # 4. Remove remaining \emph{} wrappers
        content = re.sub(r"\\emph\{([^}]+)\}", r"\1", content)

        # 5. Fix \textbar to \mid
        content = re.sub(r"\\textbar", r"\\mid", content)

        return content

    # Step 1: Fix display math with labels: {[} ... {]}\label{eq:...}{]}
    # Use greedy matching to find the LAST {]} before \label
    # Pattern: {[} ... (everything) ... {]}\label{...}{]}
    pattern_with_label = r"\{\[\}(.*)\{\]\}\\label\{([^}]+)\}\{\]\}"

    def fix_display_math_with_label(match: re.Match[str]) -> str:
        r"""Fix display math blocks that include equation labels.

        Handles the pattern {[} ... {]}\\label{eq:...}{]} which Pandoc incorrectly
        generates, converting it back to proper LaTeX: \\[...\\label{...}\\].

        Args:
            match: Regular expression match object containing:
                - group(1): The math content between delimiters
                - group(2): The equation label name

        Returns:
            Properly formatted LaTeX display math with label.
        """
        nonlocal fixed_count
        math_content = match.group(1)
        label_name = match.group(2)

        math_content = fix_math_content(math_content)
        fixed_count += 1
        return f"\\[{math_content}\\label{{{label_name}}}\\]"

    # Step 2: Fix display math without labels: {[} ... {]}
    # Match greedily to get the last {]} in a paragraph/block
    pattern_no_label = r"\{\[\}([^{]*?)\{\]\}(?!\\label)(?=\s|$)"

    def fix_display_math_no_label(match: re.Match[str]) -> str:
        r"""Fix display math blocks without equation labels.

        Handles the pattern {[} ... {]} which Pandoc incorrectly generates,
        converting it back to proper LaTeX display math: \\[...\\].

        Args:
            match: Regular expression match object containing:
                - group(1): The math content between delimiters

        Returns:
            Properly formatted LaTeX display math without label.
        """
        nonlocal fixed_count
        math_content = match.group(1)

        math_content = fix_math_content(math_content)
        fixed_count += 1
        return f"\\[{math_content}\\]"

    # Apply fixes: first with labels (greedy), then without
    tex_content = re.sub(
        pattern_with_label,
        fix_display_math_with_label,
        tex_content,
        flags=re.DOTALL,
    )
    tex_content = re.sub(
        pattern_no_label,
        fix_display_math_no_label,
        tex_content,
        flags=re.DOTALL | re.MULTILINE,
    )

    # Step 3: Fix remaining issues globally
    tex_content = re.sub(r"\\textbar", r"\\mid", tex_content)

    # Fix broken Greek letters with error handling
    greek_letters = [
        "tau",
        "pi",
        "Theta",
        "alpha",
        "beta",
        "gamma",
        "lambda",
        "kappa",
        "sigma",
        "phi",
        "eta",
    ]
    for greek in greek_letters:
        try:
            # Match: backslash + greek_letter + backslash + close-paren
            # In the LaTeX, we see: \tau\) and want: \tau)
            # Build pattern as: \\tau\\) (escaping each backslash for regex)
            pat = r"\\" + greek + r"\\\)"
            replacement = "\\\\" + greek + ")"
            tex_content = re.sub(pat, replacement, tex_content)
        except re.error as e:
            logger.warning(f"Failed to fix Greek letter '{greek}': {e}. Skipping this pattern.")
            continue
        except (TypeError, ValueError) as e:
            logger.warning(
                f"Unexpected error fixing Greek letter '{greek}': {e}. Skipping this pattern."
            )
            continue

    if fixed_count > 0:
        logger.info(f"Fixed {fixed_count} math delimiter(s)")

    return tex_content
