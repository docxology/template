"""Test suite for integrity module.

This test suite provides comprehensive validation for integrity verification
including file integrity, cross-reference validation, and data consistency.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import integrity


class TestFileIntegrity:
    """Test file integrity verification."""

    def test_verify_file_integrity_existing_file(self, tmp_path):
        """Test integrity verification for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        integrity_status = integrity.verify_file_integrity([test_file])

        assert str(test_file) in integrity_status
        assert integrity_status[str(test_file)] == True

    def test_verify_file_integrity_nonexistent_file(self, tmp_path):
        """Test integrity verification for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        integrity_status = integrity.verify_file_integrity([nonexistent])

        assert str(nonexistent) in integrity_status
        assert integrity_status[str(nonexistent)] == False

    def test_verify_file_integrity_with_expected_hashes(self, tmp_path):
        """Test integrity verification with expected hashes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Calculate expected hash
        expected_hash = integrity.calculate_file_hash(test_file)
        expected_hashes = {str(test_file): expected_hash}

        integrity_status = integrity.verify_file_integrity([test_file], expected_hashes)

        assert integrity_status[str(test_file)] == True


class TestHashCalculation:
    """Test file hash calculation."""

    def test_calculate_file_hash_existing_file(self, tmp_path):
        """Test hash calculation for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash_value = integrity.calculate_file_hash(test_file)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex length
        assert hash_value.isalnum()

    def test_calculate_file_hash_nonexistent_file(self):
        """Test hash calculation for nonexistent file."""
        nonexistent = Path("nonexistent.txt")

        hash_value = integrity.calculate_file_hash(nonexistent)

        assert hash_value is None

    def test_calculate_file_hash_deterministic(self, tmp_path):
        """Test that hash calculation is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Consistent content")

        hash1 = integrity.calculate_file_hash(test_file)
        hash2 = integrity.calculate_file_hash(test_file)

        assert hash1 == hash2


class TestCrossReferenceVerification:
    """Test cross-reference integrity verification."""

    def test_verify_cross_references_complete_document(self, tmp_path):
        """Test cross-reference verification with complete document."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""
        # Introduction {#sec:intro}

        See Section \\ref{sec:methodology}.

        \\section{Methodology} {#sec:methodology}

        The algorithm is defined in \\eqref{eq:algorithm}.

        \\begin{equation}\\label{eq:algorithm}
        x = y + z
        \\end{equation}

        See Figure \\ref{fig:example}.

        \\begin{figure}[h]
        \\caption{Example figure}
        \\label{fig:example}
        \\end{figure}
        """)

        integrity_status = integrity.verify_cross_references([md_file])

        assert integrity_status['equations'] == True
        assert integrity_status['figures'] == True
        assert integrity_status['sections'] == True

    def test_verify_cross_references_missing_labels(self, tmp_path):
        """Test cross-reference verification with missing labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""
        # Introduction {#sec:intro}

        See Section \\ref{sec:missing}.
        """)

        integrity_status = integrity.verify_cross_references([md_file])

        assert integrity_status['sections'] == False


class TestDataConsistency:
    """Test data consistency verification."""

    def test_verify_data_consistency_valid_json(self, tmp_path):
        """Test data consistency for valid JSON."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value", "number": 42}')

        consistency = integrity.verify_data_consistency([json_file])

        assert consistency['file_readable'] == True
        assert consistency['data_integrity'] == True

    def test_verify_data_consistency_invalid_json(self, tmp_path):
        """Test data consistency for invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"invalid": json}')

        consistency = integrity.verify_data_consistency([json_file])

        assert consistency['data_integrity'] == False

    def test_verify_data_consistency_csv(self, tmp_path):
        """Test data consistency for CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\n1,2\n3,4")

        consistency = integrity.verify_data_consistency([csv_file])

        assert consistency['file_readable'] == True
        assert consistency['data_integrity'] == True


class TestAcademicStandards:
    """Test academic standards verification."""

    def test_verify_academic_standards_complete(self, tmp_path):
        """Test academic standards for complete document."""
        md_file = tmp_path / "complete.md"
        md_file.write_text("""
        # Abstract
        Research summary here.

        # Introduction
        Background information.

        # Methodology
        Our approach.

        # Results
        Our findings.

        # Discussion
        Analysis.

        # Conclusion
        Summary.

        References: [1], [2], [3]
        """)

        standards = integrity.verify_academic_standards([md_file])

        assert standards['has_abstract'] == True
        assert standards['has_introduction'] == True
        assert standards['has_methodology'] == True
        assert standards['has_results'] == True
        assert standards['has_discussion'] == True
        assert standards['has_conclusion'] == True
        assert standards['proper_citations'] == True

    def test_verify_academic_standards_minimal(self, tmp_path):
        """Test academic standards for minimal document."""
        md_file = tmp_path / "minimal.md"
        md_file.write_text("Just some content without proper structure.")

        standards = integrity.verify_academic_standards([md_file])

        assert standards['has_abstract'] == False
        assert standards['has_introduction'] == False
        assert standards['has_methodology'] == False
        assert standards['has_results'] == False
        assert standards['has_discussion'] == False
        assert standards['has_conclusion'] == False
        assert standards['proper_citations'] == False


class TestIntegrityReport:
    """Test comprehensive integrity verification."""

    def test_verify_output_integrity_existing_directory(self, tmp_path):
        """Test integrity verification for existing output directory."""
        # Create test files
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("PDF content")

        data_file = tmp_path / "test.csv"
        data_file.write_text("col1,col2\n1,2")

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Document\n\nSome content.")

        report = integrity.verify_output_integrity(tmp_path)

        assert report.overall_integrity == True
        assert len(report.file_integrity) > 0
        assert len(report.cross_reference_integrity) > 0

    def test_verify_output_integrity_nonexistent_directory(self, tmp_path):
        """Test integrity verification for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        report = integrity.verify_output_integrity(nonexistent)

        assert report.overall_integrity == False
        assert len(report.issues) > 0


