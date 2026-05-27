"""LaTeX postprocessing for combined PDF rendering."""

from __future__ import annotations

import re

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_math_delimiters import fix_math_delimiters
from infrastructure.rendering._pdf_section_titles import sanitize_texorpdfstring
from infrastructure.rendering._pdf_unicode_remap import remap_prose_unicode
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
)

logger = get_logger(__name__)


def _escape_latex_def_value(value: str) -> str:
    """Escape a section title for use inside ``\\def\\@currentlabelname{...}``."""
    escaped = value.replace("\\", "\\textbackslash{}")
    return escaped.replace("{", "\\{").replace("}", "\\}")


_STARRED_HEADING_MARKERS: tuple[str, ...] = (
    "\\section*{",
    "\\subsection*{",
    "\\subsubsection*{",
)


def _next_starred_heading(tex_content: str, start: int) -> tuple[int, str] | None:
    """Return the earliest starred heading marker at or after ``start``."""
    best_at = -1
    best_marker = ""
    for marker in _STARRED_HEADING_MARKERS:
        at = tex_content.find(marker, start)
        if at >= 0 and (best_at < 0 or at < best_at):
            best_at = at
            best_marker = marker
    if best_at < 0:
        return None
    return best_at, best_marker


def fix_starred_section_nameref_labels(tex_content: str) -> tuple[str, int]:
    """Repair hyperref anchors and ``\\nameref`` titles for starred headings.

    Pandoc emits ``\\section*{Title}\\label{...}\\addcontentsline{...}`` without
    ``\\phantomsection``, so TOC links resolve to ``Doc-Start`` while page numbers
    stay correct. titlesec additionally prevents hyperref from storing section titles,
    which leaves ``\\nameref{sec:...}`` empty unless ``\\@currentlabelname`` is set.
    """
    has_titlesec = bool(re.search(r"\\usepackage(?:\[[^\]]*\])?\{titlesec\}", tex_content))
    has_hyperref = bool(re.search(r"\\usepackage(?:\[[^\]]*\])?\{hyperref\}", tex_content))
    if not has_titlesec and not has_hyperref:
        return tex_content, 0

    out: list[str] = []
    i = 0
    fixes = 0

    while True:
        found = _next_starred_heading(tex_content, i)
        if found is None:
            out.append(tex_content[i:])
            break

        start, marker = found
        out.append(tex_content[i:start])
        j = start + len(marker)
        depth = 1
        title_start = j
        while j < len(tex_content) and depth > 0:
            ch = tex_content[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1

        if depth != 0:
            out.append(tex_content[start:])
            break

        title_raw = tex_content[title_start : j - 1]
        rest = tex_content[j:]
        rest_lstrip = rest.lstrip()
        if rest_lstrip.startswith("\\phantomsection"):
            out.append(tex_content[start:j])
            i = j
            continue

        label_match = re.match(r"\\label\{([^}]+)\}", rest_lstrip)
        if label_match is None:
            out.append(tex_content[start:j])
            i = j
            continue

        label = label_match.group(1)
        consumed = len(rest) - len(rest_lstrip) + label_match.end()
        heading_open = marker
        repaired = f"{heading_open}{title_raw}}}\n"
        if has_titlesec:
            title_plain = re.sub(r"\s+", " ", title_raw).strip()
            title_escaped = _escape_latex_def_value(title_plain)
            repaired += f"\\makeatletter\n\\def\\@currentlabelname{{{title_escaped}}}\n\\makeatother\n"
        repaired += f"\\phantomsection\\label{{{label}}}"
        out.append(repaired)
        fixes += 1
        i = j + consumed

    if fixes:
        logger.info(
            "✓ Repaired %d starred heading label(s) for hyperref TOC anchors and \\nameref",
            fixes,
        )
    return "".join(out), fixes


def postprocess_latex(tex_content: str) -> str:
    """Apply lmodern disabling, hidelinks patching, and math delimiter fixes."""
    # Fix lmodern conflict with xelatex
    if "\\usepackage{lmodern}" in tex_content:
        tex_content = tex_content.replace("\\usepackage{lmodern}", "% \\usepackage{lmodern}")
        logger.info("✓ Disabled lmodern package to prevent XeLaTeX font conflicts")

    # Defensive rewrite: a user preamble that re-loads hyperref with options
    # collides with Pandoc's template (which already loads hyperref via the
    # bookmark package). Convert ``\usepackage[opts]{hyperref}`` into
    # ``\PassOptionsToPackage{opts}{hyperref}`` + ``\hypersetup{opts}`` so the
    # options are honoured without triggering ``Option clash for package
    # hyperref``. Only rewrites the option-bearing form; ``\usepackage{hyperref}``
    # without options is left alone (no clash).
    hyperref_pattern = re.compile(r"\\usepackage\[(?P<opts>[^\]]*)\]\{hyperref\}")
    rewritten_count = 0

    def _rewrite_hyperref(match: "re.Match[str]") -> str:
        nonlocal rewritten_count
        rewritten_count += 1
        opts = match.group("opts").strip()
        return f"\\PassOptionsToPackage{{{opts}}}{{hyperref}}\n\\AtBeginDocument{{\\hypersetup{{{opts}}}}}"

    tex_content, _subs = hyperref_pattern.subn(_rewrite_hyperref, tex_content)
    if rewritten_count:
        logger.info(
            "✓ Rewrote %d duplicate \\usepackage[...]{hyperref} into "
            "\\PassOptionsToPackage + \\hypersetup (avoids hyperref option clash)",
            rewritten_count,
        )

    # Fix hidelinks → colorlinks=true with uniform red hyperlinks.
    if "hidelinks" in tex_content:
        tex_content = tex_content.replace(
            "hidelinks,",
            "colorlinks=true,linkcolor=red,urlcolor=red,citecolor=red,anchorcolor=red,filecolor=red,",
        )
        tex_content = tex_content.replace(
            "  hidelinks,\n",
            "  colorlinks=true,\n  linkcolor=red,\n  urlcolor=red,\n  citecolor=red,\n",
        )
        logger.info("✓ Patched hidelinks → colorlinks=true (uniform red hyperlinks)")

    # Normalise pandoc's default hypersetup colours to uniform red. Pandoc
    # emits something like:
    #   \hypersetup{
    #     colorlinks=true,linkcolor=red,urlcolor=blue,citecolor=red,anchorcolor=red,
    #     pdfcreator={LaTeX via pandoc}}
    # Force every link colour to red so cross-refs, citations, and URLs
    # share one visual treatment. Only rewrites blocks that already declare
    # at least one link-colour key so we don't perturb unrelated metadata-
    # only hypersetup blocks (e.g. ``\hypersetup{pdftitle={...}}``).
    def _find_hypersetup_blocks(s: str) -> list[tuple[int, int, str]]:
        """Return (start, end, body) for each balanced \\hypersetup{...}."""
        out: list[tuple[int, int, str]] = []
        marker = "\\hypersetup{"
        i = 0
        while True:
            idx = s.find(marker, i)
            if idx < 0:
                return out
            body_start = idx + len(marker)
            depth = 1
            j = body_start
            while j < len(s) and depth > 0:
                ch = s[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                out.append((idx, j, s[body_start : j - 1]))
                i = j
            else:
                return out

    blocks = _find_hypersetup_blocks(tex_content)
    color_keys = ("linkcolor", "urlcolor", "citecolor", "anchorcolor", "filecolor")
    hs_count = 0
    for start, end, body in reversed(blocks):
        if not any(re.search(rf"\b{k}\s*=", body) for k in color_keys):
            continue  # metadata-only hypersetup, skip
        new_body = body
        for key in color_keys:
            new_body = re.sub(rf"\b{key}\s*=\s*[A-Za-z][A-Za-z0-9]*", f"{key}=red", new_body)
        tex_content = tex_content[:start] + "\\hypersetup{" + new_body + "}" + tex_content[end:]
        hs_count += 1
    if hs_count:
        logger.info("✓ Normalised %d \\hypersetup block(s) to uniform red link colours", hs_count)

    # Fix broken math delimiters
    try:
        tex_content = fix_math_delimiters(tex_content)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Math delimiter fixing failed: {e}. Continuing with original LaTeX content.")
        logger.debug(f"Math delimiter fixing error details: {type(e).__name__}: {e}")

    # Sanitize Pandoc's auto-emitted \texorpdfstring bookmark arguments.
    # When section titles contain math, Pandoc fills the bookmark arg with
    # \textbackslash / \_ / {[} etc. that hyperref then tries to expand
    # during the pdfstring serialize, which can blow the input stack
    # ("TeX capacity exceeded, sorry [input stack size=10000]") on heavy
    # math-laden headings and abort the build mid-section.
    try:
        tex_content, _ = sanitize_texorpdfstring(tex_content)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"texorpdfstring sanitization failed: {e}. Continuing with original LaTeX content.")

    # Remap unicode glyphs (✓, ≈, α, σ, ≪, …) that the active body/code
    # fonts cannot render. Literal verbatim blocks are preserved; Pandoc
    # Highlighting blocks receive an ASCII-safe code rewrite because their
    # macro arguments are typeset through normal text fonts.
    try:
        tex_content = remap_prose_unicode(tex_content).content
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Prose unicode remap failed: {e}. Continuing with original LaTeX content.")

    try:
        tex_content, texttt_replacements = make_long_texttt_breakable(tex_content)
        if texttt_replacements:
            logger.info("✓ Made %d long monospace path span(s) breakable", texttt_replacements)
        tex_content, literal_replacements = make_known_literals_breakable(tex_content)
        if literal_replacements:
            logger.info("✓ Made %d recurring long label(s) breakable", literal_replacements)
    except (re.error, TypeError, ValueError) as e:
        logger.warning(f"Breakable texttt postprocessing failed: {e}. Continuing with original LaTeX content.")

    tex_content, graphics_replacements = constrain_includegraphics_textheight(tex_content, "0.50")
    if graphics_replacements:
        logger.info("✓ Constrained %d Pandoc figure height bound(s)", graphics_replacements)

    return tex_content
