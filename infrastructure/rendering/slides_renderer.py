"""Slides rendering module.

Per-format preamble coverage
----------------------------
This renderer drives Pandoc directly with ``-t beamer`` (or ``revealjs``)
and intentionally **does not** route through
:func:`infrastructure.rendering._pdf_combined_renderer.inject_latex_preamble`
— Beamer ships its own document class, so the manuscript's
``geometry`` / ``hyperref`` / ``titlepage`` machinery would clash.

The math-font subset *is* propagated. Whenever ``preamble.md`` loads
``unicode-math``, :func:`_maybe_write_math_header` calls
:func:`infrastructure.rendering._pdf_latex_helpers.extract_math_font_preamble`
to write a minimal ``_slides_math_header.tex`` containing only
``\\usepackage{unicode-math}`` plus the active ``\\setmathfont`` (with
the same ``latinmodern-math.otf`` auto-fallback as the combined-PDF
path), and passes it to Pandoc via ``-H header.tex``. This gives Beamer
slides clean rendering of ``\\mid``, ``\\ll``, ``\\gg``, etc. without
inheriting the rest of the combined-PDF preamble.

The combined-PDF gate
(:func:`infrastructure.rendering._pdf_combined_renderer.prevalidate_for_render`)
is intentionally *not* invoked here because slides typically render a
single section in isolation and have a different acceptable-citation
set than the full manuscript.
"""

import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._bibliography import pandoc_bibliography_args, resolve_bibliography
from infrastructure.rendering._pdf_latex_helpers import (
    extract_command_fallbacks,
    extract_math_font_preamble,
    extract_preamble,
)
from infrastructure.rendering._slides_crossref import (
    COMBINED_AUX_BASENAME,
    parse_aux_label_numbers,
    resolve_cross_deck_references,
)
from infrastructure.rendering._slides_codelisting import make_codelisting_slide_safe
from infrastructure.rendering._slides_framebreaks import split_long_slide_frames
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex, ensure_pdf_at
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable,
)
from infrastructure.rendering.security import subprocess_options

logger = get_logger(__name__)


def _slide_bibliography_args(manuscript_dir: Path | None) -> list[str]:
    """Return the shared bibliography union for a section-level slide deck.

    Slide decks resolve in-text citations but deliberately suppress the repeated
    reference list: the combined manuscript and the dedicated references deck
    remain the reader-facing bibliography surfaces.
    """
    if manuscript_dir is None:
        return []
    bibliographies = resolve_bibliography(manuscript_dir)
    if not bibliographies:
        return []
    return [
        "--citeproc",
        *pandoc_bibliography_args(bibliographies),
        "--metadata",
        "suppress-bibliography=true",
    ]


