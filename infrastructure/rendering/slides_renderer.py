"""Slides rendering module.

Per-format preamble coverage
----------------------------
This renderer drives Pandoc directly with ``-t beamer`` (or ``revealjs``)
and intentionally **does not** route through
:func:`infrastructure.rendering._pdf_combined_renderer.inject_latex_preamble`
— Beamer ships its own document class, so the manuscript's
``geometry`` / ``hyperref`` / ``titlepage`` machinery would clash.

The math-font subset *is* propagated. Whenever ``preamble.md`` loads
``unicode-math``, :func:`infrastructure.rendering._slides_math_header.write_slides_math_header`
writes a minimal ``_slides_math_header.tex`` containing only
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

import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._bibliography import pandoc_bibliography_args, resolve_bibliography
from infrastructure.rendering._slides_crossref import (
    COMBINED_AUX_BASENAME,
    parse_aux_label_numbers,
    resolve_cross_deck_references,
)
from infrastructure.rendering._slides_codelisting import make_codelisting_slide_safe
from infrastructure.rendering._slides_accessibility import (
    enhance_accessible_reveal,
    load_and_compose_pandoc_json,
)
from infrastructure.rendering._slides_framebreaks import split_long_slide_frames
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_log_quality import parse_latex_log_findings
from infrastructure.rendering.latex_utils import compile_latex, ensure_pdf_at
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable,
)
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering._slides_tex_figures import fix_slides_figure_paths
from infrastructure.rendering.security import subprocess_options

logger = get_logger(__name__)


def _reject_accessible_beamer_overflow(log_file: Path, compiled_pdf: Path) -> None:
    """Discard a Beamer derivative whose fixed accessible layout overflowed."""

    findings = parse_latex_log_findings(
        log_file,
        blocked_layout_kinds={r"Overfull \hbox", r"Overfull \vbox"},
    )
    if not findings:
        return
    compiled_pdf.unlink(missing_ok=True)
    examples = [f"{finding.kind} at line {finding.line_number}: {finding.message}" for finding in findings[:5]]
    raise RenderingError(
        "[slides.density.beamer-overflow] Accessible Beamer content exceeds its fixed frame geometry",
        context={
            "diagnostic_code": "slides.density.beamer-overflow",
            "log_file": str(log_file),
            "finding_count": len(findings),
            "examples": examples,
        },
        suggestions=[
            "Split the source at a semantic block boundary or shorten the projected excerpt.",
            "Keep complete prose, captions, and tables in the linked canonical HTML manuscript.",
        ],
    )


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

        if output_format not in {"beamer", "revealjs"}:
            raise RenderingError(
                f"Unsupported slide output format: {output_format}",
                context={"source": str(source_file), "format": output_format},
            )

        render_source = source_file
        temporary_sources: tuple[Path, ...] = ()
        if self.config.slides_profile == "accessible":
            # A failed strict composition must not leave a prior derivative
            # that can be mistaken for the current source.
            output_file.unlink(missing_ok=True)
            render_source, temporary_sources = self._prepare_accessible_source(source_file, output_dir)

        try:
            # For beamer, we need to handle figure paths specially.
            if output_format == "beamer":
                return self._render_beamer_with_paths(
                    render_source,
                    output_file,
                    manuscript_dir,
                    figures_dir,
                    strict_cross_deck_refs=strict_cross_deck_refs,
                )
            # For reveal.js, use direct pandoc rendering.
            return self._render_revealjs(render_source, output_file, manuscript_dir, figures_dir)
        finally:
            for temporary in temporary_sources:
                temporary.unlink(missing_ok=True)

    def render_accessible_pair(
        self,
        source_file: Path,
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> tuple[Path, Path]:
        """Render one accessible Beamer/Reveal pair from one composed AST.

        The accessible profile is a paired publication contract: both the
        projected Beamer PDF and the accessibility-enhanced Reveal.js reader
        consume the same semantic Pandoc JSON document.  A failure in either
        renderer removes both public derivatives so a stale or partial pair
        cannot satisfy a later pipeline gate.
        """

        if self.config.slides_profile != "accessible":
            raise RenderingError(
                "Accessible slide-pair rendering requires slides_profile='accessible'",
                context={"source": str(source_file), "diagnostic_code": "slides.profile.pair-required"},
            )

        output_dir = Path(self.config.slides_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_output = output_dir / f"{source_file.stem}_slides.pdf"
        html_output = output_dir / f"{source_file.stem}_slides.html"
        profile = self.config.security()
        profile.validate_source(source_file)
        profile.validate_output(pdf_output)
        profile.validate_output(html_output)

        # Clear both identities before composition.  If composition itself
        # fails, neither derivative from an older source revision survives.
        pdf_output.unlink(missing_ok=True)
        html_output.unlink(missing_ok=True)
        render_source = source_file
        temporary_sources: tuple[Path, ...] = ()
        completed = False
        try:
            render_source, temporary_sources = self._prepare_accessible_source(source_file, output_dir)
            pdf_result = self._render_beamer_with_paths(
                render_source,
                pdf_output,
                manuscript_dir,
                figures_dir,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )
            html_result = self._render_revealjs(render_source, html_output, manuscript_dir, figures_dir)
            completed = True
            return pdf_result, html_result
        finally:
            if not completed:
                pdf_output.unlink(missing_ok=True)
                html_output.unlink(missing_ok=True)
            for temporary in temporary_sources:
                temporary.unlink(missing_ok=True)

    def _prepare_accessible_source(self, source_file: Path, output_dir: Path) -> tuple[Path, tuple[Path, ...]]:
        """Compose Markdown into one bounded semantic Pandoc JSON document."""

        profile = self.config.security()
        raw_handle = tempfile.NamedTemporaryFile(
            prefix=f".{source_file.stem}-",
            suffix=".pandoc.json",
            dir=output_dir,
            delete=False,
        )
        raw_json = Path(raw_handle.name)
        raw_handle.close()
        composed_json = raw_json.with_suffix(".accessible.json")
        profile.validate_output(raw_json)
        profile.validate_output(composed_json)
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "json",
            "-o",
            str(raw_json),
        ]
        try:
            self._process_runner(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                **subprocess_options(profile, 600),
            )
            composition = load_and_compose_pandoc_json(
                raw_json,
                policy=self.config.accessible_slide_policy(),
                source=str(source_file),
            )
            temporary = composed_json.with_suffix(composed_json.suffix + ".tmp")
            try:
                temporary.write_text(
                    json.dumps(
                        composition.document,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                    encoding="utf-8",
                )
                temporary.replace(composed_json)
            except OSError:
                temporary.unlink(missing_ok=True)
                raise
            logger.info(
                "Accessible slide composition: %d frames (%d section dividers, %d figure frames, %d table excerpts)",
                composition.frame_count,
                composition.section_divider_count,
                composition.figure_frame_count,
                composition.excerpted_table_count,
            )
            return composed_json, (raw_json, composed_json)
        except subprocess.CalledProcessError as exc:
            raw_json.unlink(missing_ok=True)
            composed_json.unlink(missing_ok=True)
            raise RenderingError(
                f"Failed to parse accessible slide source: {exc.stderr}",
                context={
                    "source": str(source_file),
                    "format": "pandoc-json",
                    "diagnostic_code": "slides.parse.pandoc-json",
                },
            ) from exc
        except Exception:
            raw_json.unlink(missing_ok=True)
            composed_json.unlink(missing_ok=True)
            raise

    def _render_revealjs(
        self,
        source_file: Path,
        output_file: Path,
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
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
        if self.config.slides_profile == "accessible":
            cmd.extend(["-f", "json", "--slide-level=2"])
        cmd.extend(_slide_bibliography_args(manuscript_dir))
        if manuscript_dir is not None:
            cmd.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir is not None:
            cmd.extend(["--resource-path", str(figures_dir)])

        logger.info(f"Generating reveal.js slides from {source_file}")

        try:
            self._process_runner(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                **subprocess_options(self.config.security(), 600),
            )
            if self.config.slides_profile == "accessible":
                try:
                    enhance_accessible_reveal(
                        output_file,
                        policy=self.config.accessible_slide_policy(),
                        registry_path=(figures_dir / "figure_registry.json") if figures_dir is not None else None,
                    )
                except (OSError, RenderingError):
                    output_file.unlink(missing_ok=True)
                    raise
            return output_file

        except subprocess.CalledProcessError as e:
            if self.config.slides_profile == "accessible":
                output_file.unlink(missing_ok=True)
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
        # Derive intermediates from the stable public output name. Accessible
        # mode consumes a randomized, short-lived JSON source; deriving from
        # that temporary filename would leak nondeterministic build products
        # into ``output/slides``.
        temp_tex = output_file.with_suffix(".tex")

        # Build pandoc command to convert markdown to LaTeX. A fixed slide
        # level is not safe for manuscript sections: when a source contains
        # h3/h4 headings, treating those headings as Beamer blocks wraps a
        # whole results section in one unbreakable box. Choose the deepest
        # present heading (capped at h4) so the source's semantic breaks
        # become frames; the Lua filter below then lets each frame split when
        # its body is still too long.
        slide_level = 2 if self.config.slides_profile == "accessible" else self._slide_level_for_source(source_file)
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
        if self.config.slides_profile == "accessible":
            cmd.extend(["-f", "json"])

        # Apply the allowframebreaks Lua filter so that long sections
        # without h2 sub-headings still split across slides instead of
        # triggering xelatex driver code 256 on overfull vboxes.
        allowframebreaks_filter = Path(__file__).with_name("_beamer_allowframebreaks.lua")
        if self.config.slides_profile == "archive" and allowframebreaks_filter.exists():
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
        math_header = write_slides_math_header(
            manuscript_dir,
            output_dir,
            accessible_policy=(
                self.config.accessible_slide_policy() if self.config.slides_profile == "accessible" else None
            ),
        )
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
                tex_content = fix_slides_figure_paths(tex_content, output_dir, figures_dir)

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
            figure_fraction = (
                f"{self.config.slides_min_figure_area_percent / 100:.2f}"
                if self.config.slides_profile == "accessible"
                else "0.40"
            )
            tex_content, graphics_replacements = constrain_includegraphics_textheight(
                tex_content,
                figure_fraction,
            )
            if graphics_replacements:
                logger.info("Constrained %d slide figure height bound(s)", graphics_replacements)

            if self.config.slides_profile == "archive":
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
            if self.config.slides_profile == "accessible":
                _reject_accessible_beamer_overflow(temp_tex.with_suffix(".log"), compiled_pdf)
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
