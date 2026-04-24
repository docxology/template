"""Math delimiter repair for LaTeX content from Pandoc conversion.

Fixes broken math delimiters ({[} / {]}) and related artifacts that Pandoc
introduces when converting Markdown to LaTeX.

Extracted from _pdf_tex_transforms.py for file-size health.
"""

from __future__ import annotations

import re

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


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

    # Repair Pandoc inline-math closures where the trailing backslash was lost,
    # e.g. ``\(\sigma)`` (open math, then literal ``)``) instead of ``\(\sigma\)``.
    # xelatex flags every such case as "Bad math environment delimiter" and
    # recovers, but the warnings hide real issues. Two shapes are handled:
    #   1. ``\(\<greek>)``                      -> ``\(\<greek>\)``
    #   2. ``\(<base>_\<greek>)`` with optional super/subscripts on the base
    #      e.g. ``\(s_\tau)``                   -> ``\(s_\tau\)``
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
        "mu",
        "nu",
        "rho",
        "omega",
    ]
    for greek in greek_letters:
        try:
            tex_content = re.sub(
                rf"\\\(\\{greek}\)",
                rf"\\(\\{greek}\\)",
                tex_content,
            )
            tex_content = re.sub(
                rf"\\\(([^()\\]+_\\{greek})\)",
                r"\\(\1\\)",
                tex_content,
            )
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