class SlidesRenderer:
    """Handles slide generation (Beamer/Reveal.js)."""

    def __init__(
        self,
        config: RenderingConfig,
        *,
        process_runner: Callable[..., object] = subprocess.run,
        latex_compile: Callable[..., Path] = compile_latex,
    ):
        """Initialize the slides renderer with configuration."""
        self.config = config
        self._process_runner = process_runner
        self._latex_compile = latex_compile

    def render(
        self,
        source_file: Path,
        output_format: str = "beamer",
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> Path:
        """Render slides from markdown with figure path resolution.

        Args:
            source_file: Path to markdown file
            output_format: Output format ("beamer" for PDF, "revealjs" for HTML)
            manuscript_dir: Directory containing manuscript (for resource paths)
            figures_dir: Directory containing figures (for resource paths)
            strict_cross_deck_refs: Fail when post-Pandoc TeX contains a
                non-section reference that is neither local nor present in the
                current combined-manuscript AUX label map.

        Returns:
            Path to generated slides file

        Raises:
            RenderingError: If rendering fails
        """
        output_dir = Path(self.config.slides_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_ext = "pdf" if output_format == "beamer" else "html"
        output_file = output_dir / f"{source_file.stem}_slides.{output_ext}"
        profile = self.config.security()
        profile.validate_output(output_file)
        profile.validate_source(source_file)

        # For beamer, we need to handle figure paths specially
        if output_format == "beamer":
            return self._render_beamer_with_paths(
                source_file,
                output_file,
                manuscript_dir,
                figures_dir,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )
        else:
            # For reveal.js, use direct pandoc rendering
            return self._render_revealjs(source_file, output_file, manuscript_dir)

    def _render_revealjs(
        self,
        source_file: Path,
        output_file: Path,
        manuscript_dir: Path | None = None,
    ) -> Path:
        """Render reveal.js slides."""
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "revealjs",
            "-o",
            str(output_file),
            "--standalone",
            "-V",
            f"theme={self.config.slide_theme}",
        ]
        cmd.extend(_slide_bibliography_args(manuscript_dir))
        if manuscript_dir is not None:
            cmd.extend(["--resource-path", str(manuscript_dir)])

        logger.info(f"Generating reveal.js slides from {source_file}")

        try:
            self._process_runner(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                **subprocess_options(self.config.security(), 600),
            )
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render slides: {e.stderr}",
                context={"source": str(source_file), "format": "revealjs"},
            ) from e

    def _render_beamer_with_paths(
        self,
        source_file: Path,
        output_file: Path,
        manuscript_dir: Path | None,
        figures_dir: Path | None,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> Path:
        """Render beamer slides with proper figure path handling.

        Beamer requires careful path handling because:
        1. Pandoc converts markdown to LaTeX
        2. LaTeX is compiled by xelatex
        3. Figure paths must be relative to the LaTeX compilation directory
        """
        output_dir = output_file.parent

        # Create temporary LaTeX file
        temp_tex = output_dir / f"{source_file.stem}_slides.tex"

        # Build pandoc command to convert markdown to LaTeX. A fixed slide
        # level is not safe for manuscript sections: when a source contains
        # h3/h4 headings, treating those headings as Beamer blocks wraps a
        # whole results section in one unbreakable box. Choose the deepest
        # present heading (capped at h4) so the source's semantic breaks
        # become frames; the Lua filter below then lets each frame split when
        # its body is still too long.
        slide_level = self._slide_level_for_source(source_file)
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "beamer",
            "-o",
            str(temp_tex),
            "--standalone",
            f"--slide-level={slide_level}",
        ]

        # Apply the allowframebreaks Lua filter so that long sections
        # without h2 sub-headings still split across slides instead of
        # triggering xelatex driver code 256 on overfull vboxes.
        allowframebreaks_filter = Path(__file__).with_name("_beamer_allowframebreaks.lua")
        if allowframebreaks_filter.exists():
            cmd.extend(["--lua-filter", str(allowframebreaks_filter)])

        # Keep formalism/equation labels source-owned and automatically
        # numbered in the slide deck just as they are in HTML/PDF/DOCX/EPUB.
        crossref = shutil.which("pandoc-crossref")
        if crossref:
            cmd.extend(["--filter", crossref])
        else:
            logger.warning("pandoc-crossref not on PATH; Beamer formalism numbers may remain unresolved.")

        # Beamer does not run citeproc implicitly. Without these arguments, every
        # manuscript citation survives as literal ``[@key]`` text in the
        # reviewer-facing PDF. Use the shared project bibliography union when
        # available; small renderer unit tests and standalone decks without one
        # retain Pandoc's normal no-bibliography behavior.
        cmd.extend(_slide_bibliography_args(manuscript_dir))

        # Inject the math-font subset of the manuscript preamble so
        # \mid, \ll, \gg etc. render cleanly in slide decks without
        # pulling in the full combined-PDF preamble.
        math_header = self._maybe_write_math_header(manuscript_dir, output_dir)
        if math_header is not None:
            cmd.extend(["-H", str(math_header)])

        # Add resource paths if provided
        if manuscript_dir:
            cmd.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir:
            cmd.extend(["--resource-path", str(figures_dir)])

        logger.info(f"Generating beamer slides from {source_file}")

        try:
            # Convert markdown to LaTeX
            self._process_runner(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                **subprocess_options(self.config.security(), 600),
            )

            # Read LaTeX content and fix figure paths
            tex_content = temp_tex.read_text(encoding="utf-8")

            # Fix figure paths for LaTeX compilation
            if figures_dir:
                tex_content = self._fix_figure_paths(tex_content, output_dir, figures_dir)

            tex_content = self._resolve_cross_deck_refs(
                tex_content,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )

            tex_content, codelisting_replacements = make_codelisting_slide_safe(tex_content)
            if codelisting_replacements:
                logger.info("Replaced pandoc-crossref's listing float with a Beamer-safe block")

            # Latin Modern's text face does not provide a literal U+2265 glyph
            # in every size used by Beamer. Keep the semantic comparison while
            # routing it through the math font in either text or math mode.
            tex_content = tex_content.replace("≥", r"\ensuremath{\ge}")

            tex_content, texttt_replacements = make_long_texttt_breakable(tex_content)
            if texttt_replacements:
                logger.info("Made %d long monospace path span(s) breakable in slides", texttt_replacements)

            tex_content, literal_replacements = make_known_literals_breakable(tex_content)
            if literal_replacements:
                logger.info("Made %d recurring long label(s) breakable in slides", literal_replacements)

            tex_content, reference_replacements = make_pandoc_reference_tokens_breakable(tex_content)
            if reference_replacements:
                logger.info(
                    "Made %d unresolved cross-reference token(s) breakable in slides",
                    reference_replacements,
                )

            # A long scientific caption is part of an unbreakable figure
            # environment. Keep the image legible but leave vertical room for
            # its accessibility/source caption on the same frame.
            tex_content, graphics_replacements = constrain_includegraphics_textheight(tex_content, "0.40")
            if graphics_replacements:
                logger.info("Constrained %d slide figure height bound(s)", graphics_replacements)

            tex_content, framebreak_replacements = split_long_slide_frames(tex_content)
            if framebreak_replacements:
                logger.info(
                    "Inserted safe frame breaks in %d dense slide frame(s)",
                    framebreak_replacements,
                )

            # Write fixed LaTeX back
            _tmp = temp_tex.with_suffix(temp_tex.suffix + ".tmp")
            try:
                _tmp.write_text(tex_content, encoding="utf-8")
                _tmp.replace(temp_tex)
            except OSError:
                _tmp.unlink(missing_ok=True)
                raise

            # Compile LaTeX to PDF (written as {temp_tex.stem}.pdf, e.g. slides_slides.pdf)
            compiled_pdf = self._latex_compile(temp_tex, output_dir, compiler=self.config.latex_compiler, timeout=900)
            ensure_pdf_at(compiled_pdf, output_file)

            if output_file.exists():
                logger.info(f"Generated beamer slides: {output_file.name}")
                return output_file
            raise RenderingError(
                f"LaTeX compilation succeeded but PDF not found: {output_file}",
                context={"source": str(source_file), "format": "beamer"},
            )

        except subprocess.CalledProcessError as e:
            # Enhanced error reporting for LaTeX compilation failures
            error_msg = f"Failed to render beamer slides: {e.stderr}"

            # Check for LaTeX log file and extract useful error information
            log_file = output_dir / f"{temp_tex.stem}.log"
            if log_file.exists():
                try:
                    log_content = log_file.read_text(encoding="utf-8", errors="ignore")

                    # Extract last 20 lines for context
                    log_lines = log_content.split("\n")
                    last_lines = log_lines[-20:] if len(log_lines) > 20 else log_lines
                    recent_errors = "\n".join(line for line in last_lines if line.strip())

                    # Detect specific error types
                    error_hints = []
                    if "*** (job aborted, no legal \\end found)" in log_content:
                        error_hints.append(
                            "LaTeX document structure error: missing \\end{document} or unmatched \\begin{}/\\end{} pairs"  # noqa: E501
                        )
                    if "Undefined control sequence" in log_content:
                        error_hints.append("Undefined LaTeX command - check for typos in LaTeX syntax")
                    if "File `" in log_content and "not found" in log_content:
                        error_hints.append("Missing file reference - check figure paths and bibliography files")

                    error_msg += f"\n\nLaTeX Compilation Log ({log_file}):\n{recent_errors}"

                    if error_hints:
                        error_msg += "\n\nPossible Issues:\n" + "\n".join(f"- {hint}" for hint in error_hints)

                    error_msg += f"\n\nSuggestions:\n- Check LaTeX log file: {log_file}\n- Verify LaTeX syntax in generated .tex file: {temp_tex}\n- Ensure all referenced figures exist\n- Check for missing LaTeX packages"  # noqa: E501

                except Exception as log_error:  # noqa: BLE001
                    error_msg += f"\n\nCould not read LaTeX log file: {log_error}"

            raise RenderingError(
                error_msg,
                context={
                    "source": str(source_file),
                    "format": "beamer",
                    "log_file": str(log_file) if log_file.exists() else None,
                },
            ) from e

    @staticmethod
    def _slide_level_for_source(source_file: Path) -> int:
        """Choose a frame-producing heading level for one markdown source.

        Pandoc turns headings below ``--slide-level`` into Beamer blocks. A
        deep manuscript section can therefore become one enormous block and
        overflow even when the source contains natural subheadings. Heading
        levels 2--4 are the useful presentation range: h1-only legacy decks
        retain the historical level-2 behavior, while h3/h4-heavy results
        sections get actual frame boundaries. Deeper headings remain block
        content rather than creating a pathological one-frame-per-line deck.
        """
        source = source_file.read_text(encoding="utf-8")
        levels = [len(match.group(1)) for match in re.finditer(r"^(#{1,6})[ \t]+", source, flags=re.MULTILINE)]
        return max(2, min(4, max(levels, default=2)))

    def _resolve_cross_deck_refs(
        self,
        tex_content: str,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> str:
        """Resolve cross-deck ``\\ref``/``\\eqref`` against the combined PDF's aux.

        Section decks are standalone Beamer builds, so a raw-LaTeX
        reference to a ``\\label`` defined in a *different* section's deck
        compiles to "??". The combined manuscript build resolves every
        label and retains its ``.aux`` next to the combined PDF
        (``{pdf_dir}/_combined_manuscript.aux``); this pre-pass replaces
        each cross-deck reference with the literal number that aux
        recorded — the same number the combined PDF prints. Within-deck
        references are untouched (Beamer numbers them natively), labels
        missing from the aux are left as-is and noted in the render log,
        and a missing aux (e.g. first-ever render, before any combined
        build) skips only the numeric lookup. Section references still become
        visible labels, so the first standalone render cannot ship ``??``.
        The default standalone pass remains fail-open. The producer-ordered
        refresh sets ``strict_cross_deck_refs`` and fails when any non-section
        foreign reference remains unresolved in the post-Pandoc TeX.
        """
        aux_path = Path(self.config.pdf_dir) / COMBINED_AUX_BASENAME
        label_numbers = parse_aux_label_numbers(aux_path)
        tex_content, replaced, unresolved = resolve_cross_deck_references(tex_content, label_numbers)
        if replaced:
            logger.info(
                "Resolved %d cross-deck reference(s) in slides from %s",
                replaced,
                aux_path.name,
            )
        strict_unresolved = [label for label in unresolved if not label.startswith("sec:")]
        if strict_cross_deck_refs and strict_unresolved:
            raise RenderingError(
                "Current combined-manuscript AUX cannot resolve post-Pandoc cross-deck slide references",
                context={
                    "aux_path": str(aux_path),
                    "unresolved_labels": strict_unresolved,
                },
            )
        if unresolved:
            logger.warning(
                "Left %d cross-deck reference(s) unresolved in slides (labels not in %s): %s",
                len(unresolved),
                aux_path.name,
                ", ".join(unresolved),
            )
        if not label_numbers:
            logger.debug("No combined-manuscript aux label map at %s; numeric refs left as-is", aux_path)
        # Pandoc-crossref emits ``\ref`` for section labels. Beamer does not
        # assign numbers to every subsection level used as a slide boundary,
        # so a same-deck section label can otherwise remain ``??`` even after
        # the normal two-pass compile. Preserve the target identifier as a
        # visible, breakable token rather than shipping an unresolved marker.
        section_ref_re = re.compile(r"\\(?:ref|eqref)\{(?P<label>sec:[^}]+)\}")

        def _render_section_label(match: re.Match[str]) -> str:
            # Pandoc section identifiers may contain underscores. They are
            # ordinary characters inside the ``\texttt`` argument, but TeX
            # treats an unescaped underscore as a math-mode subscript and
            # aborts the standalone slide deck. Keep the visible identifier
            # unchanged while escaping the only special character permitted
            # by the section-label grammar that is unsafe here.
            label = match.group("label").replace("_", r"\_")
            return rf"\texttt{{{label}}}"

        tex_content, section_replacements = section_ref_re.subn(
            _render_section_label,
            tex_content,
        )
        if section_replacements:
            logger.info(
                "Rendered %d unnumbered section reference(s) as visible labels",
                section_replacements,
            )
        return tex_content

    def _maybe_write_math_header(self, manuscript_dir: Path | None, output_dir: Path) -> Path | None:
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
            snippet_parts.append(
                "% Additional theorem-like environments from manuscript preamble.\n" + preamble_theorems
            )

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
                snippet_parts.append(
                    "% Non-floating stand-in for the `algorithm` float.\n"
                    "\\newenvironment{algorithm}[1][]{%\n"
                    "  \\par\\medskip\\noindent\\rule{\\linewidth}{0.4pt}\\par\\nobreak\\small\n"
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

    def _fix_figure_paths(self, tex_content: str, output_dir: Path, figures_dir: Path) -> str:
        """Fix figure paths in LaTeX content for proper compilation.

        Converts paths like ../output/figures/file.png to relative paths
        that work from the LaTeX compilation directory (output/slides).

        Handles multiple path formats and preserves optional parameters.

        Args:
            tex_content: LaTeX content to process
            output_dir: Directory where LaTeX compilation happens (output/slides)
            figures_dir: Directory containing figures (output/figures)

        Returns:
            LaTeX content with corrected figure paths
        """

        def extract_filename(path_str: str) -> str:
            """Extract filename from various path formats."""
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

            # If no prefix matched, extract filename from path
            if "/" in path_str or "\\" in path_str:
                return re.split(r"[/\\]", path_str)[-1]
            else:
                # No separators — path_str is already a bare filename
                return path_str

        def matching_delimiter(start: int, opener: str, closer: str) -> int | None:
            """Return the index just after a balanced delimiter group.

            Pandoc commonly emits ``\\includegraphics[alt={... [ ...]}]{...}``.
            A regex like ``\\[([^\\]]*)\\]`` stops at the first bracket inside
            the alt text and therefore misses the real path argument.  This
            scanner tracks braces while looking for the closing option
            bracket, which is enough for Pandoc's generated Beamer LaTeX.
            """
            depth = 0
            brace_depth = 0
            escaped = False
            for idx in range(start, len(tex_content)):
                ch = tex_content[idx]
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == "{":
                    brace_depth += 1
                    continue
                if ch == "}":
                    brace_depth = max(0, brace_depth - 1)
                    continue
                if ch == opener and brace_depth == 0:
                    depth += 1
                    continue
                if ch == closer and brace_depth == 0:
                    depth -= 1
                    if depth == 0:
                        return idx + 1
            return None

        def matching_brace(start: int) -> int | None:
            """Find the index of the matching closing brace."""
            depth = 0
            escaped = False
            for idx in range(start, len(tex_content)):
                ch = tex_content[idx]
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == "{":
                    depth += 1
                    continue
                if ch == "}":
                    depth -= 1
                    if depth == 0:
                        return idx + 1
            return None

        pieces: list[str] = []
        cursor = 0
        command = r"\includegraphics"
        while True:
            start = tex_content.find(command, cursor)
            if start == -1:
                pieces.append(tex_content[cursor:])
                break

            pieces.append(tex_content[cursor:start])
            pos = start + len(command)
            while pos < len(tex_content) and tex_content[pos].isspace():
                pos += 1

            if pos < len(tex_content) and tex_content[pos] == "[":
                opt_end = matching_delimiter(pos, "[", "]")
                if opt_end is None:
                    pieces.append(tex_content[start:])
                    cursor = len(tex_content)
                    break
                pos = opt_end
                while pos < len(tex_content) and tex_content[pos].isspace():
                    pos += 1

            if pos >= len(tex_content) or tex_content[pos] != "{":
                pieces.append(tex_content[start:pos])
                cursor = pos
                continue

            arg_end = matching_brace(pos)
            if arg_end is None:
                pieces.append(tex_content[start:])
                cursor = len(tex_content)
                break

            old_path = tex_content[pos + 1 : arg_end - 1]
            if old_path.startswith("../figures/"):
                pieces.append(tex_content[start:arg_end])
            else:
                filename = extract_filename(old_path)
                new_path = f"../figures/{filename}"
                pieces.append(tex_content[start : pos + 1])
                pieces.append(new_path)
                pieces.append("}")
            cursor = arg_end

        return "".join(pieces)
