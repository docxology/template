"""Markdown integration utilities for figure insertion.

Provides section detection and LaTeX figure block insertion into
markdown manuscript files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from .logging import get_logger

logger = get_logger(__name__)


class MarkdownIntegration:
    """Markdown integration for inserting figures into manuscript sections."""

    def __init__(self, manuscript_dir: Path) -> None:
        """Initialize with manuscript directory.

        Args:
            manuscript_dir: Path to manuscript directory
        """
        self.manuscript_dir = Path(manuscript_dir)

    def detect_sections(self, markdown_file: Path) -> List[str]:
        """Detect section headings in a markdown file.

        Args:
            markdown_file: Path to markdown file

        Returns:
            List of section heading strings found in the file
        """
        sections = []
        try:
            content = markdown_file.read_text()
            # Match ## headings (level 2 sections)
            for match in re.finditer(r"^(#{1,3})\s+(.+)$", content, re.MULTILINE):
                sections.append(match.group(2).strip())
        except Exception as e:
            logger.error(f"Error detecting sections in {markdown_file.name}: {e}")
        return sections

    def insert_figure_in_section(
        self,
        markdown_file: Path,
        figure_label: str,
        section: str,
        width: float = 0.8,
        caption: str = "",
        filename: str = "",
    ) -> bool:
        """Insert a LaTeX figure block after a specified section.

        Args:
            markdown_file: Path to the markdown file
            figure_label: LaTeX label for the figure (e.g. 'fig:quadrant_matrix')
            section: Section heading text to insert after
            width: Figure width as fraction of textwidth
            caption: Figure caption text
            filename: Figure filename relative to output/figures/

        Returns:
            True if insertion successful, False otherwise
        """
        try:
            content = markdown_file.read_text()

            # Check if figure already exists
            if f"\\label{{{figure_label}}}" in content:
                logger.info(
                    f"Figure {figure_label} already exists in {markdown_file.name}"
                )
                return True

            # Find the section header
            section_pattern = rf"^(#{{1,3}})\s+{re.escape(section)}"
            match = re.search(section_pattern, content, re.MULTILINE)

            if not match:
                logger.debug(
                    f"Section '{section}' not found in {markdown_file.name}"
                )
                return False

            # Find the end of this section (next same-level or higher heading)
            heading_level = len(match.group(1))
            section_end = match.end()
            next_pattern = r"^#{1," + str(heading_level) + r"}\s+"
            next_match = re.search(next_pattern, content[section_end:], re.MULTILINE)

            if next_match:
                insert_pos = section_end + next_match.start()
            else:
                insert_pos = len(content)

            # Build LaTeX figure block
            figure_block = (
                f"\n\n\\begin{{figure}}[h]\n"
                f"\\centering\n"
                f"\\includegraphics[width={width}\\textwidth]"
                f"{{../output/figures/{filename}}}\n"
                f"\\caption{{{caption}}}\n"
                f"\\label{{{figure_label}}}\n"
                f"\\end{{figure}}\n\n"
            )

            # Insert
            new_content = content[:insert_pos] + figure_block + content[insert_pos:]
            markdown_file.write_text(new_content)

            logger.info(
                f"Inserted {figure_label} in {markdown_file.name} "
                f"after '{section}'"
            )
            return True

        except Exception as e:
            logger.error(f"Error inserting figure {figure_label}: {e}")
            return False
