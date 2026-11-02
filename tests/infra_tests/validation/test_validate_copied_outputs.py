"""Tests for infrastructure.validation.output.validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""

import pytest

from infrastructure.validation.output.validator import (
    validate_copied_outputs,
)


def _write_pdf(path):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(path)


class TestValidateCopiedOutputs:
    """Test validate_copied_outputs function."""

    def test_validate_pdf_at_root(self, tmp_path):
        """Test validation when PDF exists in proper project structure."""
        # Setup structure: root/output/test_project
        repo_root = tmp_path
        output_root = repo_root / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()

        # Create PDF with project-specific name
        pdf_file = project_output_dir / "test_project_combined.pdf"
        _write_pdf(pdf_file)

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is True

    def test_validate_pdf_in_pdf_directory(self, tmp_path):
        """Test validation when PDF exists in pdf/ directory."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()

        # Create PDF in pdf/ directory with project-specific name
        pdf_file = pdf_dir / "test_project_combined.pdf"
        _write_pdf(pdf_file)

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is True

    def test_validate_missing_pdf(self, tmp_path):
        """Test validation when PDF is missing."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        with pytest.raises(TypeError, match="enabled_formats"):
            validate_copied_outputs(project_output_dir)

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is False

    def test_validate_empty_pdf(self, tmp_path):
        """Test validation when PDF exists but is empty."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_file = project_output_dir / "test_project_combined.pdf"
        pdf_file.write_bytes(b"")  # Empty file

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is False

    def test_validate_complete_structure(self, tmp_path):
        """Test validation with complete output structure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        _write_pdf(pdf_dir / "test_project_combined.pdf")

        # Create all expected subdirectories
        for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / f"{subdir}_file.txt").write_text("content")

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is True

    def test_validate_optional_directories(self, tmp_path):
        """Test that optional directories don't cause validation failure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        _write_pdf(pdf_dir / "test_project_combined.pdf")

        for subdir in ["figures", "data"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is True

    def test_validate_empty_subdirectories(self, tmp_path):
        """Test validation with empty subdirectories."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        _write_pdf(pdf_dir / "test_project_combined.pdf")

        for subdir in ["figures"]:
            (project_output_dir / subdir).mkdir()

        result = validate_copied_outputs(project_output_dir, enabled_formats=("pdf",))

        assert result is True
