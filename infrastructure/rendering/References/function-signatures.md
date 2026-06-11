## Function Signatures

### core.py

#### RenderManager (class)
```python
class RenderManager:
    """Manages multi-format rendering from a single source."""

    def __init__(self, config: Optional[RenderingConfig] = None,
                 manuscript_dir: Optional[Path] = None, figures_dir: Optional[Path] = None):
        """Initialize render manager.

        Args:
            config: Rendering configuration (optional)
            manuscript_dir: Manuscript directory path (optional)
            figures_dir: Figures directory path (optional)
        """

    def render_all(self, source_file: Path) -> list[Path]:
        """Render to all supported formats.

        Args:
            source_file: Path to source manuscript

        Returns:
            List of generated output paths
        """

    def render_pdf(self, source_file: Path) -> Path:
        """Render to PDF format.

        Args:
            source_file: Path to source manuscript

        Returns:
            Path to generated PDF
        """

    def render_slides(self, source_file: Path, output_format: str = "beamer") -> Path:
        """Render presentation slides.

        Args:
            source_file: Path to source manuscript
            output_format: Slide format ("beamer" or "revealjs")

        Returns:
            Path to generated slides
        """

    def render_web(self, source_file: Path) -> Path:
        """Render to web HTML format.

        Args:
            source_file: Path to source manuscript

        Returns:
            Path to generated HTML
        """

    def render_combined_pdf(self, source_files: List[Path], manuscript_dir: Path, project_name: str = "project") -> Path:
        """Render combined PDF from multiple markdown files.

        Args:
            source_files: List of markdown files in order to combine
            manuscript_dir: Directory containing manuscript files (for preamble/bib)
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined PDF file
        """

    def render_combined_web(self, source_files: List[Path], manuscript_dir: Path, project_name: str = "project") -> Path:
        """Render combined HTML from multiple markdown files.

        Args:
            source_files: List of markdown files in order to combine
            manuscript_dir: Directory containing manuscript files
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined HTML file (index.html)
        """
```

### pdf_renderer.py

#### _parse_missing_package_error (function)
```python
def _parse_missing_package_error(log_file: Path) -> Optional[str]:
    """Parse LaTeX log for missing package errors.

    Args:
        log_file: Path to LaTeX compilation log

    Returns:
        Missing package name if found, None otherwise
    """
```

#### PDFRenderer (class)
```python
class PDFRenderer:
    """Handles PDF rendering via LaTeX compilation."""

    def __init__(self, config: Optional[RenderingConfig] = None):
        """Initialize PDF renderer.

        Args:
            config: Rendering configuration
        """

    def render(self, source_path: Path) -> Path:
        """Render manuscript to PDF.

        Args:
            source_path: Path to source manuscript

        Returns:
            Path to generated PDF
        """

    def render_combined_pdf(self, manuscript_files: List[Path], manuscript_dir: Path) -> Path:
        """Render combined manuscript PDF.

        Args:
            manuscript_files: List of manuscript files to combine
            manuscript_dir: Directory containing manuscript files

        Returns:
            Path to generated combined PDF
        """
```

### manuscript_discovery.py

#### verify_figures_exist (function)
```python
def verify_figures_exist(project_root: Path, manuscript_dir: Path) -> Dict[str, Any]:
    """Verify that all figures referenced in manuscript exist.

    Args:
        project_root: Project root directory
        manuscript_dir: Manuscript directory

    Returns:
        Dictionary with verification results
    """
```

#### discover_manuscript_files (function)
```python
def discover_manuscript_files(manuscript_dir: Path) -> List[Path]:
    """Discover all manuscript files in directory.

    Args:
        manuscript_dir: Manuscript directory

    Returns:
        List of manuscript file paths
    """
```

### manuscript_injection.py

Shared `{{TOKEN}}` substitution utility. All three template projects delegate to these functions so the regex, excluded-file logic, and unresolved-token behaviour are identical across projects.

#### EXCLUDED_DOC_FILENAMES (constant)
```python
EXCLUDED_DOC_FILENAMES: frozenset[str] = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
```
Files that contain literal `{{TOKEN}}` examples and must never be substituted or copied to `output/manuscript/`.

#### substitute_manuscript_text (function)
```python
def substitute_manuscript_text(
    text: str,
    variables: dict[str, str],
) -> tuple[str, list[str]]:
    """Replace {{TOKEN}} markers in text.

    Returns:
        (resolved_text, [unresolved_key, ...])
    """
```
Only tokens matching `\{\{([A-Z][A-Z0-9_]*)\}\}` are replaced; Mermaid labels like `{{For each keyword}}` and glob patterns like `{{CONFIG_*}}` never match.

