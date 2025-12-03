"""PDF Rendering module."""
from __future__ import annotations

import subprocess
import unicodedata
import re
from pathlib import Path
from typing import Optional, List
import yaml

from infrastructure.core.logging_utils import get_logger, log_progress_bar
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
        
        SECURITY AND COMPATIBILITY CONSIDERATIONS:
        
        BibTeX operates in "paranoid" mode by default (openout_any=p) which restricts
        file access across directories. This causes two issues:
        
        1. Bibliography File Access: BibTeX cannot read the bibliography file if it's
           in a different directory than the LaTeX compilation directory. Solution: Copy
           the bibliography file into the compilation directory before running bibtex.
        
        2. Output File Restrictions: BibTeX refuses to write to the .blg (log) file
           in directories other than the compilation directory. This is a security
           restriction and is not critical - the bibliography still gets processed
           correctly even though the log file isn't written.
        
        COMPILATION WORKFLOW:
        - The .aux file (auxiliary) contains citation references from the LaTeX document
        - BibTeX reads the .aux file to find what citations are needed
        - BibTeX reads the .bib file to find the bibliography entries
        - BibTeX writes a .bbl file with formatted bibliography entries
        - LaTeX then includes the .bbl file in the final document
        
        Args:
            tex_file: Path to the LaTeX file
            output_dir: Directory containing LaTeX auxiliary files
            bib_file: Path to bibliography file
            
        Returns:
            True if bibliography processing succeeded, False otherwise
        """
        # Check if bibliography file exists with fallback logging
        try:
            if not bib_file.exists():
                logger.warning(f"Bibliography file not found: {bib_file}")
                return False
        except UnboundLocalError:
            if not bib_file.exists():
                print(f"WARNING: Bibliography file not found: {bib_file}")
                return False

        # Determine which bibliography processor to use
        bibtex_cmd = "bibtex"
        aux_file = output_dir / f"{tex_file.stem}.aux"

        # Check if auxiliary file exists with fallback logging
        try:
            if not aux_file.exists():
                logger.warning(f"Auxiliary file not found: {aux_file}")
                return False
        except UnboundLocalError:
            if not aux_file.exists():
                print(f"WARNING: Auxiliary file not found: {aux_file}")
                return False
        
        try:
            # Copy bibliography file to output directory to avoid bibtex paranoid mode issues
            # This allows bibtex to access the bibliography file without security restrictions
            local_bib = output_dir / bib_file.name
            import shutil
            shutil.copy2(str(bib_file), str(local_bib))
            try:
                logger.debug(f"Copied bibliography file to: {local_bib}")
            except UnboundLocalError:
                print(f"DEBUG: Copied bibliography file to: {local_bib}")

            # Run bibtex to generate bibliography
            # Important: bibtex must be invoked with a filename relative to the
            # working directory (not an absolute path), otherwise it will refuse
            # to write auxiliary files in paranoid mode. Since we set cwd to the
            # output directory, pass only the aux filename.
            cmd = [bibtex_cmd, aux_file.name]
            try:
                logger.info(f"Processing bibliography with {bibtex_cmd}...")
            except UnboundLocalError:
                print(f"INFO: Processing bibliography with {bibtex_cmd}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir)
            )

            try:
                if result.returncode != 0:
                    logger.warning(f"Bibliography processing warning: {result.stderr[:200]}")
                    # Don't fail on warnings - bibtex often returns non-zero for minor issues
            except UnboundLocalError:
                if result.returncode != 0:
                    print(f"WARNING: Bibliography processing warning: {result.stderr[:200]}")

            try:
                logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
            except UnboundLocalError:
                print(f"DEBUG: ✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
            return True
            
        except Exception as e:
            # Use a fallback logging approach if logger is not accessible
            try:
                logger.warning(f"Bibliography processing failed: {e}")
            except UnboundLocalError:
                # Fallback if logger is not accessible in this scope
                print(f"WARNING: Bibliography processing failed: {e}")
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
        
        # Remove existing output file to ensure fresh compilation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")
        
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
            "--toc",
            "--natbib"  # Use natbib for bibliography support with BibTeX
        ]
        
        # Note: We do NOT use --citeproc here because we want to preserve LaTeX \cite{}
        # commands for BibTeX processing. Using --citeproc would have pandoc process
        # citations directly, bypassing BibTeX. Instead, we let BibTeX handle citations
        # during the LaTeX compilation phase (see _process_bibliography() below).
        # The --natbib flag ensures that LaTeX \cite{} commands are properly formatted.
        
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
            if preamble_content:
                logger.info(f"✓ Extracted preamble from {preamble_file.name}")
            else:
                logger.warning(f"⚠️  Preamble file found but no LaTeX content extracted")
        else:
            logger.debug(f"No preamble file found at {preamble_file}")
        
        # Generate title page preamble and body commands from config.yaml
        title_page_preamble = self._generate_title_page_preamble(manuscript_dir)
        title_page_body = self._generate_title_page_body(manuscript_dir)
        
        # Ensure graphicx package is always included (required for \includegraphics)
        # Check preamble_content (from preamble.md), not tex_content (Pandoc output)
        graphicx_required = r'\usepackage{graphicx}'
        if preamble_content and graphicx_required not in preamble_content:
            logger.info("⚠️  graphicx package not found in preamble, adding it")
            preamble_content = graphicx_required + "\n" + preamble_content
        elif not preamble_content:
            # No preamble at all, ensure graphicx is included
            logger.info("⚠️  No preamble found, adding graphicx package")
            preamble_content = graphicx_required
        
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
                logger.debug(f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}")
        
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
                
                # Try both normalized and non-normalized paths
                fig_normalized = figures_dir / unicodedata.normalize('NFC', filename)
                
                if fig_path.exists():
                    found_figures.append(filename)
                    logger.debug(f"  ✓ Found: {filename}")
                elif fig_normalized.exists():
                    found_figures.append(filename)
                    logger.debug(f"  ✓ Found (normalized): {filename}")
                else:
                    missing_figures.append(filename)
                    logger.warning(f"  ✗ Missing: {filename}")
                    # Check if file exists with similar name
                    if figures_dir.exists():
                        similar = [f.name for f in figures_dir.iterdir() 
                                  if f.name.lower().startswith(filename.split('.')[0].lower())]
                        if similar:
                            logger.debug(f"    Similar files found: {', '.join(similar)}")
            
            logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
            if missing_figures:
                logger.warning(f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}")
                if len(missing_figures) > 5:
                    logger.warning(f"  ... and {len(missing_figures) - 5} more missing figures")
        
        # Now compile LaTeX to PDF using xelatex
        # IMPORTANT: 
        # 1. -shell-escape is required for XeTeX to properly determine PNG image
        #    dimensions. Without this flag, XeTeX cannot read PNG bounding box information
        #    and will produce "Division by 0" errors when including graphics.
        # 2. We run xelatex from the output directory (cwd=output_dir) rather than using
        #    -output-directory flag. This is because the tex file contains relative paths
        #    like "../figures/file.png" which must be resolved relative to the compilation
        #    directory. Using -output-directory would resolve paths from the current working
        #    directory instead, causing figure loading failures.
        cmd = [
            "xelatex",
            "-interaction=nonstopmode",
            "-shell-escape",
            combined_tex.name  # Just the filename, since we set cwd to output_dir
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
            
            # Temporary PDF file created during compilation (before renaming to final output)
            temp_pdf = output_dir / "_combined_manuscript.pdf"
            
            logger.info(f"  LaTeX compilation pass 1/4...")
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(output_dir))
            
            # Check for critical errors on first pass
            # Note: Use temp_pdf (not output_file) since output_file is created by renaming temp_pdf
            if "Fatal error occurred" in result.stdout or (result.returncode > 1 and not temp_pdf.exists()):
                raise RenderingError(
                    f"XeLaTeX compilation failed (pass 1)",
                    context={"source": str(combined_tex), "output": str(output_file)}
                )
            
            # Process bibliography if it exists
            if bib_exists:
                logger.info(f"  Bibliography processing...")
                try:
                    self._process_bibliography(combined_tex, output_dir, bib_file)
                except Exception as bib_error:
                    logger.warning(f"  Bibliography processing failed: {bib_error}")
                    logger.warning("  Continuing PDF generation without bibliography processing")
                    # Don't fail the entire PDF generation for bibliography issues
            
            # Additional passes for reference resolution (especially after bibtex)
            max_passes = 4
            for run in range(1, max_passes):
                log_progress_bar(run+1, max_passes, "LaTeX compilation", width=20)
                result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(output_dir))
                
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
                                context={"source": str(combined_tex), "output": str(output_file)},
                                suggestions=[
                                    "Check LaTeX log file for detailed error messages",
                                    "Verify all required packages are installed (check graphicx, biblatex, etc.)",
                                    "Ensure figure paths are correct relative to output directory",
                                    "Run with --verbose flag for detailed compilation output"
                                ]
                            )
                
                # Check log file for unresolved references or TOC changes
                log_file = output_dir / "_combined_manuscript.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    # If no warnings/issues found, we can stop early
                    if "Rerun" not in log_content and "undefined" not in log_content.lower():
                        logger.info(f"  All references resolved after pass {run+1}")
                        break
                    
                    # Check for graphics-specific issues
                    if run == max_passes - 1:  # Last pass
                        graphics_issues = self._check_latex_log_for_graphics_errors(log_file)
                        if graphics_issues["graphics_errors"]:
                            for error in graphics_issues["graphics_errors"]:
                                logger.warning(f"  Graphics error: {error}")
                        if graphics_issues["missing_files"]:
                            for missing in graphics_issues["missing_files"]:
                                logger.warning(f"  Missing file: {missing}")
                        if graphics_issues["graphics_warnings"]:
                            for warning in graphics_issues["graphics_warnings"]:
                                logger.warning(f"  Graphics warning: {warning[:100]}...")
            
            # Check if the temporary PDF was created and rename it
            if temp_pdf.exists():
                # Rename temporary PDF to final name
                temp_pdf.rename(output_file)
                logger.info(f"✅ Successfully generated: {output_file.name}")
                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
                return output_file
            elif output_file.exists():
                logger.info(f"✅ Successfully generated: {output_file.name}")
                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
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
        Handles various markdown code fence formats.
        
        Args:
            preamble_file: Path to preamble.md file
            
        Returns:
            LaTeX preamble content or empty string if not found
        """
        try:
            content = preamble_file.read_text()
        except Exception as e:
            logger.warning(f"Failed to read preamble file: {e}")
            return ""
        
        # Look for ```latex ... ``` blocks (handles various line ending styles)
        import re
        # Pattern handles different line endings and optional whitespace
        pattern = r'```\s*latex\s*\n(.*?)\n\s*```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Combine all latex blocks
            preamble_lines = [match.strip() for match in matches]
            result = "\n".join(preamble_lines)
            logger.debug(f"Extracted {len(matches)} LaTeX preamble block(s) ({len(result)} chars)")
            return result
        else:
            logger.debug(f"No LaTeX code blocks found in {preamble_file.name}")
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
        else:
            # No paths fixed - check if there are any figure references at all
            if pattern and re.search(pattern, tex_content):
                logger.debug("No figure paths needed fixing (already in correct format)")
        
        return tex_content

    def _check_latex_log_for_graphics_errors(self, log_file: Path) -> dict:
        """Parse LaTeX log file for graphics-related errors and warnings.
        
        Args:
            log_file: Path to LaTeX .log file
            
        Returns:
            Dictionary with graphics issues found
        """
        result = {
            "graphics_errors": [],
            "graphics_warnings": [],
            "missing_files": []
        }
        
        if not log_file.exists():
            return result
        
        try:
            log_content = log_file.read_text(errors='ignore')
            
            # Look for common graphics-related error patterns
            import re
            
            # Pattern for file not found errors
            file_not_found = re.findall(r'File `([^`]+)` not found', log_content)
            result["missing_files"].extend(file_not_found)
            
            # Pattern for graphics package warnings
            graphics_warnings = re.findall(
                r'((?:Package graphics|Graphics Error).*?)(?=\n(?:!|\s*$))',
                log_content,
                re.IGNORECASE
            )
            result["graphics_warnings"].extend(graphics_warnings)
            
            # Check for undefined control sequences related to graphics
            if r'\includegraphics' in log_content and 'Undefined' in log_content:
                result["graphics_errors"].append(
                    "includegraphics command undefined - graphicx package may not be loaded"
                )
            
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing LaTeX log: {e}")
            return result

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

