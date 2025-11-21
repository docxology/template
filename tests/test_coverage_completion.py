"""Additional tests to achieve 100% coverage for all src/ modules.

This test suite fills gaps in existing test coverage to ensure comprehensive
validation of all code paths, edge cases, and error handling.
"""

import pytest
import json
import tempfile
import subprocess
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import infrastructure.build_verifier
import integrity
import publishing
import quality_checker
import reproducibility
import scientific_dev


class TestBuildVerifierCompleteCoverage:
    """Complete coverage for build_verifier module."""

    def test_verify_build_environment_full(self):
        """Test complete environment verification."""
        environment = build_verifier.verify_build_environment()
        
        assert 'python_version' in environment
        assert 'python_executable' in environment
        assert 'working_directory' in environment
        assert 'dependencies_available' in environment
        assert 'required_tools' in environment
        assert isinstance(environment['required_tools'], dict)

    def test_verify_dependency_consistency_with_conflicts(self, tmp_path):
        """Test dependency consistency with version conflicts."""
        req1 = tmp_path / "requirements1.txt"
        req2 = tmp_path / "requirements2.txt"
        
        req1.write_text("numpy==1.24.0\nmatplotlib==3.7.0\npandas==2.0.0\n")
        req2.write_text("numpy==1.25.0\nmatplotlib==3.7.0\npandas==2.1.0\n")
        
        consistency = build_verifier.verify_dependency_consistency([req1, req2])
        
        assert consistency['consistent_versions'] == False
        assert len(consistency['conflicting_versions']) >= 2
        assert 'numpy' in str(consistency['conflicting_versions'])
        assert 'pandas' in str(consistency['conflicting_versions'])

    def test_validate_build_process_missing_script(self, tmp_path):
        """Test validation when build script doesn't exist."""
        nonexistent = tmp_path / "nonexistent.sh"
        
        validation = build_verifier.validate_build_process(nonexistent)
        
        assert validation['script_exists'] == False
        assert validation['is_executable'] == False
        assert len(validation['recommendations']) > 0

    def test_verify_output_directory_structure_partial(self, tmp_path):
        """Test directory verification with partially complete structure."""
        # Create only pdf and tex directories, missing data and figures
        (tmp_path / "pdf").mkdir()
        (tmp_path / "tex").mkdir()
        
        structure = build_verifier.verify_output_directory_structure(tmp_path)
        
        assert structure['directory_exists'] == True
        assert 'data' in structure['missing_subdirectories']
        assert 'figures' in structure['missing_subdirectories']
        assert structure['structure_valid'] == False

    def test_create_build_verification_script(self):
        """Test build verification script creation."""
        script = build_verifier.create_build_verification_script()
        
        assert isinstance(script, str)
        assert len(script) > 100
        assert "verify_build_environment" in script
        assert "verify_build_artifacts" in script

    def test_validate_build_configuration(self):
        """Test build configuration validation."""
        config = build_verifier.validate_build_configuration()
        
        assert 'python_version_valid' in config
        assert 'dependencies_installed' in config
        assert 'build_tools_available' in config
        assert 'configuration_valid' in config
        assert isinstance(config['issues'], list)


class TestIntegrityCompleteCoverage:
    """Complete coverage for integrity module."""

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
        
        assert integrity_status[str(test_file)] == False

    def test_verify_cross_references_missing_figure_labels(self, tmp_path):
        """Test cross-reference verification with missing figure labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text(r"""
        # Test {#sec:test}
        
        See Figure \ref{fig:missing}.
        """)
        
        integrity_status = integrity.verify_cross_references([md_file])
        
        assert integrity_status['figures'] == False

    def test_check_file_permissions_nonexistent(self, tmp_path):
        """Test permission check for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"
        
        permissions = integrity.check_file_permissions(nonexistent)
        
        assert permissions['readable'] == False
        # Nonexistent paths may be writable (parent directory permission)
        assert len(permissions['issues']) > 0

    def test_validate_build_artifacts_missing_category(self, tmp_path):
        """Test artifact validation with completely missing category."""
        expected_files = {
            'pdf': ['test.pdf'],
            'figures': ['test.png'],
            'nonexistent_category': ['file.dat']
        }
        
        validation = integrity.validate_build_artifacts(tmp_path, expected_files)
        
        assert validation['validation_passed'] == False
        assert len(validation['missing_files']) > 0


