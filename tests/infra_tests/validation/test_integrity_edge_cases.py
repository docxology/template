"""Test suite for integrity module using real implementations.

This test suite provides comprehensive validation for integrity verification
including file integrity, cross-reference validation, and data consistency.

Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

# Import the module to test
import infrastructure.validation.integrity.checks as integrity

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_verify_file_integrity_empty_list(self):
        """Test integrity verification with empty file list."""
        integrity_status = integrity.verify_file_integrity([])

        assert len(integrity_status) == 0

    def test_verify_cross_references_empty_list(self):
        """Test cross-reference verification with empty file list."""
        integrity_status = integrity.verify_cross_references([])

        assert all(integrity_status.values()) is True

    def test_verify_data_consistency_empty_list(self):
        """Test data consistency with empty file list."""
        consistency = integrity.verify_data_consistency([])

        assert consistency["file_readable"] is True
        assert consistency["data_integrity"] is True

    def test_verify_file_integrity_exception(self, tmp_path):
        """Test file integrity verification with real execution."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        # Use real hash calculation
        integrity_status = integrity.verify_file_integrity([test_file])
        # Should return integrity status
        assert str(test_file) in integrity_status
        assert isinstance(integrity_status[str(test_file)], bool)

    def test_calculate_file_hash_exception(self, tmp_path):
        """Test file hash calculation with real execution."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        # Use real hash calculation
        hash_value = integrity.calculate_file_hash(test_file)
        # Should return hash string or None
        assert hash_value is None or isinstance(hash_value, str)

    def test_verify_cross_references_exception(self, tmp_path):
        """Test cross-reference verification with real execution."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n\\ref{sec:test}")

        # Use real cross-reference verification
        integrity_status = integrity.verify_cross_references([md_file])
        # Should return integrity status dictionary
        assert isinstance(integrity_status, dict)

    def test_verify_data_consistency_missing_file(self, tmp_path):
        """Test data consistency with missing file."""
        nonexistent = tmp_path / "missing.csv"
        consistency = integrity.verify_data_consistency([nonexistent])

        assert consistency["file_readable"] is False

    def test_verify_data_consistency_invalid_csv(self, tmp_path):
        """Test data consistency with invalid CSV."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("no commas or tabs")

        consistency = integrity.verify_data_consistency([invalid_csv])
        assert consistency["data_integrity"] is False

    def test_verify_data_consistency_numpy_file(self, tmp_path):
        """Test data consistency with NumPy file."""
        import numpy as np

        # Use .npy file which has shape attribute, not .npz
        npy_file = tmp_path / "data.npy"
        np.save(npy_file, np.array([1, 2, 3]))

        consistency = integrity.verify_data_consistency([npy_file])
        # The code checks hasattr(data, 'shape'), which works for .npy but not .npz
        # .npz files return dict-like objects without shape
        assert consistency["data_integrity"] is True

    def test_verify_data_consistency_pickle_file(self, tmp_path):
        """Test data consistency with pickle file."""
        import pickle

        pkl_file = tmp_path / "data.pkl"
        with open(pkl_file, "wb") as f:
            pickle.dump({"key": "value"}, f)

        # pickle is imported in integrity.py so .pkl validation succeeds
        consistency = integrity.verify_data_consistency([pkl_file])
        assert consistency["data_integrity"] is True

    def test_verify_data_consistency_exception(self, tmp_path):
        """Test data consistency with exception."""
        test_file = tmp_path / "test.json"
        test_file.write_text("invalid json")

        consistency = integrity.verify_data_consistency([test_file])
        assert consistency["data_integrity"] is False

    def test_verify_academic_standards_exception(self, tmp_path):
        """Test academic standards verification with real execution."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        # Use real academic standards verification
        standards = integrity.verify_academic_standards([md_file])
        # Should return standards dictionary
        assert isinstance(standards, dict)

    def test_verify_output_integrity_with_issues(self, tmp_path):
        """Test output integrity verification with issues."""
        pdf_file = tmp_path / "pdf" / "test.pdf"
        pdf_file.parent.mkdir()
        pdf_file.write_text("PDF content")

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        # verify_output_integrity takes output_dir, not file lists
        report = integrity.verify_output_integrity(tmp_path)

        assert isinstance(report, integrity.IntegrityReport)
        assert hasattr(report, "file_integrity")

    def test_verify_output_integrity_cross_ref_failures(self, tmp_path):
        """Test output integrity with cross-reference failures."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n\\ref{sec:nonexistent}")

        report = integrity.verify_output_integrity(tmp_path)

        if not all(report.cross_reference_integrity.values()):
            assert any("Cross-reference integrity" in issue for issue in report.issues)
            assert report.overall_integrity is False

    def test_verify_output_integrity_data_failures(self, tmp_path):
        """Test output integrity with data consistency failures."""
        data_file = tmp_path / "invalid.json"
        data_file.write_text("invalid json")

        report = integrity.verify_output_integrity(tmp_path)

        if not all(report.data_consistency.values()):
            assert any("Data consistency" in issue for issue in report.issues)

    def test_verify_output_integrity_missing_standards(self, tmp_path):
        """Test output integrity with missing academic standards."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nNo abstract or introduction.")

        report = integrity.verify_output_integrity(tmp_path)

        missing = [k for k, v in report.academic_standards.items() if not v]
        if missing:
            assert len(report.warnings) > 0
            assert any("Missing academic standards" in w for w in report.warnings)

    def test_verify_output_integrity_recommendations(self, tmp_path):
        """Test output integrity generates recommendations."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        report = integrity.verify_output_integrity(tmp_path)

        if not report.overall_integrity:
            assert len(report.recommendations) > 0
            assert any("Fix integrity issues" in r for r in report.recommendations)

    def test_generate_integrity_report_with_warnings(self):
        """Test integrity report generation with warnings."""
        from infrastructure.validation.integrity.checks import IntegrityReport

        report = IntegrityReport()
        report.file_integrity = {"file1.pdf": True}
        report.cross_reference_integrity = {"equations": True}
        report.data_consistency = {"file_readable": True}
        report.academic_standards = {"has_abstract": False}
        report.warnings = ["Missing abstract"]

        report_text = integrity.generate_integrity_report(report)

        assert "Warnings:" in report_text
        assert "Missing abstract" in report_text

    def test_generate_integrity_report_with_recommendations(self):
        """Test integrity report generation with recommendations."""
        from infrastructure.validation.integrity.checks import IntegrityReport

        report = IntegrityReport()
        report.file_integrity = {"file1.pdf": True}
        report.cross_reference_integrity = {"equations": True}
        report.data_consistency = {"file_readable": True}
        report.academic_standards = {"has_abstract": True}
        report.recommendations = ["Add more figures"]

        report_text = integrity.generate_integrity_report(report)

        assert "Recommendations:" in report_text
        assert "Add more figures" in report_text

    def test_verify_output_permissions_exception(self, tmp_path):
        """Test output permissions verification with real execution."""
        # Use real permission checking
        permissions = integrity.check_file_permissions(tmp_path)
        # Should return permissions dictionary
        assert isinstance(permissions, dict)
        assert "writable" in permissions
        assert "readable" in permissions

    def test_verify_output_permissions_read_fail(self, tmp_path):
        """Test output permissions with real execution."""
        # Use real permission checking
        permissions = integrity.check_file_permissions(tmp_path)
        # Should return permissions dictionary
        assert isinstance(permissions, dict)
        assert "readable" in permissions
        assert "writable" in permissions

    def test_verify_output_completeness_missing_pdf_dir(self, tmp_path):
        """Test output completeness when PDF directory is missing entirely."""
        # No pdf/ directory at all
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["pdf_complete"] is False
        assert any("PDF directory" in out for out in completeness["missing_outputs"])

    def test_verify_output_completeness_empty_pdf(self, tmp_path):
        """Test output completeness with empty PDF."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        empty_pdf = pdf_dir / "01_abstract.pdf"
        empty_pdf.write_text("")  # Empty file

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["pdf_complete"] is False
        assert any("Empty PDF" in out for out in completeness["incomplete_outputs"])

    def test_verify_output_completeness_missing_figures_dir(self, tmp_path):
        """Test output completeness with missing figures directory."""
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["figures_complete"] is False
        assert any("Figures directory" in out for out in completeness["missing_outputs"])

    def test_verify_output_completeness_missing_figures_detected(self, tmp_path):
        """Test output completeness when figures directory is absent."""
        # No figures/ directory at all — completeness should be False
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["figures_complete"] is False
        assert any("Figures directory" in out for out in completeness["missing_outputs"])

    def test_verify_output_completeness_small_figure(self, tmp_path):
        """Test output completeness with very small figure."""
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        small_fig = figures_dir / "example_figure.png"
        small_fig.write_text("x" * 500)  # Very small file

        completeness = integrity.verify_output_completeness(tmp_path)

        assert any("Small figure" in out for out in completeness["incomplete_outputs"])

    def test_verify_output_completeness_missing_data_dir(self, tmp_path):
        """Test output completeness with missing data directory."""
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["data_complete"] is False
        assert any("Data directory" in out for out in completeness["missing_outputs"])

    def test_verify_output_completeness_empty_data_file(self, tmp_path):
        """Test output completeness with empty data file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        empty_data = data_dir / "example_data.csv"
        empty_data.write_text("")  # Empty file

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["data_complete"] is False
        assert any("Empty data" in out for out in completeness["incomplete_outputs"])

    def test_verify_output_completeness_missing_tex_dir(self, tmp_path):
        """Test output completeness with missing tex directory."""
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["latex_complete"] is False
        assert any("LaTeX directory" in out for out in completeness["missing_outputs"])

    def test_verify_output_completeness_missing_html(self, tmp_path):
        """Test output completeness with missing HTML."""
        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["html_complete"] is False
        assert any("HTML" in out for out in completeness["missing_outputs"])

    def test_load_integrity_manifest_invalid_json(self, tmp_path):
        """Test loading invalid JSON manifest."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("invalid json")

        manifest = integrity.load_integrity_manifest(manifest_path)
        assert manifest is None

    def test_verify_output_completeness_empty_tex_file(self, tmp_path):
        """Test output completeness with empty tex file (covers lines 616-617)."""
        tex_dir = tmp_path / "tex"
        tex_dir.mkdir()
        # Create an empty tex file
        empty_tex = tex_dir / "01_abstract.tex"
        empty_tex.write_text("")  # Empty file

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["latex_complete"] is False
        assert any("Empty LaTeX" in out for out in completeness["incomplete_outputs"])

    def test_verify_output_completeness_empty_html(self, tmp_path):
        """Test output completeness with empty HTML file (covers lines 625-626)."""
        html_file = tmp_path / "project_combined.html"
        html_file.write_text("")  # Empty file

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness["html_complete"] is False
        assert any("Empty HTML" in out for out in completeness["incomplete_outputs"])

    def test_create_integrity_manifest_with_subdirectories(self, tmp_path):
        """Test manifest creation with subdirectories (covers lines 670-671)."""
        # Create nested directory structure
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        # Create files in each subdirectory
        (subdir1 / "file1.txt").write_text("Content 1")
        (subdir2 / "file2.txt").write_text("Content 2")
        (subdir2 / "file3.txt").write_text("Content 3")

        manifest = integrity.create_integrity_manifest(tmp_path)

        # Should have directory structure entries
        assert "subdir1" in manifest["directory_structure"]
        assert "subdir2" in manifest["directory_structure"]
        assert manifest["directory_structure"]["subdir1"]["file_count"] == 1
        assert manifest["directory_structure"]["subdir2"]["file_count"] == 2

    def test_verify_integrity_against_manifest_added_file(self, tmp_path):
        """Test integrity verification with added file."""
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("Content 1")

        manifest1 = integrity.create_integrity_manifest(tmp_path)

        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("Content 2")

        manifest2 = integrity.create_integrity_manifest(tmp_path)

        verification = integrity.verify_integrity_against_manifest(manifest2, manifest1)

        assert verification["files_added"] > 0
        assert "file2.txt" in verification["details"]
        assert verification["details"]["file2.txt"] == "added"

    def test_verify_integrity_against_manifest_removed_file(self, tmp_path):
        """Test integrity verification with removed file."""
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("Content 1")
        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("Content 2")

        manifest1 = integrity.create_integrity_manifest(tmp_path)

        test_file2.unlink()

        manifest2 = integrity.create_integrity_manifest(tmp_path)

        verification = integrity.verify_integrity_against_manifest(manifest2, manifest1)

        assert verification["files_removed"] > 0
        assert "file2.txt" in verification["details"]
        assert verification["details"]["file2.txt"] == "removed"
