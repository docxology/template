"""Beamer math/citation preamble header generation for slide decks."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    extract_command_fallbacks,
    extract_math_font_preamble,
    extract_preamble,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy


def _latex_href(value: str) -> str:
    r"""Escape a validated reader href for one Beamer ``\href`` argument."""

    escaped = value
    for source, target in (
        ("%", r"\%"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("&", r"\&"),
        ("{", r"\{"),
        ("}", r"\}"),
    ):
        escaped = escaped.replace(source, target)
    return escaped


def write_slides_math_header(
    manuscript_dir: Path | None,
    output_dir: Path,
    *,
    accessible_policy: AccessibleSlidePolicy | None = None,
) -> Path | None:
    """Write a Pandoc ``-H`` header file for Unicode math + citation
    fallbacks, if needed.

    Looks up ``preamble.md`` next to the manuscript, extracts any
    ``\\usepackage{unicode-math}`` block, and writes a minimal
    ``_slides_math_header.tex`` next to the slide output. The file is
    rewritten on every render so it always reflects the current
    ``preamble.md``; consumers should treat it as a build artefact.

    The header also defines ``\\providecommand`` fallbacks for natbib
    commands (``\\citep``, ``\\citet``, ``\\citealp``) and manuscript
    cross-reference commands (``\\cref``, ``\\Cref``) so that
    manuscript prose already normalized for the combined PDF still
    typesets cleanly in slides. The fallback renders citations as
    ``[key]`` and unresolved cross-references as detokenized label
    strings — readable, distinct, and safe from undefined-control-
    sequence and raw-underscore errors. It also unconditionally
    declares the two auto-numbered formalism environments beamer does
    not ship natively (``proposition``, ``hypothesis`` — see below).

    Returns ``None`` only when ``manuscript_dir`` itself is ``None``;
    otherwise a header path is always returned, since the natbib/cref
    fallback and formalism-environment declarations are unconditional.
    """
    if manuscript_dir is None:
        return None
    preamble_file = manuscript_dir / "preamble.md"

    snippet_parts: list[str] = []
    if preamble_file.exists():
        preamble = extract_preamble(preamble_file)
        math_snippet = extract_math_font_preamble(preamble)
        if math_snippet is not None:
            snippet_parts.append(math_snippet)
        # Manuscript-declared macros (\calD, \cogstate, ...) must resolve
        # in slides too; rewrite newcommand -> providecommand so a clash
        # with a Beamer built-in degrades to a no-op rather than an error.
        macro_fallbacks = extract_command_fallbacks(preamble)
        # Keep only packages that are safe inside Beamer; layout/graphics
        # machinery (geometry, hyperref, ...) clashes with the class.
        _SLIDE_SAFE_PACKAGES = {
            "listings",
            "fancyvrb",
            "amsmath",
            "amssymb",
            "bm",
            "mathtools",
            "booktabs",
            "multirow",
            # "algorithm" is deliberately absent: it is safe to PARSE but not
            # to load, because its float machinery has no beamer
            # implementation. The non-floating stand-in below replaces it.
            "algpseudocode",
            "algorithmicx",
            "stmaryrd",
            "mathrsfs",
        }
        safe_lines = [
            ln
            for ln in macro_fallbacks.splitlines()
            if not ln.strip().startswith("\\usepackage") or any(pkg in ln for pkg in _SLIDE_SAFE_PACKAGES)
        ]
        macro_fallbacks = "\n".join(safe_lines)
        if macro_fallbacks:
            snippet_parts.append(
                "% Manuscript macro/package fallbacks (newcommand -> providecommand).\n" + macro_fallbacks + "\n"
            )

    # Natbib fallback definitions for slide rendering. \providecommand
    # is a no-op when natbib is loaded (real definition wins). The layout
    # defaults keep dense scientific prose and longtable-heavy sections
    # within Beamer's narrower text block.
    snippet_parts.append(
        "% Slide layout defaults for warning-clean scientific decks.\n"
        "\\usepackage{etoolbox}\n"
        "\\IfFileExists{xurl.sty}{\\usepackage{xurl}}{}\n"
        "\\IfFileExists{seqsplit.sty}{\\usepackage{seqsplit}}{\\newcommand{\\seqsplit}[1]{#1}}\n"
        "\\protected\\def\\breakseq#1{\\seqsplit{#1}}\n"
        "\\protected\\def\\breaktt#1{\\begingroup\\ttfamily\\seqsplit{#1}\\endgroup}\n"
        "\\setlength{\\emergencystretch}{6em}\n"
        "\\tolerance=5000\n"
        "\\hbadness=10000\n"
        "\\hfuzz=1pt\n"
        "\\setlength{\\tabcolsep}{2pt}\n"
        "\\AtBeginEnvironment{longtable}{\\tiny\\renewcommand{\\arraystretch}{0.86}\\setlength{\\tabcolsep}{1pt}}\n"
        "\\AtBeginEnvironment{tabular}{\\tiny\\renewcommand{\\arraystretch}{0.86}\\setlength{\\tabcolsep}{1pt}}\n"
        "\\AtBeginEnvironment{equation}{\\tiny}\n"
        "\\AtBeginEnvironment{equation*}{\\tiny}\n"
        "\\AtBeginEnvironment{align}{\\tiny}\n"
        "\\AtBeginEnvironment{align*}{\\tiny}\n"
        "\\AtBeginEnvironment{itemize}{\\footnotesize}\n"
        "\\AtBeginEnvironment{enumerate}{\\footnotesize}\n"
        "\\AtBeginEnvironment{description}{\\footnotesize}\n"
        "\\setbeamerfont{caption}{size=\\tiny}\n"
        "\\setbeamerfont{caption name}{size=\\tiny}\n"
        "\\setbeamerfont{normal text}{size=\\small}\n"
        "\\setbeamerfont{frametitle}{size=\\small}\n"
        "\\setbeamerfont{section title}{size=\\footnotesize}\n"
        "\\setbeamerfont{subsection title}{size=\\footnotesize}\n"
        "\\setbeamertemplate{section page}{%\n"
        "  \\centering\n"
        "  \\begin{beamercolorbox}[sep=12pt,center,wd=\\paperwidth]{section title}\n"
        "    \\parbox{0.86\\paperwidth}{\\centering\\usebeamerfont{section title}\\insertsection\\par}\n"
        "  \\end{beamercolorbox}\n"
        "}\n"
        "\\setbeamertemplate{subsection page}{%\n"
        "  \\centering\n"
        "  \\begin{beamercolorbox}[sep=8pt,center,wd=\\paperwidth]{subsection title}\n"
        "    \\parbox{0.86\\paperwidth}{\\centering\\usebeamerfont{subsection title}\\insertsubsection\\par}\n"
        "  \\end{beamercolorbox}\n"
        "}\n"
        "\\setlength{\\abovecaptionskip}{2pt}\n"
        "\\setlength{\\belowcaptionskip}{0pt}\n\n"
        "% Natbib and cross-reference fallbacks — slides don't load natbib\n"
        "% or cleveref, but combined-PDF manuscript prose may emit these\n"
        "% commands. The fallback renders citations as a bracketed key list\n"
        "% and cross-references as detokenized labels so slides don't fail on\n"
        "% undefined control sequences or raw underscores. \\providecommand is\n"
        "% a no-op if packages load later.\n"
        "\\providecommand{\\citep}[1]{[#1]}\n"
        "\\providecommand{\\citet}[1]{#1}\n"
        "\\providecommand{\\citealp}[1]{#1}\n"
        "\\providecommand{\\citeauthor}[1]{#1}\n"
        "\\providecommand{\\citeyear}[1]{#1}\n"
        "\\providecommand{\\cref}[1]{\\texttt{\\detokenize{#1}}}\n"
        "\\providecommand{\\Cref}[1]{\\texttt{\\detokenize{#1}}}\n"
        # cleveref's range forms take two arguments; without their own
        # fallbacks the single-argument \\cref above does not cover them
        # and beamer stops at "Undefined control sequence".
        "\\providecommand{\\crefrange}[2]{\\texttt{\\detokenize{#1}}--\\texttt{\\detokenize{#2}}}\n"
        "\\providecommand{\\Crefrange}[2]{\\texttt{\\detokenize{#1}}--\\texttt{\\detokenize{#2}}}\n"
        # Beamer lacks \paragraph (standard LaTeX sectioning); render it
        # as a bold run-in heading so dense prose sections don't fail.
        "\\providecommand{\\paragraph}[1]{\\textbf{#1}\\ }\n"
    )

    if accessible_policy is not None:
        # These declarations intentionally follow the archive defaults above:
        # Beamer applies the later font selection, so the accessible profile
        # cannot silently inherit the tiny table/equation/caption fallbacks
        # used by dense archival derivatives.
        accessible_title_pt = accessible_policy.title_font_pt
        body = accessible_policy.body_font_pt
        label = accessible_policy.figure_label_font_pt
        title_leading = accessible_title_pt + 4
        body_leading = body + 4
        label_leading = label + 3
        reader_href = _latex_href(accessible_policy.reader_href)
        snippet_parts.append(
            "% Opt-in accessible presentation profile.\n"
            f"\\setbeamerfont{{normal text}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{frametitle}}{{size*={{{accessible_title_pt}pt}}{{{title_leading}pt}}}}\n"
            f"\\setbeamerfont{{section title}}{{size*={{{accessible_title_pt}pt}}{{{title_leading}pt}}}}\n"
            f"\\setbeamerfont{{subsection title}}{{size*={{{accessible_title_pt}pt}}{{{title_leading}pt}}}}\n"
            f"\\setbeamerfont{{caption}}{{size*={{{label}pt}}{{{label_leading}pt}}}}\n"
            f"\\setbeamerfont{{caption name}}{{size*={{{label}pt}}{{{label_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize/enumerate body}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize/enumerate subbody}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize/enumerate subsubbody}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize item}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize subitem}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{itemize subsubitem}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{description body}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{description item}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{quote}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\setbeamerfont{{quotation}}{{size*={{{body}pt}}{{{body_leading}pt}}}}\n"
            f"\\AtBeginEnvironment{{longtable}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{tabular}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{equation}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{equation*}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{align}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{align*}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{itemize}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{enumerate}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            f"\\AtBeginEnvironment{{description}}{{\\fontsize{{{body}pt}}{{{body_leading}pt}}\\selectfont}}\n"
            "\\AtBeginDocument{\\usebeamerfont{normal text}}\n"
            "\\setbeamertemplate{footline}{%\n"
            "  \\leavevmode\\hbox{%\n"
            "    \\begin{beamercolorbox}[wd=\\paperwidth,ht=2.6ex,dp=1.1ex,center]{author in head/foot}%\n"
            f"      \\fontsize{{{label}pt}}{{{label_leading}pt}}\\selectfont "
            f"Untagged PDF derivative \\textbar\\ "
            f"\\href{{{reader_href}}}{{HTML reader}}%\n"
            "    \\end{beamercolorbox}%\n"
            "  }%\n"
            "}\n"
        )

    # Manuscript preambles may declare additional theorem-like environments
    # (warning, note, ...) chained onto theorem. Recover any
    # \newtheorem declaration whose environment beamer does not already
    # define; redeclare via \newtheorem is an error for built-ins, so
    # guard each with \lv@ifundefinedstyle-style check via \@ifundefined
    # on the environment's begin macro.
    preamble_theorems = ""
    if preamble_file.exists():
        import re as _re

        known = {"theorem", "lemma", "corollary", "definition", "example", "fact"}
        for _m in _re.finditer(
            r"\\newtheorem\{(\w+)\}(?:\[(\\w+)\])?(?:\[[^\]]+\])?\{([^}]+)\}",
            extract_preamble(preamble_file),
        ):
            env, chained, title = _m.group(1), _m.group(2), _m.group(3)
            if env in known | {"proposition", "hypothesis", "remark", "axiom", "property"}:
                continue  # already declared or declared below/above
            counter = f"[{chained}]" if chained else ""
            preamble_theorems += f"\\newtheorem{{{env}}}{counter}{{{title}}}\n"
    if preamble_theorems:
        snippet_parts.append("% Additional theorem-like environments from manuscript preamble.\n" + preamble_theorems)

    # Content-providing packages the manuscript preamble loads. The header
    # deliberately drops layout machinery (geometry, hyperref, titlepage)
    # because beamer ships its own, but a package that DEFINES environments
    # the body uses is a different case: without it beamer stops at
    # "Environment algorithm undefined" and the stage discards the deck.
    # Part 2 of the cognitive_integrity series found this with 14
    # \begin{algorithm} blocks. Kept to an allowlist rather than passing
    # everything through, since that is what the drop exists to prevent.
    # `algorithm` itself is NOT safe: it defines the environment but its
    # float machinery (\\@float@Hx, \\float@makebox) has no beamer
    # implementation, so the deck dies on "Undefined control sequence"
    # instead of "Environment undefined" -- one step further, still dead.
    # algpseudocode brings the algorithmic body, and a non-floating
    # `algorithm` wrapper is supplied below in its place.
    _ENV_PACKAGES = ("algpseudocode", "algorithmicx")
    if preamble_file.exists():
        loaded = extract_preamble(preamble_file)
        wanted = [name for name in _ENV_PACKAGES if f"\\usepackage{{{name}}}" in loaded]
        if wanted:
            snippet_parts.append(
                "% Environment-providing packages carried over from the manuscript.\n"
                + "".join(f"\\usepackage{{{name}}}\n" for name in wanted)
            )
        if "\\usepackage{algorithm}" in loaded:
            # A plain rule-delimited block: same visual role on a slide,
            # none of the float machinery beamer cannot run.
            accessible_algorithm_font = (
                rf"\fontsize{{{accessible_policy.body_font_pt}pt}}"
                rf"{{{accessible_policy.body_font_pt + 4}pt}}\selectfont"
                if accessible_policy is not None
                else ""
            )
            algorithm_font = r"\small" if accessible_policy is None else accessible_algorithm_font
            snippet_parts.append(
                "% Non-floating stand-in for the `algorithm` float.\n"
                "\\newenvironment{algorithm}[1][]{%\n"
                f"  \\par\\medskip\\noindent\\rule{{\\linewidth}}{{0.4pt}}\\par\\nobreak{algorithm_font}\n"
                "  \\renewcommand{\\caption}[1]{\\par\\noindent\\textbf{##1}\\par}}{%\n"
                "  \\par\\nobreak\\noindent\\rule{\\linewidth}{0.4pt}\\par\\medskip}\n"
            )

    # Auto-numbered formalism environments the manuscript body may use
    # (mirrors the \newtheorem declarations `preamble.md` defines for the
    # combined PDF, per @sec:type-architecture-style raw-LaTeX blocks).
    # Beamer's own document class already provides \theorem, \lemma,
    # \corollary, and \definition as built-in styled blocks (redeclaring
    # them via \newtheorem fails with "Command ... already defined"), so
    # only the two environments beamer does *not* ship — proposition and
    # hypothesis — need a declaration here. Each gets its own independent
    # counter rather than chaining onto beamer's internal theorem counter
    # (whose name is not a public API): slides already render several
    # PDF-only features in simplified form (see the natbib/cref
    # fallbacks above), so a proposition/hypothesis number that doesn't
    # exactly match the PDF's shared sequence is consistent with that
    # existing degraded-but-non-fatal slides behavior, not a regression.
    snippet_parts.append(
        "\\newtheorem{proposition}{Proposition}\n"
        "\\newtheorem{hypothesis}{Hypothesis}\n"
        # Beamer provides theorem/lemma/corollary/definition but NOT
        # remark; combined-PDF preambles chain remark onto theorem.
        "\\newtheorem{remark}[theorem]{Remark}\n"
        # axiom and property sit in the skip-set above, whose comment says
        # "declared below/above" -- but they were declared in neither, so a
        # manuscript using \\begin{property} or \\begin{axiom} had them
        # dropped by the extractor and never redeclared here. Beamer then
        # failed with "Environment property undefined" and the stage
        # discarded the slide deck it had just written.
        "\\newtheorem{axiom}{Axiom}\n"
        "\\newtheorem{property}{Property}\n"
    )

    # snippet_parts is never empty past this point (the natbib/cref
    # fallback and the formalism-environment declarations above are both
    # unconditional appends) -- a header is always written here.
    output_dir.mkdir(parents=True, exist_ok=True)
    header_path = output_dir / "_slides_math_header.tex"
    header_path.write_text("\n".join(snippet_parts), encoding="utf-8")
    logger.debug(f"Wrote slides math header: {header_path}")
    return header_path
