"""Web/HTML rendering module."""

import re
import shutil
import subprocess
from pathlib import Path

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)

# Shared design-token + dark-mode block embedded ahead of the rendered CSS so
# the web surface participates in the same design system (one --brand-1 source
# and a prefers-color-scheme block) as the reporting HTML surfaces. Maps a few
# of those tokens onto this renderer's existing serif/blue palette without
# touching ide_style.css class names. Static string → deterministic output.
_SHARED_DESIGN_TOKENS_CSS = """:root {
  --brand-1: #5b6ee0;
  --web-bg: #f8f8f8;
  --web-surface: #ffffff;
  --web-text: #2c3e50;
  --web-border: #bdc3c7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --brand-1: #7e8ce8;
    --web-bg: #0f1420;
    --web-surface: #161c2b;
    --web-text: #e6eaf2;
    --web-border: #2a3447;
  }
}
/* Numbered theorem-like environments. Pandoc's HTML writer drops raw-LaTeX
   \\newtheorem blocks, so WebRenderer rewrites them (web-only) into
   .theorem-box Divs; this styles them as boxed, numbered blocks that read like
   the PDF's theorem environments. The PDF path is unchanged (it uses the LaTeX
   preamble). */
.theorem-box {
  border-left: 4px solid var(--brand-1);
  background: var(--web-surface);
  padding: 0.6em 1em;
  margin: 1.1em 0;
  border-radius: 0 4px 4px 0;
}
.theorem-box.definition { border-left-style: dashed; }
.theorem-box > p:first-child { margin-top: 0; }
.theorem-box > p:last-child { margin-bottom: 0; }"""