#### write_resolved_manuscript_tree (function)
```python
def write_resolved_manuscript_tree(
    project_root: Path | str,
    variables: dict[str, str],
) -> Path:
    """Write output/manuscript/ from manuscript/*.md with substitutions.

    - Excludes EXCLUDED_DOC_FILENAMES from output
    - Copies config.yaml and *.bib verbatim
    - Returns the output/manuscript/ Path
    """
```

### web_renderer.py

#### WebRenderer (class)
```python
class WebRenderer:
    """Handles web HTML rendering with MathJax."""

    def __init__(self, config: Optional[RenderingConfig] = None):
        """Initialize web renderer.

        Args:
            config: Rendering configuration
        """

    def render(self, source_path: Path) -> Path:
        """Render manuscript to web HTML.

        Args:
            source_path: Path to source manuscript

        Returns:
            Path to generated HTML
        """

    def render_combined(self, source_files: List[Path], manuscript_dir: Path, project_name: str = "project") -> Path:
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

    def _combine_markdown_files(self, source_files: List[Path]) -> str:
        """Combine multiple markdown files into one.

        Args:
            source_files: List of markdown files in order

        Returns:
            Combined markdown content

        Raises:
            RenderingError: If any file cannot be read or contains invalid content
        """

    def _embed_css(self, html_file: Path) -> None:
        """Embed CSS styling directly into HTML file.

        Reads ide_style.css and inserts it into the <head> section of the HTML.

        Args:
            html_file: Path to HTML file to modify
        """
```

### slides_renderer.py

#### SlidesRenderer (class)
```python
class SlidesRenderer:
    """Handles presentation slide rendering."""

    def __init__(self, config: Optional[RenderingConfig] = None):
        """Initialize slides renderer.

        Args:
            config: Rendering configuration
        """

    def render(self, source_path: Path, output_format: str = "beamer") -> Path:
        """Render manuscript to presentation slides.

        Args:
            source_path: Path to source manuscript
            output_format: Slide format ("beamer" or "revealjs")

        Returns:
            Path to generated slides
        """

    def _render_beamer_with_paths(self, source_file: Path, output_file: Path,
                                   manuscript_dir: Optional[Path], figures_dir: Optional[Path]) -> Path:
        """Render beamer slides with error reporting.

        error handling includes:
        - LaTeX log file path and last 20 lines for context
        - Specific error type detection (missing \end, undefined commands, missing files)
        - Actionable suggestions for common LaTeX compilation issues
        - Better context for debugging compilation failures

        Args:
            source_file: Markdown source file
            output_file: Desired PDF output path
            manuscript_dir: Manuscript directory for resource paths
            figures_dir: Figures directory for image paths

        Returns:
            Path to generated PDF

        Raises:
            RenderingError: With error context and suggestions
        """
```

### _pdf_latex_helpers.py

Preamble extraction, Unicode math font injection, and log-parse delegates. Title-page generation lives in [`_pdf_title_page.py`](../_pdf_title_page.py).

#### extract_preamble (function)
```python
def extract_preamble(preamble_file: Path) -> str:
    """Extract LaTeX preamble from a markdown ```latex ...``` fence.

    When the extracted preamble loads ``unicode-math`` without a
    ``\\setmathfont``, a default ``\\setmathfont{latinmodern-math.otf}``
    is auto-appended (see :func:`ensure_setmathfont`) so prose math
    glyphs (e.g. ``\\mid``, ``\\ll``, ``\\gg``) render through a math
    font instead of falling back to lmroman.
    """
```

#### ensure_setmathfont (function)
```python
def ensure_setmathfont(preamble: str, math_font: str = "latinmodern-math.otf") -> str:
    """Append a default ``\\setmathfont`` when ``unicode-math`` is loaded
    without one. No-op when ``unicode-math`` is absent or the user already
    declared a ``\\setmathfont`` (any font, any options). Returns the
    preamble string unchanged in those cases."""
```

### Combined PDF helpers (`_pdf_combined_*.py`)

`PDFRenderer.render_combined()` delegates to focused modules (re-exported from
`_pdf_combined_renderer.py` for backward compatibility):

