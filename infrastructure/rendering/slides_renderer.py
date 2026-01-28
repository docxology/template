"""Slides rendering module."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


class SlidesRenderer:
    """Handles slide generation (Beamer/Reveal.js)."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(
        self,
        source_file: Path,
        format: str = "beamer",
        manuscript_dir: Optional[Path] = None,
        figures_dir: Optional[Path] = None,
    ) -> Path:
        """Render slides from markdown with figure path resolution.

        Args:
            source_file: Path to markdown file
            format: Output format ("beamer" for PDF, "revealjs" for HTML)
            manuscript_dir: Directory containing manuscript (for resource paths)
            figures_dir: Directory containing figures (for resource paths)

        Returns:
            Path to generated slides file

        Raises:
            RenderingError: If rendering fails
        """
        output_dir = Path(self.config.slides_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_ext = "pdf" if format == "beamer" else "html"
        output_file = output_dir / f"{source_file.stem}_slides.{output_ext}"

        # For beamer, we need to handle figure paths specially
        if format == "beamer":
            return self._render_beamer_with_paths(
                source_file, output_file, manuscript_dir, figures_dir
            )
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
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render slides: {e.stderr}",
                context={"source": str(source_file), "format": "revealjs"},
            )

    def _render_beamer_with_paths(
        self,
        source_file: Path,
        output_file: Path,
        manuscript_dir: Optional[Path],
        figures_dir: Optional[Path],
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

        # Build pandoc command to convert markdown to LaTeX
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t",
            "beamer",
            "-o",
            str(temp_tex),
            "--standalone",
        ]

        # Add resource paths if provided
        if manuscript_dir:
            cmd.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir:
            cmd.extend(["--resource-path", str(figures_dir)])

        logger.info(f"Generating beamer slides from {source_file}")

        try:
            # Convert markdown to LaTeX
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Read LaTeX content and fix figure paths
            tex_content = temp_tex.read_text()

            # Fix figure paths for LaTeX compilation
            if figures_dir:
                tex_content = self._fix_figure_paths(
                    tex_content, output_dir, figures_dir
                )

            # Write fixed LaTeX back
            temp_tex.write_text(tex_content)

            # Compile LaTeX to PDF
            compile_latex(temp_tex, output_dir, compiler=self.config.latex_compiler)

            # Check if PDF was created
            if output_file.exists():
                logger.info(f"Generated beamer slides: {output_file.name}")
                return output_file
            else:
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
                    recent_errors = "\n".join(
                        line for line in last_lines if line.strip()
                    )

                    # Detect specific error types
                    error_hints = []
                    if "*** (job aborted, no legal \\end found)" in log_content:
                        error_hints.append(
                            "LaTeX document structure error: missing \\end{document} or unmatched \\begin{}/\\end{} pairs"
                        )
                    if "Undefined control sequence" in log_content:
                        error_hints.append(
                            "Undefined LaTeX command - check for typos in LaTeX syntax"
                        )
                    if "File `" in log_content and "not found" in log_content:
                        error_hints.append(
                            "Missing file reference - check figure paths and bibliography files"
                        )

                    error_msg += (
                        f"\n\nLaTeX Compilation Log ({log_file}):\n{recent_errors}"
                    )

                    if error_hints:
                        error_msg += f"\n\nPossible Issues:\n" + "\n".join(
                            f"- {hint}" for hint in error_hints
                        )

                    error_msg += f"\n\nSuggestions:\n- Check LaTeX log file: {log_file}\n- Verify LaTeX syntax in generated .tex file: {temp_tex}\n- Ensure all referenced figures exist\n- Check for missing LaTeX packages"

                except Exception as log_error:
                    error_msg += f"\n\nCould not read LaTeX log file: {log_error}"

            raise RenderingError(
                error_msg,
                context={
                    "source": str(source_file),
                    "format": "beamer",
                    "log_file": str(log_file) if log_file.exists() else None,
                },
            )

    def _fix_figure_paths(
        self, tex_content: str, output_dir: Path, figures_dir: Path
    ) -> str:
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
        # Pattern to match \includegraphics with or without options
        # Handles both \includegraphics{path} and \includegraphics[options]{path}
        pattern = r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}"

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
                return path_str

        def fix_path(match: re.Match) -> str:
            r"""Fix a single includegraphics path to be relative to the slides compilation directory.

            Transforms figure paths from various formats (absolute, manuscript-relative,
            etc.) to paths relative to the LaTeX compilation directory (output/slides/).
            Preserves any optional parameters like width, height, or scale specifications.

            Args:
                match: Regular expression match object containing:
                    - group(1): Optional parameters in square brackets (e.g., width=0.8\\textwidth)
                    - group(2): The figure path within braces

            Returns:
                The corrected \\includegraphics command with path relative to ../figures/
                and any optional parameters preserved.
            """
            options = match.group(1)  # Optional [options] parameter
            old_path = match.group(2)  # Path in braces

            # Check if already in correct format
            if old_path.startswith("../figures/"):
                return match.group(0)

            # Extract filename from various path formats
            filename = extract_filename(old_path)

            # Build new path relative to compilation directory
            # Since we're compiling in output_dir (output/slides), figures are in ../figures/
            new_path = f"../figures/{filename}"

            # Reconstruct command with optional parameters preserved
            if options:
                return f"\\includegraphics[{options}]{{{new_path}}}"
            else:
                return f"\\includegraphics{{{new_path}}}"

        # Apply path fixes
        tex_content = re.sub(pattern, fix_path, tex_content)

        return tex_content