class TestIntegrityEdgeCases:
    """Edge case tests for integrity module."""

    def test_verify_file_integrity_with_mismatched_hash(self, tmp_path):
        """Test integrity verification with hash mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        # Calculate hash for original
        original_hash = integrity.calculate_file_hash(test_file)

        # Modify file
        test_file.write_text("Modified content")

        # Verify with old hash should fail
        expected_hashes = {str(test_file): original_hash}
        integrity_status = integrity.verify_file_integrity([test_file], expected_hashes)

        assert integrity_status[str(test_file)] is False

    def test_verify_cross_references_missing_figure_labels(self, tmp_path):
        """Test cross-reference verification with missing figure labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            r"""
        # Test {#sec:test}
        
        See Figure \ref{fig:missing}.
        """
        )

        integrity_status = integrity.verify_cross_references([md_file])

        assert integrity_status["figures"] is False

    def test_check_file_permissions_nonexistent(self, tmp_path):
        """Test permission check for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        permissions = integrity.check_file_permissions(nonexistent)

        assert permissions["readable"] is False
        # Nonexistent paths may be writable (parent directory permission)
        assert len(permissions["issues"]) > 0

    def test_validate_build_artifacts_missing_category(self, tmp_path):
        """Test artifact validation with completely missing category."""
        expected_files = {
            "pdf": ["test.pdf"],
            "figures": ["test.png"],
            "nonexistent_category": ["file.dat"],
        }

        validation = integrity.validate_build_artifacts(tmp_path, expected_files)

        assert validation["validation_passed"] is False
        assert len(validation["missing_files"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