| Module | Role |
| --- | --- |
| `_pdf_combined_markdown.py` | Mermaid, figure paths, dotted-key `manuscript_vars.yaml` substitution (`{{maturity.real}}`, etc.) — not UPPER_SNAKE project tokens (see `manuscript_injection.py`) |
| `_pdf_combined_pandoc.py` | Pandoc CLI construction and subprocess execution |
| `_pdf_combined_latex.py` | Starred-heading hyperref repair, post-Pandoc LaTeX normalisation |
| `_pdf_combined_preamble.py` | `preamble.md` + title page injection (via `_pdf_title_page.py`) |
| `_pdf_combined_bibliography.py` | Multi-`.bib` discovery and `\bibliography{}` placement |
| `_pdf_combined_prevalidate.py` | Figure reference checks, markdown/citation hard gate |
| `_pdf_combined_transmission.py` | Transmission bookend TOC relocation helpers |

### prevalidate_source_markdown (function — `_pdf_combined_prevalidate.py`)
```python
def prevalidate_source_markdown(
    source: Path | list[Path] | list[str],
    repo_root: Path | None = None,
    bib_file: str | Path | list[str | Path] | None = None,
) -> None:
    """Hard-gate the combined-PDF render on source-markdown integrity.

    Runs validate_pandoc_pitfalls (bare ``|word|``, ``\\|`` in tables) and
    validate_citations (every ``[@key]`` resolves in the manuscript ``*.bib``
    union, or in an explicit ``bib_file`` path/list when supplied) over
    the actual source files about to be rendered. Both classes of finding
    are promoted to render-blockers — pitfall warnings materialise
    downstream as silent ``Missing character`` warnings + ``U+FFFD`` glyphs
    in the PDF, exactly the failure mode this gate exists to prevent.

    Raises:
        RenderingError: when any blocker is found, with file path and line
            range for every occurrence so the editor can jump straight to
            the problem in the source markdown.
    """
```

### fix_starred_section_nameref_labels (function — `_pdf_combined_latex.py`)
```python
def fix_starred_section_nameref_labels(tex_content: str) -> tuple[str, int]:
    """Repair hyperref anchors and ``\\nameref`` titles for starred headings.

    Inserts ``\\phantomsection`` before ``\\label`` on ``\\section*`` /
    ``\\subsection*`` / ``\\subsubsection*`` so TOC links do not resolve to
    ``Doc-Start``. When titlesec is loaded, also sets ``\\@currentlabelname`` so
    ``\\nameref{sec:...}`` resolves on unnumbered surfaces.
    """
```

### Per-format preamble & gate coverage

| Renderer | `extract_preamble` / `ensure_setmathfont` | `prevalidate_source_markdown` | Lua filters |
|----------|-------------------------------------------|-------------------------------|-------------|
| `PDFRenderer.render_combined` (xelatex)    | ✅ full preamble via `inject_latex_preamble` | ✅ runs before Pandoc | — |
| `SlidesRenderer.render` (Beamer)           | ✅ math fonts only via `extract_math_font_preamble` (`-H _slides_math_header.tex`) | ❌ single-section scope | ✅ `_beamer_allowframebreaks.lua` |
| `SlidesRenderer.render` (Reveal.js)        | ❌ N/A (HTML output)                 | ❌ HTML tolerates Unicode | — |
| `WebRenderer` (HTML)                       | ❌ N/A (no LaTeX preamble)           | ❌ HTML tolerates Unicode | — |

`SlidesRenderer` invokes Pandoc directly, so the *full* combined-PDF
preamble (geometry, hyperref, titlepage) is intentionally bypassed —
those packages would clash with Beamer's document class. Only the
math-font subset is propagated, via
[`extract_math_font_preamble`](../_pdf_latex_helpers.py) and
`SlidesRenderer._maybe_write_math_header`, which write a minimal
`_slides_math_header.tex` next to the slide deck and pass it to Pandoc
through `-H header.tex`. This gives slides the same `\mid` / `\ll` /
`\gg` rendering as the combined PDF without the rest of the preamble.

The pre-render gate is also skipped because slides typically render a
single section in isolation with a different acceptable-citation set
than the full manuscript.

#### Beamer overflow handling

Pandoc's Beamer writer wraps each section in a single
`\begin{frame}…\end{frame}`. When a markdown source has long sections
without h2 sub-breaks the resulting frame can overflow its vbox by
thousands of points; xelatex then aborts with driver code 256 and
leaves a 15-byte PDF stub on disk. `SlidesRenderer._render_beamer_with_paths`
defends against this on two complementary axes:

1. **`--slide-level=2`**: forces every h2 heading to start its own frame
   (h1 becomes a section divider). A single h1 with several h2
   subsections renders as several slides instead of one massive
   overflowing frame.
2. **`--lua-filter _beamer_allowframebreaks.lua`**: the filter tags
   every h1/h2 with the `allowframebreaks` class, so Pandoc emits
   `\begin{frame}[allowframebreaks]` and Beamer splits any remaining
   long h2 across slides automatically.

