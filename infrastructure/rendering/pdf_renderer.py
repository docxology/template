"""PDF Rendering module."""

from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path
from typing import List, Optional

import yaml

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging_utils import get_logger, log_progress_bar
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)


def _parse_missing_package_error(log_file: Path) -> Optional[str]:
    """Parse LaTeX log for missing package errors.

    Args:
        log_file: Path to LaTeX .log file

    Returns:
        Name of missing package, or None if no package error found
    """
    if not log_file.exists():
        return None

    try:
        log_content = log_file.read_text(encoding="utf-8", errors="ignore")

        # Look for "File `*.sty' not found" pattern
        import re

        match = re.search(r"File `([^']+\.sty)' not found", log_content)
        if match:
            sty_file = match.group(1)
            # Extract package name (remove .sty extension)
            package_name = sty_file.replace(".sty", "")
            return package_name

        # Also check for the "! LaTeX Error: File *.sty not found" pattern
        match = re.search(
            r"! LaTeX Error: File `?([^'`\s]+\.sty)'? not found", log_content
        )
        if match:
            sty_file = match.group(1)
            package_name = sty_file.replace(".sty", "")
            return package_name

    except Exception as e:
        logger.debug(f"Error parsing log file for package errors: {e}")

    return None


class PDFRenderer:
    """Handles PDF generation logic."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path, output_name: Optional[str] = None) -> Path:
        """Render manuscript to PDF.

        This assumes source_file is a LaTeX file or Markdown file to be converted.
        For this implementation, we focus on LaTeX compilation.
        """
        if source_file.suffix == ".tex":
            return compile_latex(
                source_file,
                Path(self.config.pdf_dir),
                compiler=self.config.latex_compiler,
            )

        # Use Markdown rendering for .md files
        if source_file.suffix == ".md":
            return self.render_markdown(source_file)

        logger.warning(f"Unsupported format for direct rendering: {source_file.suffix}")
        return Path("")

    def render_markdown(
        self, source_file: Path, output_name: Optional[str] = None
    ) -> Path:
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
            "-o",
            str(output_file),
            "--pdf-engine=xelatex",
            "--standalone",
        ]

        # Add resource paths
        cmd.extend(resource_paths)

        logger.info(
            f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}"
        )

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render markdown to PDF: {e.stderr}",
                context={"source": str(source_file), "target": str(output_file)},
            )

    def _process_bibliography(
        self, tex_file: Path, output_dir: Path, bib_file: Path
    ) -> bool:
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
                logger.warning(
                    f"Bibliography file not found: {bib_file} (bibliography processing will be skipped)"
                )
                return False
        except UnboundLocalError:
            if not bib_file.exists():
                logger.warning(
                    f"Bibliography file not found: {bib_file} (bibliography processing will be skipped)"
                )
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
                logger.warning(f"Auxiliary file not found: {aux_file}")
                return False

        try:
            # Copy bibliography file to output directory to avoid bibtex paranoid mode issues
            # This allows bibtex to access the bibliography file without security restrictions
            local_bib = output_dir / bib_file.name
            import shutil

            shutil.copy2(str(bib_file), str(local_bib))
            logger.debug(f"Copied bibliography file to: {local_bib}")

            # Run bibtex to generate bibliography
            # Important: bibtex must be invoked with a filename relative to the
            # working directory (not an absolute path), otherwise it will refuse
            # to write auxiliary files in paranoid mode. Since we set cwd to the
            # output directory, pass only the aux filename.
            cmd = [bibtex_cmd, aux_file.name]
            logger.info(f"Processing bibliography with {bibtex_cmd}...")

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(output_dir)
            )

            if result.returncode != 0 and result.stderr.strip():
                logger.warning(
                    f"Bibliography processing warning: {result.stderr[:200]}"
                )
                # Don't fail on warnings - bibtex often returns non-zero for minor issues

            logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
            return True

        except Exception as e:
            logger.warning(f"Bibliography processing failed: {e}", exc_info=True)
            return False

    def render_combined(
        self,
        source_files: List[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:
        """Render multiple markdown files as a combined PDF.

        Combines all source files, applies preamble, and generates a single PDF.

        Args:
            source_files: List of markdown files in order
            manuscript_dir: Directory containing manuscript files
            project_name: Name of the project for filename generation

        Returns:
            Path to generated combined PDF

        Raises:
            RenderingError: If combination or rendering fails
        """

        # NEW: Log sections being combined
        logger.info("\n" + "=" * 60)
        logger.info("COMBINED MANUSCRIPT RENDERING")
        logger.info("=" * 60)
        logger.info(f"Combining {len(source_files)} section(s):")
        for i, md_file in enumerate(source_files, 1):
            size_kb = md_file.stat().st_size / 1024
            logger.info(
                f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)"
            )

        total_size_kb = sum(f.stat().st_size for f in source_files) / 1024
        logger.info(f"  {'Total input size:':<48} ({total_size_kb:>6.1f} KB)")
        logger.info("=" * 60 + "\n")

        output_dir = Path(self.config.pdf_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use only the project basename for the output filename (not the full qualified path)
        # For nested projects like "cognitive_integrity/cogsec_multiagent_1_theory",
        # extract just "cogsec_multiagent_1_theory" for the filename
        project_basename = Path(project_name).name
        output_file = output_dir / f"{project_basename}_combined.pdf"

        # Remove existing output file to ensure fresh compilation
        if output_file.exists():
            output_file.unlink()
            logger.debug(f"Removed existing output file: {output_file.name}")

        # Check if bibliography exists (prefer references.bib, fallback to 99_references.bib)
        bib_file = manuscript_dir / "references.bib"
        if not bib_file.exists():
            bib_file = manuscript_dir / "99_references.bib"
        bib_exists = bib_file.exists()

        # Create temporary combined LaTeX file from combined markdown
        combined_tex = output_dir / "_combined_manuscript.tex"
        combined_md = output_dir / "_combined_manuscript.md"
        combined_content = self._combine_markdown_files(source_files)
        # Write with explicit UTF-8 encoding
        combined_md.write_text(combined_content, encoding="utf-8")
        logger.debug(
            f"Combined markdown written to: {combined_md} ({len(combined_content)} characters)"
        )

        # Convert combined markdown to LaTeX using Pandoc
        # This handles raw LaTeX commands properly
        # --standalone: Create a complete LaTeX document with document class and preamble
        pandoc_to_tex = [
            self.config.pandoc_path,
            str(combined_md),
            "-o",
            str(combined_tex),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",  # Preserve LaTeX math, raw blocks, and header attributes like {#sec:...}
            "--to=latex",
            "--standalone",
            "--number-sections",
            # "--toc",  # Managed manually in manuscript for precise placement
            "--natbib",  # Use natbib for bibliography support with BibTeX
        ]

        # Note: We do NOT use --citeproc here because we want to preserve LaTeX \cite{}
        # commands for BibTeX processing. Using --citeproc would have pandoc process
        # citations directly, bypassing BibTeX. Instead, we let BibTeX handle citations
        # during the LaTeX compilation phase (see _process_bibliography() below).
        # The --natbib flag ensures that LaTeX \cite{} commands are properly formatted.

        # Add resource paths for figure resolution
        figures_dir = manuscript_dir.parent / "output" / "figures"
        pandoc_to_tex.extend(
            [
                "--resource-path=" + str(manuscript_dir),
                "--resource-path=" + str(figures_dir),
            ]
        )

        logger.info(f"Converting combined markdown to LaTeX...")
        logger.debug(f"Combined markdown file: {combined_md}")

        # Pre-validate combined markdown for common issues
        validation_errors = []
        md_content = ""
        if combined_md.exists():
            try:
                md_content = combined_md.read_text(encoding="utf-8")
                import re

                # Validate basic markdown structure
                # Check for common syntax issues that Pandoc might complain about
                # Validate section header attributes syntax {#sec:...}
                # Check for properly formatted header attributes
                # Note: Pandoc attributes may include extra options like width=95%
                # Pattern captures only the ID part (up to first space or end)
                header_attr_pattern = r"\{#([a-zA-Z0-9_:.-]+)"
                header_attrs = re.findall(header_attr_pattern, md_content)
                for attr in header_attrs:
                    # Check for balanced braces in the attribute itself
                    if attr.count("{") != attr.count("}"):
                        validation_errors.append(
                            f"Unbalanced braces in section header attribute: {{#{attr}}}"
                        )
                    # ID portion is already validated by the regex pattern itself
                    # No need for separate character check - pattern only captures valid chars


                # Check for unmatched opening braces in header attributes
                # Pattern: # Header {#sec:name} - should have balanced braces
                header_lines = re.findall(r"^#+\s+.*\{#.*$", md_content, re.MULTILINE)
                for header_line in header_lines:
                    # Count braces in header line
                    open_braces = header_line.count("{")
                    close_braces = header_line.count("}")
                    if open_braces != close_braces:
                        validation_errors.append(
                            f"Unbalanced braces in header line: {header_line[:80]}"
                        )

                # NOTE: We intentionally do NOT check for unbalanced parentheses
                # inside LaTeX commands. The regex pattern only captures partial
                # command content (e.g., first argument of \frac{}{} or \text{}),
                # leading to false positives for valid LaTeX expressions like:
                # - H(\mathcal{F}_c) in \frac{H(\mathcal{F}_c)}{...}
                # - (\cref{sec:omega4}) in \text{... (\cref{sec:omega4})}
                # LaTeX has its own comprehensive error reporting during compilation.


                # Check for unmatched braces in markdown (outside code blocks)
                # Remove code blocks first
                content_for_brace_check = re.sub(
                    r"```.*?```", "", md_content, flags=re.DOTALL
                )
                content_for_brace_check = re.sub(
                    r"`[^`]+`", "", content_for_brace_check
                )

                # Count braces (but ignore LaTeX commands which use braces)
                # Simple check: count { and } outside LaTeX commands
                brace_count = 0
                in_latex_cmd = False
                for i, char in enumerate(content_for_brace_check):
                    if char == "\\" and i < len(content_for_brace_check) - 1:
                        # Check if this is a LaTeX command start
                        next_char = content_for_brace_check[i + 1]
                        if next_char.isalpha():
                            in_latex_cmd = True
                            # Skip to end of command
                            j = i + 2
                            while (
                                j < len(content_for_brace_check)
                                and content_for_brace_check[j].isalpha()
                            ):
                                j += 1
                            # Skip optional arguments and required argument
                            if j < len(content_for_brace_check):
                                if content_for_brace_check[j] == "[":
                                    # Skip optional argument
                                    depth = 1
                                    j += 1
                                    while (
                                        j < len(content_for_brace_check) and depth > 0
                                    ):
                                        if content_for_brace_check[j] == "[":
                                            depth += 1
                                        elif content_for_brace_check[j] == "]":
                                            depth -= 1
                                        j += 1
                                if (
                                    j < len(content_for_brace_check)
                                    and content_for_brace_check[j] == "{"
                                ):
                                    # Skip required argument
                                    depth = 1
                                    j += 1
                                    while (
                                        j < len(content_for_brace_check) and depth > 0
                                    ):
                                        if content_for_brace_check[j] == "{":
                                            depth += 1
                                        elif content_for_brace_check[j] == "}":
                                            depth -= 1
                                        j += 1
                            continue
                    elif char == "{" and not in_latex_cmd:
                        brace_count += 1
                    elif char == "}" and not in_latex_cmd:
                        brace_count -= 1
                    in_latex_cmd = False

                if brace_count != 0:
                    validation_errors.append(
                        f"Potential unbalanced braces in markdown: "
                        f"difference={brace_count} (positive=more {{, negative=more }})"
                    )

                # NOTE: We intentionally do NOT count parentheses in math blocks.
                # The regex patterns for extracting math blocks ($...$, $$...$$)
                # do not reliably capture complete mathematical expressions, especially:
                # - Multi-line display math spanning \begin{align}...\end{align}
                # - Inline math with nested commands like H(\mathcal{F}_c)
                # - Math containing \left( \right) pairs
                # - Expression continuations across lines
                # 
                # LaTeX compilation provides comprehensive error reporting for actual
                # syntax issues. These pre-validation checks produced false positives
                # for valid expressions like:
                # - $H(\mathcal{F}_c)$ in fractions
                # - Text containing parens inside \text{} commands
                # - Cross-references like (\cref{sec:omega4})


                if validation_errors:
                    logger.warning(
                        f"Pre-validation found {len(validation_errors)} potential issue(s):"
                    )
                    for err in validation_errors:
                        logger.warning(f"  • {err}")
                    # Note: These are warnings only, don't block PDF generation
                    logger.info("  (These are warnings - PDF generation will proceed)")
            except Exception as e:
                logger.debug(f"Pre-validation check failed: {e}")
                # Try to read content anyway for error reporting
                try:
                    md_content = combined_md.read_text(encoding="utf-8")
                except Exception:
                    pass

        try:
            result = subprocess.run(
                pandoc_to_tex, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            # Provide more detailed error information
            error_msg = f"Failed to convert markdown to LaTeX"

            # Combine stderr and stdout for comprehensive error extraction
            all_output = ""
            if e.stderr:
                all_output += f"STDERR:\n{e.stderr}\n"
            if e.stdout:
                all_output += f"STDOUT:\n{e.stdout}\n"

            # Extract and format error messages
            error_lines = []
            position_info = None

            # Parse stderr for error messages
            if e.stderr:
                stderr_lines = e.stderr.strip().split("\n")
                for line in stderr_lines:
                    line_lower = line.lower()
                    # Look for position errors (e.g., "unbalanced parenthesis at position 7")
                    if "position" in line_lower and (
                        "unbalanced" in line_lower
                        or "parenthesis" in line_lower
                        or "error" in line_lower
                    ):
                        error_lines.append(f"Pandoc Error: {line}")
                        # Extract position number
                        import re

                        pos_match = re.search(r"position\s+(\d+)", line_lower)
                        if pos_match:
                            position_info = int(pos_match.group(1))
                    elif "unbalanced" in line_lower or "parenthesis" in line_lower:
                        error_lines.append(f"Pandoc Error: {line}")
                    elif "error" in line_lower and line.strip():
                        error_lines.append(f"Pandoc: {line}")

            # Parse stdout for error messages (Pandoc sometimes outputs errors to stdout)
            if e.stdout:
                stdout_lines = e.stdout.strip().split("\n")
                for line in stdout_lines:
                    line_lower = line.lower()
                    if "position" in line_lower and (
                        "unbalanced" in line_lower
                        or "parenthesis" in line_lower
                        or "error" in line_lower
                    ):
                        if f"Pandoc Error: {line}" not in error_lines:
                            error_lines.append(f"Pandoc Error (stdout): {line}")
                        # Extract position number if not already found
                        if position_info is None:
                            import re

                            pos_match = re.search(r"position\s+(\d+)", line_lower)
                            if pos_match:
                                position_info = int(pos_match.group(1))
                    elif (
                        "error" in line_lower or "warning" in line_lower
                    ) and line.strip():
                        if line not in [
                            err.split(":", 1)[-1].strip() for err in error_lines
                        ]:
                            error_lines.append(f"Pandoc (stdout): {line}")

            # Build error message - always include full Pandoc output for debugging
            if error_lines:
                error_msg += "\n\n" + "\n".join(error_lines)

            # Always include full Pandoc output for comprehensive debugging
            if all_output:
                error_msg += f"\n\nFull Pandoc output:\n{all_output}"
            elif not error_lines:
                # If no specific errors found and no output, include return code
                error_msg += f"\n\nPandoc failed with return code {e.returncode} (no output captured)"

            # Check if combined_md exists and show relevant context
            context_info = {"source": str(combined_md), "target": str(combined_tex)}
            suggestions = []

            if combined_md.exists():
                try:
                    # Use md_content if already read, otherwise read it
                    if not md_content:
                        md_content = combined_md.read_text(encoding="utf-8")

                    context_info["total_size"] = len(md_content)

                    # Show content around error position if available
                    if position_info is not None:
                        pos = position_info
                        start = max(0, pos - 150)
                        end = min(len(md_content), pos + 150)
                        context_info["error_position"] = pos
                        context_info["error_context"] = md_content[start:end]

                        # Calculate line number for the position
                        line_num = md_content[:pos].count("\n") + 1
                        context_info["error_line"] = line_num

                        # Extract the line containing the error
                        lines = md_content.split("\n")
                        if line_num <= len(lines):
                            context_info["error_line_content"] = lines[line_num - 1]

                        suggestions.append(
                            f"Check character position {pos} (line {line_num}) in combined markdown file"
                        )
                        suggestions.append(
                            f"Review content around position: {repr(md_content[max(0, pos-20):min(len(md_content), pos+20)])}"
                        )
                    else:
                        # Show first and last 200 chars for context if no position info
                        context_info["first_200_chars"] = md_content[:200]
                        context_info["last_200_chars"] = md_content[-200:]

                    # Add suggestions based on error type
                    if (
                        "unbalanced" in error_msg.lower()
                        or "parenthesis" in error_msg.lower()
                    ):
                        suggestions.append(
                            "Check for unmatched parentheses, brackets, or braces in markdown"
                        )
                        suggestions.append(
                            "Verify LaTeX commands have properly matched delimiters"
                        )
                        suggestions.append(
                            "Review math expressions for balanced parentheses"
                        )

                    suggestions.append(f"Inspect combined markdown file: {combined_md}")
                    suggestions.append(
                        "Try converting individual markdown files to identify the problematic file"
                    )

                except Exception as ex:
                    logger.debug(f"Error gathering context: {ex}")
                    suggestions.append(f"Could not read combined markdown file: {ex}")

            # Add general suggestions
            suggestions.extend(
                [
                    "Verify all markdown files are valid",
                    "Check for special characters or encoding issues",
                    "Ensure LaTeX commands in markdown are properly formatted",
                    f"Review Pandoc command: {' '.join(pandoc_to_tex)}",
                ]
            )

            # Log full error details at ERROR level
            logger.error(f"Pandoc conversion failed: {error_msg}")
            if context_info.get("error_position") is not None:
                pos = context_info["error_position"]
                line = context_info.get("error_line", "unknown")
                logger.error(
                    f"  Error at position {pos} (line {line}) in combined markdown"
                )
                # Show the actual characters at that position
                if md_content and pos < len(md_content):
                    start = max(0, pos - 20)
                    end = min(len(md_content), pos + 20)
                    logger.error(
                        f"  Characters around position {pos}: {repr(md_content[start:end])}"
                    )
                    # Show character-by-character analysis
                    logger.error(f"  Character-by-character analysis (position {pos}):")
                    for i in range(max(0, pos - 5), min(len(md_content), pos + 6)):
                        marker = " >>> " if i == pos else "     "
                        char = md_content[i]
                        logger.error(
                            f"    {marker}Position {i}: {repr(char)} (ord: {ord(char)})"
                        )
            if context_info.get("error_context"):
                logger.error(
                    f"  Context around error:\n{context_info['error_context']}"
                )
            # Always log the combined markdown file location for inspection
            logger.error(f"  Combined markdown file saved at: {combined_md}")
            logger.error(f"  Combined markdown file size: {len(md_content)} characters")

            # Try to identify which source file contains the error
            if position_info is not None and md_content:
                # Find which source file the error position corresponds to
                current_pos = 0
                for i, source_file in enumerate(source_files):
                    try:
                        file_content = source_file.read_text(encoding="utf-8")
                        # Account for trailing newline and spacing
                        file_content_processed = file_content.rstrip() + "\n"
                        file_size = len(file_content_processed)

                        # Account for separator between files (if not the last file)
                        separator_size = 0
                        if i < len(source_files) - 1:
                            separator_size = len("\n```{=latex}\n\\newpage\n```\n")

                        if current_pos <= position_info < current_pos + file_size:
                            context_info["problematic_file"] = str(source_file)
                            context_info["problematic_file_index"] = i + 1
                            logger.error(
                                f"  Error likely in source file {i+1}/{len(source_files)}: {source_file.name}"
                            )
                            # Show position within that file
                            file_pos = position_info - current_pos
                            line_num = file_content[:file_pos].count("\n") + 1
                            logger.error(
                                f"  Position within file: {file_pos} (line {line_num})"
                            )

                            # Show context around the error position in the source file
                            start = max(0, file_pos - 50)
                            end = min(len(file_content), file_pos + 50)
                            context_snippet = file_content[start:end]
                            logger.error(
                                f"  Context in source file (chars {start}-{end}):"
                            )
                            # Show with line numbers if reasonable
                            lines = context_snippet.split("\n")
                            if len(lines) <= 10:
                                for j, line in enumerate(lines):
                                    actual_line = line_num - (len(lines) - j - 1)
                                    marker = (
                                        " >>> "
                                        if start + sum(len(l) + 1 for l in lines[:j])
                                        <= file_pos
                                        < start
                                        + sum(len(l) + 1 for l in lines[: j + 1])
                                        else "     "
                                    )
                                    logger.error(
                                        f"    {marker}Line {actual_line}: {repr(line)}"
                                    )
                            else:
                                logger.error(f"    {repr(context_snippet)}")

                            # Show the exact character at the error position
                            if file_pos < len(file_content):
                                char_at_pos = file_content[file_pos]
                                logger.error(
                                    f"  Character at error position: {repr(char_at_pos)} (ord: {ord(char_at_pos)})"
                                )
                            break

                        # Move to next file position
                        current_pos += file_size + separator_size
                    except Exception as ex:
                        logger.debug(
                            f"Error analyzing file {i+1} ({source_file.name}): {ex}"
                        )
                        pass

            raise RenderingError(
                error_msg, context=context_info, suggestions=suggestions
            )

        # Read and process LaTeX content
        tex_content = combined_tex.read_text()

        # Fix lmodern conflict with xelatex (causes run-on words)
        # The lmodern package relies on T1 font encoding which can conflict with 
        # XeLaTeX's font handling, leading to missing spaces between words.
        if "\\usepackage{lmodern}" in tex_content:
            tex_content = tex_content.replace("\\usepackage{lmodern}", "% \\usepackage{lmodern}")
            logger.info("✓ Disabled lmodern package to prevent XeLaTeX font conflicts")

        # Fix broken math delimiters from Pandoc conversion
        try:
            tex_content = self._fix_math_delimiters(tex_content)
        except Exception as e:
            logger.warning(
                f"Math delimiter fixing failed: {e}. Continuing with original LaTeX content."
            )
            logger.debug(
                f"Math delimiter fixing error details: {type(e).__name__}: {e}"
            )
            # Continue with original tex_content - it may still compile

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
        graphicx_required = r"\usepackage{graphicx}"
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
                # Insert defaults (config.yaml) first, but checking for duplicates
                if title_page_preamble:
                    # Filter out commands that would overwrite existing Pandoc-generated metadata
                    lines = title_page_preamble.split('\n')
                    filtered_lines = []
                    for line in lines:
                        # We want to inject our formatted metadata even if Pandoc generated some.
                        # Since we append to combined_preamble which is inserted before \begin{document}
                        # (likely after Pandoc's preamble), our definitions should take precedence or at least exist.
                        # For \author and \date, redefinition is standard.
                        filtered_lines.append(line)
                    
                    if filtered_lines:
                        combined_preamble += "\n".join(filtered_lines) + "\n\n"

                # Insert overrides (preamble.md) second
                if preamble_content:
                    combined_preamble += preamble_content + "\n\n"

                # Insert before \begin{document}
                tex_content = (
                    tex_content[:begin_doc_idx]
                    + combined_preamble
                    + tex_content[begin_doc_idx:]
                )
                logger.debug(
                    f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}"
                )

        # Insert title page body commands AFTER \begin{document}
        if title_page_body:
            # Check if \maketitle is already present (e.g. from Pandoc)
            if "\\maketitle" in tex_content:
                logger.debug("✓ \\maketitle already present in LaTeX content (skipping injection)")
            else:
                begin_doc_idx = tex_content.find("\\begin{document}")
                if begin_doc_idx > 0:
                    # Find position right after \begin{document}
                    end_of_begin_doc = tex_content.find("\n", begin_doc_idx) + 1
                    if end_of_begin_doc > begin_doc_idx:
                        # Insert \maketitle and formatting after \begin{document}
                        tex_content = (
                            tex_content[:end_of_begin_doc]
                            + "\n"
                            + title_page_body
                        + "\n\n"
                        + tex_content[end_of_begin_doc:]
                    )
                    logger.info(
                        r"✓ Inserted title page (\maketitle) after \begin{document}"
                    )

        # Insert bibliography commands before \end{document} if bibliography exists
        if bib_exists and "\\bibliography{" not in tex_content:
            end_doc_idx = tex_content.rfind("\\end{document}")
            if end_doc_idx > 0:
                bibliography_commands = (
                    "\n\n\\bibliographystyle{unsrt}\n\\bibliography{references}\n"
                )
                tex_content = (
                    tex_content[:end_doc_idx]
                    + bibliography_commands
                    + tex_content[end_doc_idx:]
                )
                logger.info("✓ Inserted bibliography commands before \\end{document}")
            else:
                logger.warning(
                    "⚠️  Could not find \\end{document} to insert bibliography commands"
                )

        combined_tex.write_text(tex_content)

        # Verify figure files exist before compilation
        figures_dir = manuscript_dir.parent / "output" / "figures"
        import re

        fig_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
        referenced_figures = re.findall(fig_pattern, tex_content)

        if referenced_figures:
            logger.info(f"Verifying {len(referenced_figures)} figure reference(s)...")
            missing_figures = []
            found_figures = []

            for fig_ref in referenced_figures:
                # Extract filename from path
                filename = fig_ref.split("/")[-1]
                fig_path = figures_dir / filename

                # Try both normalized and non-normalized paths
                fig_normalized = figures_dir / unicodedata.normalize("NFC", filename)

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
                        similar = [
                            f.name
                            for f in figures_dir.iterdir()
                            if f.name.lower().startswith(filename.split(".")[0].lower())
                        ]
                        if similar:
                            logger.debug(
                                f"    Similar files found: {', '.join(similar)}"
                            )

            logger.info(
                f"  Found: {len(found_figures)}/{len(referenced_figures)} figures"
            )
            if missing_figures:
                logger.warning(
                    f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}"
                )
                if len(missing_figures) > 5:
                    logger.warning(
                        f"  ... and {len(missing_figures) - 5} more missing figures"
                    )

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
            combined_tex.name,  # Just the filename, since we set cwd to output_dir
        ]

        import time

        start_time = time.time()

        logger.info(f"Rendering combined manuscript to PDF: {output_file.name}")
        logger.info(f"  Source files: {len(source_files)}")
        if bib_exists:
            logger.info(f"  Bibliography: {bib_file.name}")
        logger.debug(f"  Output directory: {output_dir}")
        logger.debug(f"  Combined TeX file: {combined_tex.name}")
        logger.debug(f"  Combined MD file: {combined_md.name}")

        try:
            # Run xelatex with bibliography processing for proper cross-references, TOC, and bibliography
            # Pass 1: Initial xelatex compilation
            # Pass 2: Bibtex processing (if bibliography exists)
            # Pass 3-4: Additional xelatex passes for reference resolution

            # Temporary PDF file created during compilation (before renaming to final output)
            temp_pdf = output_dir / "_combined_manuscript.pdf"

            logger.info(f"  LaTeX compilation pass 1/4...")
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, cwd=str(output_dir)
            )

            # Check for critical errors on first pass
            # Note: Use temp_pdf (not output_file) since output_file is created by renaming temp_pdf
            if "Fatal error occurred" in result.stdout or (
                result.returncode > 1 and not temp_pdf.exists()
            ):
                raise RenderingError(
                    f"XeLaTeX compilation failed (pass 1)",
                    context={"source": str(combined_tex), "output": str(output_file)},
                )

            # Process bibliography if it exists
            if bib_exists:
                logger.info(f"  Bibliography processing...")
                try:
                    self._process_bibliography(combined_tex, output_dir, bib_file)
                except Exception as bib_error:
                    logger.warning(f"  Bibliography processing failed: {bib_error}")
                    logger.warning(
                        "  Continuing PDF generation without bibliography processing"
                    )
                    # Don't fail the entire PDF generation for bibliography issues

            # Additional passes for reference resolution (especially after bibtex)
            max_passes = 4
            consecutive_failures = 0
            max_consecutive_failures = 2

            for run in range(1, max_passes):
                log_progress_bar(run + 1, max_passes, "LaTeX compilation", bar_width=20)
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=str(output_dir),
                )

                # Check for critical errors
                if "Fatal error occurred" in result.stdout or result.returncode > 1:
                    consecutive_failures += 1

                    if output_file.exists():
                        logger.warning(
                            f"⚠️  PDF generated but with warnings (run {run+1})"
                        )
                        # Reset failure count if we have a PDF
                        consecutive_failures = 0
                        break
                    else:
                        # Check for recoverable errors
                        log_file = output_dir / "_combined_manuscript.log"
                        if log_file.exists():
                            log_content = log_file.read_text()

                            # Check for missing package errors
                            missing_pkg = _parse_missing_package_error(log_file)
                            if missing_pkg:
                                raise RenderingError(
                                    f"Missing LaTeX package: {missing_pkg}",
                                    context={
                                        "package": missing_pkg,
                                        "source": str(combined_tex),
                                        "log_file": str(log_file),
                                    },
                                    suggestions=[
                                        f"Install package: sudo tlmgr install {missing_pkg}",
                                        "Verify LaTeX packages: python3 -m infrastructure.rendering.latex_package_validator",
                                        "Update TeX Live: sudo tlmgr update --self",
                                        f"Check log file for details: {log_file}",
                                    ],
                                )

                            # Check for other recoverable errors
                            if consecutive_failures >= max_consecutive_failures:
                                raise RenderingError(
                                    f"LaTeX compilation failed after {consecutive_failures} consecutive attempts",
                                    context={
                                        "source": str(combined_tex),
                                        "log_file": str(log_file),
                                        "last_error": (
                                            result.stderr[:500]
                                            if result.stderr
                                            else "No stderr"
                                        ),
                                    },
                                    suggestions=[
                                        "Check LaTeX syntax in manuscript files",
                                        "Verify all figures exist and paths are correct",
                                        "Ensure bibliography file is properly formatted",
                                        f"Review compilation log: {log_file}",
                                    ],
                                )
                        else:
                            logger.warning(
                                f"⚠️  LaTeX compilation failed (run {run+1}), continuing..."
                            )

                            if missing_pkg:
                                raise RenderingError(
                                    f"Missing LaTeX package: {missing_pkg}",
                                    context={
                                        "package": missing_pkg,
                                        "source": str(combined_tex),
                                        "log_file": str(log_file),
                                    },
                                    suggestions=[
                                        f"Install package: sudo tlmgr install {missing_pkg}",
                                        "Verify BasicTeX packages: python3 -m infrastructure.rendering.latex_package_validator",
                                        "Update TeX Live: sudo tlmgr update --self",
                                        "Or install full MacTeX instead of BasicTeX: https://www.tug.org/mactex/",
                                        f"Check log file for details: {log_file}",
                                    ],
                                )
                            else:
                                raise RenderingError(
                                    f"XeLaTeX compilation failed (run {run+1})",
                                    context={
                                        "source": str(combined_tex),
                                        "output": str(output_file),
                                    },
                                    suggestions=[
                                        "Check LaTeX log file for detailed error messages",
                                        "Verify all required packages are installed",
                                        "Ensure figure paths are correct relative to output directory",
                                        "Run: python3 -m infrastructure.rendering.latex_package_validator",
                                        "Run with --verbose flag for detailed compilation output",
                                    ],
                                )

                # Check log file for unresolved references or TOC changes
                log_file = output_dir / "_combined_manuscript.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    # If no warnings/issues found, we can stop early
                    if (
                        "Rerun" not in log_content
                        and "undefined" not in log_content.lower()
                    ):
                        logger.info(f"  All references resolved after pass {run+1}")
                        break

                    # Check for graphics-specific issues
                    if run == max_passes - 1:  # Last pass
                        graphics_issues = self._check_latex_log_for_graphics_errors(
                            log_file
                        )
                        if graphics_issues["graphics_errors"]:
                            for error in graphics_issues["graphics_errors"]:
                                logger.warning(f"  Graphics error: {error}")
                        if graphics_issues["missing_files"]:
                            for missing in graphics_issues["missing_files"]:
                                logger.warning(f"  Missing file: {missing}")
                        if graphics_issues["graphics_warnings"]:
                            for warning in graphics_issues["graphics_warnings"]:
                                logger.warning(
                                    f"  Graphics warning: {warning[:100]}..."
                                )

            # Check if the temporary PDF was created and rename it
            if temp_pdf.exists():
                # Rename temporary PDF to final name
                temp_pdf.rename(output_file)
                # NEW: Log successful combination with output size
                if output_file.exists():
                    output_size_kb = output_file.stat().st_size / 1024
                    logger.info(
                        f"\n✅ Successfully combined {len(source_files)} sections"
                    )
                    logger.info(f"   Output: {output_file.name}")
                    logger.info(
                        f"   Size: {output_size_kb:.1f} KB ({output_size_kb/1024:.2f} MB)"
                    )
                    logger.info(f"   Location: {output_file.parent}")

                    # Log performance metrics
                    end_time = time.time()
                    total_duration = end_time - start_time
                    logger.info(f"   Duration: {total_duration:.2f} seconds")

                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
                return output_file
            elif output_file.exists():
                # NEW: Log successful combination with output size
                output_size_kb = output_file.stat().st_size / 1024
                logger.info(f"\n✅ Successfully combined {len(source_files)} sections")
                logger.info(f"   Output: {output_file.name}")
                logger.info(
                    f"   Size: {output_size_kb:.1f} KB ({output_size_kb/1024:.2f} MB)"
                )
                logger.info(f"   Location: {output_file.parent}")

                # Log performance metrics
                end_time = time.time()
                total_duration = end_time - start_time
                logger.info(f"   Duration: {total_duration:.2f} seconds")

                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
                return output_file
            else:
                raise RenderingError(
                    f"PDF file was not created",
                    context={"source": str(combined_tex), "output": str(output_file)},
                )

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to compile LaTeX to PDF: {e.stderr or e.stdout}",
                context={"source": str(combined_tex), "output": str(output_file)},
            )

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
                content = md_file.read_text(encoding="utf-8", errors="strict")

                # Validate file ends with newline for proper spacing
                if not content.endswith("\n"):
                    content += "\n"

                # Strip trailing whitespace from each file to avoid double newlines
                # But preserve a single trailing newline
                content = content.rstrip() + "\n"

                # Validate section header syntax in this file
                import re

                header_attrs = re.findall(r"\{#([^}]+)\}", content)
                for attr in header_attrs:
                    # Check for balanced braces
                    if attr.count("{") != attr.count("}"):
                        logger.warning(
                            f"Potential unbalanced braces in {md_file.name} header attribute: {{#{attr}}}"
                        )

                # Add file content
                combined_parts.append(content)

                # Add page break between sections (only if not the last file)
                if i < len(source_files) - 1:
                    # Use Pandoc raw LaTeX block syntax for \newpage command
                    # This ensures Pandoc properly handles it with +raw_tex extension
                    # Add proper spacing around the page break
                    combined_parts.append("\n```{=latex}\n\\newpage\n```\n")

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
                )
            except Exception as e:
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
                )

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

        # Validate basic structure - check for common issues at the start
        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if combined.startswith("\ufeff"):
            logger.warning("Removing UTF-8 BOM from combined markdown")
            combined = combined[1:]

        # Ensure the file doesn't start with problematic characters
        # Pandoc might complain about certain characters at position 0
        if combined and combined[0] in ["(", ")", "[", "]", "{", "}"]:
            logger.warning(
                f"Combined markdown starts with potentially problematic character: {repr(combined[0])}"
            )

        return combined

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
        pattern = r"```\s*latex\s*\n(.*?)\n\s*```"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            # Combine all latex blocks
            preamble_lines = [match.strip() for match in matches]
            result = "\n".join(preamble_lines)
            logger.debug(
                f"Extracted {len(matches)} LaTeX preamble block(s) ({len(result)} chars)"
            )
            return result
        else:
            logger.debug(f"No LaTeX code blocks found in {preamble_file.name}")
            return ""

    def _fix_figure_paths(
        self, tex_content: str, manuscript_dir: Path, output_dir: Path
    ) -> str:
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
        # Note: This basic pattern may miss \pandocbounded with nested braces in alt={}
        pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
        
        # Additional pattern for \pandocbounded{\includegraphics[...]{path}}
        # This handles the complex case where options contain nested braces (alt={...})
        # We'll use a fallback string replacement after regex for any missed paths
        pandocbounded_pattern = r"](\{\.\.\/output\/figures\/[^}]+\.png\})\}"

        figures_dir = manuscript_dir.parent / "output" / "figures"
        fixed_count = 0
        paths_fixed = []

        def normalize_path(path_str: str) -> str:
            """Normalize path to handle Unicode and encoding issues."""
            # Normalize Unicode characters using NFC (composition form)
            normalized = unicodedata.normalize("NFC", path_str)
            return normalized

        def extract_filename(path_str: str) -> str:
            """Extract filename from various path formats."""
            # Normalize first
            path_str = normalize_path(path_str)

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

            # If no prefix matched, could be just a filename or absolute path
            if "/" in path_str or "\\" in path_str:
                # Split by last / or \
                return re.split(r"[/\\]", path_str)[-1]
            else:
                # Just a filename
                return path_str

        def fix_path(match: re.Match) -> str:
            r"""Fix a single includegraphics path to be relative to the compilation directory.

            Transforms figure paths from various formats (absolute, manuscript-relative,
            etc.) to paths relative to the LaTeX compilation directory (output/pdf/).
            Preserves any optional parameters like width or height specifications.

            Args:
                match: Regular expression match object containing:
                    - group(0): The full \\includegraphics command
                    - group(1): The figure path within braces

            Returns:
                The corrected \\includegraphics command with path relative to ../figures/.

            Note:
                - Logs a warning if the referenced figure file does not exist
                - Still returns the fixed path even for missing files to allow
                  compilation to continue with other content
            """
            nonlocal fixed_count

            old_path = match.group(1)
            original_path = old_path

            # Check if already in correct format
            if old_path.startswith("../figures/"):
                return match.group(0)

            # Extract filename, handling encoding issues
            filename = extract_filename(old_path)

            # Build new path relative to compilation directory
            # Since we're compiling in output_dir (output/pdf), figures are in ../figures/
            new_path = f"../figures/{filename}"

            # Verify the figure file exists (try both normalized and non-normalized)
            fig_full_path = figures_dir / filename
            fig_normalized = figures_dir / normalize_path(filename)

            file_exists = fig_full_path.exists() or fig_normalized.exists()

            if file_exists:
                fixed_count += 1
                paths_fixed.append(f"{original_path} → {new_path}")
                # Preserve options if present
                full_match = match.group(0)
                if "[" in full_match:
                    # Extract options
                    options_start = full_match.find("[")
                    options_end = full_match.find("]")
                    options = full_match[options_start : options_end + 1]
                    return f"\\includegraphics{options}{{{new_path}}}"
                else:
                    return f"\\includegraphics{{{new_path}}}"
            else:
                logger.warning(f"⚠️  Figure file not found: {fig_full_path}")
                fixed_count += 1
                paths_fixed.append(f"{original_path} → {new_path} (FILE NOT FOUND)")
                # Still return fixed path so compilation continues
                full_match = match.group(0)
                if "[" in full_match:
                    options_start = full_match.find("[")
                    options_end = full_match.find("]")
                    options = full_match[options_start : options_end + 1]
                    return f"\\includegraphics{options}{{{new_path}}}"
                else:
                    return f"\\includegraphics{{{new_path}}}"

        # Apply path fixes
        tex_content = re.sub(pattern, fix_path, tex_content)

        # Fallback: Simple string replacement for paths the regex missed
        # This handles \pandocbounded{\includegraphics[...,alt={...}]{../output/figures/xxx.png}}
        # where nested braces in options break the regex pattern
        remaining_old_paths = tex_content.count("../output/figures/")
        if remaining_old_paths > 0:
            tex_content = tex_content.replace("../output/figures/", "../figures/")
            fixed_count += remaining_old_paths
            logger.info(f"✓ Fixed {remaining_old_paths} additional figure path(s) via fallback")

        if fixed_count > 0:
            logger.info(f"✓ Fixed {fixed_count} figure path(s)")
            for path_info in paths_fixed[:10]:  # Show first 10
                logger.debug(f"  {path_info}")
            if len(paths_fixed) > 10:
                logger.debug(f"  ... and {len(paths_fixed) - 10} more")
        else:
            # No paths fixed - check if there are any figure references at all
            if pattern and re.search(pattern, tex_content):
                logger.debug(
                    "No figure paths needed fixing (already in correct format)"
                )

        return tex_content

    def _fix_math_delimiters(self, tex_content: str) -> str:
        r"""Fix broken math delimiters from Pandoc conversion.

        Pandoc incorrectly converts \[ and \] to {[} and {]}, breaking math mode.
        This function fixes these issues and restores proper LaTeX math formatting.

        Args:
            tex_content: LaTeX content with broken math delimiters

        Returns:
            LaTeX content with fixed math delimiters
        """
        fixed_count = 0

        # Helper function to fix math content
        def fix_math_content(content: str) -> str:
            """Fix broken patterns within math content."""
            # 1. Remove all nested {[} and {]} that Pandoc incorrectly inserted
            content = re.sub(r"\{\[\}", "", content)
            content = re.sub(r"\{\]\}", "", content)

            # 2. Fix \mathbb{E}\emph{\{q(s}\tau)\} -> \mathbb{E}_{q(s_\tau)}
            # Pattern: \mathbb{E}\emph{\{q(s}\tau)\} or \mathbb{E}\emph{\{o}\tau)\}
            content = re.sub(
                r"\\mathbb\{E\}\\emph\{\\\{([^}]+)\}([a-zA-Z_]+)\\\}\)",
                r"\\mathbb{E}_{\1_\2}",
                content,
            )

            # 3. Fix broken subscripts: s\_\tau -> s_\tau, o\_\tau -> o_\tau
            content = re.sub(r"([a-zA-Z])\\_([a-zA-Z_]+)", r"\1_\2", content)

            # 4. Remove remaining \emph{} wrappers
            content = re.sub(r"\\emph\{([^}]+)\}", r"\1", content)

            # 5. Fix \textbar to \mid
            content = re.sub(r"\\textbar", r"\\mid", content)

            return content

        # Step 1: Fix display math with labels: {[} ... {]}\label{eq:...}{]}
        # Use greedy matching to find the LAST {]} before \label
        # Pattern: {[} ... (everything) ... {]}\label{...}{]}
        pattern_with_label = r"\{\[\}(.*)\{\]\}\\label\{([^}]+)\}\{\]\}"

        def fix_display_math_with_label(match: re.Match) -> str:
            r"""Fix display math blocks that include equation labels.

            Handles the pattern {[} ... {]}\\label{eq:...}{]} which Pandoc incorrectly
            generates, converting it back to proper LaTeX: \\[...\\label{...}\\].

            Args:
                match: Regular expression match object containing:
                    - group(1): The math content between delimiters
                    - group(2): The equation label name

            Returns:
                Properly formatted LaTeX display math with label.
            """
            nonlocal fixed_count
            math_content = match.group(1)
            label_name = match.group(2)

            math_content = fix_math_content(math_content)
            fixed_count += 1
            return f"\\[{math_content}\\label{{{label_name}}}\\]"

        # Step 2: Fix display math without labels: {[} ... {]}
        # Match greedily to get the last {]} in a paragraph/block
        pattern_no_label = r"\{\[\}([^{]*?)\{\]\}(?!\\label)(?=\s|$)"

        def fix_display_math_no_label(match: re.Match) -> str:
            r"""Fix display math blocks without equation labels.

            Handles the pattern {[} ... {]} which Pandoc incorrectly generates,
            converting it back to proper LaTeX display math: \\[...\\].

            Args:
                match: Regular expression match object containing:
                    - group(1): The math content between delimiters

            Returns:
                Properly formatted LaTeX display math without label.
            """
            nonlocal fixed_count
            math_content = match.group(1)

            math_content = fix_math_content(math_content)
            fixed_count += 1
            return f"\\[{math_content}\\]"

        # Apply fixes: first with labels (greedy), then without
        tex_content = re.sub(
            pattern_with_label,
            fix_display_math_with_label,
            tex_content,
            flags=re.DOTALL,
        )
        tex_content = re.sub(
            pattern_no_label,
            fix_display_math_no_label,
            tex_content,
            flags=re.DOTALL | re.MULTILINE,
        )

        # Step 3: Fix remaining issues globally
        tex_content = re.sub(r"\\textbar", r"\\mid", tex_content)

        # Fix broken Greek letters with error handling
        greek_letters = [
            "tau",
            "pi",
            "Theta",
            "alpha",
            "beta",
            "gamma",
            "lambda",
            "kappa",
            "sigma",
            "phi",
            "eta",
        ]
        for greek in greek_letters:
            try:
                # Match: backslash + greek_letter + backslash + close-paren
                # In the LaTeX, we see: \tau\) and want: \tau)
                # Build pattern as: \\tau\\) (escaping each backslash for regex)
                pattern = r"\\" + greek + r"\\\)"
                replacement = "\\\\" + greek + ")"
                tex_content = re.sub(pattern, replacement, tex_content)
            except re.error as e:
                logger.warning(
                    f"Failed to fix Greek letter '{greek}': {e}. Skipping this pattern."
                )
                continue
            except Exception as e:
                logger.warning(
                    f"Unexpected error fixing Greek letter '{greek}': {e}. Skipping this pattern."
                )
                continue

        if fixed_count > 0:
            logger.info(f"✓ Fixed {fixed_count} math delimiter(s)")

        return tex_content

    def _check_latex_log_for_graphics_errors(self, log_file: Path) -> dict:
        """Parse LaTeX log file for graphics-related errors and warnings.

        Args:
            log_file: Path to LaTeX .log file

        Returns:
            Dictionary with graphics issues found
        """
        result = {"graphics_errors": [], "graphics_warnings": [], "missing_files": []}

        if not log_file.exists():
            return result

        try:
            log_content = log_file.read_text(errors="ignore")

            # Look for common graphics-related error patterns
            import re

            # Pattern for file not found errors
            file_not_found = re.findall(r"File `([^`]+)` not found", log_content)
            result["missing_files"].extend(file_not_found)

            # Pattern for graphics package warnings
            graphics_warnings = re.findall(
                r"((?:Package graphics|Graphics Error).*?)(?=\n(?:!|\s*$))",
                log_content,
                re.IGNORECASE,
            )
            result["graphics_warnings"].extend(graphics_warnings)

            # Check for undefined control sequences related to graphics
            if r"\includegraphics" in log_content and "Undefined" in log_content:
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
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            if not config:
                return ""

            # Extract metadata
            paper = config.get("paper", {})
            authors = config.get("authors", [])

            title = paper.get("title", "Research Paper")
            subtitle = paper.get("subtitle", "")
            date = paper.get("date", "")
            doi = config.get("publication", {}).get("doi", "")

            # Build preamble commands (must be before \begin{document})
            preamble_lines = [
                f"\\title{{{title}}}",
            ]
            # Add subtitle if present
            if subtitle:
                preamble_lines[-1] = f"\\title{{{title}\\\\\\normalsize {subtitle}}}"

            # Add authors with proper formatting (including email, affiliation, ORCID)
            if authors:
                author_blocks = []
                for author in authors:
                    if "name" not in author:
                        continue
                    
                    name = author["name"]
                    parts = [name]
                    
                    # Add affiliation if present
                    if "affiliation" in author:
                        parts.append(f"\\\\\\footnotesize{{{author['affiliation']}}}")
                    
                    # Add email if present
                    if "email" in author:
                        parts.append(f"\\\\\\footnotesize{{\\texttt{{{author['email']}}}}}")
                    
                    # Add ORCID if present (with hyperlink)
                    if "orcid" in author:
                        orcid = author["orcid"]
                        parts.append(f"\\\\\\footnotesize{{\\href{{https://orcid.org/{orcid}}}{{ORCID: {orcid}}}}}")
                    
                    # Join all parts for this author
                    author_block = "".join(parts)
                    author_blocks.append(author_block)
                
                if author_blocks:
                    # Use standard \and for multiple authors, but tight formatting within each
                    author_str = " \\\\and ".join(author_blocks)
                    
                    # Add DOI and Date to the author block for tight vertical layout
                    extras = []
                    if doi:
                        extras.append(f"\\href{{https://doi.org/{doi}}}{{DOI: {doi}}}")
                    
                    if date:
                        extras.append(date)

                    if extras:
                        # Add extras with small vertical space and small font
                        author_str += " \\\\ " + " \\\\ ".join([f"\\footnotesize{{{e}}}" for e in extras])

                    preamble_lines.append(f"\\author{{{author_str}}}")

            if date:
                preamble_lines.append(f"\\date{{{date}}}")
            else:
                preamble_lines.append(r"\date{\today}")

            logger.debug(
                f"Generated title page preamble with {len(preamble_lines)} commands"
            )
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
            with open(config_file, "r") as f:
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