class WebRenderer:
    """Handles HTML generation."""

    _RAW_LATEX_INLINE_RE = re.compile(r"`([^`]+)`\{=latex\}")
    _CITE_RE = re.compile(
        r"\\cite(?:p|t|alp|alt|author|year|yearpar)?"
        r"(?:\[[^\]]*\]\s*){0,2}\{([^{}]+)\}"
    )
    _HYPERREF_RE = re.compile(r"\\hyperref\[[^\]]+\]\{([^{}]+)\}")
    _HREF_RE = re.compile(r"\\href\{[^{}]+\}\{([^{}]+)\}")
    _LABEL_RE = re.compile(r"\\(?:phantomsection\s*)?\\?label\{[^{}]+\}")
    _REF_RE = re.compile(r"\\(?:eqref|ref|autoref)\{([^{}]+)\}")
    # Pandoc-style citations ``[@key]`` / ``[@key1; @key2]`` / ``[-@key]``.
    # The PDF path resolves these via ``--citeproc``; the HTML writer leaves them
    # raw, so this web-only pass renders them as readable ``[key1; key2]`` text
    # (mirroring the ``\citep{...}`` handling) instead of emitting literal
    # ``[@key]`` markdown into the rendered page.
    _PANDOC_CITATION_RE = re.compile(r"\[(?P<body>[^\]]*?@[A-Za-z0-9_][^\]]*?)\]")
    _PANDOC_CITEKEY_RE = re.compile(r"-?@([A-Za-z0-9_][A-Za-z0-9_:.#$%&+?<>~/-]*)")
    _PANDOC_CROSSREF_PREFIXES = ("fig:", "tbl:", "sec:", "eq:")
    # Raw-LaTeX theorem-like environments. Pandoc's HTML writer silently DROPS
    # these blocks (the ``\newtheorem`` definitions live in the LaTeX-only
    # preamble), so a manuscript's Theorems/Definitions vanish from the web page.
    # WebRenderer rewrites them (web-only) into numbered ``.theorem-box`` Divs.
    # The display names share one running counter, mirroring the conventional
    # ``\newtheorem{lemma}[theorem]{Lemma}`` shared-counter linkage so the web
    # numbers match the PDF's.
    _THEOREM_ENVS = {
        "theorem": "Theorem",
        "lemma": "Lemma",
        "proposition": "Proposition",
        "corollary": "Corollary",
        "definition": "Definition",
    }
    _THEOREM_BLOCK_RE = re.compile(
        r"\\begin\{(theorem|lemma|proposition|corollary|definition)\}"
        r"(?:\[([^\]]*)\])?[ \t]*\n(.*?)\n\\end\{\1\}",
        re.DOTALL,
    )

    def __init__(self, config: RenderingConfig):
        """Initialize the web renderer with configuration."""
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render markdown to HTML."""
        output_dir = Path(self.config.web_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = self._output_file_for_source(source_file)

        # Apply the same web-only markdown pass used for the combined build so
        # per-section HTML resolves Pandoc ``[@key]`` citations and raw-LaTeX
        # spans instead of emitting them literally (the HTML writer, unlike the
        # citeproc PDF path, leaves them untouched).
        safe_source = source_file.with_suffix(source_file.suffix + ".web.tmp")
        try:
            safe_source.write_text(
                self._html_safe_markdown(source_file.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
        except OSError:
            safe_source = source_file

        cmd = [
            self.config.pandoc_path,
            str(safe_source),
            "-t",
            "html5",
            "-o",
            str(output_file),
            "--standalone",
            "--mathjax",
        ]

        logger.info(f"Generating HTML from {source_file}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            if output_file.exists():
                self._normalize_figure_paths_in_file(output_file)
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render HTML: {e.stderr}",
                context={"source": str(source_file)},
            ) from e
        finally:
            if safe_source != source_file:
                safe_source.unlink(missing_ok=True)

    def _output_file_for_source(self, source_file: Path) -> Path:
        """Return a collision-resistant HTML path for an individual section."""
        output_dir = Path(self.config.web_dir)
        parent_name = source_file.parent.name
        if parent_name and parent_name not in {".", ""}:
            raw_stem = f"{parent_name}__{source_file.stem}"
        else:
            raw_stem = source_file.stem
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", raw_stem).strip("-._") or source_file.stem
        return output_dir / f"{safe_stem}.html"

    def render_combined(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
        """Render multiple markdown files as a combined HTML document.

        Combines all source files, applies CSS styling, and generates a single index.html
        with table of contents and embedded CSS.

        Args:
            source_files: List of markdown files in order
            manuscript_dir: Directory containing manuscript files
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined HTML file (index.html)

        Raises:
            RenderingError: If combination or rendering fails
        """
        logger.info("\n" + "=" * BANNER_WIDTH)
        logger.info("COMBINED HTML RENDERING")
        logger.info("=" * BANNER_WIDTH)
        logger.info(f"Combining {len(source_files)} section(s):")
        for i, md_file in enumerate(source_files, 1):
            size_kb = md_file.stat().st_size / 1024
            logger.info(f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)")

        total_size_kb = sum(f.stat().st_size for f in source_files) / 1024
        logger.info(f"  {'Total input size:':<48} ({total_size_kb:>6.1f} KB)")
        logger.info("=" * BANNER_WIDTH + "\n")

        output_dir = Path(self.config.web_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "index.html"

        # Remove existing output file to ensure fresh generation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")

        # Combine markdown files
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = self._html_safe_markdown(self._combine_markdown_files(source_files))
        _tmp = combined_md.with_suffix(combined_md.suffix + ".tmp")
        try:
            _tmp.write_text(combined_content, encoding="utf-8")
            _tmp.replace(combined_md)
        except OSError:
            _tmp.unlink(missing_ok=True)
            raise
        logger.debug(f"Combined markdown written to: {combined_md} ({len(combined_content)} characters)")

        # Build pandoc command for HTML conversion
        figures_dir = manuscript_dir.parent / "output" / "figures"
        lua_filter = Path(__file__).parent / "convert_latex_images.lua"

        cmd = [
            self.config.pandoc_path,
            str(combined_md),
            "-t",
            "html5",
            "-o",
            str(output_file),
            "--standalone",
            "--mathjax",
            "--toc",
            "--toc-depth=3",
            "--number-sections",
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        ]
        cmd.extend(self._pandoc_metadata_args(manuscript_dir))

        # Add resource paths for figure resolution
        if manuscript_dir.exists():
            cmd.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir.exists():
            cmd.extend(["--resource-path", str(figures_dir)])

        # Add Lua filter for LaTeX image conversion
        if lua_filter.exists():
            cmd.extend(["--lua-filter", str(lua_filter)])

        crossref = shutil.which("pandoc-crossref")
        if crossref:
            cmd.extend(["--filter", crossref])
            logger.info("Using pandoc-crossref at %s for combined HTML", crossref)
        else:
            logger.warning(
                "pandoc-crossref not on PATH; @sec:/@tbl:/@fig:/@eq: will not resolve in combined HTML. "
                "Install: https://github.com/lierdakil/pandoc-crossref (e.g. brew install pandoc-crossref)"
            )

        logger.info("Converting combined markdown to HTML...")
        logger.debug(f"Combined markdown file: {combined_md}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        except subprocess.CalledProcessError as e:
            error_msg = "Failed to convert markdown to HTML"
            all_output = ""
            if e.stderr:
                all_output += f"STDERR:\n{e.stderr}\n"
            if e.stdout:
                all_output += f"STDOUT:\n{e.stdout}\n"

            if all_output:
                error_msg += f"\n\nFull Pandoc output:\n{all_output}"

            raise RenderingError(
                error_msg,
                context={"source": str(combined_md), "target": str(output_file)},
                suggestions=[
                    "Verify all markdown files are valid",
                    "Check for special characters or encoding issues",
                    f"Review Pandoc command: {' '.join(cmd)}",
                ],
            ) from e

        # Embed CSS styling in the generated HTML
        if output_file.exists():
            self._embed_css(output_file)
            self._normalize_figure_paths_in_file(output_file)
            logger.info(f"✓ Embedded CSS styling in {output_file.name}")

        logger.info(f"✅ Generated combined HTML: {output_file.name}")
        return output_file

    @staticmethod
    def _pandoc_metadata_args(manuscript_dir: Path) -> list[str]:
        config_path = manuscript_dir / "config.yaml"
        if not config_path.exists():
            return []
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("Could not read HTML metadata from %s: %s", config_path, exc)
            return []
        if not isinstance(config, dict):
            return []
        paper = config.get("paper") or {}
        if not isinstance(paper, dict):
            return []

        args: list[str] = []
        title = paper.get("title")
        subtitle = paper.get("subtitle")
        if title:
            title_text = str(title)
            args.append(f"--metadata=title:{title_text}")
            args.append(f"--metadata=pagetitle:{title_text}")
        if subtitle:
            args.append(f"--metadata=subtitle:{subtitle}")
        return args

    def _combine_markdown_files(self, source_files: list[Path]) -> str:
        """Combine multiple markdown files into one.

        Args:
            source_files: List of markdown files in order

        Returns:
            Combined markdown content

        Raises:
            RenderingError: If any file cannot be read or contains invalid content
        """
        combined_parts = []

        for i, md_file in enumerate(source_files):
            try:
                # Read with explicit UTF-8 encoding and error handling
                content = md_file.read_text(encoding="utf-8", errors="strict")

                # Validate file ends with newline for proper spacing
                if not content.endswith("\n"):
                    content += "\n"

                # Strip trailing whitespace from each file to avoid double newlines
                # But preserve a single trailing newline
                content = content.rstrip() + "\n"

                # Add file content
                combined_parts.append(content)

                # Add section separator between sections (only if not the last file)
                # For HTML, we use a horizontal rule instead of LaTeX \newpage
                if i < len(source_files) - 1:
                    combined_parts.append("\n---\n\n")

            except UnicodeDecodeError as e:
                raise RenderingError(
                    f"Failed to read markdown file (encoding error): {md_file.name}",
                    context={
                        "file": str(md_file),
                        "error": str(e),
                        "position": i + 1,
                        "total_files": len(source_files),
                    },
                    suggestions=[
                        f"Check file encoding: {md_file}",
                        "Ensure file is UTF-8 encoded",
                        "Remove any non-UTF-8 characters from the file",
                    ],
                ) from e
            except OSError as e:
                raise RenderingError(
                    f"Failed to read markdown file: {md_file.name}",
                    context={
                        "file": str(md_file),
                        "error": str(e),
                        "position": i + 1,
                        "total_files": len(source_files),
                    },
                    suggestions=[
                        f"Verify file exists and is readable: {md_file}",
                        "Check file permissions",
                        "Ensure file is valid markdown",
                    ],
                ) from e

        # Join with newlines, ensuring proper spacing
        combined = "\n\n".join(combined_parts)

        # Ensure the combined content starts cleanly (no leading whitespace issues)
        combined = combined.lstrip("\n\r")

        # Validate that the combined markdown is not empty
        if not combined.strip():
            raise RenderingError(
                "Combined markdown is empty",
                context={
                    "source_files": [str(f) for f in source_files],
                    "file_count": len(source_files),
                },
                suggestions=[
                    "Verify that all source markdown files contain content",
                    "Check file permissions and encoding",
                ],
            )

        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if combined.startswith("\ufeff"):
            logger.warning("Removing UTF-8 BOM from combined markdown")
            combined = combined[1:]

        return combined

    @classmethod
    def _html_safe_markdown(cls, content: str) -> str:
        """Convert PDF-only raw-LaTeX inline spans into readable HTML text.

        The canonical manuscript uses Pandoc raw-LaTeX spans such as
        ``\\citep{...}`` and ``\\hyperref[label]{visible text}`` because those
        are the right primitives for the PDF build.  Pandoc's HTML writer drops
        raw LaTeX, which can turn prose like "NumPy \\citep{...}, SciPy
        \\citep{...}" into "NumPy , SciPy".  This web-only pass preserves the
        visible text while leaving the source manuscript and PDF path unchanged.
        """

        def _citation_text(keys_csv: str) -> str:
            keys = [key.strip() for key in keys_csv.split(",") if key.strip()]
            return "[" + "; ".join(keys) + "]" if keys else ""

        def _visible_ref(label: str) -> str:
            return label.replace("_", " ")

        def _clean_latex_text(text: str) -> str:
            text = text.replace(r"\S", "§")
            text = text.replace(r"\%", "%")
            text = text.replace(r"\&", "&")
            text = text.replace(r"\_", "_")
            text = text.replace(r"~", " ")
            text = text.replace(r"\ ", " ")
            return re.sub(r"\s+", " ", text).strip()

        def _replace_raw_span(match: re.Match[str]) -> str:
            latex = match.group(1).strip()
            latex = cls._HYPERREF_RE.sub(
                lambda m: _clean_latex_text(m.group(1)),
                latex,
            )
            latex = cls._HREF_RE.sub(
                lambda m: _clean_latex_text(m.group(1)),
                latex,
            )
            latex = cls._CITE_RE.sub(
                lambda m: _citation_text(m.group(1)),
                latex,
            )
            latex = cls._LABEL_RE.sub("", latex)
            latex = latex.replace(r"\phantomsection", "")
            latex = cls._REF_RE.sub(lambda m: _visible_ref(m.group(1)), latex)
            return _clean_latex_text(latex)

        # Rewrite raw-LaTeX theorem blocks into numbered Divs BEFORE the inline
        # raw-span pass strips them; the Div body then flows through citation /
        # ref handling like any other prose.
        content = cls._html_theorem_blocks(content)
        content = cls._render_pandoc_citations(content)
        return cls._normalize_figure_paths(cls._RAW_LATEX_INLINE_RE.sub(_replace_raw_span, content))

    @classmethod
    def _html_theorem_blocks(cls, content: str) -> str:
        """Rewrite raw-LaTeX theorem-like environments into numbered ``.theorem-box`` Divs.

        Web-only. Each ``\\begin{theorem}[optional name]...\\end{theorem}`` block (for
        theorem / lemma / proposition / corollary / definition) becomes a Pandoc
        fenced Div ``::: {.theorem-box .<env>}`` led by a bold ``**Theorem N**``
        label (the optional name follows, with its math left outside the bold so it
        renders). The environments share one running counter so the web numbers
        match the PDF's shared-counter convention. The PDF path never sees this —
        it consumes the original ``\\begin{theorem}`` against the LaTeX preamble.
        """
        counter = {"n": 0}

        def _replace(match: re.Match[str]) -> str:
            env, name, body = match.group(1), match.group(2), match.group(3)
            counter["n"] += 1
            label = f"**{cls._THEOREM_ENVS[env]} {counter['n']}**"
            if name and name.strip():
                label += f" ({name.strip()})"
            return f"\n\n::: {{.theorem-box .{env}}}\n{label}. {body.strip()}\n:::\n\n"

        return cls._THEOREM_BLOCK_RE.sub(_replace, content)

    @classmethod
    def _render_pandoc_citations(cls, content: str) -> str:
        """Render Pandoc ``[@key]`` citation groups as readable ``[key]`` text.

        The HTML writer (unlike the citeproc-driven PDF path) leaves Pandoc
        citation syntax untouched, which would surface literal ``[@key]`` markup
        on the page and trip publication validators. Bracket groups that contain
        only bibliographic citekeys are rewritten to ``[key1; key2]``; pandoc-
        crossref keys such as ``[@fig:plot]`` are preserved so the crossref
        filter can resolve them during combined HTML rendering.
        """

        def _replace(match: re.Match[str]) -> str:
            keys = cls._PANDOC_CITEKEY_RE.findall(match.group("body"))
            if not keys:
                return match.group(0)
            if any(key.startswith(cls._PANDOC_CROSSREF_PREFIXES) for key in keys):
                return match.group(0)
            return "[" + "; ".join(keys) + "]"

        return cls._PANDOC_CITATION_RE.sub(_replace, content)

    @staticmethod
    def _normalize_figure_paths(content: str) -> str:
        """Rewrite manuscript figure paths for files emitted under ``output/web``."""
        return (
            content.replace("../../output/figures/", "../figures/")
            .replace("../output/figures/", "../figures/")
            .replace("output/figures/", "../figures/")
        )

    @classmethod
    def _normalize_figure_paths_in_file(cls, html_file: Path) -> None:
        """Normalize figure paths in an emitted HTML file in place."""
        html_content = html_file.read_text(encoding="utf-8")
        normalized = cls._normalize_figure_paths(html_content)
        if normalized == html_content:
            return
        _tmp = html_file.with_suffix(html_file.suffix + ".tmp")
        try:
            _tmp.write_text(normalized, encoding="utf-8")
            _tmp.replace(html_file)
        except OSError:
            _tmp.unlink(missing_ok=True)
            raise

    def _embed_css(self, html_file: Path) -> None:
        """Embed CSS styling directly into HTML file.

        Reads ide_style.css and inserts it into the <head> section of the HTML.

        Args:
            html_file: Path to HTML file to modify
        """
        try:
            # Read CSS file
            css_file = Path(__file__).parent / "ide_style.css"
            if not css_file.exists():
                logger.warning(f"CSS file not found: {css_file}, skipping CSS embedding")
                return

            # Prepend the shared design-token + dark-mode block so the web
            # surface shares one --brand-1 source and a prefers-color-scheme
            # block with the reporting HTML surfaces.
            css_content = _SHARED_DESIGN_TOKENS_CSS + "\n" + css_file.read_text(encoding="utf-8")

            # Read HTML file
            html_content = html_file.read_text(encoding="utf-8")

            # Find </head> tag and insert CSS before it
            if "</head>" in html_content:
                # Create style tag with CSS content
                style_tag = f"\n<style>\n{css_content}\n</style>\n"
                html_content = html_content.replace("</head>", style_tag + "</head>")
            else:
                # If no </head> tag, try to find <head> and insert after it
                if "<head>" in html_content:
                    style_tag = f"<head>\n<style>\n{css_content}\n</style>\n"
                    html_content = html_content.replace("<head>", style_tag, 1)
                else:
                    logger.warning("Could not find <head> tag in HTML, CSS not embedded")
                    return

            # Write modified HTML back
            _tmp = html_file.with_suffix(html_file.suffix + ".tmp")
            try:
                _tmp.write_text(html_content, encoding="utf-8")
                _tmp.replace(html_file)
            except OSError:
                _tmp.unlink(missing_ok=True)
                raise
            logger.debug(f"Embedded CSS from {css_file.name} into {html_file.name}")

        except OSError as e:
            logger.warning(f"Failed to embed CSS: {e}")
            # Don't fail the entire process if CSS embedding fails
