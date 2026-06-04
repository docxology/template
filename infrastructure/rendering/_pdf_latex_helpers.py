"""Private helper functions for PDF/LaTeX processing.

Extracted from pdf_renderer.py to reduce file size. These are module-level
functions that operate on data parameters rather than instance state.
"""

import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_title_page import (
    generate_title_page_body,
    generate_title_page_preamble,
)

logger = get_logger(__name__)

__all__ = [
    "check_latex_log_for_graphics_errors",
    "ensure_setmathfont",
    "extract_math_font_preamble",
    "extract_preamble",
    "generate_title_page_body",
    "generate_title_page_preamble",
    "parse_missing_latex_package_from_log",
]

_DEFAULT_MATH_FONT = "latinmodern-math.otf"
_UNICODE_MATH_PATTERN = re.compile(
    r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{[^}]*\bunicode-math\b[^}]*\}"
)
_SETMATHFONT_PATTERN = re.compile(r"\\setmathfont\b")
# Match a real ``\setmathfont{...}`` declaration (not a comment that
# merely mentions the macro). Skips lines starting with ``%``.
_SETMATHFONT_DECLARATION = re.compile(r"^[^%\n]*\\setmathfont(?:\[[^\]]*\])?\{[^}]*\}[^\n]*", re.MULTILINE)


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
        "% U+226A / U+226B) and emit Missing-character warnings. " + math_font + " ships\n"
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

    # Fallback: a preamble.md authored as RAW LaTeX (no ```latex fence) used to be
    # dropped silently here, so manuscript-declared margins/fonts never reached the
    # PDF. Recover only SELF-CONTAINED, single-line, brace/bracket-balanced directives
    # from a curated whitelist and emit a warning so the failure is observable.
    # Deliberately conservative (a fence is the supported contract): prose, ``\input``
    # (arbitrary-file scope expansion), and any multi-line construct are dropped rather
    # than recovered — recovering a multi-line command line-by-line would truncate it
    # into malformed LaTeX, which is worse than dropping it.
    raw_latex_cmd_re = re.compile(
        r"^\s*(?:%|\\(?:usepackage|RequirePackage|geometry|newcommand|renewcommand"
        r"|providecommand|DeclareMathOperator|DeclareUnicodeCharacter|setlength"
        r"|definecolor|changefontsize|hypersetup|PassOptionsToPackage"
        r"|newenvironment|setmainfont|setmonofont|setsansfont|usetikzlibrary)\b)"
    )

    def _self_contained(line: str) -> bool:
        """True if the line is safe to recover standalone.

        A comment line is inert. A command line is recovered only when its braces and
        brackets balance on the line itself, so a multi-line construct (whose body
        lives on continuation lines this line-oriented filter would drop) is never
        emitted as a truncated, unbalanced fragment.
        """
        if line.lstrip().startswith("%"):
            return True
        return line.count("{") == line.count("}") and line.count("[") == line.count("]")

    raw_lines = [
        ln.rstrip() for ln in content.splitlines() if raw_latex_cmd_re.match(ln) and _self_contained(ln.rstrip())
    ]
    if raw_lines:
        result = ensure_setmathfont("\n".join(raw_lines))
        logger.warning(
            "%s contains raw LaTeX with no ```latex fence; recovered %d self-contained "
            "preamble line(s) by whitelist (multi-line constructs and \\input are "
            "dropped). Wrap the preamble in a ```latex ... ``` fence to silence this "
            "warning and capture every directive.",
            preamble_file.name,
            len(raw_lines),
        )
        return result

    logger.debug(f"No LaTeX code blocks found in {preamble_file.name}")
    return ""


def check_latex_log_for_graphics_errors(log_file: Path) -> dict[str, list[str]]:
    """Parse LaTeX log file for graphics-related errors and warnings."""
    from infrastructure.rendering._latex_log_parse import check_latex_log_for_graphics_errors as _check

    return _check(log_file)


def parse_missing_latex_package_from_log(log_file: Path) -> str | None:
    """Parse LaTeX log for missing package errors."""
    from infrastructure.rendering._latex_log_parse import parse_missing_latex_package_from_log as _parse

    return _parse(log_file)
