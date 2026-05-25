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
(:func:`infrastructure.rendering._pdf_combined_renderer.prevalidate_source_markdown`)
is intentionally *not* invoked here because slides typically render a
single section in isolation and have a different acceptable-citation
set than the full manuscript.
"""

import re
import subprocess
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    extract_math_font_preamble,
    extract_preamble,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex, ensure_pdf_at
from infrastructure.rendering.latex_texttt import (
    constrain_includegraphics_textheight,
    make_known_literals_breakable,
    make_long_texttt_breakable,
    make_pandoc_reference_tokens_breakable,
)

logger = get_logger(__name__)


class SlidesRenderer:
    """Handles slide generation (Beamer/Reveal.js)."""

    def __init__(self, config: RenderingConfig):
        """Initialize the slides renderer with configuration."""
        self.config = config

    def render(
        self,
        source_file: Path,
        output_format: str = "beamer",
        manuscript_dir: Path | None = None,
        figures_dir: Path | None = None,
    ) -> Path:
        """Render slides from markdown with figure path resolution.

        Args:
            source_file: Path to markdown file
            output_format: Output format ("beamer" for PDF, "revealjs" for HTML)
            manuscript_dir: Directory containing manuscript (for resource paths)
            figures_dir: Directory containing figures (for resource paths)

        Returns:
            Path to generated slides file

        Raises:
            RenderingError: If rendering fails
        """
        output_dir = Path(self.config.slides_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_ext = "pdf" if output_format == "beamer" else "html"
        output_file = output_dir / f"{source_file.stem}_slides.{output_ext}"

        # For beamer, we need to handle figure paths specially
        if output_format == "beamer":
            return self._render_beamer_with_paths(source_file, output_file, manuscript_dir, figures_dir)
        else:
            # For reveal.js, use direct pandoc rendering
            return self._render_revealjs(source_file, output_file)

    def _render_revealjs(self, source_file: Path, output_file: Path) -> Path:
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

        logger.info(f"Generating reveal.js slides from {source_file}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
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

        # Build pandoc command to convert markdown to LaTeX.
        # ``--slide-level=2`` makes every h2 start its own Beamer frame
        # (h1 becomes a section break) so a single h1 with several h2
        # subsections renders as several slides instead of one huge
        # overflowing frame. Combined with the allowframebreaks Lua
        # filter below, even h2 sections with long body text split
        # cleanly across multiple slides.
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "beamer",
            "-o",
            str(temp_tex),
            "--standalone",
            "--slide-level=2",
        ]

        # Apply the allowframebreaks Lua filter so that long sections
        # without h2 sub-headings still split across slides instead of
        # triggering xelatex driver code 256 on overfull vboxes.
        allowframebreaks_filter = Path(__file__).with_name("_beamer_allowframebreaks.lua")
        if allowframebreaks_filter.exists():
            cmd.extend(["--lua-filter", str(allowframebreaks_filter)])

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
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)

            # Read LaTeX content and fix figure paths
            tex_content = temp_tex.read_text()

            # Fix figure paths for LaTeX compilation
            if figures_dir:
                tex_content = self._fix_figure_paths(tex_content, output_dir, figures_dir)

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

            tex_content, graphics_replacements = constrain_includegraphics_textheight(tex_content, "0.46")
            if graphics_replacements:
                logger.info("Constrained %d slide figure height bound(s)", graphics_replacements)

            # Write fixed LaTeX back
            _tmp = temp_tex.with_suffix(temp_tex.suffix + ".tmp")
            try:
                _tmp.write_text(tex_content)
                _tmp.replace(temp_tex)
            except OSError:
                _tmp.unlink(missing_ok=True)
                raise

            # Compile LaTeX to PDF (written as {temp_tex.stem}.pdf, e.g. slides_slides.pdf)
            compiled_pdf = compile_latex(temp_tex, output_dir, compiler=self.config.latex_compiler, timeout=900)
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
        sequence and raw-underscore errors.

        Returns the header path when a snippet was produced, or ``None``
        when neither a math snippet nor a citation fallback is needed.
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
            "\\AtBeginEnvironment{tabular}{\\tiny\\renewcommand{\\arraystretch}{0.86}\\setlength{\\tabcolsep}{1pt}}\n\n"
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
        )

        if not snippet_parts:
            logger.debug("preamble.md does not need a slides header; skipping")
            return None

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
