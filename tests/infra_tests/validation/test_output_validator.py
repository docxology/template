"""Tests for infrastructure.validation.output_validator module.

Comprehensive tests for output validation functionality including
copied outputs validation and output structure validation.
"""

from pathlib import Path

import pytest

from infrastructure.validation.output_validator import (
    validate_copied_outputs, validate_output_structure)


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
        pdf_file.write_bytes(b"PDF content" * 1000)

        result = validate_copied_outputs(project_output_dir)

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
        pdf_file.write_bytes(b"PDF content" * 1000)

        result = validate_copied_outputs(project_output_dir)

        assert result is True

    def test_validate_missing_pdf(self, tmp_path):
        """Test validation when PDF is missing."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        result = validate_copied_outputs(project_output_dir)

        assert result is False

    def test_validate_empty_pdf(self, tmp_path):
        """Test validation when PDF exists but is empty."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_file = project_output_dir / "test_project_combined.pdf"
        pdf_file.write_bytes(b"")  # Empty file

        result = validate_copied_outputs(project_output_dir)

        assert result is False

    def test_validate_complete_structure(self, tmp_path):
        """Test validation with complete output structure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 1000)

        # Create all expected subdirectories
        for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / f"{subdir}_file.txt").write_text("content")

        result = validate_copied_outputs(project_output_dir)

        assert result is True

    def test_validate_optional_directories(self, tmp_path):
        """Test that optional directories don't cause validation failure."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 1000)

        for subdir in ["figures", "data"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / "file.txt").write_text("content")

        result = validate_copied_outputs(project_output_dir)

        assert result is True

    def test_validate_empty_subdirectories(self, tmp_path):
        """Test validation with empty subdirectories."""
        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 1000)

        for subdir in ["figures"]:
            (project_output_dir / subdir).mkdir()

        result = validate_copied_outputs(project_output_dir)

        assert result is True


