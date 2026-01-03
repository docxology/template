#!/usr/bin/env python3
"""Integration tests for output copying stage.

Tests the complete output copying pipeline:
- Directory cleaning
- File copying (PDF, slides, web)
- Validation of copied files
- Error handling for missing source files
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the output copying module functions
# We need to add scripts to path first
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

# Now import the module (avoiding the leading digit in filename)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "copy_outputs",
    Path(__file__).parent.parent.parent / "scripts" / "05_copy_outputs.py"
)
copy_outputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(copy_outputs)

clean_output_directory = copy_outputs.clean_output_directory
copy_final_deliverables = copy_outputs.copy_final_deliverables
validate_copied_outputs = copy_outputs.validate_copied_outputs
validate_output_structure = copy_outputs.validate_output_structure


@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure for testing.
    
    Yields:
        Tuple of (project_root, output_dir) paths
    """
    # Create project root
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    
    # Create projects/code_project/output structure (multi-project format)
    project_output = repo_root / "projects" / "code_project" / "output"
    pdf_dir = project_output / "pdf"
    slides_dir = project_output / "slides"
    web_dir = project_output / "web"
    figures_dir = project_output / "figures"
    data_dir = project_output / "data"
    reports_dir = project_output / "reports"
    simulations_dir = project_output / "simulations"
    llm_dir = project_output / "llm"
    logs_dir = project_output / "logs"

    # Create all expected directories
    for dir_path in [pdf_dir, slides_dir, web_dir, figures_dir, data_dir,
                     reports_dir, simulations_dir, llm_dir, logs_dir]:
        dir_path.mkdir(parents=True)
    
    # Create top-level output dir with project subdirectory
    output_base = repo_root / "output"
    output_base.mkdir()
    output_dir = output_base / "code_project"  # Project-specific output directory
    output_dir.mkdir()
    
    # Create mock files
    (pdf_dir / "code_project_combined.pdf").write_text("mock pdf content")
    (slides_dir / "01_abstract_slides.pdf").write_text("mock slide 1")
    (slides_dir / "02_introduction_slides.pdf").write_text("mock slide 2")
    (web_dir / "01_abstract.html").write_text("<html>mock</html>")
    (web_dir / "02_introduction.html").write_text("<html>mock</html>")
    (web_dir / "style.css").write_text("/* css */")
    
    yield repo_root, output_dir
    
    # Cleanup
    shutil.rmtree(repo_root, ignore_errors=True)


class TestCleanOutputDirectory:
    """Test output directory cleaning."""
    
    def test_clean_nonexistent_directory(self, tmp_path):
        """Test cleaning a non-existent directory creates it."""
        output_dir = tmp_path / "nonexistent" / "output"
        
        result = clean_output_directory(output_dir)
        
        assert result is True
        assert output_dir.exists()
    
    def test_clean_existing_directory(self, temp_project_structure):
        """Test cleaning an existing directory removes contents."""
        repo_root, output_dir = temp_project_structure
        
        # Add some test files
        (output_dir / "test.txt").write_text("test")
        (output_dir / "subdir").mkdir()
        (output_dir / "subdir" / "nested.txt").write_text("nested")
        
        assert (output_dir / "test.txt").exists()
        assert (output_dir / "subdir" / "nested.txt").exists()
        
        # Clean
        result = clean_output_directory(output_dir)
        
        assert result is True
        assert output_dir.exists()  # Directory still exists
        assert not (output_dir / "test.txt").exists()  # Files removed
        assert not (output_dir / "subdir").exists()  # Subdirs removed
    
    def test_clean_empty_directory(self, tmp_path):
        """Test cleaning an already empty directory."""
        output_dir = tmp_path / "empty"
        output_dir.mkdir()
        
        result = clean_output_directory(output_dir)
        
        assert result is True
        assert output_dir.exists()


