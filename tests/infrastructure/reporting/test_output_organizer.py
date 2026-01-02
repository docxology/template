#!/usr/bin/env python3
"""Tests for infrastructure/reporting/output_organizer.py

Tests the unified output organization system for executive summary and
multi-project summary outputs.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from infrastructure.reporting.output_organizer import (
    FileType,
    OutputOrganizer,
    OrganizationResult
)


class TestFileType:
    """Test FileType enum properties and behavior."""

    def test_file_type_enum_values(self):
        """Test that FileType enum has correct values."""
        assert FileType.PNG.extension == "png"
        assert FileType.PNG.subdirectory == "png"

        assert FileType.PDF.extension == "pdf"
        assert FileType.PDF.subdirectory == "pdf"

        assert FileType.CSV.extension == "csv"
        assert FileType.CSV.subdirectory == "csv"

        assert FileType.HTML.extension == "html"
        assert FileType.HTML.subdirectory == "html"

        assert FileType.JSON.extension == "json"
        assert FileType.JSON.subdirectory == "json"

        assert FileType.MARKDOWN.extension == "md"
        assert FileType.MARKDOWN.subdirectory == "md"

    def test_all_file_types_covered(self):
        """Test that all expected file types are defined."""
        expected_extensions = {"png", "pdf", "csv", "html", "json", "md"}
        actual_extensions = {ft.extension for ft in FileType}

        assert actual_extensions == expected_extensions

    def test_file_type_properties(self):
        """Test FileType property access."""
        file_type = FileType.PNG
        assert file_type.extension == "png"
        assert file_type.subdirectory == "png"

        file_type = FileType.JSON
        assert file_type.extension == "json"
        assert file_type.subdirectory == "json"


class TestOutputOrganizer:
    """Test OutputOrganizer class functionality."""

    @pytest.fixture
    def organizer(self):
        """Create OutputOrganizer instance."""
        return OutputOrganizer()

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory for testing."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_detect_file_type_known_extensions(self, organizer):
        """Test file type detection for known extensions."""
        # Test PNG
        png_path = Path("test.png")
        assert organizer.detect_file_type(png_path) == FileType.PNG

        # Test PDF
        pdf_path = Path("document.pdf")
        assert organizer.detect_file_type(pdf_path) == FileType.PDF

        # Test CSV
        csv_path = Path("data.csv")
        assert organizer.detect_file_type(csv_path) == FileType.CSV

        # Test HTML
        html_path = Path("report.html")
        assert organizer.detect_file_type(html_path) == FileType.HTML

        # Test JSON
        json_path = Path("config.json")
        assert organizer.detect_file_type(json_path) == FileType.JSON

        # Test Markdown
        md_path = Path("README.md")
        assert organizer.detect_file_type(md_path) == FileType.MARKDOWN

    def test_detect_file_type_unknown_extension(self, organizer):
        """Test file type detection for unknown extensions."""
        unknown_path = Path("file.unknown")
        assert organizer.detect_file_type(unknown_path) is None

        no_ext_path = Path("file_no_extension")
        assert organizer.detect_file_type(no_ext_path) is None

    def test_detect_file_type_case_insensitive(self, organizer):
        """Test file type detection is case insensitive."""
        uppercase_path = Path("FILE.PDF")
        assert organizer.detect_file_type(uppercase_path) == FileType.PDF

        mixed_case_path = Path("File.Json")
        assert organizer.detect_file_type(mixed_case_path) == FileType.JSON

    def test_get_subdirectory(self, organizer):
        """Test subdirectory retrieval for file types."""
        assert organizer.get_subdirectory(FileType.PNG) == "png"
        assert organizer.get_subdirectory(FileType.PDF) == "pdf"
        assert organizer.get_subdirectory(FileType.CSV) == "csv"
        assert organizer.get_subdirectory(FileType.HTML) == "html"
        assert organizer.get_subdirectory(FileType.JSON) == "json"
        assert organizer.get_subdirectory(FileType.MARKDOWN) == "md"

    def test_get_output_path_basic(self, organizer, temp_output_dir):
        """Test basic output path generation."""
        file_path = Path("chart.png")
        result_path = organizer.get_output_path(file_path, temp_output_dir, FileType.PNG)

        expected = temp_output_dir / "png" / "chart.png"
        assert result_path == expected

    def test_get_output_path_with_filename_only(self, organizer, temp_output_dir):
        """Test output path generation with filename string."""
        result_path = organizer.get_output_path("report.pdf", temp_output_dir, FileType.PDF)

        expected = temp_output_dir / "pdf" / "report.pdf"
        assert result_path == expected

    def test_get_output_path_preserves_relative_structure(self, organizer, temp_output_dir):
        """Test that output path preserves relative structure."""
        file_path = Path("subdir/chart.png")
        result_path = organizer.get_output_path(file_path, temp_output_dir, FileType.PNG)

        # Should use just the filename, not the full relative path
        expected = temp_output_dir / "png" / "chart.png"
        assert result_path == expected

    def test_ensure_directory_structure_creates_all_dirs(self, organizer, temp_output_dir):
        """Test that directory structure creates all required subdirectories."""
        organizer.ensure_directory_structure(temp_output_dir)

        # Check all file type subdirectories exist
        for file_type in FileType:
            subdir = temp_output_dir / file_type.subdirectory
            assert subdir.exists()
            assert subdir.is_dir()

        # Check combined_pdfs directory exists
        combined_dir = temp_output_dir / "combined_pdfs"
        assert combined_dir.exists()
        assert combined_dir.is_dir()

    def test_ensure_directory_structure_idempotent(self, organizer, temp_output_dir):
        """Test that ensure_directory_structure is idempotent."""
        # Call multiple times
        organizer.ensure_directory_structure(temp_output_dir)
        organizer.ensure_directory_structure(temp_output_dir)

        # Should still have correct structure
        for file_type in FileType:
            subdir = temp_output_dir / file_type.subdirectory
            assert subdir.exists()

        combined_dir = temp_output_dir / "combined_pdfs"
        assert combined_dir.exists()

    def test_organize_existing_files_moves_files_correctly(self, organizer, temp_output_dir):
        """Test that existing files are moved to correct subdirectories."""
        # Create test files
        png_file = temp_output_dir / "chart.png"
        pdf_file = temp_output_dir / "report.pdf"
        csv_file = temp_output_dir / "data.csv"
        unknown_file = temp_output_dir / "unknown.xyz"

        png_file.write_text("PNG content")
        pdf_file.write_text("PDF content")
        csv_file.write_text("CSV content")
        unknown_file.write_text("Unknown content")

        # Organize files
        result = organizer.organize_existing_files(temp_output_dir)

        # Check results
        assert result.moved_files == 3  # PNG, PDF, CSV moved
        assert result.skipped_files == 0
        assert result.error_files == 1  # Unknown file not moved

        # Check files moved to correct locations
        assert not png_file.exists()  # Original file gone
        assert not pdf_file.exists()
        assert not csv_file.exists()
        assert unknown_file.exists()  # Unknown file still there

        # Check moved files exist in correct locations
        assert (temp_output_dir / "png" / "chart.png").exists()
        assert (temp_output_dir / "pdf" / "report.pdf").exists()
        assert (temp_output_dir / "csv" / "data.csv").exists()

    def test_organize_existing_files_already_organized(self, organizer, temp_output_dir):
        """Test organization when files are already in correct subdirectories."""
        # Create directory structure first
        organizer.ensure_directory_structure(temp_output_dir)

        # Create files in correct locations
        png_file = temp_output_dir / "png" / "chart.png"
        pdf_file = temp_output_dir / "pdf" / "report.pdf"

        png_file.write_text("PNG content")
        pdf_file.write_text("PDF content")

        # Organize files
        result = organizer.organize_existing_files(temp_output_dir)

        # Should skip already organized files
        assert result.moved_files == 0
        assert result.skipped_files == 2  # PNG and PDF already correct
        assert result.error_files == 0

    def test_organize_existing_files_nonexistent_directory(self, organizer, tmp_path):
        """Test organization with nonexistent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        result = organizer.organize_existing_files(nonexistent_dir)

        # Should handle gracefully
        assert result.moved_files == 0
        assert result.skipped_files == 0
        assert result.error_files == 0

    def test_copy_combined_pdfs_copies_correct_files(self, organizer, tmp_path):
        """Test copying combined PDFs from project directories."""
        # Create mock repository structure
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        # Create project directories with combined PDFs
        project1_dir = repo_root / "output" / "project1"
        project1_dir.mkdir(parents=True)
        pdf1 = project1_dir / "project1_combined.pdf"
        pdf1.write_text("PDF1 content")

        project2_dir = repo_root / "output" / "project2"
        project2_dir.mkdir(parents=True)
        pdf2 = project2_dir / "project2_combined.pdf"
        pdf2.write_text("PDF2 content")

        # Create target directory
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        # Copy combined PDFs
        copied_count = organizer.copy_combined_pdfs(repo_root, target_dir)

        # Check results
        assert copied_count == 2

        # Check files copied correctly
        combined_dir = target_dir / "combined_pdfs"
        assert combined_dir.exists()

        copied_pdf1 = combined_dir / "project1_combined.pdf"
        copied_pdf2 = combined_dir / "project2_combined.pdf"

        assert copied_pdf1.exists()
        assert copied_pdf2.exists()
        assert copied_pdf1.read_text() == "PDF1 content"
        assert copied_pdf2.read_text() == "PDF2 content"

    def test_copy_combined_pdfs_no_projects(self, organizer, tmp_path):
        """Test copying combined PDFs when no project directories exist."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        copied_count = organizer.copy_combined_pdfs(repo_root, target_dir)

        assert copied_count == 0

        # combined_pdfs directory should still be created
        combined_dir = target_dir / "combined_pdfs"
        assert combined_dir.exists()

    def test_copy_combined_pdfs_missing_pdf(self, organizer, tmp_path):
        """Test copying when some projects don't have combined PDFs."""
        # Create mock repository structure
        repo_root = tmp_path / "repo"
        repo_root.mkdir()

        # Create one project with PDF, one without
        project1_dir = repo_root / "output" / "project1"
        project1_dir.mkdir(parents=True)
        pdf1 = project1_dir / "project1_combined.pdf"
        pdf1.write_text("PDF1 content")

        project2_dir = repo_root / "output" / "project2"
        project2_dir.mkdir(parents=True)
        # No PDF for project2

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        copied_count = organizer.copy_combined_pdfs(repo_root, target_dir)

        assert copied_count == 1

        combined_dir = target_dir / "combined_pdfs"
        copied_pdf1 = combined_dir / "project1_combined.pdf"

        assert copied_pdf1.exists()
        assert copied_pdf1.read_text() == "PDF1 content"

    def test_get_organized_structure_summary(self, organizer, temp_output_dir):
        """Test getting summary of organized file structure."""
        # Create directory structure and some files
        organizer.ensure_directory_structure(temp_output_dir)

        # Create some test files
        (temp_output_dir / "png" / "chart1.png").write_text("PNG1")
        (temp_output_dir / "png" / "chart2.png").write_text("PNG2")
        (temp_output_dir / "pdf" / "report.pdf").write_text("PDF")
        (temp_output_dir / "combined_pdfs" / "proj1.pdf").write_text("COMBINED")

        # Get summary
        summary = organizer.get_organized_structure_summary(temp_output_dir)

        # Check structure
        assert "png" in summary
        assert "pdf" in summary
        assert "csv" in summary  # Even if empty
        assert "combined_pdfs" in summary

        # Check file lists
        assert summary["png"] == ["chart1.png", "chart2.png"]
        assert summary["pdf"] == ["report.pdf"]
        assert summary["csv"] == []  # Empty directory
        assert summary["combined_pdfs"] == ["proj1.pdf"]

    def test_get_organized_structure_summary_empty_dirs(self, organizer, temp_output_dir):
        """Test summary when directories exist but are empty."""
        organizer.ensure_directory_structure(temp_output_dir)

        summary = organizer.get_organized_structure_summary(temp_output_dir)

        # All directories should be present with empty lists
        for file_type in FileType:
            assert file_type.subdirectory in summary
            assert summary[file_type.subdirectory] == []

        assert "combined_pdfs" in summary
        assert summary["combined_pdfs"] == []

    @pytest.mark.parametrize("file_type,expected_subdir", [
        (FileType.PNG, "png"),
        (FileType.PDF, "pdf"),
        (FileType.CSV, "csv"),
        (FileType.HTML, "html"),
        (FileType.JSON, "json"),
        (FileType.MARKDOWN, "md"),
    ])
    def test_get_subdirectory_parametrized(self, organizer, file_type, expected_subdir):
        """Test get_subdirectory with parametrized inputs."""
        assert organizer.get_subdirectory(file_type) == expected_subdir