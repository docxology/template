"""File inventory and collection utilities.

This module provides utilities for collecting and managing file inventories
from output directories, extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.

Sub-modules:
    inventory_entry  -- FileInventoryEntry dataclass and format_file_size
    inventory_reports -- Report generation (text, JSON, HTML)
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.inventory_entry import FileInventoryEntry, format_file_size
from infrastructure.core.files.inventory_reports import (
    OUTPUT_CATEGORIES,
    generate_html_report,
    generate_json_report,
    generate_text_report,
    group_by_category,
)
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Re-export so every existing ``from infrastructure.core.files.inventory import X`` keeps working.
__all__ = [
    "FileInventoryEntry",
    "FileInventoryManager",
    "collect_output_files",
    "format_file_size",
    "generate_inventory_report",
]


class FileInventoryManager:
    """Manage file inventory and reports."""

    # Standard output categories to scan and display
    OUTPUT_CATEGORIES = OUTPUT_CATEGORIES

    def collect_output_files(
        self, output_dir: Path, categories: tuple[str, ...] | list[str] | None = None
    ) -> list[FileInventoryEntry]:
        """Collect all generated files from output directory.

        Args:
            output_dir: Base directory to scan (projects/project/output or output)
            categories: List of categories to scan (default: all standard categories)

        Returns:
            List of FileInventoryEntry objects
        """
        if categories is None:
            categories = self.OUTPUT_CATEGORIES

        entries: list[FileInventoryEntry] = []

        # Check if output directory exists and is a directory
        if not output_dir.exists() or not output_dir.is_dir():
            logger.warning(f"Output directory not found: {output_dir}")
            return entries

        # Scan each category directory
        for category in categories:
            category_dir = output_dir / category
            if category_dir.exists() and category_dir.is_dir():
                entries.extend(self._collect_files_in_directory(category_dir, category))

        # Also check for root-level combined PDFs (project-specific naming like
        # code_project_combined.pdf or the legacy project_combined.pdf)
        for file_path in output_dir.glob("*combined*.pdf"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    entries.append(
                        FileInventoryEntry(
                            path=file_path,
                            size=stat.st_size,
                            category=self._guess_category_from_filename(file_path.name),
                            modified=stat.st_mtime,
                        )
                    )
                except OSError as e:
                    logger.debug(f"Failed to stat file {file_path}: {e}")

        return entries

    def _collect_files_in_directory(
        self, directory: Path, category: str
    ) -> list[FileInventoryEntry]:
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
        entries: list[FileInventoryEntry],
        output_format: str = "text",
        base_dir: Path | None = None,
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
            return generate_json_report(entries, base_dir)
        elif output_format == "html":
            return generate_html_report(entries, base_dir)
        else:
            return generate_text_report(entries, base_dir)

    # Kept for internal use by report methods that need category grouping
    _group_by_category = staticmethod(group_by_category)


def collect_output_files(
    output_dir: Path, categories: list[str] | None = None
) -> list[FileInventoryEntry]:
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
    entries: list[FileInventoryEntry],
    output_format: str = "text",
    base_dir: Path | None = None,
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
