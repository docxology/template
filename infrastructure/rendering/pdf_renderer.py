"""PDF Rendering module."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, List
import yaml

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


class PDFRenderer:
    """Handles PDF generation logic."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path, output_name: Optional[str] = None) -> Path:
        """Render manuscript to PDF.
        
        This assumes source_file is a LaTeX file or Markdown file to be converted.
        For this implementation, we focus on LaTeX compilation.
        """
        if source_file.suffix == '.tex':
            return compile_latex(
                source_file,
                Path(self.config.pdf_dir),
                compiler=self.config.latex_compiler
            )
        
        # Use Markdown rendering for .md files
        if source_file.suffix == '.md':
            return self.render_markdown(source_file)
        
        logger.warning(f"Unsupported format for direct rendering: {source_file.suffix}")
        return Path("")

    def render_markdown(self, source_file: Path, output_name: Optional[str] = None) -> Path:
        """Render a single markdown file to PDF using Pandoc.
        
        Args:
            source_file: Path to markdown file
            output_name: Optional custom output filename
            
        Returns:
            Path to generated PDF file
            
        Raises:
            RenderingError: If Pandoc rendering fails
        """
        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / (output_name or f"{source_file.stem}.pdf")
        
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-o", str(output_file),
            "--pdf-engine=xelatex",
            "--standalone"
        ]
        
        logger.info(f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render markdown to PDF: {e.stderr}",
                context={"source": str(source_file), "target": str(output_file)}
            )

    def render_combined(self, source_files: List[Path], manuscript_dir: Path) -> Path:
        """Render multiple markdown files as a combined PDF.
        
        Combines all source files, applies preamble, and generates a single PDF.
        
        Args:
            source_files: List of markdown files in order
            manuscript_dir: Directory containing manuscript files
            
        Returns:
            Path to generated combined PDF
            
        Raises:
            RenderingError: If combination or rendering fails
        """
        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "project_combined.pdf"
        
        # Check if bibliography exists
        bib_file = manuscript_dir / "references.bib"
        bib_exists = bib_file.exists()
        
        # Create temporary combined LaTeX file from combined markdown
        combined_tex = output_dir / "_combined_manuscript.tex"
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = self._combine_markdown_files(source_files)
        combined_md.write_text(combined_content)
        
        # Convert combined markdown to LaTeX using Pandoc
        # This handles raw LaTeX commands properly
        pandoc_to_tex = [
            self.config.pandoc_path,
            str(combined_md),
            "-o", str(combined_tex),
            "--from=markdown",
            "--to=latex",
            "--number-sections",
            "--toc"
        ]
        
        # Add bibliography if it exists
        if bib_exists:
            pandoc_to_tex.extend([
                "--bibliography=" + str(bib_file),
                "--citeproc"
            ])
        
        # Add resource paths for figure resolution
        figures_dir = manuscript_dir.parent / "output" / "figures"
        pandoc_to_tex.extend([
            "--resource-path=" + str(manuscript_dir),
            "--resource-path=" + str(figures_dir)
        ])
        
        logger.info(f"Converting combined markdown to LaTeX...")
        
        try:
            subprocess.run(pandoc_to_tex, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to convert markdown to LaTeX: {e.stderr}",
                context={"source": str(combined_md), "target": str(combined_tex)}
            )
        
        # Read and process LaTeX content
        tex_content = combined_tex.read_text()
        
        # Fix figure paths for LaTeX compilation
        tex_content = self._fix_figure_paths(tex_content, manuscript_dir, output_dir)
        
        # Extract and apply preamble directly to LaTeX
        preamble_file = manuscript_dir / "preamble.md"
        preamble_content = ""
        if preamble_file.exists():
            preamble_content = self._extract_preamble(preamble_file)
        
        # Generate title page from config.yaml
        title_page_content = self._generate_title_page_latex(manuscript_dir)
        
        if preamble_content or title_page_content:
            # Insert preamble and title page into LaTeX file
            begin_doc_idx = tex_content.find("\\begin{document}")
            if begin_doc_idx > 0:
                # Build combined preamble content
                combined_preamble = ""
                if preamble_content:
                    combined_preamble += preamble_content + "\n\n"
                if title_page_content:
                    combined_preamble += title_page_content + "\n\n"
                
                # Insert before \begin{document}
                tex_content = (
                    tex_content[:begin_doc_idx] +
                    combined_preamble +
                    tex_content[begin_doc_idx:]
                )
        
        combined_tex.write_text(tex_content)
        
        # Now compile LaTeX to PDF using xelatex
        cmd = [
            "xelatex",
            "-interaction=nonstopmode",
            "-output-directory=" + str(output_dir),
            str(combined_tex)
        ]
        
        logger.info(f"Rendering combined manuscript to PDF: {output_file.name}")
        logger.info(f"  Source files: {len(source_files)}")
        if bib_exists:
            logger.info(f"  Bibliography: {bib_file.name}")
        
        try:
            # Run xelatex multiple passes for proper cross-references, TOC, and bibliography
            # Up to 4 passes: 1st = initial, 2nd/3rd = cross-refs, 4th = final checks
            max_passes = 4
            for run in range(max_passes):
                logger.info(f"  LaTeX compilation pass {run+1}/{max_passes}...")
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                
                # Check for critical errors
                if "Fatal error occurred" in result.stdout or result.returncode > 1:
                    if output_file.exists():
                        logger.warning(f"⚠️  PDF generated but with warnings (run {run+1})")
                        break
                    else:
                        # Only fail if it's the first run or critical error
                        if run == 0 or "!" in result.stdout:
                            raise RenderingError(
                                f"XeLaTeX compilation failed (run {run+1})",
                                context={"source": str(combined_tex), "output": str(output_file)}
                            )
                
                # Check log file for unresolved references or TOC changes
                log_file = output_dir / "_combined_manuscript.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    # If no warnings/issues found, we can stop early
                    if run > 0 and "Rerun" not in log_content and "undefined" not in log_content.lower():
                        logger.info(f"  All references resolved after pass {run+1}")
                        break
            
            # Check if the temporary PDF was created and rename it
            temp_pdf = output_dir / "_combined_manuscript.pdf"
            if temp_pdf.exists():
                # Rename temporary PDF to final name
                temp_pdf.rename(output_file)
                logger.info(f"✅ Successfully generated: {output_file.name}")
                # Clean up temporary files
                combined_md.unlink(missing_ok=True)
                combined_tex.unlink(missing_ok=True)
                (output_dir / "_combined_manuscript.log").unlink(missing_ok=True)
                return output_file
            elif output_file.exists():
                logger.info(f"✅ Successfully generated: {output_file.name}")
                # Clean up temporary files
                combined_md.unlink(missing_ok=True)
                combined_tex.unlink(missing_ok=True)
                (output_dir / "_combined_manuscript.log").unlink(missing_ok=True)
                return output_file
            else:
                raise RenderingError(
                    f"PDF file was not created",
                    context={"source": str(combined_tex), "output": str(output_file)}
                )
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to compile LaTeX to PDF: {e.stderr or e.stdout}",
                context={"source": str(combined_tex), "output": str(output_file)}
            )

    def _combine_markdown_files(self, source_files: List[Path]) -> str:
        """Combine multiple markdown files into one.
        
        Args:
            source_files: List of markdown files in order
            
        Returns:
            Combined markdown content
        """
        combined_parts = []
        
        for i, md_file in enumerate(source_files):
            content = md_file.read_text()
            # Add file content
            combined_parts.append(content)
            # Add page break between sections
            if i < len(source_files) - 1:
                combined_parts.append("\n\\newpage\n")
        
        return "\n".join(combined_parts)

    def _extract_preamble(self, preamble_file: Path) -> str:
        """Extract LaTeX preamble from markdown file.
        
        Looks for content between ```latex and ``` blocks.
        
        Args:
            preamble_file: Path to preamble.md file
            
        Returns:
            LaTeX preamble content or empty string if not found
        """
        content = preamble_file.read_text()
        
        # Look for ```latex ... ``` blocks
        import re
        pattern = r'```latex\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Combine all latex blocks
            return "\n".join(matches)
        
        return ""

    def _fix_figure_paths(self, tex_content: str, manuscript_dir: Path, output_dir: Path) -> str:
        """Fix figure paths in LaTeX content for proper compilation.
        
        Converts relative paths like ../output/figures/ to paths relative to the
        LaTeX compilation directory, ensuring \includegraphics commands work correctly.
        
        Args:
            tex_content: LaTeX content to process
            manuscript_dir: Directory containing manuscript files
            output_dir: Output directory where LaTeX is compiled
            
        Returns:
            LaTeX content with corrected figure paths
        """
        import re
        
        # Pattern to match \includegraphics{...}
        pattern = r'\\includegraphics\{([^}]+)\}'
        
        def fix_path(match):
            old_path = match.group(1)
            
            # If path contains ../output/figures/, resolve it
            if '../output/figures/' in old_path:
                # Extract just the filename
                filename = old_path.split('../output/figures/')[-1]
                # Return path relative to compilation directory
                # Since we're compiling in output_dir (which is output/pdf), figures are in ../figures/
                new_path = f'../figures/{filename}'
                return f'\\includegraphics{{{new_path}}}'
            
            # If path is already absolute or relative correctly, return as-is
            return match.group(0)
        
        # Apply path fixes
        tex_content = re.sub(pattern, fix_path, tex_content)
        
        return tex_content

    def _generate_title_page_latex(self, manuscript_dir: Path) -> str:
        """Generate LaTeX title page from config.yaml metadata.
        
        Args:
            manuscript_dir: Directory containing manuscript files and config.yaml
            
        Returns:
            LaTeX code for title page, or empty string if config not found
        """
        config_file = manuscript_dir / "config.yaml"
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return ""
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return ""
            
            # Extract metadata
            paper = config.get('paper', {})
            authors = config.get('authors', [])
            
            title = paper.get('title', 'Research Paper')
            date = paper.get('date', '')
            
            # Build title page LaTeX
            title_page_lines = [
                "\\maketitle",
                "%% Generated title page from config.yaml",
                "\\thispagestyle{empty}",
                f"\\title{{{title}}}",
            ]
            
            # Add authors
            if authors:
                author_names = [f["name"] for f in authors if "name" in f]
                if author_names:
                    author_str = " \\and ".join(author_names)
                    title_page_lines.append(f"\\author{{{author_str}}}")
            
            # Add date if specified
            if date:
                title_page_lines.append(f"\\date{{{date}}}")
            else:
                title_page_lines.append("\\date{\\today}")
            
            return "\n".join(title_page_lines)
            
        except Exception as e:
            logger.warning(f"Error reading config.yaml: {e}")
            return ""