class TestValidateRootOutputStructure:
    """Test validate_root_output_structure function."""

    def test_output_directory_not_exists(self, tmp_path):
        """Test validation when output directory doesn't exist."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert "does not exist" in result["issues"][0]
        assert result["project_folders"] == []
        assert result["invalid_folders"] == []

    def test_valid_project_folders_only(self, tmp_path):
        """Test validation with only valid project folders."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder in output
        (output_dir / "test_project").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True
        assert "test_project" in result["project_folders"]
        assert result["invalid_folders"] == []

    def test_invalid_root_level_directories(self, tmp_path):
        """Test validation with invalid root-level directories."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create invalid root-level directories
        (output_dir / "data").mkdir()
        (output_dir / "figures").mkdir()
        (output_dir / "pdf").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert len(result["invalid_folders"]) == 3
        assert "data" in result["invalid_folders"]
        assert "figures" in result["invalid_folders"]
        assert "pdf" in result["invalid_folders"]

    def test_unknown_directories_flagged(self, tmp_path):
        """Test that unknown directories are flagged."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create unknown directory (not a project, not a standard folder)
        (output_dir / "random_folder").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is False
        assert any("Unknown directory" in issue for issue in result["issues"])

    def test_files_in_output_ignored(self, tmp_path):
        """Test that files in output directory are ignored."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create file (should be ignored)
        (output_dir / "readme.txt").write_text("readme content")

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True

    def test_gitkeep_ignored(self, tmp_path):
        """Test that .gitkeep and .gitignore are ignored."""
        from infrastructure.validation.output_validator import \
            validate_root_output_structure

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a projects directory with valid project (needs full structure)
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: Test")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "output").mkdir()

        # Create project folder
        (output_dir / "test_project").mkdir()

        # Create .gitkeep directory (unusual but should be ignored)
        (output_dir / ".gitkeep").mkdir()
        (output_dir / ".gitignore").mkdir()

        result = validate_root_output_structure(tmp_path)

        assert result["valid"] is True


class TestCollectDetailedValidationResults:
    """Test collect_detailed_validation_results function."""

    def test_collect_complete_results(self, tmp_path):
        """Test collecting results with complete structure."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 50000)

        # Create other directories with files
        for subdir in ["figures", "data", "reports", "web", "slides"]:
            subdir_path = project_output_dir / subdir
            subdir_path.mkdir()
            (subdir_path / f"{subdir}_file.txt").write_text("content")

        result = collect_detailed_validation_results(project_output_dir)

        assert "structure" in result
        assert "directories" in result
        assert "file_counts" in result
        assert "total_size_mb" in result
        assert "issues_by_severity" in result
        assert "recommendations" in result

        # Check directory details populated
        assert result["directories"]["pdf"]["exists"] is True
        assert result["directories"]["figures"]["exists"] is True
        assert result["file_counts"]["pdf"] >= 1

    def test_collect_missing_directories(self, tmp_path):
        """Test collecting results with missing directories."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create only PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 50000)

        result = collect_detailed_validation_results(project_output_dir)

        # Missing directories should be flagged as warnings
        assert len(result["issues_by_severity"]["warning"]) > 0
        assert result["directories"]["figures"]["exists"] is False
        assert result["directories"]["data"]["exists"] is False

    def test_collect_missing_pdf_critical(self, tmp_path):
        """Test that missing PDF is flagged as critical."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create other directories but no PDF
        (project_output_dir / "pdf").mkdir()
        (project_output_dir / "figures").mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Missing PDF should be critical issue
        assert len(result["issues_by_severity"]["critical"]) > 0

    def test_collect_generates_recommendations(self, tmp_path):
        """Test that recommendations are generated based on issues."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Minimal structure - no PDF, no figures
        (project_output_dir / "pdf").mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Should have recommendations
        assert len(result["recommendations"]) > 0
        # Check for figures recommendation
        priorities = [r["priority"] for r in result["recommendations"]]
        assert "high" in priorities or "medium" in priorities

    def test_collect_calculates_total_size(self, tmp_path):
        """Test that total size is calculated correctly."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"X" * 1024 * 1024)  # 1 MB

        # Create figures
        figures_dir = project_output_dir / "figures"
        figures_dir.mkdir()
        (figures_dir / "figure1.png").write_bytes(b"Y" * 512 * 1024)  # 0.5 MB

        result = collect_detailed_validation_results(project_output_dir)

        # Total should be around 1.5 MB
        assert result["total_size_mb"] > 1.0

    def test_collect_finds_largest_file(self, tmp_path):
        """Test that largest file is identified per directory."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF directory with multiple files
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "small.pdf").write_bytes(b"X" * 100)
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"Y" * 50000)
        (pdf_dir / "medium.pdf").write_bytes(b"Z" * 1000)

        result = collect_detailed_validation_results(project_output_dir)

        # Largest file should be identified
        assert (
            result["directories"]["pdf"]["largest_file"] == "test_project_combined.pdf"
        )

    def test_collect_handles_empty_output(self, tmp_path):
        """Test handling of completely empty output directory."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        result = collect_detailed_validation_results(project_output_dir)

        # Should have issues
        assert result["structure"]["valid"] is False
        assert result["total_size_mb"] == 0.0

    def test_collect_suspicious_sizes_from_structure(self, tmp_path):
        """Test that suspicious sizes from structure validation are propagated."""
        from infrastructure.validation.output_validator import \
            collect_detailed_validation_results

        output_root = tmp_path / "output"
        output_root.mkdir()
        project_output_dir = output_root / "test_project"
        project_output_dir.mkdir()

        # Create PDF with small size (suspicious)
        pdf_dir = project_output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "test_project_combined.pdf").write_bytes(b"PDF" * 10)  # Very small

        result = collect_detailed_validation_results(project_output_dir)

        # Suspicious size should be in warnings
        assert len(result["issues_by_severity"]["warning"]) > 0


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
        assert result["directory_structure"]["project_combined_pdf"]["exists"] is True
        assert result["directory_structure"]["project_combined_pdf"]["size_mb"] > 0

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

        assert result["directory_structure"]["project_combined_pdf"]["readable"] is True