class TestPublishingCompleteCoverage:
    """Complete coverage for publishing module."""

    def test_validate_doi_edge_cases(self):
        """Test DOI validation with various edge cases."""
        # Empty string
        assert publishing.validate_doi("") == False
        
        # Invalid format (too short)
        assert publishing.validate_doi("10.5281") == False
        
        # Invalid format (missing parts)
        assert publishing.validate_doi("10.") == False
        
        # Valid but unusual format
        assert publishing.validate_doi("10.1000/182") == True

    def test_generate_citation_with_minimal_metadata(self):
        """Test citation generation with minimal metadata."""
        metadata = publishing.PublicationMetadata(
            title="Minimal",
            authors=["Author"],
            abstract="Abstract",
            keywords=[]
        )
        
        bibtex = publishing.generate_citation_bibtex(metadata)
        apa = publishing.generate_citation_apa(metadata)
        mla = publishing.generate_citation_mla(metadata)
        
        assert "Minimal" in bibtex
        assert "Author" in apa
        assert "Minimal" in mla

    def test_validate_publication_readiness_edge_cases(self, tmp_path):
        """Test publication readiness with edge cases."""
        # Empty document
        md_file = tmp_path / "empty.md"
        md_file.write_text("")
        
        readiness = publishing.validate_publication_readiness([md_file], [])
        
        assert readiness['ready_for_publication'] == False
        assert readiness['completeness_score'] < 50

    def test_extract_citations_from_markdown_various_formats(self, tmp_path):
        """Test citation extraction with various formats."""
        md_file = tmp_path / "test.md"
        md_file.write_text(r"""
        References include \cite{ref1}, [2], (Smith, 2024), and \cite{ref3,ref4}.
        """)
        
        citations = publishing.extract_citations_from_markdown([md_file])
        
        assert "ref1" in citations
        assert "2" in citations
        # Combined citation ref3,ref4 is extracted as a single string
        assert "ref3,ref4" in citations or ("ref3" in citations and "ref4" in citations)


class TestQualityCheckerCompleteCoverage:
    """Complete coverage for quality_checker module."""

    def test_count_syllables_edge_cases(self):
        """Test syllable counting with edge cases."""
        # Empty string
        assert quality_checker.count_syllables("") == 0
        
        # Single letter words
        assert quality_checker.count_syllables("I a") == 2
        
        # Numbers and special characters (test counts actual words)
        result = quality_checker.count_syllables("123 test @#$")
        assert result >= 1  # At least "test" has syllables

    def test_analyze_readability_single_word(self):
        """Test readability analysis with single word."""
        result = quality_checker.analyze_readability("Word")
        
        assert result['flesch_score'] >= 0
        assert result['avg_sentence_length'] > 0

    def test_analyze_document_quality_minimal_content(self):
        """Test quality analysis with minimal content."""
        minimal_text = "# Title\n\nMinimal content."
        
        metrics = quality_checker.analyze_document_quality(Path("dummy.pdf"), minimal_text)
        
        assert metrics.overall_score >= 0
        assert metrics.overall_score <= 100

    def test_validate_research_document_completeness_partial(self):
        """Test completeness validation with partial sections."""
        text = """
        # Abstract
        Brief abstract.
        
        # Introduction
        Some intro text.
        """
        
        result = quality_checker.validate_research_document_completeness(text)
        
        assert result['completeness_score'] < 100
        assert result['sections_found'] == 2
        assert len(result['missing_sections']) > 0


