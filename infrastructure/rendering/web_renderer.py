"""Web/HTML rendering module."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig

logger = get_logger(__name__)


class WebRenderer:
    """Handles HTML generation."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path) -> Path:
        """Render markdown to HTML."""
        output_dir = Path(self.config.web_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{source_file.stem}.html"
        
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-t", "html5",
            "-o", str(output_file),
            "--standalone",
            "--mathjax"
        ]
        
        logger.info(f"Generating HTML from {source_file}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render HTML: {e.stderr}",
                context={"source": str(source_file)}
            )

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
        logger.info("\n" + "="*60)
        logger.info("COMBINED HTML RENDERING")
        logger.info("="*60)
        logger.info(f"Combining {len(source_files)} section(s):")
        for i, md_file in enumerate(source_files, 1):
            size_kb = md_file.stat().st_size / 1024
            logger.info(f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)")

        total_size_kb = sum(f.stat().st_size for f in source_files) / 1024
        logger.info(f"  {'Total input size:':<48} ({total_size_kb:>6.1f} KB)")
        logger.info("="*60 + "\n")

        output_dir = Path(self.config.web_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "index.html"

        # Remove existing output file to ensure fresh generation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")

        # Combine markdown files
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = self._combine_markdown_files(source_files)
        combined_md.write_text(combined_content, encoding='utf-8')
        logger.debug(f"Combined markdown written to: {combined_md} ({len(combined_content)} characters)")

        # Build pandoc command for HTML conversion
        figures_dir = manuscript_dir.parent / "output" / "figures"
        lua_filter = Path(__file__).parent / "convert_latex_images.lua"

        cmd = [
            self.config.pandoc_path,
            str(combined_md),
            "-t", "html5",
            "-o", str(output_file),
            "--standalone",
            "--mathjax",
            "--toc",
            "--toc-depth=3",
            "--number-sections",
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        ]

        # Add resource paths for figure resolution
        if manuscript_dir.exists():
            cmd.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir.exists():
            cmd.extend(["--resource-path", str(figures_dir)])

        # Add Lua filter for LaTeX image conversion
        if lua_filter.exists():
            cmd.extend(["--lua-filter", str(lua_filter)])

        logger.info(f"Converting combined markdown to HTML...")
        logger.debug(f"Combined markdown file: {combined_md}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to convert markdown to HTML"
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
                    f"Review Pandoc command: {' '.join(cmd)}"
                ]
            )

        # Embed CSS styling in the generated HTML
        if output_file.exists():
            self._embed_css(output_file)
            logger.info(f"✓ Embedded CSS styling in {output_file.name}")

        logger.info(f"✅ Generated combined HTML: {output_file.name}")
        return output_file

    def _combine_markdown_files(self, source_files: List[Path]) -> str:
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
                content = md_file.read_text(encoding='utf-8', errors='strict')

                # Validate file ends with newline for proper spacing
                if not content.endswith('\n'):
                    content += '\n'

                # Strip trailing whitespace from each file to avoid double newlines
                # But preserve a single trailing newline
                content = content.rstrip() + '\n'

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
                        "total_files": len(source_files)
                    },
                    suggestions=[
                        f"Check file encoding: {md_file}",
                        "Ensure file is UTF-8 encoded",
                        "Remove any non-UTF-8 characters from the file"
                    ]
                )
            except Exception as e:
                raise RenderingError(
                    f"Failed to read markdown file: {md_file.name}",
                    context={
                        "file": str(md_file),
                        "error": str(e),
                        "position": i + 1,
                        "total_files": len(source_files)
                    },
                    suggestions=[
                        f"Verify file exists and is readable: {md_file}",
                        "Check file permissions",
                        "Ensure file is valid markdown"
                    ]
                )

        # Join with newlines, ensuring proper spacing
        combined = "\n\n".join(combined_parts)

        # Ensure the combined content starts cleanly (no leading whitespace issues)
        combined = combined.lstrip('\n\r')

        # Validate that the combined markdown is not empty
        if not combined.strip():
            raise RenderingError(
                "Combined markdown is empty",
                context={
                    "source_files": [str(f) for f in source_files],
                    "file_count": len(source_files)
                },
                suggestions=[
                    "Verify that all source markdown files contain content",
                    "Check file permissions and encoding"
                ]
            )

        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if combined.startswith('\ufeff'):
            logger.warning("Removing UTF-8 BOM from combined markdown")
            combined = combined[1:]

        return combined

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

            css_content = css_file.read_text(encoding='utf-8')

            # Read HTML file
            html_content = html_file.read_text(encoding='utf-8')

            # Find </head> tag and insert CSS before it
            if '</head>' in html_content:
                # Create style tag with CSS content
                style_tag = f'\n<style>\n{css_content}\n</style>\n'
                html_content = html_content.replace('</head>', style_tag + '</head>')
            else:
                # If no </head> tag, try to find <head> and insert after it
                if '<head>' in html_content:
                    style_tag = f'<head>\n<style>\n{css_content}\n</style>\n'
                    html_content = html_content.replace('<head>', style_tag, 1)
                else:
                    logger.warning("Could not find <head> tag in HTML, CSS not embedded")
                    return

            # Write modified HTML back
            html_file.write_text(html_content, encoding='utf-8')
            logger.debug(f"Embedded CSS from {css_file.name} into {html_file.name}")

        except Exception as e:
            logger.warning(f"Failed to embed CSS: {e}")
            # Don't fail the entire process if CSS embedding fails