#!/usr/bin/env python3
"""
Output Organizer - Unified File Organization System

This module provides a centralized system for organizing executive summary and
multi-project summary outputs by file type. It ensures consistent directory
structure and file placement across all reporting modules.

Key Features:
- Type-safe file type classification using enums
- Centralized path resolution logic
- Automatic directory structure creation
- Combined PDF collection and organization
- Comprehensive error handling and logging

Usage:
    from infrastructure.reporting.output_organizer import OutputOrganizer

    organizer = OutputOrganizer()
    output_path = organizer.get_output_path("chart.png", output_dir, FileType.PNG)
    organizer.copy_combined_pdfs(repo_root, output_dir)
"""

import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class FileType(Enum):
    """
    Enumeration of supported file types for output organization.

    Each enum value contains:
    - First element: file extension (lowercase)
    - Second element: subdirectory name
    """

    PNG = ("png", "png")
    PDF = ("pdf", "pdf")
    CSV = ("csv", "csv")
    HTML = ("html", "html")
    JSON = ("json", "json")
    MARKDOWN = ("md", "md")

    @property
    def extension(self) -> str:
        """Get the file extension for this file type."""
        return self.value[0]

    @property
    def subdirectory(self) -> str:
        """Get the subdirectory name for this file type."""
        return self.value[1]


@dataclass
class OrganizationResult:
    """
    Result of file organization operations.

    Attributes:
        moved_files: Number of files successfully moved
        skipped_files: Number of files skipped (already in correct location)
        error_files: Number of files that couldn't be organized
        created_dirs: Number of directories created
    """

    moved_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    created_dirs: int = 0