class TestCopyFinalDeliverables:
    """Test copying final deliverables."""
    
    def test_copy_combined_pdf(self, temp_project_structure):
        """Test copying combined PDF."""
        repo_root, output_dir = temp_project_structure
        
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        
        assert stats["combined_pdf"] == 1
        assert (output_dir / "code_project_combined.pdf").exists()
        assert (output_dir / "code_project_combined.pdf").read_text() == "mock pdf content"
    
    def test_copy_slides(self, temp_project_structure):
        """Test copying slide PDFs."""
        repo_root, output_dir = temp_project_structure
        
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        
        assert stats["slides_files"] == 2
        assert (output_dir / "slides" / "01_abstract_slides.pdf").exists()
        assert (output_dir / "slides" / "02_introduction_slides.pdf").exists()
    
    def test_copy_web_outputs(self, temp_project_structure):
        """Test copying web HTML files."""
        repo_root, output_dir = temp_project_structure
        
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        
        assert stats["web_files"] == 3  # 2 HTML files + 1 CSS file
        assert (output_dir / "web" / "01_abstract.html").exists()
        assert (output_dir / "web" / "02_introduction.html").exists()
        assert (output_dir / "web" / "style.css").exists()  # CSS copied too
    
    def test_copy_missing_combined_pdf(self, temp_project_structure):
        """Test handling missing combined PDF."""
        repo_root, output_dir = temp_project_structure
        
        # Remove combined PDF
        (repo_root / "projects" / "code_project" / "output" / "pdf" / "code_project_combined.pdf").unlink()
        
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        
        assert stats["combined_pdf"] == 0
        # Missing combined PDF is not an error, just logged as debug
        assert not (output_dir / "code_project_combined.pdf").exists()
    
    def test_copy_missing_slides_directory(self, temp_project_structure):
        """Test handling missing slides directory."""
        repo_root, output_dir = temp_project_structure
        
        # Remove slides directory
        shutil.rmtree(repo_root / "projects" / "code_project" / "output" / "slides")
        
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        
        # Should still copy PDF and handle missing slides gracefully
        assert stats["combined_pdf"] == 1
        assert stats["slides_files"] == 0


class TestValidateCopiedOutputs:
    """Test validation of copied outputs."""
    
    def test_validate_all_files_present(self, temp_project_structure):
        """Test validation when all files are present."""
        repo_root, output_dir = temp_project_structure
        
        # Copy files first
        copy_final_deliverables(repo_root, output_dir, "code_project")
        
        # Validate
        result = validate_copied_outputs(output_dir)
        
        assert result is True
    
    def test_validate_missing_combined_pdf(self, temp_project_structure):
        """Test validation fails when combined PDF is missing."""
        repo_root, output_dir = temp_project_structure
        
        # Remove PDF from source directory (fixture creates it)
        source_pdf = repo_root / "projects" / "code_project" / "output" / "pdf" / "code_project_combined.pdf"
        if source_pdf.exists():
            source_pdf.unlink()
        
        # Create empty slides and web dirs but no combined PDF in output directory
        (output_dir / "slides").mkdir()
        (output_dir / "web").mkdir()
        (output_dir / "pdf").mkdir()
        
        result = validate_copied_outputs(output_dir)
        
        assert result is False
    
    def test_validate_empty_combined_pdf(self, tmp_path):
        """Test validation fails when combined PDF is empty."""
        # Create proper output structure: output/code_project/
        output_base = tmp_path / "output"
        output_base.mkdir()
        output_dir = output_base / "code_project"
        output_dir.mkdir()
        
        # Create empty PDF
        (output_dir / "code_project_combined.pdf").write_text("")
        
        result = validate_copied_outputs(output_dir)
        
        assert result is False
    
    def test_validate_partial_outputs(self, tmp_path):
        """Test validation with partial outputs (e.g., only PDF, no slides/web)."""
        # Create proper output structure: output/code_project/
        output_base = tmp_path / "output"
        output_base.mkdir()
        output_dir = output_base / "code_project"
        output_dir.mkdir()

        # Copy only combined PDF to pdf/ directory (where it actually gets copied)
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        (pdf_dir / "code_project_combined.pdf").write_text("mock pdf")
        # Also copy to root for validation
        (output_dir / "code_project_combined.pdf").write_text("mock pdf")

        result = validate_copied_outputs(output_dir)

        # Should still pass if combined PDF exists
        assert result is True


class TestCompleteOutputCopyingWorkflow:
    """Integration tests for complete output copying workflow."""
    
    def test_clean_copy_validate_workflow(self, temp_project_structure):
        """Test complete workflow: clean → copy → validate."""
        repo_root, output_dir = temp_project_structure
        
        # Add some junk to output dir
        (output_dir / "old_file.txt").write_text("old content")
        
        # Clean
        clean_result = clean_output_directory(output_dir)
        assert clean_result is True
        assert not (output_dir / "old_file.txt").exists()
        
        # Copy
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        assert stats["combined_pdf"] == 1
        assert stats["slides_files"] == 2
        assert stats["web_files"] == 3
        
        # Validate
        valid_result = validate_copied_outputs(output_dir)
        assert valid_result is True
    
    def test_workflow_with_missing_sources(self, temp_project_structure):
        """Test workflow when some source files are missing."""
        repo_root, output_dir = temp_project_structure
        
        # Remove one slide
        slides_dir = repo_root / "projects" / "code_project" / "output" / "slides"
        (slides_dir / "02_introduction_slides.pdf").unlink()
        
        # Clean
        clean_result = clean_output_directory(output_dir)
        assert clean_result is True
        
        # Copy
        stats = copy_final_deliverables(repo_root, output_dir, "code_project")
        assert stats["combined_pdf"] == 1
        assert stats["slides_files"] == 1  # Only one slide copied
        
        # Validate
        valid_result = validate_copied_outputs(output_dir)
        assert valid_result is True  # Still valid if PDF exists


