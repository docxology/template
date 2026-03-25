"""Pandoc conversion logic for PDF rendering."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def build_pandoc_render_error(
    e: subprocess.CalledProcessError,
    combined_md: Path,
    source_files: list[Path],
    md_content: str,
    pandoc_cmd: list[str],
) -> RenderingError:
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
                "unbalanced" in line_lower
                or "parenthesis" in line_lower
                or "error" in line_lower
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

    context_info: dict = {
        "source": str(combined_md),
        "target": str(combined_md.with_suffix(".tex")),
    }
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
                    f"Check character position {pos} "
                    f"(line {line_num}) in combined markdown file"
                )
                suggestions.append(
                    f"Review content around position: "
                    f"{repr(md_content[max(0, pos - 20) : min(len(md_content), pos + 20)])}"
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
        except Exception as ex:  # noqa: BLE001
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
                        f"  Error likely in source file "
                        f"{i + 1}/{len(source_files)}: {source_file.name}"
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
                                if start + sum(len(l) + 1 for l in snippet_lines[:j])
                                <= file_pos
                                < start + sum(len(l) + 1 for l in snippet_lines[: j + 1])
                                else "     "
                            )
                            logger.error(
                                f"    {marker}Line {actual_line}: {repr(snippet_line)}"
                            )
                    else:
                        logger.error(f"    {repr(context_snippet)}")
                    if file_pos < len(file_content):
                        char_at_pos = file_content[file_pos]
                        logger.error(
                            f"  Character at error position: "
                            f"{repr(char_at_pos)} (ord: {ord(char_at_pos)})"
                        )
                    break

                current_pos += file_size + separator_size
            except (OSError, ValueError) as ex:  # noqa: BLE001
                logger.debug(f"Error analyzing file {i + 1} ({source_file.name}): {ex}")

    return RenderingError(error_msg, context=context_info, suggestions=suggestions)