class OutputOrganizer:
    """
    Centralized organizer for executive summary and multi-project outputs.

    This class provides unified methods for organizing output files by type,
    ensuring consistent directory structure across all reporting modules.
    """

    def __init__(self):
        """Initialize the OutputOrganizer."""
        self.logger = logger

    def detect_file_type(self, file_path: Path) -> Optional[FileType]:
        """
        Detect file type from file extension.

        Args:
            file_path: Path to the file to analyze

        Returns:
            FileType enum value if extension is supported, None otherwise
        """
        if not file_path.suffix:
            return None

        extension = file_path.suffix.lower().lstrip(".")

        for file_type in FileType:
            if file_type.extension == extension:
                return file_type

        return None

    def get_subdirectory(self, file_type: FileType) -> str:
        """
        Get the subdirectory name for a given file type.

        Args:
            file_type: FileType enum value

        Returns:
            Subdirectory name as string
        """
        return file_type.subdirectory

    def get_output_path(
        self, file_path: Path, output_dir: Path, file_type: FileType
    ) -> Path:
        """
        Get the organized output path for a file.

        Args:
            file_path: Original file path or filename
            output_dir: Base output directory
            file_type: Type of file being saved

        Returns:
            Path to the organized location (output_dir/subdir/filename)
        """
        subdirectory = self.get_subdirectory(file_type)
        filename = file_path.name if isinstance(file_path, Path) else str(file_path)

        return output_dir / subdirectory / filename

    def ensure_directory_structure(self, output_dir: Path) -> None:
        """
        Ensure all required subdirectories exist in the output directory.

        Args:
            output_dir: Base output directory to organize
        """
        for file_type in FileType:
            subdirectory = output_dir / file_type.subdirectory
            subdirectory.mkdir(parents=True, exist_ok=True)

        # Also create combined_pdfs directory
        combined_dir = output_dir / "combined_pdfs"
        combined_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Ensured directory structure in {output_dir}")

    def organize_existing_files(self, directory: Path) -> OrganizationResult:
        """
        Organize existing files in a directory by moving them to appropriate subdirectories.

        This method scans all files in the given directory and moves them to type-specific
        subdirectories based on their extensions. Files already in correct subdirectories
        are left untouched.

        Args:
            directory: Directory containing files to organize

        Returns:
            OrganizationResult with operation statistics
        """
        result = OrganizationResult()

        if not directory.exists():
            self.logger.warning(f"Directory {directory} does not exist")
            return result

        # Ensure directory structure exists
        self.ensure_directory_structure(directory)
        result.created_dirs = len(list(FileType)) + 1  # +1 for combined_pdfs

        # Get all files in the directory (including subdirectories)
        all_files = list(directory.rglob("*"))
        files = [f for f in all_files if f.is_file()]

        for file_path in files:
            # Skip files that are already in any of the organized subdirectories
            relative_path = file_path.relative_to(directory)
            if len(relative_path.parts) > 1:  # File is in a subdirectory
                parent_dir = relative_path.parts[0]
                # Check if it's in one of our organized subdirectories
                if (
                    parent_dir in {ft.subdirectory for ft in FileType}
                    or parent_dir == "combined_pdfs"
                ):
                    # Check if it's in the correct subdirectory for its type
                    file_type = self.detect_file_type(file_path)
                    if file_type is not None and parent_dir == file_type.subdirectory:
                        self.logger.debug(
                            f"File already in correct location: {file_path}"
                        )
                        result.skipped_files += 1
                        continue
                    elif parent_dir == "combined_pdfs":
                        # combined_pdfs files are handled separately, skip them
                        result.skipped_files += 1
                        continue

            file_type = self.detect_file_type(file_path)

            if file_type is None:
                self.logger.warning(
                    f"Skipping file with unknown extension: {file_path}"
                )
                result.error_files += 1
                continue

            # Move file to correct subdirectory
            target_path = self.get_output_path(file_path, directory, file_type)

            try:
                shutil.move(str(file_path), str(target_path))
                self.logger.info(
                    f"Moved {file_path.name} -> {target_path.relative_to(directory)}"
                )
                result.moved_files += 1
            except Exception as e:
                self.logger.error(f"Failed to move {file_path}: {e}")
                result.error_files += 1

        self.logger.info(
            f"Organization complete: {result.moved_files} moved, {result.skipped_files} skipped, {result.error_files} errors"
        )
        return result

    def copy_combined_pdfs(self, repo_root: Path, target_dir: Path) -> int:
        """
        Copy all combined PDFs from project output directories to the target directory.

        Searches for files matching the pattern {project_name}_combined.pdf in each
        project's output directory and copies them to target_dir/combined_pdfs/.

        Args:
            repo_root: Root directory of the repository (contains projects/ and output/)
            target_dir: Target directory where combined_pdfs/ subdirectory should be created

        Returns:
            Number of PDF files copied
        """
        combined_dir = target_dir / "combined_pdfs"
        combined_dir.mkdir(parents=True, exist_ok=True)

        copied_count = 0
        output_projects_dir = repo_root / "output"

        if not output_projects_dir.exists():
            self.logger.warning(
                f"Output projects directory not found: {output_projects_dir}"
            )
            return 0

        # Find all project directories in output/
        project_dirs = [d for d in output_projects_dir.iterdir() if d.is_dir()]

        for project_dir in project_dirs:
            # Look for combined PDF
            combined_pdf = project_dir / f"{project_dir.name}_combined.pdf"

            if combined_pdf.exists():
                target_path = combined_dir / combined_pdf.name
                try:
                    shutil.copy2(str(combined_pdf), str(target_path))
                    self.logger.info(f"Copied combined PDF: {combined_pdf.name}")
                    copied_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to copy {combined_pdf}: {e}")
            else:
                self.logger.debug(
                    f"No combined PDF found for project: {project_dir.name}"
                )

        self.logger.info(f"Copied {copied_count} combined PDF files")
        return copied_count

    def get_organized_structure_summary(self, output_dir: Path) -> Dict[str, List[str]]:
        """
        Get a summary of the organized file structure.

        Args:
            output_dir: Base output directory to analyze

        Returns:
            Dictionary mapping subdirectory names to lists of filenames
        """
        summary = {}

        # Check each file type subdirectory
        for file_type in FileType:
            subdir = output_dir / file_type.subdirectory
            if subdir.exists():
                files = [f.name for f in subdir.iterdir() if f.is_file()]
                summary[file_type.subdirectory] = sorted(files)
            else:
                summary[file_type.subdirectory] = []

        # Check combined_pdfs directory
        combined_dir = output_dir / "combined_pdfs"
        if combined_dir.exists():
            files = [f.name for f in combined_dir.iterdir() if f.is_file()]
            summary["combined_pdfs"] = sorted(files)
        else:
            summary["combined_pdfs"] = []

        return summary
