"""Private helper functions for PDF/LaTeX processing.

Extracted from pdf_renderer.py to reduce file size. These are module-level
functions that operate on data parameters rather than instance state.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Re-exports for backward compatibility — implementations moved to _pdf_tex_transforms.py
from infrastructure.rendering._pdf_tex_transforms import fix_figure_paths as fix_figure_paths  # noqa: F401
from infrastructure.rendering._pdf_tex_transforms import fix_math_delimiters as fix_math_delimiters  # noqa: F401


def extract_preamble(preamble_file: Path) -> str:
    """Extract LaTeX preamble from markdown file.

    Looks for content between ```latex and ``` blocks.
    Handles various markdown code fence formats.

    Args:
        preamble_file: Path to preamble.md file

    Returns:
        LaTeX preamble content or empty string if not found
    """
    try:
        content = preamble_file.read_text()
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to read preamble file: {e}")
        return ""

    # Look for ```latex ... ``` blocks (handles various line ending styles)

    # Pattern handles different line endings and optional whitespace
    pattern = r"```\s*latex\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        # Combine all latex blocks
        preamble_lines = [match.strip() for match in matches]
        result = "\n".join(preamble_lines)
        logger.debug(f"Extracted {len(matches)} LaTeX preamble block(s) ({len(result)} chars)")
        return result
    else:
        logger.debug(f"No LaTeX code blocks found in {preamble_file.name}")
        return ""


def check_latex_log_for_graphics_errors(log_file: Path) -> dict[str, list[str]]:
    """Parse LaTeX log file for graphics-related errors and warnings.

    Args:
        log_file: Path to LaTeX .log file

    Returns:
        Dictionary with graphics issues found
    """
    result: dict[str, list[str]] = {
        "graphics_errors": [],
        "graphics_warnings": [],
        "missing_files": [],
    }

    if not log_file.exists():
        return result

    try:
        log_content = log_file.read_text(errors="ignore")

        # Look for common graphics-related error patterns

        # Pattern for file not found errors
        file_not_found = re.findall(r"File `([^`]+)` not found", log_content)
        result["missing_files"].extend(file_not_found)

        # Pattern for graphics package warnings
        graphics_warnings = re.findall(
            r"((?:Package graphics|Graphics Error).*?)(?=\n(?:!|\s*$))",
            log_content,
            re.IGNORECASE,
        )
        result["graphics_warnings"].extend(graphics_warnings)

        # Check for undefined control sequences related to graphics
        if r"\includegraphics" in log_content and "Undefined" in log_content:
            result["graphics_errors"].append(
                "includegraphics command undefined - graphicx package may not be loaded"
            )

        return result

    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"Error parsing LaTeX log: {e}")
        return result


def generate_title_page_preamble(manuscript_dir: Path) -> str:
    """Generate LaTeX title page preamble commands from config.yaml metadata.

    These commands (\\title, \\author, \\date) must be in the preamble
    (before \\begin{document}).

    Args:
        manuscript_dir: Directory containing manuscript files and config.yaml

    Returns:
        LaTeX preamble commands for title page, or empty string if config not found
    """
    config_file = manuscript_dir / "config.yaml"

    if not config_file.exists():
        logger.debug(f"Config file not found: {config_file}")
        return ""

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        if not config:
            return ""

        # Extract metadata
        paper = config.get("paper", {})
        authors = config.get("authors", [])

        title = paper.get("title", "Research Paper")
        subtitle = paper.get("subtitle", "")
        date = paper.get("date", "")
        doi = config.get("publication", {}).get("doi", "")

        # Build preamble commands (must be before \begin{document})
        preamble_lines = [
            f"\\title{{{title}}}",
        ]
        # Add subtitle if present
        if subtitle:
            preamble_lines[-1] = f"\\title{{{title}\\\\\\normalsize {subtitle}}}"

        # Add authors with proper formatting (including email, affiliation, ORCID)
        if authors:
            author_blocks = []
            for author in authors:
                if "name" not in author:
                    continue

                name = author["name"]
                parts = [name]

                # Add affiliation if present
                if "affiliation" in author:
                    parts.append(f"\\\\\\footnotesize{{{author['affiliation']}}}")

                # Add email if present
                if "email" in author:
                    parts.append(f"\\\\\\footnotesize{{\\texttt{{{author['email']}}}}}")

                # Add ORCID if present (with hyperlink)
                if "orcid" in author:
                    orcid = author["orcid"]
                    parts.append(
                        f"\\\\\\footnotesize{{\\href{{https://orcid.org/{orcid}}}{{ORCID: {orcid}}}}}"  # noqa: E501
                    )

                # Join all parts for this author
                author_block = "".join(parts)
                author_blocks.append(author_block)

            if author_blocks:
                # Use standard \and for multiple authors, but tight formatting within each
                author_str = " \\\\and ".join(author_blocks)

                # Add DOI and Date to the author block for tight vertical layout
                extras = []
                if doi:
                    extras.append(f"\\href{{https://doi.org/{doi}}}{{DOI: {doi}}}")

                if date:
                    extras.append(date)

                if extras:
                    # Add extras with small vertical space and small font
                    author_str += " \\\\ " + " \\\\ ".join(
                        [f"\\footnotesize{{{e}}}" for e in extras]
                    )

                preamble_lines.append(f"\\author{{{author_str}}}")

        if date:
            preamble_lines.append(f"\\date{{{date}}}")
        else:
            preamble_lines.append(r"\date{\today}")

        logger.debug(f"Generated title page preamble with {len(preamble_lines)} commands")
        return "\n".join(preamble_lines)

    except (OSError, yaml.YAMLError, KeyError, ValueError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return ""


def generate_title_page_body(manuscript_dir: Path) -> str:
    """Generate LaTeX title page body command from config.yaml metadata.

    The \\maketitle command must be called AFTER \\begin{document}.

    Args:
        manuscript_dir: Directory containing manuscript files and config.yaml

    Returns:
        LaTeX \\maketitle command with proper formatting, or empty string if config not found
    """
    config_file = manuscript_dir / "config.yaml"

    if not config_file.exists():
        return ""

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        if not config:
            return ""

        # Build body commands (must be after \begin{document})
        body_lines = [
            "\\maketitle",
            "\\thispagestyle{empty}",
        ]

        logger.debug(f"Generated title page body with {len(body_lines)} commands")
        return "\n".join(body_lines)

    except (OSError, yaml.YAMLError, KeyError, ValueError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return ""