class TestBuildArtifacts:
    """Test build artifact validation."""

    def test_validate_build_artifacts_complete(self, tmp_path):
        """Test validation of complete build artifacts."""
        # Create expected directory structure
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()

        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Create some expected files
        (pdf_dir / "01_abstract.pdf").write_text("PDF content")
        (pdf_dir / "02_introduction.pdf").write_text("PDF content")

        # Create the expected figure file
        (figures_dir / "example_figure.png").write_text("image content")

        expected_files = {
            'pdf': ['01_abstract.pdf', '02_introduction.pdf', '03_methodology.pdf'],
            'figures': ['example_figure.png']
        }

        validation = integrity.validate_build_artifacts(tmp_path, expected_files)

        assert validation['missing_files'] == ['03_methodology.pdf']
        assert validation['validation_passed'] == False

    def test_validate_build_artifacts_empty(self, tmp_path):
        """Test validation of empty build artifacts."""
        expected_files = {
            'pdf': ['01_abstract.pdf'],
            'figures': ['example_figure.png']
        }

        validation = integrity.validate_build_artifacts(tmp_path, expected_files)

        assert len(validation['missing_files']) > 0
        assert validation['validation_passed'] == False


class TestFilePermissions:
    """Test file permission checking."""

    def test_check_file_permissions_readable_directory(self, tmp_path):
        """Test permission check for readable directory."""
        permissions = integrity.check_file_permissions(tmp_path)

        assert permissions['readable'] == True
        assert permissions['writable'] == True
        assert len(permissions['issues']) == 0

    def test_check_file_permissions_nonexistent_directory(self, tmp_path):
        """Test permission check for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        permissions = integrity.check_file_permissions(nonexistent)

        assert permissions['readable'] == False
        assert len(permissions['issues']) > 0


class TestOutputCompleteness:
    """Test output completeness verification."""

    def test_verify_output_completeness_complete(self, tmp_path):
        """Test completeness verification for complete outputs."""
        # Create all expected directories and files
        for category in ['pdf', 'tex', 'data', 'figures']:
            category_dir = tmp_path / category
            category_dir.mkdir()

        # Create all expected files in each category
        for pdf in ['01_abstract.pdf', '02_introduction.pdf', '03_methodology.pdf',
                   '04_experimental_results.pdf', '05_discussion.pdf', '06_conclusion.pdf',
                   '07_references.pdf', '10_symbols_glossary.pdf', 'project_combined.pdf']:
            (tmp_path / "pdf" / pdf).write_text("PDF")

        for tex in ['01_abstract.tex', '02_introduction.tex', '03_methodology.tex',
                   '04_experimental_results.tex', '05_discussion.tex', '06_conclusion.tex',
                   '07_references.tex', '10_symbols_glossary.tex', 'project_combined.tex']:
            (tmp_path / "tex" / tex).write_text("LaTeX")

        for data in ['convergence_data.npz', 'dataset_summary.csv', 'example_data.csv',
                    'example_data.npz', 'performance_comparison.csv']:
            (tmp_path / "data" / data).write_text("data")

        for fig in ['ablation_study.png', 'convergence_plot.png', 'data_structure.png',
                   'example_figure.png', 'experimental_setup.png', 'hyperparameter_sensitivity.png',
                   'image_classification_results.png', 'recommendation_scalability.png',
                   'scalability_analysis.png', 'step_size_analysis.png']:
            (tmp_path / "figures" / fig).write_text("image")

        (tmp_path / "project_combined.html").write_text("HTML")

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness['pdf_complete'] == True
        assert completeness['figures_complete'] == True
        assert completeness['data_complete'] == True
        assert completeness['latex_complete'] == True
        assert completeness['html_complete'] == True

    def test_verify_output_completeness_incomplete(self, tmp_path):
        """Test completeness verification for incomplete outputs."""
        # Create only some directories
        (tmp_path / "pdf").mkdir()

        completeness = integrity.verify_output_completeness(tmp_path)

        assert completeness['figures_complete'] == False
        assert completeness['data_complete'] == False
        assert completeness['latex_complete'] == False
        assert completeness['html_complete'] == False


class TestIntegrityManifest:
    """Test integrity manifest generation."""

    def test_create_integrity_manifest_empty_dir(self, tmp_path):
        """Test manifest creation for empty directory."""
        manifest = integrity.create_integrity_manifest(tmp_path)

        assert manifest['file_count'] == 0
        assert manifest['total_size'] == 0
        assert len(manifest['file_hashes']) == 0

    def test_create_integrity_manifest_with_files(self, tmp_path):
        """Test manifest creation with files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        manifest = integrity.create_integrity_manifest(tmp_path)

        assert manifest['file_count'] == 1
        assert manifest['total_size'] == len("Hello, World!")
        assert 'test.txt' in manifest['file_hashes']

    def test_save_and_load_integrity_manifest(self, tmp_path):
        """Test saving and loading integrity manifests."""
        # Create and save manifest
        original_manifest = integrity.create_integrity_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        integrity.save_integrity_manifest(original_manifest, manifest_path)

        # Load and verify
        loaded_manifest = integrity.load_integrity_manifest(manifest_path)

        assert loaded_manifest is not None
        assert loaded_manifest['file_count'] == original_manifest['file_count']

    def test_load_integrity_manifest_nonexistent(self):
        """Test loading nonexistent manifest."""
        nonexistent = Path("nonexistent.json")

        manifest = integrity.load_integrity_manifest(nonexistent)

        assert manifest is None


