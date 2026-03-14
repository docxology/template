"""PDF Rendering module."""

from __future__ import annotations

import re
import subprocess
import time
import unicodedata
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.logging_progress import log_progress_bar
from infrastructure.rendering._pdf_latex_helpers import (
    check_latex_log_for_graphics_errors,
    extract_preamble,
    fix_figure_paths,
    fix_math_delimiters,
    generate_title_page_body,
    generate_title_page_preamble,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import compile_latex

logger = get_logger(__name__)

def _parse_missing_package_error(log_file: Path) -> str | None:
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

        match = re.search(r"File `([^']+\.sty)' not found", log_content)
        if match:
            sty_file = match.group(1)
            # Extract package name (remove .sty extension)
            package_name = sty_file.replace(".sty", "")
            return package_name

        # Also check for the "! LaTeX Error: File *.sty not found" pattern
        match = re.search(r"! LaTeX Error: File `?([^'`\s]+\.sty)'? not found", log_content)
        if match:
            sty_file = match.group(1)
            package_name = sty_file.replace(".sty", "")
            return package_name

    except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — optional log inspection; return None on failure
        logger.debug(f"Error parsing log file for package errors: {e}")

    return None

class PDFRenderer:
    """Handles PDF generation logic."""

    def __init__(self, config: RenderingConfig):
        self.config = config

    def render(self, source_file: Path, output_name: str | None = None) -> Path:
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

        raise RenderingError(
            f"Unsupported file format for rendering: {source_file.suffix}",
            context={"source_file": str(source_file), "supported_formats": [".tex", ".md"]},
        )

    def render_markdown(self, source_file: Path, output_name: str | None = None) -> Path:
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

        logger.info(f"Rendering markdown to PDF: {source_file.name} -> {output_file.name}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            return output_file

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to render markdown to PDF: {e.stderr}",
                context={"source": str(source_file), "target": str(output_file)},
            ) from e

    def _repair_truncated_aux(self, aux_file: Path) -> None:
        """Repair a truncated .aux file by removing the last incomplete entry.

        xelatex has an internal write-buffer limit. On documents that produce
        large .aux files (>80 KB from many figures, cross-references, and
        labels), the .aux may be truncated mid-entry (e.g., an incomplete
        \\newlabel or \\@writefile with unmatched braces). This is an inherent
        xelatex behavior on large documents, not caused by signal handling.

        The resulting 'File ended while scanning use of \\@newl@bel' error
        prevents subsequent xelatex passes from completing. This method
        detects and removes the last incomplete entry so bibtex and later
        passes can read the .aux cleanly.
        """
        if not aux_file.exists():
            return

        try:
            content = aux_file.read_text(encoding="utf-8", errors="replace")
            if not content:
                return

            lines = content.split("\n")

            # Remove trailing empty lines
            while lines and not lines[-1].strip():
                lines.pop()

            if not lines:
                return

            # Check if the last line has balanced braces
            last_line = lines[-1]
            brace_depth = last_line.count("{") - last_line.count("}")

            if brace_depth != 0:
                # Last line is incomplete — remove it
                removed = lines.pop()
                logger.info(
                    f"  ✓ Repaired truncated .aux: removed incomplete entry "
                    f"({len(removed)} chars, brace depth {brace_depth})"
                )

                # Also check the new last line in case multiple lines were truncated
                while lines and lines[-1].strip():
                    new_last = lines[-1]
                    depth = new_last.count("{") - new_last.count("}")
                    if depth != 0:
                        lines.pop()
                    else:
                        break

                # Write the repaired content
                _tmp = aux_file.with_suffix(aux_file.suffix + ".tmp")
                try:
                    _tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    _tmp.replace(aux_file)
                except Exception:
                    _tmp.unlink(missing_ok=True)
                    raise
        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — .aux repair is best-effort; skip on failure
            logger.debug(f"  .aux repair skipped: {e}")

    def _validate_pdf_structure(self, pdf_path: Path) -> bool:
        """Check that a PDF file has valid trailer markers.

        A structurally valid PDF must end with a cross-reference table
        (``xref`` or ``startxref``) and a ``%%EOF`` marker.  When xelatex
        is killed by SIGPIPE (exit 141), the file may be truncated before
        these markers are written, producing a file that opens partially
        or not at all in some readers.

        Args:
            pdf_path: Path to the PDF file to validate.

        Returns:
            True if the PDF has valid structure, False otherwise.
        """
        try:
            with open(pdf_path, "rb") as f:
                # Read the last 4 KB — xref + EOF are at the very end
                f.seek(0, 2)  # seek to end
                size = f.tell()
                tail_size = min(size, 4096)
                f.seek(size - tail_size)
                tail = f.read(tail_size)

            has_eof = b"%%EOF" in tail
            has_startxref = b"startxref" in tail
            if not has_eof or not has_startxref:
                logger.debug(
                    f"  PDF validation: %%EOF={has_eof}, startxref={has_startxref} "
                    f"in {pdf_path.name} ({size:,} bytes)"
                )
                return False
            return True
        except Exception as e:  # noqa: BLE001 — LaTeX subprocess exceptions vary
            logger.debug(f"  PDF validation skipped: {e}")
            return False

    def _process_bibliography(self, tex_file: Path, output_dir: Path, bib_file: Path) -> bool:
        """Process bibliography using bibtex/biber.

        Copies the .bib file into the compilation directory (BibTeX's paranoid mode
        restricts cross-directory access), then runs bibtex against the .aux file.
        """
        # Check if bibliography file exists
        if not bib_file.exists():
            logger.warning(
                f"Bibliography file not found: {bib_file} (bibliography processing will be skipped)"  # noqa: E501
            )
            return False

        # Determine which bibliography processor to use
        bibtex_cmd = "bibtex"
        aux_file = output_dir / f"{tex_file.stem}.aux"

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

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(output_dir), timeout=600)

            if result.returncode != 0 and result.stderr.strip():
                logger.warning(f"Bibliography processing warning: {result.stderr[:200]}")
                # Don't fail on warnings - bibtex often returns non-zero for minor issues

            logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
            return True

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Bibliography processing failed: {e}", exc_info=True)
            return False

    def _check_brace_balance(self, md_content: str) -> list[str]:
        """Check markdown content for unbalanced braces.

        Performs three checks:
        1. Balanced braces in section header attributes {#id}
        2. Balanced braces in header lines
        3. Character-by-character brace balance outside code blocks and LaTeX commands

        Args:
            md_content: Raw markdown string to validate

        Returns:
            List of warning message strings (empty if no issues found)
        """
        warnings: list[str] = []

        # Check balanced braces in section header attributes
        header_attr_pattern = r"\{#([a-zA-Z0-9_:.-]+)"
        for attr in re.findall(header_attr_pattern, md_content):
            if attr.count("{") != attr.count("}"):
                warnings.append(f"Unbalanced braces in section header attribute: {{#{attr}}}")

        # Check balanced braces in full header lines
        for header_line in re.findall(r"^#+\s+.*\{#.*$", md_content, re.MULTILINE):
            if header_line.count("{") != header_line.count("}"):
                warnings.append(f"Unbalanced braces in header line: {header_line[:80]}")

        # Character-by-character brace balance outside code blocks and LaTeX commands
        # Strip fenced and inline code blocks first to avoid false positives
        content = re.sub(r"```.*?```", "", md_content, flags=re.DOTALL)
        content = re.sub(r"`[^`]+`", "", content)

        brace_count = 0
        in_latex_cmd = False
        i = 0
        while i < len(content):
            char = content[i]
            if char == "\\" and i < len(content) - 1 and content[i + 1].isalpha():
                # Skip LaTeX command name
                j = i + 2
                while j < len(content) and content[j].isalpha():
                    j += 1
                # Skip optional argument [...]
                if j < len(content) and content[j] == "[":
                    depth = 1
                    j += 1
                    while j < len(content) and depth > 0:
                        if content[j] == "[":
                            depth += 1
                        elif content[j] == "]":
                            depth -= 1
                        j += 1
                # Skip required argument {...}
                if j < len(content) and content[j] == "{":
                    depth = 1
                    j += 1
                    while j < len(content) and depth > 0:
                        if content[j] == "{":
                            depth += 1
                        elif content[j] == "}":
                            depth -= 1
                        j += 1
                i = j
                in_latex_cmd = False
                continue
            elif char == "{" and not in_latex_cmd:
                brace_count += 1
            elif char == "}" and not in_latex_cmd:
                brace_count -= 1
            in_latex_cmd = False
            i += 1

        if brace_count != 0:
            warnings.append(
                f"Potential unbalanced braces in markdown: "
                f"difference={brace_count} (positive=more {{, negative=more }})"
            )

        return warnings

    def _build_pandoc_render_error(
        self,
        e: "subprocess.CalledProcessError",
        combined_md: Path,
        source_files: list[Path],
        md_content: str,
        pandoc_cmd: list[str],
    ) -> "RenderingError":
        """Parse a CalledProcessError from pandoc and build a RenderingError with full context.

        Args:
            e: The CalledProcessError raised by subprocess.run
            combined_md: Path to the combined markdown input file
            source_files: Ordered list of source markdown files
            md_content: Content of combined_md (may be empty string if unread)
            pandoc_cmd: The pandoc command list (for diagnostics)

        Returns:
            RenderingError with parsed error message, position info, and source attribution
        """
        error_msg = "Failed to convert markdown to LaTeX"

        # Combine stderr and stdout for comprehensive error extraction
        all_output = ""
        if e.stderr:
            all_output += f"STDERR:\n{e.stderr}\n"
        if e.stdout:
            all_output += f"STDOUT:\n{e.stdout}\n"

        # Parse output for structured error lines and position
        error_lines: list[str] = []
        position_info: int | None = None

        for label, text in [("Pandoc Error", e.stderr), ("Pandoc Error (stdout)", e.stdout)]:
            if not text:
                continue
            for line in text.strip().split("\n"):
                line_lower = line.lower()
                has_position = "position" in line_lower and (
                    "unbalanced" in line_lower or "parenthesis" in line_lower or "error" in line_lower
                )
                has_error = "unbalanced" in line_lower or "parenthesis" in line_lower
                if has_position:
                    formatted = f"{label}: {line}"
                    if formatted not in error_lines:
                        error_lines.append(formatted)
                    if position_info is None:
                        pos_match = re.search(r"position\s+(\d+)", line_lower)
                        if pos_match:
                            position_info = int(pos_match.group(1))
                elif has_error or ("error" in line_lower and line.strip()):
                    candidate = f"{label.split()[0]}: {line}"
                    if candidate not in error_lines:
                        error_lines.append(candidate)

        if error_lines:
            error_msg += "\n\n" + "\n".join(error_lines)
        if all_output:
            error_msg += f"\n\nFull Pandoc output:\n{all_output}"
        elif not error_lines:
            error_msg += f"\n\nPandoc failed with return code {e.returncode} (no output captured)"

        context_info: dict = {"source": str(combined_md), "target": str(combined_md.with_suffix(".tex"))}
        suggestions: list[str] = []

        if combined_md.exists():
            try:
                if not md_content:
                    md_content = combined_md.read_text(encoding="utf-8")
                context_info["total_size"] = len(md_content)

                if position_info is not None:
                    pos = position_info
                    start = max(0, pos - 150)
                    end = min(len(md_content), pos + 150)
                    context_info["error_position"] = pos
                    context_info["error_context"] = md_content[start:end]
                    line_num = md_content[:pos].count("\n") + 1
                    context_info["error_line"] = line_num
                    lines = md_content.split("\n")
                    if line_num <= len(lines):
                        context_info["error_line_content"] = lines[line_num - 1]
                    suggestions.append(
                        f"Check character position {pos} (line {line_num}) in combined markdown file"
                    )
                    suggestions.append(
                        f"Review content around position: {repr(md_content[max(0, pos - 20):min(len(md_content), pos + 20)])}"
                    )
                else:
                    context_info["first_200_chars"] = md_content[:200]
                    context_info["last_200_chars"] = md_content[-200:]

                if "unbalanced" in error_msg.lower() or "parenthesis" in error_msg.lower():
                    suggestions += [
                        "Check for unmatched parentheses, brackets, or braces in markdown",
                        "Verify LaTeX commands have properly matched delimiters",
                        "Review math expressions for balanced parentheses",
                    ]

                suggestions.append(f"Inspect combined markdown file: {combined_md}")
                suggestions.append(
                    "Try converting individual markdown files to identify the problematic file"
                )
            except Exception as ex:  # noqa: BLE001 — LaTeX subprocess exceptions vary
                logger.debug(f"Error gathering context: {ex}")
                suggestions.append(f"Could not read combined markdown file: {ex}")

        suggestions += [
            "Verify all markdown files are valid",
            "Check for special characters or encoding issues",
            "Ensure LaTeX commands in markdown are properly formatted",
            f"Review Pandoc command: {' '.join(pandoc_cmd)}",
        ]

        # Log full details
        logger.error(f"Pandoc conversion failed: {error_msg}")
        if context_info.get("error_position") is not None:
            pos = context_info["error_position"]
            line = context_info.get("error_line", "unknown")
            logger.error(f"  Error at position {pos} (line {line}) in combined markdown")
            if md_content and pos < len(md_content):
                start = max(0, pos - 20)
                end = min(len(md_content), pos + 20)
                logger.error(f"  Characters around position {pos}: {repr(md_content[start:end])}")
                logger.error(f"  Character-by-character analysis (position {pos}):")
                for i in range(max(0, pos - 5), min(len(md_content), pos + 6)):
                    marker = " >>> " if i == pos else "     "
                    char = md_content[i]
                    logger.error(f"    {marker}Position {i}: {repr(char)} (ord: {ord(char)})")
        if context_info.get("error_context"):
            logger.error(f"  Context around error:\n{context_info['error_context']}")
        logger.error(f"  Combined markdown file saved at: {combined_md}")
        logger.error(f"  Combined markdown file size: {len(md_content)} characters")

        # Attribute error to source file if position is known
        if position_info is not None and md_content:
            current_pos = 0
            for i, source_file in enumerate(source_files):
                try:
                    file_content = source_file.read_text(encoding="utf-8")
                    file_content_processed = file_content.rstrip() + "\n"
                    file_size = len(file_content_processed)
                    separator_size = (
                        len("\n```{=latex}\n\\newpage\n```\n") if i < len(source_files) - 1 else 0
                    )

                    if current_pos <= position_info < current_pos + file_size:
                        context_info["problematic_file"] = str(source_file)
                        context_info["problematic_file_index"] = i + 1
                        logger.error(
                            f"  Error likely in source file {i + 1}/{len(source_files)}: {source_file.name}"
                        )
                        file_pos = position_info - current_pos
                        line_num = file_content[:file_pos].count("\n") + 1
                        logger.error(f"  Position within file: {file_pos} (line {line_num})")
                        start = max(0, file_pos - 50)
                        end = min(len(file_content), file_pos + 50)
                        context_snippet = file_content[start:end]
                        logger.error(f"  Context in source file (chars {start}-{end}):")
                        snippet_lines = context_snippet.split("\n")
                        if len(snippet_lines) <= 10:
                            for j, snippet_line in enumerate(snippet_lines):
                                actual_line = line_num - (len(snippet_lines) - j - 1)
                                marker = (
                                    " >>> "
                                    if start + sum(len(l) + 1 for l in snippet_lines[:j]) <= file_pos
                                    < start + sum(len(l) + 1 for l in snippet_lines[: j + 1])
                                    else "     "
                                )
                                logger.error(f"    {marker}Line {actual_line}: {repr(snippet_line)}")
                        else:
                            logger.error(f"    {repr(context_snippet)}")
                        if file_pos < len(file_content):
                            char_at_pos = file_content[file_pos]
                            logger.error(
                                f"  Character at error position: {repr(char_at_pos)} (ord: {ord(char_at_pos)})"
                            )
                        break

                    current_pos += file_size + separator_size
                except (OSError, ValueError) as ex:  # noqa: BLE001 — error context gathering is best-effort
                    logger.debug(f"Error analyzing file {i + 1} ({source_file.name}): {ex}")

        return RenderingError(error_msg, context=context_info, suggestions=suggestions)

    def render_combined(
        self,
        source_files: list[Path],
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
            logger.info(f"  [{i:>2}/{len(source_files)}] {md_file.name:<40} ({size_kb:>6.1f} KB)")

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
        _tmp = combined_md.with_suffix(combined_md.suffix + ".tmp")
        try:
            _tmp.write_text(combined_content, encoding="utf-8")
            _tmp.replace(combined_md)
        except Exception:
            _tmp.unlink(missing_ok=True)
            raise
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
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",  # Preserve LaTeX math, raw blocks, and header attributes like {#sec:...}  # noqa: E501
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

        logger.info("Converting combined markdown to LaTeX...")
        logger.debug(f"Combined markdown file: {combined_md}")

        # Pre-validate combined markdown for common issues
        validation_errors = []
        md_content = ""
        if combined_md.exists():
            try:
                md_content = combined_md.read_text(encoding="utf-8")

                # Validate basic markdown structure for common issues that Pandoc reports poorly.
                # NOTE: We do not check parentheses inside math blocks — the regex patterns
                # for $...$ and $$...$$ produce false positives for valid LaTeX like
                # H(\mathcal{F}_c) or (\cref{sec:omega4}). LaTeX compilation handles those.
                validation_errors = self._check_brace_balance(md_content)

                if validation_errors:
                    logger.warning(
                        f"Pre-validation found {len(validation_errors)} potential issue(s):"
                    )
                    for err in validation_errors:
                        logger.warning(f"  • {err}")
                    # Note: These are warnings only, don't block PDF generation
                    logger.info("  (These are warnings - PDF generation will proceed)")
            except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001 — pre-validation is advisory; PDF generation continues
                logger.debug(f"Pre-validation check failed: {e}")
                # Try to read content anyway for error reporting
                try:
                    md_content = combined_md.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as read_err:
                    logger.debug(f"Failed to read markdown for error reporting: {read_err}")

        try:
            subprocess.run(pandoc_to_tex, check=True, capture_output=True, text=True, timeout=600)
        except subprocess.CalledProcessError as e:
            raise self._build_pandoc_render_error(e, combined_md, source_files, md_content, pandoc_to_tex) from e

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
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"Math delimiter fixing failed: {e}. Continuing with original LaTeX content."
            )
            logger.debug(f"Math delimiter fixing error details: {type(e).__name__}: {e}")
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
                logger.warning("⚠️  Preamble file found but no LaTeX content extracted")
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
                    lines = title_page_preamble.split("\n")
                    filtered_lines = []
                    for line in lines:
                        # We want to inject our formatted metadata even if Pandoc generated some.
                        # Since we append to combined_preamble which is inserted before \begin{document}  # noqa: E501
                        # (likely after Pandoc's preamble), our definitions should take precedence or at least exist.  # noqa: E501
                        # For \author and \date, redefinition is standard.
                        filtered_lines.append(line)

                    if filtered_lines:
                        combined_preamble += "\n".join(filtered_lines) + "\n\n"

                # Insert overrides (preamble.md) second
                if preamble_content:
                    combined_preamble += preamble_content + "\n\n"

                # Insert before \begin{document}
                tex_content = (
                    tex_content[:begin_doc_idx] + combined_preamble + tex_content[begin_doc_idx:]
                )
                logger.debug(
                    f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}"  # noqa: E501
                )

        # Insert title page body commands AFTER \begin{document}
        if title_page_body:
            # We want to ensure our custom title page body is used and we also
            # want a table of contents and a newpage.
            full_title_body = title_page_body + "\n\\tableofcontents\n\\newpage"

            begin_doc_idx = tex_content.find("\\begin{document}")
            if begin_doc_idx > 0:
                tex_preamble = tex_content[:begin_doc_idx]
                tex_body = tex_content[begin_doc_idx:]
                
                # Check if \maketitle is already present in the body
                if "\\maketitle" in tex_body:
                    logger.debug(
                        "✓ \\maketitle already present in LaTeX body - replacing with our full title/TOC body"  # noqa: E501
                    )
                    # Find the first occurrence of \maketitle in the body and replace it
                    tex_body = tex_body.replace("\\maketitle", full_title_body, 1)
                else:
                    # Find position right after \begin{document}
                    end_of_begin_doc = tex_body.find("\n") + 1
                    if end_of_begin_doc > 0:
                        # Insert full title body and formatting after \begin{document}
                        tex_body = (
                            tex_body[:end_of_begin_doc]
                            + "\n"
                            + full_title_body
                            + "\n\n"
                            + tex_body[end_of_begin_doc:]
                        )
                    logger.info(
                        r"✓ Inserted title page (\maketitle), TOC, and newpage after \begin{document}"  # noqa: E501
                    )
                
                tex_content = tex_preamble + tex_body

        # Insert \bibliography{references} before \end{document} if not already present.
        # Pandoc's --natbib flag generates \bibliographystyle{plainnat} in the preamble
        # but does NOT generate \bibliography{} unless used with --citeproc.
        # We insert it here using the same style (plainnat) to avoid conflicts.
        if bib_exists and "\\bibliography{" not in tex_content:
            end_doc_idx = tex_content.rfind("\\end{document}")
            if end_doc_idx > 0:
                tex_content = (
                    tex_content[:end_doc_idx]
                    + "\n\n\\bibliography{references}\n"
                    + tex_content[end_doc_idx:]
                )
                logger.info("✓ Inserted \\bibliography{references} before \\end{document}")
            else:
                logger.warning("⚠️  Could not find \\end{document} to insert bibliography")

        # Ensure \bibdata{references} is written to .aux early via an \AtBeginDocument hook.
        # xelatex has internal write-buffer limits that truncate the .aux file on large
        # documents (>80 KB). When \bibliography{references} is at the end of the document,
        # its \bibdata entry may be lost in the truncated tail. Writing it at document
        # start guarantees bibtex can always find the bibliography database.
        if bib_exists:
            bibdata_hook = (
                "\\makeatletter\n"
                "\\AtBeginDocument{\\immediate\\write\\@auxout{\\string\\bibdata{references}}}\n"
                "\\makeatother\n"
            )
            begin_doc_idx = tex_content.find("\\begin{document}")
            if begin_doc_idx > 0:
                tex_content = (
                    tex_content[:begin_doc_idx] + bibdata_hook + tex_content[begin_doc_idx:]
                )
                logger.info("✓ Inserted early \\bibdata hook for .aux buffer safety")

        _tmp = combined_tex.with_suffix(combined_tex.suffix + ".tmp")
        try:
            _tmp.write_text(tex_content)
            _tmp.replace(combined_tex)
        except Exception:
            _tmp.unlink(missing_ok=True)
            raise

        # Verify figure files exist before compilation
        figures_dir = manuscript_dir.parent / "output" / "figures"

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
                            logger.debug(f"    Similar files found: {', '.join(similar)}")

            logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
            if missing_figures:
                logger.warning(
                    f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}"
                )
                if len(missing_figures) > 5:
                    logger.warning(f"  ... and {len(missing_figures) - 5} more missing figures")

        # Compile LaTeX to PDF with multi-pass xelatex
        return self._compile_latex_to_pdf(
            combined_tex=combined_tex,
            combined_md=combined_md,
            output_dir=output_dir,
            output_file=output_file,
            bib_file=bib_file,
            bib_exists=bib_exists,
            source_files=source_files,
        )

    def _compile_latex_to_pdf(
        self,
        combined_tex: Path,
        combined_md: Path,
        output_dir: Path,
        output_file: Path,
        bib_file: Path,
        bib_exists: bool,
        source_files: list[Path],
    ) -> Path:
        """Run multi-pass xelatex compilation with bibliography processing.

        Args:
            combined_tex: Path to the combined .tex file
            combined_md: Path to the combined .md file (for logging)
            output_dir: Directory for compilation output
            output_file: Final PDF output path
            bib_file: Path to bibliography file
            bib_exists: Whether bibliography file exists
            source_files: Original source files (for logging)

        Returns:
            Path to generated PDF

        Raises:
            RenderingError: If compilation fails
        """
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

        start_time = time.time()

        logger.info(f"Rendering combined manuscript to PDF: {output_file.name}")
        logger.info(f"  Source files: {len(source_files)}")
        if bib_exists:
            logger.info(f"  Bibliography: {bib_file.name}")
        logger.debug(f"  Output directory: {output_dir}")
        logger.debug(f"  Combined TeX file: {combined_tex.name}")
        logger.debug(f"  Combined MD file: {combined_md.name}")

        try:
            # Run xelatex with bibliography processing for proper cross-references, TOC, and bibliography  # noqa: E501
            # Pass 1: Initial xelatex compilation
            # Pass 2: Bibtex processing (if bibliography exists)
            # Pass 3-4: Additional xelatex passes for reference resolution

            # Temporary PDF file created during compilation (before renaming to final output)
            temp_pdf = output_dir / "_combined_manuscript.pdf"

            # Clean stale auxiliary files before compilation to prevent corruption.
            # A corrupted .aux from a previous build (e.g., truncated figure caption labels
            # with unmatched braces) causes "File ended while scanning use of \@newl@bel"
            # and prevents bibtex from finding \bibdata, making all citations undefined.
            stale_extensions = [".aux", ".bbl", ".blg", ".toc", ".out", ".lof", ".lot"]
            tex_stem = combined_tex.stem
            for ext in stale_extensions:
                stale_file = output_dir / f"{tex_stem}{ext}"
                if stale_file.exists():
                    stale_file.unlink()
                    logger.debug(f"  Cleaned stale auxiliary file: {stale_file.name}")

            logger.info("  LaTeX compilation pass 1/4...")
            # Redirect stdout/stderr to a log file instead of DEVNULL.
            # Using DEVNULL causes SIGPIPE (exit 141) when xelatex's
            # -shell-escape child processes (e.g. extractbb) write to
            # a broken pipe. SIGPIPE kills xelatex before it writes the
            # xref table and %%EOF marker, producing a truncated PDF.
            # Writing to a file keeps the pipe open and avoids SIGPIPE.
            SIGPIPE_EXIT = 141  # 128 + signal 13 (SIGPIPE)
            xelatex_stdout_log = output_dir / "_xelatex_stdout.log"
            with open(xelatex_stdout_log, "w") as stdout_sink:
                result = subprocess.run(
                    cmd, check=False,
                    stdout=stdout_sink, stderr=subprocess.STDOUT,
                    cwd=str(output_dir),
                    timeout=600,
                )

            # Repair truncated .aux file after each pass.
            # xelatex's internal write-buffer limits may truncate the .aux on
            # documents with >~80 KB of auxiliary data (many figures, labels, etc.).
            aux_file = output_dir / f"{tex_stem}.aux"
            self._repair_truncated_aux(aux_file)

            # Check for critical errors on first pass using the .log file.
            # Exit code 141 (SIGPIPE) is expected on large documents and not fatal.
            log_file = output_dir / "_combined_manuscript.log"
            log_content = log_file.read_text() if log_file.exists() else ""
            is_fatal = result.returncode > 1 and result.returncode != SIGPIPE_EXIT
            if "Fatal error occurred" in log_content or (
                is_fatal and not temp_pdf.exists()
            ):
                raise RenderingError(
                    "XeLaTeX compilation failed (pass 1)",
                    context={"source": str(combined_tex), "output": str(output_file)},
                )
            if result.returncode == SIGPIPE_EXIT:
                logger.debug(f"  xelatex exited with {SIGPIPE_EXIT} (SIGPIPE) — expected on large documents")

            # Process bibliography if it exists
            if bib_exists:
                logger.info("  Bibliography processing...")
                try:
                    self._process_bibliography(combined_tex, output_dir, bib_file)
                except Exception as bib_error:  # noqa: BLE001 — bibtex/biber exceptions vary
                    logger.warning(f"  Bibliography processing failed: {bib_error}")
                    logger.warning("  Continuing PDF generation without bibliography processing")
                    # Don't fail the entire PDF generation for bibliography issues

            # Additional passes for reference resolution (especially after bibtex)
            max_passes = 4
            consecutive_failures = 0
            max_consecutive_failures = 2

            for run in range(1, max_passes):
                log_progress_bar(run + 1, max_passes, "LaTeX compilation", bar_width=20)
                with open(xelatex_stdout_log, "w") as stdout_sink:
                    result = subprocess.run(
                        cmd,
                        check=False,
                        stdout=stdout_sink,
                        stderr=subprocess.STDOUT,
                        cwd=str(output_dir),
                        timeout=600,
                    )

                # Repair truncated .aux after each pass
                self._repair_truncated_aux(aux_file)

                # Check for critical errors using .log file
                # Exit code 141 (SIGPIPE) is expected on large documents and not fatal.
                log_content = log_file.read_text() if log_file.exists() else ""
                is_fatal = result.returncode > 1 and result.returncode != SIGPIPE_EXIT
                if "Fatal error occurred" in log_content or is_fatal:
                    consecutive_failures += 1

                    if output_file.exists():
                        logger.warning(f"PDF generated but with warnings (run {run + 1})")
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
                                        "Verify LaTeX packages: python3 -m infrastructure.rendering.latex_package_validator",  # noqa: E501
                                        "Update TeX Live: sudo tlmgr update --self",
                                        f"Check log file for details: {log_file}",
                                    ],
                                )

                            # Check for other recoverable errors
                            if consecutive_failures >= max_consecutive_failures:
                                raise RenderingError(
                                    f"LaTeX compilation failed after {consecutive_failures} consecutive attempts",  # noqa: E501
                                    context={
                                        "source": str(combined_tex),
                                        "log_file": str(log_file),
                                        "last_error": (
                                            result.stderr[:500] if result.stderr else "No stderr"
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
                                f"LaTeX compilation failed (run {run + 1}), continuing..."
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
                                        "Verify BasicTeX packages: python3 -m infrastructure.rendering.latex_package_validator",  # noqa: E501
                                        "Update TeX Live: sudo tlmgr update --self",
                                        "Or install full MacTeX instead of BasicTeX: https://www.tug.org/mactex/",
                                        f"Check log file for details: {log_file}",
                                    ],
                                )
                            else:
                                raise RenderingError(
                                    f"XeLaTeX compilation failed (run {run + 1})",
                                    context={
                                        "source": str(combined_tex),
                                        "output": str(output_file),
                                    },
                                    suggestions=[
                                        "Check LaTeX log file for detailed error messages",
                                        "Verify all required packages are installed",
                                        "Ensure figure paths are correct relative to output directory",  # noqa: E501
                                        "Run: python3 -m infrastructure.rendering.latex_package_validator",  # noqa: E501
                                        "Run with --verbose flag for detailed compilation output",
                                    ],
                                )

                # Check log file for unresolved references or TOC changes
                log_file = output_dir / "_combined_manuscript.log"
                if log_file.exists():
                    log_content = log_file.read_text()
                    # If no warnings/issues found, we can stop early
                    if "Rerun" not in log_content and "undefined" not in log_content.lower():
                        logger.info(f"  All references resolved after pass {run + 1}")
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

            # Check if the temporary PDF was created, validate, and rename it
            if temp_pdf.exists():
                # Validate PDF structure before accepting it
                if not self._validate_pdf_structure(temp_pdf):
                    logger.warning(
                        "PDF structurally invalid (truncated xref/%%EOF). "
                        "Re-running xelatex for recovery pass..."
                    )
                    with open(xelatex_stdout_log, "w") as stdout_sink:
                        subprocess.run(
                            cmd, check=False,
                            stdout=stdout_sink, stderr=subprocess.STDOUT,
                            cwd=str(output_dir),
                            timeout=600,
                        )
                    if not self._validate_pdf_structure(temp_pdf):
                        logger.warning(
                            "PDF still invalid after recovery pass. "
                            "Proceeding with best-effort output."
                        )
                # Rename temporary PDF to final name
                temp_pdf.rename(output_file)
                # Log successful combination with output size
                if output_file.exists():
                    self._log_pdf_success(output_file, source_files, start_time)

                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
                return output_file
            elif output_file.exists():
                # Log successful combination with output size
                self._log_pdf_success(output_file, source_files, start_time)

                # Note: Temporary files (_combined_manuscript.md, .tex, .log, .bbl, .aux)
                # are preserved for debugging and reference purposes
                return output_file
            else:
                raise RenderingError(
                    "PDF file was not created",
                    context={"source": str(combined_tex), "output": str(output_file)},
                )

        except subprocess.CalledProcessError as e:
            raise RenderingError(
                f"Failed to compile LaTeX to PDF: {e.stderr or e.stdout}",
                context={"source": str(combined_tex), "output": str(output_file)},
            ) from e

    def _log_pdf_success(
        self, output_file: Path, source_files: list[Path], start_time: float
    ) -> None:
        """Log successful PDF generation with size and duration metrics."""
        output_size_kb = output_file.stat().st_size / 1024
        logger.info(f"\nSuccessfully combined {len(source_files)} sections")
        logger.info(f"   Output: {output_file.name}")
        logger.info(f"   Size: {output_size_kb:.1f} KB ({output_size_kb / 1024:.2f} MB)")
        logger.info(f"   Location: {output_file.parent}")
        end_time = time.time()
        total_duration = end_time - start_time
        logger.info(f"   Duration: {total_duration:.2f} seconds")

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

                # Validate section header syntax in this file

                header_attrs = re.findall(r"\{#([^}]+)\}", content)
                for attr in header_attrs:
                    # Check for balanced braces
                    if attr.count("{") != attr.count("}"):
                        logger.warning(
                            f"Potential unbalanced braces in {md_file.name} header attribute: {{#{attr}}}"  # noqa: E501
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
                ) from e
            except Exception as e:  # noqa: BLE001
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

        # Validate basic structure - check for common issues at the start
        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if combined.startswith("\ufeff"):
            logger.warning("Removing UTF-8 BOM from combined markdown")
            combined = combined[1:]

        # Ensure the file doesn't start with problematic characters
        # Pandoc might complain about certain characters at position 0
        if combined and combined[0] in ["(", ")", "[", "]", "{", "}"]:
            logger.warning(
                f"Combined markdown starts with potentially problematic character: {repr(combined[0])}"  # noqa: E501
            )

        return combined

    def _extract_preamble(self, preamble_file: Path) -> str:
        """Extract LaTeX preamble from markdown file. Delegates to module-level helper."""
        return extract_preamble(preamble_file)

    def _fix_figure_paths(self, tex_content: str, manuscript_dir: Path, output_dir: Path) -> str:
        """Fix figure paths in LaTeX content. Delegates to module-level helper."""
        return fix_figure_paths(tex_content, manuscript_dir, output_dir)

    def _fix_math_delimiters(self, tex_content: str) -> str:
        """Fix broken math delimiters from Pandoc conversion. Delegates to module-level helper."""
        return fix_math_delimiters(tex_content)

    def _check_latex_log_for_graphics_errors(self, log_file: Path) -> dict[str, list[str]]:
        """Parse LaTeX log for graphics errors. Delegates to module-level helper."""
        return check_latex_log_for_graphics_errors(log_file)

    def _generate_title_page_preamble(self, manuscript_dir: Path) -> str:
        """Generate title page preamble from config.yaml. Delegates to module-level helper."""
        return generate_title_page_preamble(manuscript_dir)

    def _generate_title_page_body(self, manuscript_dir: Path) -> str:
        """Generate title page body from config.yaml. Delegates to module-level helper."""
        return generate_title_page_body(manuscript_dir)
