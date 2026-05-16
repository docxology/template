"""Private helper functions for PDF/LaTeX processing.

Extracted from pdf_renderer.py to reduce file size. These are module-level
functions that operate on data parameters rather than instance state.
"""

import re
from pathlib import Path
from typing import Any

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
_SETMATHFONT_DECLARATION = re.compile(r"^[^%\n]*\\setmathfont(?:\[[^\]]*\])?\{[^}]*\}[^\n]*", re.MULTILINE)
_LATEX_ESCAPE_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


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
            result["graphics_errors"].append("includegraphics command undefined - graphicx package may not be loaded")

        return result

    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"Error parsing LaTeX log: {e}")
        return result


def _resolve_config_yaml(manuscript_dir: Path) -> Path | None:
    """Locate ``config.yaml`` near a manuscript directory.

    Looks in ``manuscript_dir`` first; if missing, walks one level up to look
    for a sibling ``manuscript/config.yaml``. This handles the injected
    rendering layout (``project/output/manuscript``) where the original
    ``config.yaml`` lives at ``project/manuscript/config.yaml``.
    """
    primary = manuscript_dir / "config.yaml"
    if primary.is_file():
        return primary
    # Walk up looking for a sibling manuscript/ with config.yaml.
    for parent in (manuscript_dir.parent, manuscript_dir.parent.parent):
        try:
            candidate = parent / "manuscript" / "config.yaml"
        except (TypeError, ValueError):
            continue
        if candidate.is_file() and candidate != primary:
            return candidate
    return None