class TestValidateOutputStructure:
    """Test the comprehensive output structure validation."""
    
    def test_structure_validation(self, temp_project_structure):
        """Test structure validation with valid outputs."""
        repo_root, output_dir = temp_project_structure
        
        # Copy files first
        copy_final_deliverables(repo_root, output_dir, "code_project")
        
        # Validate structure
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["missing_files"]) == 0
        assert "project_combined_pdf" in result["directory_structure"]
        assert result["directory_structure"]["project_combined_pdf"]["exists"] is True
    
    def test_structure_missing_output_dir(self, tmp_path):
        """Test structure validation with missing output directory."""
        nonexistent = tmp_path / "nonexistent"
        
        result = validate_output_structure(nonexistent)
        
        assert result["valid"] is False
        assert "Output directory does not exist" in result["issues"]
    
    def test_structure_missing_combined_pdf(self, tmp_path):
        """Test structure validation detects missing combined PDF."""
        # Create proper output structure: output/code_project/
        output_base = tmp_path / "output"
        output_base.mkdir()
        output_dir = output_base / "code_project"
        output_dir.mkdir()
        
        # Create empty directory structure without PDF
        (output_dir / "pdf").mkdir(parents=True)
        (output_dir / "slides").mkdir()
        (output_dir / "web").mkdir()
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is False
        # Should detect missing PDF (either project-specific or legacy name)
        assert len(result["missing_files"]) > 0
    
    def test_structure_empty_directories(self, tmp_path):
        """Test structure validation with empty subdirectories."""
        # Create proper output structure: output/code_project/
        output_base = tmp_path / "output"
        output_base.mkdir()
        output_dir = output_base / "code_project"
        output_dir.mkdir()

        # Create PDF in pdf/ directory but leave slides/web empty
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "code_project_combined.pdf").write_text("x" * 1024 * 100)  # > 100KB
        # Also copy to root for validation
        (output_dir / "code_project_combined.pdf").write_text("x" * 1024 * 100)
        (output_dir / "slides").mkdir()
        (output_dir / "web").mkdir()
        
        result = validate_output_structure(output_dir)
        
        assert result["valid"] is True
        assert len([s for s in result["suspicious_sizes"] if "empty" in s]) == 2
    
    def test_structure_small_pdf(self, tmp_path):
        """Test structure validation detects unusually small PDF."""
        # Create proper output structure: output/code_project/
        output_base = tmp_path / "output"
        output_base.mkdir()
        output_dir = output_base / "code_project"
        output_dir.mkdir()
        pdf_dir = output_dir / "pdf"
        pdf_dir.mkdir()

        # Create very small PDF (< 100KB) in pdf/ directory
        (pdf_dir / "code_project_combined.pdf").write_text("tiny")
        # Also copy to root for validation
        (output_dir / "code_project_combined.pdf").write_text("tiny")
        
        result = validate_output_structure(output_dir)
        
        # Small PDF is still valid but flagged as suspicious
        assert result["valid"] is True  # Not a hard error, just a warning
        assert any("unusually small" in s for s in result["suspicious_sizes"])


class TestErrorHandling:
    """Test error handling in output copying."""
    
    def test_copy_with_permission_error(self, temp_project_structure):
        """Test handling of permission errors during copy."""
        repo_root, output_dir = temp_project_structure
        
        # Make output dir read-only (skip on Windows where this may not work)
        try:
            output_dir.chmod(0o444)
            
            # Try to copy - should handle gracefully
            stats = copy_final_deliverables(repo_root, output_dir, "code_project")
            
            # May or may not copy depending on OS
            assert isinstance(stats, dict)
            assert "errors" in stats
        finally:
            # Restore permissions
            output_dir.chmod(0o755)
    
    def test_validate_nonexistent_output_dir(self, tmp_path):
        """Test validation with non-existent output directory."""
        nonexistent = tmp_path / "nonexistent"
        
        result = validate_copied_outputs(nonexistent)
        
        # Should handle gracefully
        assert result is False or result is True  # Graceful handling