class TestIntegrityVerification:
    """Test integrity verification against manifests."""

    def test_verify_integrity_against_manifest_identical(self, tmp_path):
        """Test verification with identical manifests."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create two identical manifests
        manifest1 = integrity.create_integrity_manifest(tmp_path)
        manifest2 = integrity.create_integrity_manifest(tmp_path)

        verification = integrity.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_changed'] == 0
        assert verification['files_added'] == 0
        assert verification['files_removed'] == 0

    def test_verify_integrity_against_manifest_modified_file(self, tmp_path):
        """Test verification with modified file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        manifest1 = integrity.create_integrity_manifest(tmp_path)

        test_file.write_text("Modified content")

        manifest2 = integrity.create_integrity_manifest(tmp_path)

        verification = integrity.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_changed'] == 1


class TestReportGeneration:
    """Test integrity report generation."""

    def test_generate_integrity_report_complete(self):
        """Test generation of complete integrity report."""
        from integrity import IntegrityReport

        report = IntegrityReport()
        report.file_integrity = {'file1.pdf': True, 'file2.pdf': False}
        report.cross_reference_integrity = {'equations': True, 'figures': False}
        report.data_consistency = {'file_readable': True}
        report.academic_standards = {'has_abstract': True}
        report.issues = ["Missing file", "Broken reference"]
        report.warnings = ["Academic standard warning"]

        report_text = integrity.generate_integrity_report(report)

        assert "INTEGRITY VERIFICATION REPORT" in report_text
        assert "Missing file" in report_text
        assert "Broken reference" in report_text
        assert "Academic standard warning" in report_text


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_verify_file_integrity_empty_list(self):
        """Test integrity verification with empty file list."""
        integrity_status = integrity.verify_file_integrity([])

        assert len(integrity_status) == 0

    def test_verify_cross_references_empty_list(self):
        """Test cross-reference verification with empty file list."""
        integrity_status = integrity.verify_cross_references([])

        assert all(integrity_status.values()) == True

    def test_verify_data_consistency_empty_list(self):
        """Test data consistency with empty file list."""
        consistency = integrity.verify_data_consistency([])

        assert consistency['file_readable'] == True
        assert consistency['data_integrity'] == True


if __name__ == "__main__":
    pytest.main([__file__])