The Lua filter is applied defensively (only when the file is present),
so removing it falls back to the previous behaviour without breaking
the renderer.

### latex_utils.py

#### ensure_pdf_at (function)
```python
def ensure_pdf_at(compiled: Path, target: Path) -> Path:
    """Move *compiled* to *target* when LaTeX wrote a different filename.

    Returns:
        *target* after any rename.
    """
```

#### compile_latex (function)
```python
def compile_latex(
    tex_file: Path | str,
    output_dir: Path | str | None = None,
    compiler: str = "xelatex",
    timeout: int = 300,
    passes: int = 2,
) -> Path:
    """Compile LaTeX document with multiple passes.

    Args:
        tex_file: Path to LaTeX source file
        output_dir: Directory for output files
        compiler: LaTeX compiler to use
        timeout: Timeout in seconds per pass
        passes: Number of compilation passes

    Returns:
        Path to generated PDF ({tex_stem}.pdf under output_dir)
    """
```

### latex_package_validator.py

#### PackageStatus (class)
```python
class PackageStatus(NamedTuple):
    """Status of a LaTeX package check."""
    package: str
    available: bool
    version: Optional[str] = None
    error: Optional[str] = None
```

#### ValidationReport (class)
```python
class ValidationReport:
    """Report of LaTeX package validation."""
    checked_packages: List[str]
    available_packages: List[str]
    missing_packages: List[str]
    errors: List[str]

    def summary(self) -> str:
        """Generate validation summary."""

    def install_commands(self) -> str:
        """Generate installation commands for missing packages."""
```

#### find_kpsewhich (function)
```python
def find_kpsewhich() -> Optional[Path]:
    """Find kpsewhich executable.

    Returns:
        Path to kpsewhich if found, None otherwise
    """
```

#### check_latex_package (function)
```python
def check_latex_package(package_name: str, kpsewhich_path: Optional[Path] = None) -> PackageStatus:
    """Check if LaTeX package is available.

    Args:
        package_name: Name of LaTeX package to check
        kpsewhich_path: Path to kpsewhich executable

    Returns:
        PackageStatus with availability information
    """
```

#### validate_packages (function)
```python
def validate_packages(
    required_packages: Optional[List[str]] = None,
    kpsewhich_path: Optional[Path] = None
) -> ValidationReport:
    """Validate all required LaTeX packages.

    Args:
        required_packages: List of packages to check (uses defaults if None)
        kpsewhich_path: Path to kpsewhich executable

    Returns:
        ValidationReport with results
    """
```

#### get_missing_packages_command (function)
```python
def get_missing_packages_command(missing: List[str]) -> str:
    """Generate command to install missing packages.

    Args:
        missing: List of missing package names

    Returns:
        Installation command string
    """
```

#### validate_preamble_packages (function)
```python
def validate_preamble_packages(strict: bool = False) -> ValidationReport:
    """Validate packages required by manuscript preamble.

    Args:
        strict: Enable strict validation mode

    Returns:
        ValidationReport for preamble packages
    """
```

#### main (function)
```python
def main():
    """Main function for LaTeX package validation CLI."""
```

### config.py

#### RenderingConfig (class)
```python
class RenderingConfig:
    """Configuration for rendering operations."""

    def __init__(
        self,
        latex_compiler: str = "xelatex",
        pandoc_path: str = "pandoc",
        output_dir: Path = Path("output"),
        max_compilation_passes: int = 4,
        validate_packages: bool = True
    ):
        """Initialize rendering configuration.

        Args:
            latex_compiler: LaTeX compiler command
            pandoc_path: Path to pandoc executable
            output_dir: Root output directory
            max_compilation_passes: Maximum LaTeX compilation passes
            validate_packages: Whether to validate LaTeX packages
        """
```

### cli.py

#### render_pdf_command (function)
```python
def render_pdf_command(args):
    """CLI command for PDF rendering.

    Args:
        args: Parsed command line arguments
    """
```

#### render_all_command (function)
```python
def render_all_command(args):
    """CLI command for rendering all formats.

    Args:
        args: Parsed command line arguments
    """
```

#### render_slides_command (function)
```python
def render_slides_command(args):
    """CLI command for slide rendering.

    Args:
        args: Parsed command line arguments
    """
```

#### render_web_command (function)
```python
def render_web_command(args):
    """CLI command for web rendering.

    Args:
        args: Parsed command line arguments
    """
```

#### main (function)
```python
def main():
    """Main CLI entry point for rendering tools."""
```

### render_all_cli.py

#### main (function)
```python
def main():
    """Main function for render all CLI."""
```
