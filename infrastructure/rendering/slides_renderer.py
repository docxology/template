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
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._slides_crossref import (
    COMBINED_AUX_BASENAME,
    parse_aux_label_numbers,
    resolve_cross_deck_references,
    transform_tex_prose,
)
from infrastructure.rendering._slides_codelisting import make_codelisting_slide_safe as make_codelisting_slide_safe
from infrastructure.rendering._slides_accessibility import (
    accessible_reveal_output_issues,
    enhance_accessible_reveal,
    load_and_compose_pandoc_json,
)
from infrastructure.rendering._slides_framebreaks import split_long_slide_frames as split_long_slide_frames
from infrastructure.rendering._slides_beamer import (
    _ACCESSIBLE_BEAMER_ASPECT_RATIO as _ACCESSIBLE_BEAMER_ASPECT_RATIO,
    constrain_includegraphics_textheight as constrain_includegraphics_textheight,
    make_known_literals_breakable as make_known_literals_breakable,
    make_long_texttt_breakable as make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable as make_pandoc_reference_tokens_breakable,
    normalize_accessible_projection_latex as normalize_accessible_projection_latex,
    pandoc_bibliography_args as pandoc_bibliography_args,
    resolve_bibliography as resolve_bibliography,
    write_slides_math_header as write_slides_math_header,
    parse_latex_log_findings as parse_latex_log_findings,
    _reject_accessible_beamer_overflow as _reject_accessible_beamer_overflow,
    _slide_bibliography_args as _slide_bibliography_args,
    beamer_command,
    transform_beamer_latex,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex, ensure_pdf_at
from infrastructure.rendering._slides_reveal_content import ACCESSIBLE_REVEAL_URL, ACCESSIBLE_REVEAL_VERSION
from infrastructure.rendering._slides_tex_figures import fix_slides_figure_paths
from infrastructure.rendering._web_postprocess import MATHJAX_URL
from infrastructure.rendering.security import subprocess_options

logger = get_logger(__name__)


# Accessible Reveal derivatives use a known Reveal theme rather than reusing
# the Beamer-only ``metropolis`` default. Reveal.js does not ship a Metropolis
# theme, so forwarding that name produces a broken stylesheet request. Pin the
# companion runtime as part of the published reader contract; archive mode
# retains its historical caller-configured URL/theme behavior.
_ACCESSIBLE_REVEAL_VERSION = ACCESSIBLE_REVEAL_VERSION
_ACCESSIBLE_REVEAL_URL = ACCESSIBLE_REVEAL_URL
_ACCESSIBLE_REVEAL_THEME = "white"
_SECTION_REF_RE = re.compile(
    r"(?P<escaped_join>\\textasciitilde\{\})?"
    r"(?P<authored_open>\()?"
    r"\\(?P<command>ref|eqref)\{(?P<label>sec:[^}]+)\}"
)


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

    def _require_accessible_seqsplit(self) -> None:
        """Require the package that makes accessible long-code pricing truthful.

        Archive rendering keeps the historical graceful LaTeX fallback. Accessible
        composition, however, discounts a long simple inline Code node only because
        the downstream ``breaktt`` macro inserts character-level opportunities.
        If ``seqsplit.sty`` is unavailable, that macro is intentionally an identity
        fallback and the geometric premise is false. Detect the capability through
        the same injected, security-profiled process boundary as every other slide
        subprocess.
        """

        located = ""
        try:
            completed = self._process_runner(
                ["kpsewhich", "seqsplit.sty"],
                check=False,
                capture_output=True,
                text=True,
                **subprocess_options(self.config.security(), 30),
            )
        except (OSError, subprocess.SubprocessError):
            completed = None
        if completed is not None and getattr(completed, "returncode", None) == 0:
            stdout = getattr(completed, "stdout", "")
            if isinstance(stdout, str):
                located = stdout.strip()
        if located:
            return
        raise RenderingError(
            "[slides.capability.seqsplit-required] Accessible long monospace wrapping requires seqsplit.sty",
            context={
                "diagnostic_code": "slides.capability.seqsplit-required",
                "required_latex_package": "seqsplit",
            },
            suggestions=[
                "Install the TeX seqsplit package before rendering the accessible slide profile.",
                "Shorten or remove the long projected monospace token; archive rendering retains its historical fallback.",
            ],
        )

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
            render_source, temporary_sources = self._prepare_accessible_source(
                source_file,
                output_dir,
                manuscript_dir=manuscript_dir,
            )

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
            return self._render_revealjs(
                render_source,
                output_file,
                manuscript_dir,
                figures_dir,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )
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
            render_source, temporary_sources = self._prepare_accessible_source(
                source_file,
                output_dir,
                manuscript_dir=manuscript_dir,
            )
            pdf_result = self._render_beamer_with_paths(
                render_source,
                pdf_output,
                manuscript_dir,
                figures_dir,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )
            html_result = self._render_revealjs(
                render_source,
                html_output,
                manuscript_dir,
                figures_dir,
                strict_cross_deck_refs=strict_cross_deck_refs,
            )
            completed = True
            return pdf_result, html_result
        finally:
            if not completed:
                pdf_output.unlink(missing_ok=True)
                html_output.unlink(missing_ok=True)
            for temporary in temporary_sources:
                temporary.unlink(missing_ok=True)

    def _prepare_accessible_source(
        self,
        source_file: Path,
        output_dir: Path,
        *,
        manuscript_dir: Path | None,
    ) -> tuple[Path, tuple[Path, ...]]:
        """Resolve citations, then compose one bounded Pandoc JSON document."""

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
        temporary = composed_json.with_suffix(composed_json.suffix + ".tmp")
        completed = False
        try:
            profile.validate_output(raw_json)
            profile.validate_output(composed_json)
            profile.validate_output(temporary)
            cmd = [
                self.config.pandoc_path,
                str(source_file),
                "-t",
                "json",
                "-o",
                str(raw_json),
            ]
            # Citeproc deliberately runs at the geometry boundary as well as at
            # the final writers. Pandoc retains Cite nodes, so pandoc-crossref can
            # still resolve protocol/figure/section identifiers later, while the
            # composer sees the exact visible author-year strings, affixes, and
            # locators rather than a fixed placeholder that can underprice long
            # family names.
            cmd.extend(_slide_bibliography_args(manuscript_dir))
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
            completed = True
            return composed_json, (raw_json, composed_json)
        except subprocess.CalledProcessError as exc:
            raise RenderingError(
                f"Failed to parse accessible slide source: {exc.stderr}",
                context={
                    "source": str(source_file),
                    "format": "pandoc-json",
                    "diagnostic_code": "slides.parse.pandoc-json",
                },
            ) from exc
        finally:
            if not completed:
                raw_json.unlink(missing_ok=True)
                composed_json.unlink(missing_ok=True)
                temporary.unlink(missing_ok=True)

    def _render_revealjs(
        self,
        source_file: Path,
        output_file: Path,
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
        *,
        strict_cross_deck_refs: bool = False,
    ) -> Path:
        """Render reveal.js slides."""
        theme = _ACCESSIBLE_REVEAL_THEME if self.config.slides_profile == "accessible" else self.config.slide_theme
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "revealjs",
            "-o",
            str(output_file),
            "--standalone",
            "-V",
            f"theme={theme}",
        ]
        if self.config.slides_profile == "accessible":
            cmd.extend(
                [
                    "-f",
                    "json",
                    "--slide-level=2",
                    f"--mathjax={MATHJAX_URL}",
                    "-V",
                    f"revealjs-url={_ACCESSIBLE_REVEAL_URL}",
                ]
            )
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
                        label_numbers=(
                            parse_aux_label_numbers(Path(self.config.pdf_dir) / COMBINED_AUX_BASENAME)
                            if strict_cross_deck_refs
                            else None
                        ),
                        strict_cross_deck_refs=strict_cross_deck_refs,
                    )
                    issues = accessible_reveal_output_issues(output_file)
                    if issues:
                        raise RenderingError(
                            "[slides.accessibility.reveal-output] Accessible Reveal output failed validation",
                            context={
                                "diagnostic_code": "slides.accessibility.reveal-output",
                                "source": str(source_file),
                                "output": str(output_file),
                                "issues": list(issues),
                            },
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

        cmd = beamer_command(
            self.config,
            source_file,
            temp_tex,
            manuscript_dir,
            figures_dir,
            slide_level=2 if self.config.slides_profile == "accessible" else self._slide_level_for_source(source_file),
        )

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

            tex_content = transform_beamer_latex(
                tex_content, self.config, require_seqsplit=self._require_accessible_seqsplit
            )

            # Replace only our TeX target through an exclusive confined temp.
            atomic_write_text_confined(output_dir, temp_tex, tex_content)

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
        build) skips only the numeric lookup. In the accessible profile,
        section references use the combined-PDF number even when their label
        is local to the deck; Beamer does not reliably number every heading
        level that becomes a frame. A non-strict first pass uses a readable
        section-name fallback rather than exposing the internal label.
        The default standalone pass remains fail-open. The producer-ordered
        refresh sets ``strict_cross_deck_refs`` and, in accessible mode, fails
        when any reference (including a local section reference) is absent
        from the current combined-manuscript AUX.
        """
        aux_path = Path(self.config.pdf_dir) / COMBINED_AUX_BASENAME
        label_numbers = parse_aux_label_numbers(aux_path)
        missing_accessible_sections: set[str] = set()
        accessible_section_replacements = 0
        if self.config.slides_profile == "accessible":

            def _resolve_accessible_section_segment(segment: str) -> str:
                def _resolve_accessible_section(match: re.Match[str]) -> str:
                    nonlocal accessible_section_replacements
                    command = match.group("command")
                    label = match.group("label")
                    number = label_numbers.get(label)
                    if number is None:
                        missing_accessible_sections.add(label)
                        return match.group(0)
                    accessible_section_replacements += 1
                    join = "~" if match.group("escaped_join") else ""
                    authored_open = match.group("authored_open") or ""
                    authored_pair = bool(authored_open and segment[match.end() :].startswith(")"))
                    resolved_number = number if command == "ref" or authored_pair else f"({number})"
                    return join + authored_open + resolved_number

                return _SECTION_REF_RE.sub(_resolve_accessible_section, segment)

            tex_content = transform_tex_prose(tex_content, _resolve_accessible_section_segment)
            if accessible_section_replacements:
                logger.info(
                    "Resolved %d accessible section reference(s) from %s",
                    accessible_section_replacements,
                    aux_path.name,
                )
        tex_content, replaced, unresolved = resolve_cross_deck_references(
            tex_content,
            label_numbers,
            resolve_local=self.config.slides_profile == "accessible" and strict_cross_deck_refs,
        )
        if replaced:
            logger.info(
                "Resolved %d cross-deck reference(s) in slides from %s",
                replaced,
                aux_path.name,
            )
        all_unresolved = sorted({*unresolved, *missing_accessible_sections})
        strict_unresolved = (
            all_unresolved
            if self.config.slides_profile == "accessible"
            else [label for label in all_unresolved if not label.startswith("sec:")]
        )
        if strict_cross_deck_refs and strict_unresolved:
            raise RenderingError(
                "Current combined-manuscript AUX cannot resolve post-Pandoc cross-deck slide references",
                context={
                    "aux_path": str(aux_path),
                    "unresolved_labels": strict_unresolved,
                },
            )
        if all_unresolved:
            logger.warning(
                "Left %d cross-deck reference(s) unresolved in slides (labels not in %s): %s",
                len(all_unresolved),
                aux_path.name,
                ", ".join(all_unresolved),
            )
        if not label_numbers:
            logger.debug("No combined-manuscript aux label map at %s; numeric refs left as-is", aux_path)

        # Pandoc-crossref emits ``\ref`` for section labels. Beamer does not
        # assign numbers to every subsection level used as a slide boundary,
        # so a same-deck section label can otherwise remain ``??`` even after
        # the normal two-pass compile. Preserve the target identifier as a
        # visible, breakable token rather than shipping an unresolved marker.
        section_replacements = 0

        def _render_section_segment(segment: str) -> str:
            def _render_section_label(match: re.Match[str]) -> str:
                nonlocal section_replacements
                section_replacements += 1
                join = "~" if match.group("escaped_join") else ""
                authored_open = match.group("authored_open") or ""
                if self.config.slides_profile == "accessible":
                    slug = match.group("label").partition(":")[2]
                    readable = re.sub(r"[^A-Za-z0-9]+", " ", slug).strip() or "referenced"
                    return join + authored_open + rf"\emph{{{readable} section}}"
                # Pandoc section identifiers may contain underscores. They are
                # ordinary characters inside the ``\texttt`` argument, but TeX
                # treats an unescaped underscore as a math-mode subscript and
                # aborts the standalone slide deck. Keep the visible identifier
                # unchanged while escaping the only special character permitted
                # by the section-label grammar that is unsafe here.
                label = match.group("label").replace("_", r"\_")
                return join + authored_open + rf"\texttt{{{label}}}"

            return _SECTION_REF_RE.sub(_render_section_label, segment)

        tex_content = transform_tex_prose(tex_content, _render_section_segment)
        if section_replacements:
            mode = "readable names" if self.config.slides_profile == "accessible" else "visible labels"
            logger.info("Rendered %d unnumbered section reference(s) as %s", section_replacements, mode)
        return tex_content
