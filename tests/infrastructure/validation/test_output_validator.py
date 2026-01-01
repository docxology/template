"""Tests for infrastructure.validation.output_validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""

from pathlib import Path
import pytest

from infrastructure.validation.output_validator import (
    validate_copied_outputs,
    validate_output_structure,
)


class TestValidateCopiedOutputs:
    """Test validate_copied_outputs function."""

    def test_validate_pdf_at_root(self, tmp_path):
        """Test validation when PDF exists in pdf/ directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()

        # Create PDF in pdf/ directory (where it's actually expected)
        pdf_file = pdf_dir / "project_combined.pdf"
        pdf_file.write_bytes(b"PDF content" * 1000)  # Make it substantial

        result = validate_copied_outputs(output_dir)

        assert result is True

    def test_validate_pdf_in_pdf_directory(self, tmp_path):
        """Test validation when PDF exists in pdf/ directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        
        # Create PDF in pdf/ directory
        pdf_file = pdf_dir / "project_combined.pdf"
        pdf_file.write_bytes(b"PDF content" * 1000)
        
        result = validate_copied_outputs(output_dir)
        
        # Should not fail (fallback location)
        assert result is True

    def test_validate_missing_pdf(self, tmp_path):
        """Test validation when PDF is missing."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = validate_copied_outputs(output_dir)
        
        assert result is False

    def test_validate_empty_pdf(self, tmp_path):
        """Test validation when PDF exists but is empty."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        pdf_file = output_dir / "project_combined.pdf"
        pdf_file.write_bytes(b"")  # Empty file
        
        result = validate_copied_outputs(output_dir)
        
        assert result is False

    def test_validate_complete_structure(self, tmp_path):
        """Test validation with complete output structure."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory (where it's actually expected)
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 1000)

        # Create all expected subdirectories with files (skip pdf since already created)
        for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
            subdir_path = output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / f"{subdir}_file.txt").write_text("content")
        
        result = validate_copied_outputs(output_dir)
        
        assert result is True

    def test_validate_optional_directories(self, tmp_path):
        """Test that optional directories don't cause validation failure."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory (where it's actually expected)
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 1000)

        # Create required directories (skip pdf since already created)
        for subdir in ["figures", "data"]:
            subdir_path = output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")
        
        # Don't create optional directories (llm, logs)
        
        result = validate_copied_outputs(output_dir)
        
        # Should pass even without optional directories
        assert result is True

    def test_validate_empty_subdirectories(self, tmp_path):
        """Test validation with empty subdirectories."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory (where it's actually expected)
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 1000)

        # Create empty subdirectories (skip pdf since already created)
        for subdir in ["figures"]:
            (output_dir / subdir).mkdir()
        
        result = validate_copied_outputs(output_dir)
        
        # Should still pass (warns but doesn't fail)
        assert result is True


class TestValidateOutputStructure:
    """Test validate_output_structure function."""

    def test_validate_complete_structure(self, tmp_path):
        """Test validation with complete structure."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory (where it's actually expected)
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF content" * 10000)
        
        # Create all subdirectories with files (skip pdf since already created)
        for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
            subdir_path = output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["missing_files"]) == 0

    def test_validate_missing_directory(self, tmp_path):
        """Test validation when output directory doesn't exist."""
        output_dir = tmp_path / "nonexistent"
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert "does not exist" in result["issues"][0]

    def test_validate_missing_pdf(self, tmp_path):
        """Test validation when PDF is missing."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is False
        assert len(result["missing_files"]) > 0
        assert "project_combined.pdf" in result["missing_files"][0]

    def test_validate_small_pdf(self, tmp_path):
        """Test validation with suspiciously small PDF."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()

        # Create very small PDF (< 100KB) in pdf/ directory
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 100)
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True  # Still valid, just suspicious
        assert len(result["suspicious_sizes"]) > 0
        assert any("unusually small" in s for s in result["suspicious_sizes"])

    def test_validate_empty_subdirectories(self, tmp_path):
        """Test validation with empty subdirectories."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 10000)
        
        # Create empty subdirectories (skip pdf since already created)
        for subdir in ["figures"]:
            (output_dir / subdir).mkdir()
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True
        assert len(result["suspicious_sizes"]) > 0
        assert any("empty" in s for s in result["suspicious_sizes"])

    def test_validate_optional_directories(self, tmp_path):
        """Test that optional directories don't cause validation failure."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 10000)
        
        # Create required directories (skip pdf since already created)
        for subdir in ["figures", "data"]:
            subdir_path = output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")
        
        # Don't create optional directories (llm, logs)
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True
        # Optional directories should be marked as optional
        assert result["directory_structure"]["llm"]["optional"] is True
        assert result["directory_structure"]["logs"]["optional"] is True

    def test_validate_directory_structure_metadata(self, tmp_path):
        """Test that directory structure metadata is correct."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        pdf_file = pdf_dir / "project_combined.pdf"
        pdf_file.write_bytes(b"PDF" * 10000)
        
        # Create subdirectory with files
        figures_dir = output_dir / "figures"
        figures_dir.mkdir()
        (figures_dir / "figure1.png").write_bytes(b"PNG" * 1000)
        (figures_dir / "figure2.png").write_bytes(b"PNG" * 1000)
        
        result = validate_output_structure(output_dir)
        
        # Check PDF metadata
        assert result["directory_structure"]["project_combined_pdf"]["exists"] is True
        assert result["directory_structure"]["project_combined_pdf"]["size_mb"] > 0
        
        # Check figures directory metadata
        assert result["directory_structure"]["figures"]["exists"] is True
        assert result["directory_structure"]["figures"]["files"] == 2
        assert result["directory_structure"]["figures"]["size_mb"] > 0

    def test_validate_multiple_issues(self, tmp_path):
        """Test validation with multiple issues."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Missing PDF
        # Missing required directories
        # Only create one directory
        (output_dir / "pdf").mkdir()
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert len(result["missing_files"]) > 0

    def test_validate_readable_files(self, tmp_path):
        """Test that file readability is checked."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create PDF in pdf/ directory
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        pdf_file = pdf_dir / "project_combined.pdf"
        pdf_file.write_bytes(b"PDF" * 10000)
        
        result = validate_output_structure(output_dir)
        
        assert result["directory_structure"]["project_combined_pdf"]["readable"] is True