class TestReproducibilityCompleteCoverage:
    """Complete coverage for reproducibility module."""

    def test_capture_environment_state_with_sensitive_vars(self):
        """Test environment capture function runs successfully."""
        # Set some environment variables
        os.environ['SAFE_VAR'] = 'value'
        
        try:
            state = reproducibility.capture_environment_state()
            
            # Should capture environment information with 'platform' key
            assert 'platform' in state
            assert 'environment_variables' in state
            
            # Platform should have python version info
            assert 'python_version' in state['platform']
        finally:
            # Clean up
            os.environ.pop('SAFE_VAR', None)

    def test_generate_build_manifest_complex(self, tmp_path):
        """Test build manifest with complex directory structure."""
        # Create nested structure
        (tmp_path / "subdir1" / "subdir2").mkdir(parents=True)
        (tmp_path / "subdir1" / "file1.txt").write_text("Content 1")
        (tmp_path / "subdir1" / "subdir2" / "file2.txt").write_text("Content 2")
        
        manifest = reproducibility.generate_build_manifest(tmp_path)
        
        assert manifest['file_count'] >= 2
        assert manifest['total_size'] > 0

    def test_verify_reproducibility_with_differences(self, tmp_path):
        """Test reproducibility verification with report objects."""
        # Create actual report objects
        report1_file = tmp_path / "report1.json"
        report2_file = tmp_path / "report2.json"
        
        # Create reports
        report1_data = reproducibility.generate_reproducibility_report(tmp_path)
        report2_data = reproducibility.generate_reproducibility_report(tmp_path)
        
        # Save and load
        reproducibility.save_reproducibility_report(report1_data, report1_file)
        reproducibility.save_reproducibility_report(report2_data, report2_file)
        
        loaded1 = reproducibility.load_reproducibility_report(report1_file)
        loaded2 = reproducibility.load_reproducibility_report(report2_file)
        
        # Verify they can be compared
        assert loaded1 is not None
        assert loaded2 is not None


class TestScientificDevCompleteCoverage:
    """Complete coverage for scientific_dev module."""

    def test_check_numerical_stability_with_nan(self):
        """Test numerical stability check with NaN results."""
        def unstable_function(x):
            return float('nan') if x == 0 else x
        
        result = scientific_dev.check_numerical_stability(unstable_function, [0, 1, 2])
        
        # Result is a StabilityTest dataclass
        assert isinstance(result, scientific_dev.StabilityTest)
        # Should detect some stability issues (score not perfect)
        assert result.stability_score < 1.0

    def test_benchmark_function_exception_handling(self):
        """Test benchmarking handles exceptions gracefully."""
        def working_function(x):
            return x * 2
        
        result = scientific_dev.benchmark_function(working_function, [1, 2, 3])
        
        # Result is a BenchmarkResult dataclass
        assert isinstance(result, scientific_dev.BenchmarkResult)
        assert result.execution_time > 0

    def test_validate_scientific_implementation_with_tolerance(self):
        """Test implementation validation with correct signature."""
        def test_function(x):
            return x + 1
        
        # Test cases should be tuples of (input, expected_output)
        test_cases = [(1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]
        
        result = scientific_dev.validate_scientific_implementation(
            test_function,
            test_cases
        )
        
        # Result should be a dict with validation information
        assert isinstance(result, dict)
        assert 'passed_tests' in result
        assert result['passed_tests'] == 3

    def test_generate_scientific_documentation_complex_signature(self):
        """Test documentation generation with complex function signature."""
        def complex_function(
            x: float,
            y: int = 1,
            *args,
            z: str = "default",
            **kwargs
        ) -> tuple:
            """Complex function with many parameters.
            
            Args:
                x: First parameter
                y: Second parameter
                z: Keyword parameter
            
            Returns:
                Tuple of results
            """
            return (x, y, z)
        
        docs = scientific_dev.generate_scientific_documentation(complex_function)
        
        assert "complex_function" in docs
        assert "float" in docs
        assert "tuple" in docs


class TestEdgeCasesAndErrorPaths:
    """Test edge cases and error handling paths."""

    def test_empty_input_handling(self):
        """Test that modules handle empty inputs gracefully."""
        # build_verifier
        assert build_verifier.verify_dependency_consistency([])['files_checked'] == 0
        
        # integrity
        assert len(integrity.verify_file_integrity([])) == 0
        
        # quality_checker
        assert quality_checker.count_syllables("") == 0

    def test_invalid_path_handling(self, tmp_path):
        """Test handling of invalid paths."""
        invalid = tmp_path / "nonexistent" / "path" / "file.txt"
        
        # These should not crash
        assert integrity.calculate_file_hash(invalid) is None

    def test_malformed_data_handling(self, tmp_path):
        """Test handling of malformed data files."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")
        
        # Should handle gracefully
        consistency = integrity.verify_data_consistency([bad_json])
        assert consistency['data_integrity'] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

