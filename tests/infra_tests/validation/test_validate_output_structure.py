"""Tests for infrastructure.validation.output.validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""

import subprocess

from infrastructure.validation.output.validator import validate_output_structure


class TestValidateOutputStructure:
    """Test validate_output_structure function."""

    def test_validate_complete_structure(self, tmp_path):
        """Test validation with complete structure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF content" * 10000)

        for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_output_structure(project_output_dir)

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
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is False
        assert len(result["missing_files"]) > 0
        assert "test_project_combined.pdf" in result["missing_files"][0]

    def test_pdf_disabled_structure_does_not_require_pdf(self, tmp_path):
        """Format-aware callers must not receive a synthetic PDF failure."""
        project_output_dir = tmp_path / "output" / "test_project"
        web_dir = project_output_dir / "web"
        web_dir.mkdir(parents=True)
        (web_dir / "index.html").write_text("<!doctype html><html></html>\n", encoding="utf-8")

        result = validate_output_structure(project_output_dir, require_pdf=False)

        assert result["valid"] is True
        assert result["missing_files"] == []
        assert result["directory_structure"]["combined_pdf"]["required"] is False

    def test_validate_small_pdf(self, tmp_path):
        """Test validation with suspiciously small PDF."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()

        # Create very small PDF (< 100KB)
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 100)

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert len(result["suspicious_sizes"]) > 0
        assert any("unusually small" in s for s in result["suspicious_sizes"])

    def test_validate_empty_subdirectories(self, tmp_path):
        """Test validation with empty subdirectories."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 10000)

        for subdir in ["figures"]:
            (project_output_dir / subdir).mkdir()

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert len(result["suspicious_sizes"]) > 0
        assert any("empty" in s for s in result["suspicious_sizes"])

    def test_validate_optional_directories(self, tmp_path):
        """Test that optional directories don't cause validation failure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 10000)

        for subdir in ["figures", "data"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert result["directory_structure"]["llm"]["optional"] is True
        assert result["directory_structure"]["logs"]["optional"] is True

    def test_validate_directory_structure_metadata(self, tmp_path):
        """Test that directory structure metadata is correct."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        pdf_file = pdf_dir / "test_project_combined.pdf"
        pdf_file.write_bytes(b"PDF" * 10000)

        figures_dir = project_output_dir / "figures"
        figures_dir.mkdir()
        (figures_dir / "figure1.png").write_bytes(b"PNG" * 1000)
        (figures_dir / "figure2.png").write_bytes(b"PNG" * 1000)

        result = validate_output_structure(project_output_dir)

        # Check PDF metadata
        assert result["directory_structure"]["combined_pdf"]["exists"] is True
        assert result["directory_structure"]["combined_pdf"]["size_mb"] > 0

        # Check figures directory metadata
        assert result["directory_structure"]["figures"]["exists"] is True
        assert result["directory_structure"]["figures"]["files"] == 2
        assert result["directory_structure"]["figures"]["size_mb"] > 0

    def test_validate_before_copy_stage(self, tmp_path):
        """Test validation passes when PDF exists in source but not output directory."""
        repo_root = tmp_path
        projects_dir = repo_root / "projects"
        projects_dir.mkdir()
        output_root = repo_root / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir(parents=True)

        # Source structure
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        source_output_dir = project_dir / "output"
        source_output_dir.mkdir()
        source_pdf_dir = source_output_dir / "pdf"
        source_pdf_dir.mkdir()

        # PDF in source, project specific naming
        pdf_file = source_pdf_dir / "test_project_combined.pdf"
        pdf_file.write_bytes(b"PDF" * 10000)

        # Output dir (not copied yet)
        (project_output_dir / "pdf").mkdir()
        (project_output_dir / "figures").mkdir()
        (project_output_dir / "data").mkdir()

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert len(result["missing_files"]) == 0

    def test_validate_before_copy_stage_rejects_ignored_source_pdf(self, tmp_path):
        """A non-shippable source PDF cannot satisfy pre-copy validation."""
        copied = tmp_path / "output" / "test_project"
        copied.mkdir(parents=True)
        source_pdf = tmp_path / "projects" / "test_project" / "output" / "pdf" / "test_project_combined.pdf"
        source_pdf.parent.mkdir(parents=True)
        source_pdf.write_bytes(b"P" * 120_000)
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
        (tmp_path / ".gitignore").write_text(
            "projects/test_project/output/pdf/*.pdf\n",
            encoding="utf-8",
        )

        result = validate_output_structure(copied)

        assert result["valid"] is False
        assert result["directory_structure"]["combined_pdf"]["exists"] is False

    def test_validate_before_copy_stage_rejects_source_inventory_symlink(self, tmp_path):
        """Any unsafe source-inventory member blocks the PDF fallback."""
        copied = tmp_path / "output" / "test_project"
        copied.mkdir(parents=True)
        source_output = tmp_path / "projects" / "test_project" / "output"
        source_pdf = source_output / "pdf" / "test_project_combined.pdf"
        source_pdf.parent.mkdir(parents=True)
        source_pdf.write_bytes(b"P" * 120_000)
        outside = tmp_path / "private.json"
        outside.write_text("{}\n", encoding="utf-8")
        linked = source_output / "data" / "linked.json"
        linked.parent.mkdir(parents=True)
        linked.symlink_to(outside)

        result = validate_output_structure(copied)

        assert result["valid"] is False
        assert result["directory_structure"]["combined_pdf"]["exists"] is False
        assert any("symlink artifact forbidden" in issue for issue in result["issues"])

    def test_validate_nested_source_output_structure(self, tmp_path):
        """Source output validation detects qualified project names."""
        project_output_dir = tmp_path / "projects" / "my_program" / "nested_project" / "output"
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "nested_project_combined.pdf").write_bytes(b"PDF" * 10000)

        for subdir in ["web", "slides", "figures", "data", "reports"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert len(result["missing_files"]) == 0

    def test_validate_wip_source_output_structure(self, tmp_path):
        """Source output validation detects projects/working/ project names."""
        project_output_dir = tmp_path / "projects" / "working" / "draft_project" / "output"
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "draft_project_combined.pdf").write_bytes(b"PDF" * 10000)

        result = validate_output_structure(project_output_dir)

        assert result["directory_structure"]["combined_pdf"]["exists"] is True

    def test_validate_nested_copied_output_structure(self, tmp_path):
        """Copied nested output validation uses the qualified output path."""
        project_output_dir = tmp_path / "output" / "my_program" / "nested_project"
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (project_output_dir / "nested_project_combined.pdf").write_bytes(b"PDF" * 10000)

        for subdir in ["web", "slides", "figures", "data", "reports"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is True
        assert result["directory_structure"]["combined_pdf"]["exists"] is True

    def test_validate_multiple_issues(self, tmp_path):
        """Test validation with multiple issues."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        (project_output_dir / "pdf").mkdir()

        result = validate_output_structure(project_output_dir)

        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert len(result["missing_files"]) > 0

    def test_validate_readable_files(self, tmp_path):
        """Test that file readability is checked."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        pdf_file = pdf_dir / "test_project_combined.pdf"
        pdf_file.write_bytes(b"PDF" * 10000)

        result = validate_output_structure(project_output_dir)

        assert result["directory_structure"]["combined_pdf"]["readable"] is True
