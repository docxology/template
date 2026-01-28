"""File inventory and collection utilities.

This module provides utilities for collecting and managing file inventories
from output directories, extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class FileInventoryEntry:
    """Entry in file inventory."""

    path: Path
    size: int
    category: str
    modified: float

    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        return format_file_size(self.size)


class FileInventoryManager:
    """Manage file inventory and reports."""

    # Standard output categories to scan
    OUTPUT_CATEGORIES = [
        "pdf",
        "figures",
        "data",
        "reports",
        "simulations",
        "llm",
        "logs",
        "web",
        "slides",
        "tex",
    ]

    def collect_output_files(
        self, output_dir: Path, categories: Optional[List[str]] = None
    ) -> List[FileInventoryEntry]:
        """Collect all generated files from output directory.

        Args:
            output_dir: Base directory to scan (projects/project/output or output)
            categories: List of categories to scan (default: all standard categories)

        Returns:
            List of FileInventoryEntry objects
        """
        if categories is None:
            categories = self.OUTPUT_CATEGORIES

        entries = []

        # Check if output directory exists and is a directory
        exists_check = output_dir.exists()
        is_dir_check = output_dir.is_dir()

        if not exists_check or not is_dir_check:
            logger.warning(f"Output directory not found: {output_dir}")
            return entries

        # Scan each category directory
        for category in categories:
            category_dir = output_dir / category
            if category_dir.exists() and category_dir.is_dir():
                entries.extend(self._collect_files_in_directory(category_dir, category))

        # Also check for root-level files (like project_combined.pdf)
        root_files = ["project_combined.pdf"]
        for filename in root_files:
            file_path = output_dir / filename
            if file_path.exists() and file_path.is_file():
                try:
                    stat = file_path.stat()
                    entries.append(
                        FileInventoryEntry(
                            path=file_path,
                            size=stat.st_size,
                            category=self._guess_category_from_filename(filename),
                            modified=stat.st_mtime,
                        )
                    )
                except OSError as e:
                    logger.debug(f"Failed to stat file {file_path}: {e}")

        return entries

    def _collect_files_in_directory(
        self, directory: Path, category: str
    ) -> List[FileInventoryEntry]:
        """Collect all files in a directory recursively.

        Args:
            directory: Directory to scan
            category: Category name for these files

        Returns:
            List of FileInventoryEntry objects
        """
        entries = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        entries.append(
                            FileInventoryEntry(
                                path=file_path,
                                size=stat.st_size,
                                category=category,
                                modified=stat.st_mtime,
                            )
                        )
                    except OSError as e:
                        logger.debug(f"Failed to stat file {file_path}: {e}")
        except OSError as e:
            logger.debug(f"Failed to scan directory {directory}: {e}")

        return entries

    def _guess_category_from_filename(self, filename: str) -> str:
        """Guess category from filename.

        Args:
            filename: Name of file

        Returns:
            Guessed category name
        """
        if filename.endswith(".pdf"):
            return "pdf"
        elif filename.endswith((".png", ".jpg", ".jpeg", ".svg", ".eps")):
            return "figures"
        elif filename.endswith((".csv", ".json", ".npy", ".npz")):
            return "data"
        elif "log" in filename.lower():
            return "logs"
        else:
            return "misc"

    def generate_inventory_report(
        self,
        entries: List[FileInventoryEntry],
        output_format: str = "text",
        base_dir: Optional[Path] = None,
    ) -> str:
        """Generate inventory report (text, json, or html).

        Args:
            entries: List of file inventory entries
            output_format: Output format ("text", "json", or "html")
            base_dir: Base directory for relative paths (optional)

        Returns:
            Formatted inventory report
        """
        if not entries:
            return "No files found in output directory"

        if output_format == "json":
            return self._generate_json_report(entries, base_dir)
        elif output_format == "html":
            return self._generate_html_report(entries, base_dir)
        else:
            return self._generate_text_report(entries, base_dir)

    def _generate_text_report(
        self, entries: List[FileInventoryEntry], base_dir: Optional[Path] = None
    ) -> str:
        """Generate text format inventory report.

        Args:
            entries: File inventory entries
            base_dir: Base directory for relative paths

        Returns:
            Text report
        """
        if not entries:
            return "No files found"

        # Group by category
        category_groups = self._group_by_category(entries)

        lines = []
        lines.append("Generated Files Inventory:")
        lines.append("")

        # Display order for categories
        display_order = [
            "pdf",
            "figures",
            "data",
            "reports",
            "simulations",
            "llm",
            "logs",
            "web",
            "slides",
            "tex",
        ]

        for category in display_order:
            if category in category_groups:
                category_entries = category_groups[category]
                total_size = sum(entry.size for entry in category_entries)
                count = len(category_entries)

                # Use uppercase for known categories, title case for others
                category_name = (
                    category.upper() if category in ["pdf", "tex"] else category.title()
                )
                lines.append(
                    f"  {category_name} ({count} file(s), {format_file_size(total_size)}):"
                )

                # Show first 10 files, then count if more
                shown_count = 0
                for entry in sorted(category_entries, key=lambda e: e.path):
                    if shown_count >= 10:
                        remaining = len(category_entries) - 10
                        if remaining > 0:
                            lines.append(f"    ... and {remaining} more file(s)")
                        break

                    rel_path = (
                        entry.path.relative_to(base_dir) if base_dir else entry.path
                    )
                    lines.append(f"    - {rel_path} ({entry.size_formatted})")
                    shown_count += 1

                lines.append("")

        return "\n".join(lines)

    def _generate_json_report(
        self, entries: List[FileInventoryEntry], base_dir: Optional[Path] = None
    ) -> str:
        """Generate JSON format inventory report.

        Args:
            entries: File inventory entries
            base_dir: Base directory for relative paths

        Returns:
            JSON report
        """
        import json

        # Group by category
        category_groups = self._group_by_category(entries)

        # Convert to JSON-serializable format
        result = {}
        for category, category_entries in category_groups.items():
            result[category] = {
                "count": len(category_entries),
                "total_size": sum(entry.size for entry in category_entries),
                "total_size_formatted": format_file_size(
                    sum(entry.size for entry in category_entries)
                ),
                "files": [
                    {
                        "path": (
                            str(entry.path.relative_to(base_dir))
                            if base_dir
                            else str(entry.path)
                        ),
                        "size": entry.size,
                        "size_formatted": entry.size_formatted,
                        "modified": entry.modified,
                    }
                    for entry in sorted(category_entries, key=lambda e: e.path)
                ],
            }

        return json.dumps(result, indent=2)

    def _generate_html_report(
        self, entries: List[FileInventoryEntry], base_dir: Optional[Path] = None
    ) -> str:
        """Generate HTML format inventory report.

        Args:
            entries: File inventory entries
            base_dir: Base directory for relative paths

        Returns:
            HTML report
        """
        if not entries:
            return "<p>No files found in output directory</p>"

        # Group by category
        category_groups = self._group_by_category(entries)

        html_parts = []
        html_parts.append("<div class='file-inventory'>")
        html_parts.append("<h3>Generated Files Inventory</h3>")

        # Display order for categories
        display_order = [
            "pdf",
            "figures",
            "data",
            "reports",
            "simulations",
            "llm",
            "logs",
            "web",
            "slides",
            "tex",
        ]

        for category in display_order:
            if category in category_groups:
                category_entries = category_groups[category]
                total_size = sum(entry.size for entry in category_entries)
                count = len(category_entries)

                # Use uppercase for known categories, title case for others
                category_name = (
                    category.upper() if category in ["pdf", "tex"] else category.title()
                )
                html_parts.append(
                    f"<h4>{category_name} ({count} file(s), {format_file_size(total_size)})</h4>"
                )
                html_parts.append("<ul>")

                for entry in sorted(category_entries, key=lambda e: e.path):
                    rel_path = (
                        entry.path.relative_to(base_dir) if base_dir else entry.path
                    )
                    html_parts.append(
                        f"<li><code>{rel_path}</code> ({entry.size_formatted})</li>"
                    )

                html_parts.append("</ul>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _group_by_category(
        self, entries: List[FileInventoryEntry]
    ) -> Dict[str, List[FileInventoryEntry]]:
        """Group entries by category.

        Args:
            entries: File inventory entries

        Returns:
            Dictionary mapping category names to lists of entries
        """
        groups = {}
        for entry in entries:
            if entry.category not in groups:
                groups[entry.category] = []
            groups[entry.category].append(entry)
        return groups


def format_file_size(bytes_size: int) -> str:
    """Convert bytes to human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Human-readable size string
    """
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{round(bytes_size / 1024)}KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{round(bytes_size / (1024 * 1024))}MB"
    else:
        return f"{round(bytes_size / (1024 * 1024 * 1024))}GB"


def collect_output_files(
    output_dir: Path, categories: Optional[List[str]] = None
) -> List[FileInventoryEntry]:
    """Convenience function to collect output files.

    Args:
        output_dir: Directory to scan
        categories: Categories to scan (default: all)

    Returns:
        List of file inventory entries
    """
    manager = FileInventoryManager()
    return manager.collect_output_files(output_dir, categories)


def generate_inventory_report(
    entries: List[FileInventoryEntry],
    output_format: str = "text",
    base_dir: Optional[Path] = None,
) -> str:
    """Convenience function to generate inventory report.

    Args:
        entries: File entries to report on
        output_format: Output format ("text", "json", "html")
        base_dir: Base directory for relative paths

    Returns:
        Formatted report
    """
    manager = FileInventoryManager()
    return manager.generate_inventory_report(entries, output_format, base_dir)