def _load_render_config(manuscript_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the nearest manuscript config file."""
    config_file = _resolve_config_yaml(manuscript_dir)
    if config_file is None:
        logger.debug(f"Config file not found near: {manuscript_dir}")
        return None, None
    try:
        with config_file.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return None, None
    if not isinstance(config, dict):
        return None, config_file
    return config, config_file


def _latex_text(value: object) -> str:
    """Escape a short text value for LaTeX text mode."""
    text = str(value)
    return "".join(_LATEX_ESCAPE_REPLACEMENTS.get(ch, ch) for ch in text)


def _metadata_from_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return book/paper metadata with book fields taking precedence."""
    book = config.get("book", {}) or {}
    paper = config.get("paper", {}) or {}
    if not isinstance(book, dict):
        book = {}
    if not isinstance(paper, dict):
        paper = {}
    title = book.get("title") or paper.get("title") or "Research Paper"
    subtitle = book.get("subtitle") or paper.get("subtitle") or ""
    year = book.get("year") or paper.get("year") or ""
    edition = book.get("edition") or ""
    date = paper.get("date") or (str(year) if year else "")
    return {
        "book": book,
        "paper": paper,
        "title": str(title),
        "subtitle": str(subtitle),
        "date": str(date),
        "year": str(year),
        "edition": str(edition),
        "license": str(book.get("license", "")),
        "code_license": str(book.get("code_license", "")),
    }


def _author_blocks(config: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize author metadata from config."""
    raw_authors = config.get("authors", [])
    authors: list[dict[str, str]] = []
    if isinstance(raw_authors, list):
        for author in raw_authors:
            if not isinstance(author, dict) or not author.get("name"):
                continue
            affil = author.get("affiliation", "")
            if not affil and isinstance(author.get("affiliations"), list):
                affil = ", ".join(str(item) for item in author["affiliations"])
            authors.append(
                {
                    "name": str(author.get("name", "")),
                    "affiliation": str(affil),
                    "email": str(author.get("email", "")),
                    "orcid": str(author.get("orcid", "")),
                }
            )
    if authors:
        return authors

    book = config.get("book", {}) or {}
    if isinstance(book, dict) and book.get("author"):
        authors.append(
            {
                "name": str(book.get("author", "")),
                "affiliation": "",
                "email": "",
                "orcid": str(book.get("orcid", "")),
            }
        )
    return authors


def _cover_image_path(config: dict[str, Any], config_file: Path) -> Path | None:
    """Resolve the configured cover image path, if any."""
    book = config.get("book", {}) or {}
    if not isinstance(book, dict):
        return None
    cover = book.get("cover", {}) or {}
    if not isinstance(cover, dict):
        return None
    raw_image = cover.get("image")
    if not raw_image:
        return None
    image_path = Path(str(raw_image))
    if image_path.is_absolute():
        return image_path
    candidates = [config_file.parent / image_path]
    for parent in config_file.parents:
        candidates.append(parent / "manuscript" / image_path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _book_cover_body(config: dict[str, Any], config_file: Path) -> str:
    """Generate a book-style cover, publishing page, and contents page."""
    metadata = _metadata_from_config(config)
    authors = _author_blocks(config)
    publication = config.get("publication", {}) or {}
    if not isinstance(publication, dict):
        publication = {}
    doi = str(publication.get("doi", ""))
    cover_image = _cover_image_path(config, config_file)

    title = _latex_text(metadata["title"])
    subtitle = _latex_text(metadata["subtitle"])
    edition = _latex_text(metadata["edition"])
    year = _latex_text(metadata["year"])
    license_name = _latex_text(metadata["license"])
    code_license = _latex_text(metadata["code_license"])

    author_lines: list[str] = []
    for author in authors:
        author_lines.append(r"{\Large\bfseries " + _latex_text(author["name"]) + r"}\\[0.35em]")
        if author["affiliation"]:
            author_lines.append(r"{\normalsize " + _latex_text(author["affiliation"]) + r"}\\[0.25em]")
        if author["email"]:
            email = _latex_text(author["email"])
            author_lines.append(r"{\normalsize\texttt{" + email + r"}}\\[0.25em]")
        if author["orcid"]:
            orcid = _latex_text(author["orcid"])
            author_lines.append(
                r"{\normalsize\href{https://orcid.org/"
                + _latex_text(author["orcid"])
                + r"}{ORCID: "
                + orcid
                + r"}}\\[0.5em]"
            )
    if not author_lines:
        author_lines.append(r"{\Large\bfseries Project Author}\\[0.5em]")

    image_block = ""
    if cover_image is not None and cover_image.is_file():
        image_block = (
            r"\includegraphics[width=0.98\textwidth,height=0.62\textheight,keepaspectratio]{"
            + r"\detokenize{"
            + cover_image.as_posix()
            + r"}}"
        )
    elif cover_image is not None:
        logger.warning("Configured cover image does not exist: %s", cover_image)

    edition_line = ""
    if edition or year:
        edition_line = r"{\small Edition " + (edition or "1.0") + (" -- " + year if year else "") + r"}"

    publishing_lines = [
        r"\clearpage",
        r"\thispagestyle{empty}",
        r"\section*{Publishing Information}",
        "",
        r"\noindent{\Large\bfseries " + title + r"}\\",
    ]
    if subtitle:
        publishing_lines.append(r"{\large " + subtitle + r"}\\[1.2em]")
    publishing_lines.extend(author_lines)
    publishing_lines.extend(
        [
            r"\vspace{1.0em}",
            r"\noindent Edition " + (edition or "1.0") + (" -- " + year if year else "") + r"\\",
            r"\noindent Text license: " + (license_name or "CC BY 4.0") + r"\\",
            r"\noindent Source-code license: " + (code_license or "Apache-2.0") + r"\\",
        ]
    )
    if doi:
        escaped_doi = _latex_text(doi)
        publishing_lines.append(r"\noindent DOI: \href{https://doi.org/" + escaped_doi + r"}{" + escaped_doi + r"}\\")
    publishing_lines.extend(
        [
            r"\vspace{1.0em}",
            r"\noindent Suggested citation: Friedman, D. A. ("
            + (year or r"\the\year")
            + r"). \textit{"
            + title
            + (": " + subtitle if subtitle else "")
            + r"} (Edition "
            + (edition or "1.0")
            + r"). Active Inference Institute.",
            "",
            r"\vspace{1.0em}",
            r"\noindent This open textbook is generated from version-controlled Markdown, tested Python modules, "
            r"programmatic figures, and rendered Mermaid diagrams. Corrections and improvements may be submitted "
            r"through the project repository.",
            "",
            r"\vfill",
            r"\noindent Accessibility note: the compact PDF is optimized for dense print. Reader-profile builds, "
            r"HTML output, and source Markdown can be generated from the same manuscript materials.",
            r"\clearpage",
            r"\tableofcontents",
            r"\clearpage",
        ]
    )

    return "\n".join(
        [
            r"\begin{titlepage}",
            r"\thispagestyle{empty}",
            r"\setcounter{page}{1}",
            r"\centering",
            r"\vspace*{0.6cm}",
            r"{\Huge\sffamily\bfseries " + title + r"\par}",
            r"\vspace{0.35cm}",
            r"{\Large\sffamily " + subtitle + r"\par}" if subtitle else "",
            r"\vspace{0.8cm}",
            *author_lines,
            r"\vfill",
            image_block,
            r"\vfill",
            edition_line,
            r"\end{titlepage}",
            *publishing_lines,
        ]
    )


def generate_title_page_preamble(manuscript_dir: Path) -> str:
    """Generate LaTeX title page preamble commands from config.yaml metadata.

    These commands (\\title, \\author, \\date) must be in the preamble
    (before \\begin{document}).

    Args:
        manuscript_dir: Directory containing manuscript files and config.yaml

    Returns:
        LaTeX preamble commands for title page, or empty string if config not found
    """
    config, _config_file = _load_render_config(manuscript_dir)
    if not config:
        return ""

    try:
        metadata = _metadata_from_config(config)
        authors = config.get("authors", [])

        title = _latex_text(metadata["title"])
        subtitle = _latex_text(metadata["subtitle"])
        date = metadata["date"]
        publication = config.get("publication", {}) or {}
        doi = publication.get("doi", "") if isinstance(publication, dict) else ""

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
                    author_str += " \\\\ " + " \\\\ ".join([f"\\footnotesize{{{e}}}" for e in extras])

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
    config, config_file = _load_render_config(manuscript_dir)
    if not config or config_file is None:
        return ""

    try:
        if isinstance(config.get("book"), dict) and config["book"].get("title"):
            body = _book_cover_body(config, config_file)
            logger.debug("Generated book-style title, publishing, and contents opening")
            return body

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
