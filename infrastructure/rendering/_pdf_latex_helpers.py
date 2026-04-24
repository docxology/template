"""Private helper functions for PDF/LaTeX processing.

Extracted from pdf_renderer.py to reduce file size. These are module-level
functions that operate on data parameters rather than instance state.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


_DEFAULT_MATH_FONT = "latinmodern-math.otf"
_UNICODE_MATH_PATTERN = re.compile(
    r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{[^}]*\bunicode-math\b[^}]*\}"
)
_SETMATHFONT_PATTERN = re.compile(r"\\setmathfont\b")
# Match a real ``\setmathfont{...}`` declaration (not a comment that
# merely mentions the macro). Skips lines starting with ``%``.
_SETMATHFONT_DECLARATION = re.compile(
    r"^[^%\n]*\\setmathfont(?:\[[^\]]*\])?\{[^}]*\}[^\n]*", re.MULTILINE
)


def ensure_setmathfont(preamble: str, math_font: str = _DEFAULT_MATH_FONT) -> str:
    """Append a default ``\\setmathfont`` when ``unicode-math`` is loaded without one.

    ``unicode-math`` falls back through the active text font when no math
    font is declared. With Pandoc's default lmroman text font, characters
    like U+2223 (``\\mid``) and U+226A/226B (``\\ll``/``\\gg``) trigger
    *Missing character* warnings and ``U+FFFD`` glyphs in the rendered
    PDF. Bundling a ``\\setmathfont{latinmodern-math.otf}`` declaration
    when the user already loads ``unicode-math`` keeps every project
    glyph-clean by default and remains a no-op when the user supplied
    their own ``\\setmathfont`` directive.

    Args:
        preamble: LaTeX preamble content as a string.
        math_font: Filename or fontspec name of the math font to load.

    Returns:
        Preamble content, possibly extended with one ``\\setmathfont`` line.
    """
    if not preamble:
        return preamble
    if not _UNICODE_MATH_PATTERN.search(preamble):
        return preamble
    if _SETMATHFONT_PATTERN.search(preamble):
        return preamble

    annotation = (
        "% Auto-injected by infrastructure/rendering/_pdf_latex_helpers.py::"
        "ensure_setmathfont:\n"
        "% unicode-math is loaded but no \\setmathfont was declared. Without "
        "an explicit math\n"
        "% font the macros \\mid, \\ll, \\gg fall back to the lmroman text "
        "font (no U+2223 /\n"
        "% U+226A / U+226B) and emit Missing-character warnings. "
        + math_font + " ships\n"
        "% with TeX Live and covers the BMP math symbols.\n"
        "\\setmathfont{" + math_font + "}"
    )
    logger.debug("Auto-injecting \\setmathfont because unicode-math was loaded without one")
    return preamble.rstrip() + "\n\n" + annotation + "\n"


def extract_math_font_preamble(preamble: str) -> str | None:
    """Return the minimal LaTeX header needed to render Unicode math.

    Scans ``preamble`` for ``\\usepackage{unicode-math}`` or any
    ``\\setmathfont{...}`` declaration (the latter is itself a
    ``unicode-math`` macro). When either is present, returns a
    self-contained snippet of the form::

        \\usepackage{unicode-math}
        \\setmathfont{...}

    suitable for Pandoc's ``-H header.tex`` flag — typically used by the
    slides renderer to pick up the same Unicode math coverage as the
    combined-PDF path without inheriting the manuscript's
    ``geometry``/``hyperref`` machinery (which would clash with Beamer's
    document class).

    The ``\\usepackage{unicode-math}`` line is always emitted, even when
    only an explicit ``\\setmathfont`` was found in the preamble. This
    ensures Beamer can resolve the macro independently of whatever
    side-effects loaded ``unicode-math`` in the combined-PDF path.

    Reuses :func:`ensure_setmathfont` so the auto-fallback to
    ``latinmodern-math.otf`` is byte-for-byte identical to the
    combined-PDF path: any future change to the default math font lands
    in slides automatically.

    Args:
        preamble: LaTeX preamble content as a string (usually the output
            of :func:`extract_preamble`).

    Returns:
        A snippet containing ``\\usepackage{unicode-math}`` and a
        ``\\setmathfont{...}`` line, or ``None`` when the preamble
        loads neither (slides keep Beamer's default fonts).
    """
    if not preamble:
        return None

    has_unicode_math_pkg = bool(_UNICODE_MATH_PATTERN.search(preamble))
    has_setmathfont = bool(_SETMATHFONT_DECLARATION.search(preamble))
    if not has_unicode_math_pkg and not has_setmathfont:
        return None

    augmented = ensure_setmathfont(preamble) if has_unicode_math_pkg else preamble

    font_match = _SETMATHFONT_DECLARATION.search(augmented)
    if font_match is None:
        # Only reachable if ``\usepackage{unicode-math}`` was present but
        # ensure_setmathfont declined to inject (e.g. empty preamble).
        return None
    setmathfont_line = font_match.group(0).strip()

    package_line = "\\usepackage{unicode-math}"

    snippet = (
        "% Auto-generated by infrastructure/rendering/_pdf_latex_helpers.py::"
        "extract_math_font_preamble.\n"
        "% Minimal header passed to Pandoc via -H so Beamer slides pick up "
        "the same math font\n"
        "% as the combined-PDF path. Adjust the manuscript's preamble.md to "
        "change the font globally.\n"
        f"{package_line}\n"
        f"{setmathfont_line}\n"
    )
    return snippet


def extract_preamble(preamble_file: Path) -> str:
    """Extract LaTeX preamble from markdown file.

    Looks for content between ```latex and ``` blocks.
    Handles various markdown code fence formats. When the extracted
    preamble loads ``unicode-math`` without a ``\\setmathfont``, a default
    ``\\setmathfont{latinmodern-math.otf}`` is appended via
    :func:`ensure_setmathfont` so prose math glyphs render cleanly.

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

    # Pattern handles different line endings and optional whitespace
    pattern = r"```\s*latex\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        preamble_lines = [match.strip() for match in matches]
        result = "\n".join(preamble_lines)
        result = ensure_setmathfont(result)
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

                # Add affiliation(s) if present — support both singular string and plural list
                affils: list[str] = []
                if "affiliations" in author:
                    raw = author["affiliations"]
                    affils = [raw] if isinstance(raw, str) else list(raw)
                elif "affiliation" in author:
                    affils = [author["affiliation"]]
                for affil in affils:
                    parts.append(f"\\\\\\footnotesize{{{affil}}}")

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


def parse_missing_latex_package_from_log(log_file: Path) -> str | None:
    """Parse LaTeX log for missing package errors.

    Args:
        log_file: Path to LaTeX .log file.

    Returns:
        Missing package name, or None if not found.
    """
    if not log_file.exists():
        return None

    try:
        log_content = log_file.read_text(encoding="utf-8", errors="ignore")

        match = re.search(r"File `([^']+\.sty)' not found", log_content)
        if match:
            sty_file = match.group(1)
            return sty_file.replace(".sty", "")

        match = re.search(r"! LaTeX Error: File `?([^'`\s]+\.sty)'? not found", log_content)
        if match:
            sty_file = match.group(1)
            return sty_file.replace(".sty", "")

    except OSError as e:
        logger.debug("Error parsing log file for package errors: %s", e)

    return None
