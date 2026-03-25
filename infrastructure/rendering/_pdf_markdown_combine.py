"""Combine manuscript markdown sections for combined PDF rendering."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def combine_manuscript_markdown_sections(source_files: list[Path]) -> str:
    """Combine multiple markdown files into one document body.

    Args:
        source_files: Markdown files in manuscript order.

    Returns:
        Combined markdown content.

    Raises:
        RenderingError: If any file cannot be read or combined content is empty.
    """
    combined_parts: list[str] = []

    for i, md_file in enumerate(source_files):
        try:
            content = md_file.read_text(encoding="utf-8", errors="strict")

            if not content.endswith("\n"):
                content += "\n"

            content = content.rstrip() + "\n"

            header_attrs = re.findall(r"\{#([^}]+)\}", content)
            for attr in header_attrs:
                if attr.count("{") != attr.count("}"):
                    logger.warning(
                        "Potential unbalanced braces in %s header attribute: {#%s}",
                        md_file.name,
                        attr,
                    )

            combined_parts.append(content)

            if i < len(source_files) - 1:
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

    combined = "\n\n".join(combined_parts)
    combined = combined.lstrip("\n\r")

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

    if combined.startswith("\ufeff"):
        logger.warning("Removing UTF-8 BOM from combined markdown")
        combined = combined[1:]

    if combined and combined[0] in ["(", ")", "[", "]", "{", "}"]:
        logger.warning(
            "Combined markdown starts with potentially problematic character: %r",
            combined[0],
        )

    return combined
