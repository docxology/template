"""PDF Rendering module."""
from __future__ import annotations

import subprocess
import unicodedata
import re
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
        
        # Build resource paths to help pandoc find figures
        resource_paths = []
        manuscript_dir = Path(self.config.manuscript_dir)
        figures_dir = Path(self.config.figures_dir)
        
        if manuscript_dir.exists():
            resource_paths.extend(["--resource-path", str(manuscript_dir)])
        if figures_dir.exists():
            resource_paths.extend(["--resource-path", str(figures_dir)])
        
        cmd = [
            self.config.pandoc_path,
            str(source_file),
            "-o", str(output_file),
            "--pdf-engine=xelatex",
            "--standalone"
        ]
        
        # Add resource paths
        cmd.extend(resource_paths)
        
        logger.info(f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render markdown to PDF: {e.stderr}",
                context={"source": str(source_file), "target": str(output_file)}
            )

    def _process_bibliography(self, tex_file: Path, output_dir: Path, bib_file: Path) -> bool:
        """Process bibliography using bibtex/biber.
        
        Args:
            tex_file: Path to the LaTeX file
            output_dir: Directory containing LaTeX auxiliary files
            bib_file: Path to bibliography file
            
        Returns:
            True if bibliography processing succeeded, False otherwise
        """
        if not bib_file.exists():
            logger.warning(f"Bibliography file not found: {bib_file}")
            return False
        
        # Determine which bibliography processor to use
        bibtex_cmd = "bibtex"
        aux_file = output_dir / f"{tex_file.stem}.aux"
        
        if not aux_file.exists():
            logger.warning(f"Auxiliary file not found: {aux_file}")
            return False
        
        try:
            # Run bibtex to generate bibliography
            cmd = [bibtex_cmd, str(aux_file)]
            logger.info(f"Processing bibliography with {bibtex_cmd}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir)
            )
            
            if result.returncode != 0:
                logger.warning(f"Bibliography processing warning: {result.stderr[:200]}")
                # Don't fail on warnings - bibtex often returns non-zero for minor issues
            
            logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
            return True
            
        except Exception as e:
            logger.warning(f"Bibliography processing failed: {e}")
            return False

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
        # --standalone: Create a complete LaTeX document with document class and preamble
        pandoc_to_tex = [
            self.config.pandoc_path,
            str(combined_md),
            "-o", str(combined_tex),
            "--from=markdown",
            "--to=latex",
            "--standalone",
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
        
        # Generate title page preamble and body commands from config.yaml
        title_page_preamble = self._generate_title_page_preamble(manuscript_dir)
        title_page_body = self._generate_title_page_body(manuscript_dir)
        
        if preamble_content or title_page_preamble:
            # Insert preamble and title page preamble commands BEFORE \begin{document}
            begin_doc_idx = tex_content.find("\\begin{document}")
            if begin_doc_idx > 0:
                # Build combined preamble content
                combined_preamble = ""
                if preamble_content:
                    combined_preamble += preamble_content + "\n\n"
                if title_page_preamble:
                    combined_preamble += title_page_preamble + "\n\n"
                
                # Insert before \begin{document}
                tex_content = (
                    tex_content[:begin_doc_idx] +
                    combined_preamble +
                    tex_content[begin_doc_idx:]
                )
        
        # Insert title page body commands AFTER \begin{document}
        if title_page_body:
            begin_doc_idx = tex_content.find("\\begin{document}")
            if begin_doc_idx > 0:
                # Find position right after \begin{document}
                end_of_begin_doc = tex_content.find("\n", begin_doc_idx) + 1
                if end_of_begin_doc > begin_doc_idx:
                    # Insert \maketitle and formatting after \begin{document}
                    tex_content = (
                        tex_content[:end_of_begin_doc] +
                        "\n" + title_page_body + "\n\n" +
                        tex_content[end_of_begin_doc:]
                    )
                    logger.info(r"✓ Inserted title page (\maketitle) after \begin{document}")
        
        combined_tex.write_text(tex_content)
        
        # Verify figure files exist before compilation
        figures_dir = manuscript_dir.parent / "output" / "figures"
        import re
        fig_pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        referenced_figures = re.findall(fig_pattern, tex_content)
        
        if referenced_figures:
            logger.info(f"Verifying {len(referenced_figures)} figure reference(s)...")
            missing_figures = []
            found_figures = []
            
            for fig_ref in referenced_figures:
                # Extract filename from path
                filename = fig_ref.split('/')[-1]
                fig_path = figures_dir / filename
                
                if fig_path.exists():
                    found_figures.append(filename)
                    logger.debug(f"  ✓ Found: {filename}")
                else:
                    missing_figures.append(filename)
                    logger.warning(f"  ✗ Missing: {filename}")
            
            logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
            if missing_figures:
                logger.warning(f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures)}")
        
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
            # Run xelatex with bibliography processing for proper cross-references, TOC, and bibliography
            # Pass 1: Initial xelatex compilation
            # Pass 2: Bibtex processing (if bibliography exists)
            # Pass 3-4: Additional xelatex passes for reference resolution
            
            logger.info(f"  LaTeX compilation pass 1/4...")
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            
            # Check for critical errors on first pass
            if "Fatal error occurred" in result.stdout or (result.returncode > 1 and not output_file.exists()):
                raise RenderingError(
                    f"XeLaTeX compilation failed (pass 1)",
                    context={"source": str(combined_tex), "output": str(output_file)}
                )
            
            # Process bibliography if it exists
            if bib_exists:
                logger.info(f"  Bibliography processing...")
                self._process_bibliography(combined_tex, output_dir, bib_file)
            
            # Additional passes for reference resolution (especially after bibtex)
            max_passes = 4
            for run in range(1, max_passes):
                logger.info(f"  LaTeX compilation pass {run+1}/{max_passes}...")
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                
                # Check for critical errors
                if "Fatal error occurred" in result.stdout or result.returncode > 1:
                    if output_file.exists():
                        logger.warning(f"⚠️  PDF generated but with warnings (run {run+1})")
                        break
                    else:
                        # Only fail on critical errors after first pass
                        if "!" in result.stdout:
                            raise RenderingError(
                                f"XeLaTeX compilation failed (run {run+1})",
                                context={"source": str(combined_tex), "output": str(output_file)}
                            )
                
                # Check log file for unresolved references or TOC changes
                log_file = output_dir / "_combined_manuscript.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    # If no warnings/issues found, we can stop early
                    if "Rerun" not in log_content and "undefined" not in log_content.lower():
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
        r"""Fix figure paths in LaTeX content for proper compilation.
        
        Converts relative paths like ../output/figures/ to paths relative to the
        LaTeX compilation directory, ensuring \includegraphics commands work correctly.
        
        The LaTeX compiler runs from output/pdf/, so figures in output/figures/
        should be referenced as ../figures/filename.png
        
        Args:
            tex_content: LaTeX content to process
            manuscript_dir: Directory containing manuscript files
            output_dir: Output directory where LaTeX is compiled (typically output/pdf/)
            
        Returns:
            LaTeX content with corrected figure paths
        """
        # Pattern to match \includegraphics with or without options
        # Handles both \includegraphics{path} and \includegraphics[options]{path}
        pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        
        figures_dir = manuscript_dir.parent / "output" / "figures"
        fixed_count = 0
        paths_fixed = []
        
        def normalize_path(path_str: str) -> str:
            """Normalize path to handle Unicode and encoding issues."""
            # Normalize Unicode characters using NFC (composition form)
            normalized = unicodedata.normalize('NFC', path_str)
            return normalized
        
        def extract_filename(path_str: str) -> str:
            """Extract filename from various path formats."""
            # Normalize first
            path_str = normalize_path(path_str)
            
            # Handle various path formats
            path_variations = [
                '../output/figures/',
                'output/figures/',
                '../figures/',
                './figures/',
            ]
            
            for prefix in path_variations:
                if prefix in path_str:
                    return path_str.split(prefix)[-1]
            
            # If no prefix matched, could be just a filename or absolute path
            if '/' in path_str or '\\' in path_str:
                # Split by last / or \
                return re.split(r'[/\\]', path_str)[-1]
            else:
                # Just a filename
                return path_str
        
        def fix_path(match):
            nonlocal fixed_count
            
            old_path = match.group(1)
            original_path = old_path
            
            # Check if already in correct format
            if old_path.startswith('../figures/'):
                return match.group(0)
            
            # Extract filename, handling encoding issues
            filename = extract_filename(old_path)
            
            # Build new path relative to compilation directory
            # Since we're compiling in output_dir (output/pdf), figures are in ../figures/
            new_path = f'../figures/{filename}'
            
            # Verify the figure file exists (try both normalized and non-normalized)
            fig_full_path = figures_dir / filename
            fig_normalized = figures_dir / normalize_path(filename)
            
            file_exists = fig_full_path.exists() or fig_normalized.exists()
            
            if file_exists:
                fixed_count += 1
                paths_fixed.append(f"{original_path} → {new_path}")
                # Preserve options if present
                full_match = match.group(0)
                if '[' in full_match:
                    # Extract options
                    options_start = full_match.find('[')
                    options_end = full_match.find(']')
                    options = full_match[options_start:options_end+1]
                    return f'\\includegraphics{options}{{{new_path}}}'
                else:
                    return f'\\includegraphics{{{new_path}}}'
            else:
                logger.warning(f"⚠️  Figure file not found: {fig_full_path}")
                fixed_count += 1
                paths_fixed.append(f"{original_path} → {new_path} (FILE NOT FOUND)")
                # Still return fixed path so compilation continues
                full_match = match.group(0)
                if '[' in full_match:
                    options_start = full_match.find('[')
                    options_end = full_match.find(']')
                    options = full_match[options_start:options_end+1]
                    return f'\\includegraphics{options}{{{new_path}}}'
                else:
                    return f'\\includegraphics{{{new_path}}}'
        
        # Apply path fixes
        tex_content = re.sub(pattern, fix_path, tex_content)
        
        if fixed_count > 0:
            logger.info(f"✓ Fixed {fixed_count} figure path(s)")
            for path_info in paths_fixed[:10]:  # Show first 10
                logger.debug(f"  {path_info}")
            if len(paths_fixed) > 10:
                logger.debug(f"  ... and {len(paths_fixed) - 10} more")
        
        return tex_content

    def _generate_title_page_preamble(self, manuscript_dir: Path) -> str:
        """Generate LaTeX title page preamble commands from config.yaml metadata.
        
        These commands (\\title, \\author, \\date) must be in the preamble
        (before \\begin{document}).
        
        Args:
            manuscript_dir: Directory containing manuscript files and config.yaml
            
        Returns:
            LaTeX preamble commands for title page, or empty string if config not found
        """
        config_file = manuscript_dir / "config.yaml"
        
        if not config_file.exists():
            logger.debug(f"Config file not found: {config_file}")
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
            subtitle = paper.get('subtitle', '')
            date = paper.get('date', '')
            
            # Build preamble commands (must be before \begin{document})
            preamble_lines = [
                f"\\title{{{title}}}",
            ]
            
            # Add subtitle if present
            if subtitle:
                preamble_lines[-1] = f"\\title{{{title}\\\\\\normalsize {subtitle}}}"
            
            # Add authors with proper formatting
            if authors:
                author_names = [f["name"] for f in authors if "name" in f]
                if author_names:
                    author_str = " \\and ".join(author_names)
                    preamble_lines.append(f"\\author{{{author_str}}}")
            
            # Add date if specified, otherwise use \today
            if date:
                preamble_lines.append(f"\\date{{{date}}}")
            else:
                preamble_lines.append("\\date{\\today}")
            
            logger.debug(f"Generated title page preamble with {len(preamble_lines)} commands")
            return "\n".join(preamble_lines)
            
        except Exception as e:
            logger.warning(f"Error reading config.yaml: {e}")
            return ""

    def _generate_title_page_body(self, manuscript_dir: Path) -> str:
        """Generate LaTeX title page body command from config.yaml metadata.
        
        The \\maketitle command must be called AFTER \\begin{document}.
        
        Args:
            manuscript_dir: Directory containing manuscript files and config.yaml
            
        Returns:
            LaTeX \\maketitle command with proper formatting, or empty string if config not found
        """
        config_file = manuscript_dir / "config.yaml"
        
        if not config_file.exists():
            return ""
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return ""
            
            # Build body commands (must be after \begin{document})
            body_lines = [
                "\\maketitle",
                "\\thispagestyle{empty}",
            ]
            
            logger.debug(f"Generated title page body with {len(body_lines)} commands")
            return "\n".join(body_lines)
            
        except Exception as e:
            logger.warning(f"Error reading config.yaml: {e}")
            return ""

