"""Test suite for build_verifier module.

This test suite provides comprehensive validation for build verification tools
including build process validation, artifact verification, and reproducibility testing.
"""

import pytest
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import build_verifier


class TestBuildCommandExecution:
    """Test build command execution functionality."""

    @patch('subprocess.run')
    def test_run_build_command_success(self, mock_run):
        """Test successful build command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Build successful"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        exit_code, stdout, stderr = build_verifier.run_build_command(['echo', 'test'])

        assert exit_code == 0
        assert stdout == "Build successful"
        assert stderr == ""

    @patch('subprocess.run')
    def test_run_build_command_timeout(self, mock_run):
        """Test build command timeout handling."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(['sleep', '10'], 5)

        exit_code, stdout, stderr = build_verifier.run_build_command(['sleep', '10'], timeout=5)

        assert exit_code == -1
        assert "timed out" in stderr


class TestBuildArtifacts:
    """Test build artifact verification."""

    def test_verify_build_artifacts_complete(self, tmp_path):
        """Test verification of complete build artifacts."""
        # Create expected directory structure
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()

        # Create some expected files
        (pdf_dir / "01_abstract.pdf").write_text("PDF content")
        (pdf_dir / "02_introduction.pdf").write_text("PDF content")

        expected_files = {
            'pdf': ['01_abstract.pdf', '02_introduction.pdf', '03_methodology.pdf'],
            'figures': ['example_figure.png']
        }

        verification = build_verifier.verify_build_artifacts(tmp_path, expected_files)

        assert '03_methodology.pdf' in verification['missing_files']
        assert verification['verification_passed'] == False

    def test_verify_build_artifacts_empty(self, tmp_path):
        """Test verification of empty build artifacts."""
        expected_files = {
            'pdf': ['01_abstract.pdf']
        }

        verification = build_verifier.verify_build_artifacts(tmp_path, expected_files)

        assert len(verification['missing_files']) >= 1
        assert verification['verification_passed'] == False


class TestBuildReproducibility:
    """Test build reproducibility verification."""

    @patch('build_verifier.run_build_command')
    def test_verify_build_reproducibility_success(self, mock_run):
        """Test reproducibility verification with successful builds."""
        # Mock successful build commands
        mock_run.return_value = (0, "Build successful", "")

        build_command = ['./test_build.sh']
        expected_outputs = {}

        reproducibility = build_verifier.verify_build_reproducibility(build_command, expected_outputs, iterations=2)

        assert reproducibility['iterations_completed'] == 2
        assert reproducibility['consistent_results'] == True
        assert len(reproducibility['exit_codes']) == 2
        assert all(code == 0 for code in reproducibility['exit_codes'])

    @patch('build_verifier.run_build_command')
    def test_verify_build_reproducibility_failure(self, mock_run):
        """Test reproducibility verification with failing builds."""
        # Mock failing build command
        mock_run.return_value = (1, "", "Build failed")

        build_command = ['./failing_build.sh']
        expected_outputs = {}

        reproducibility = build_verifier.verify_build_reproducibility(build_command, expected_outputs, iterations=2)

        assert reproducibility['iterations_completed'] == 2
        assert reproducibility['consistent_results'] == False
        assert len(reproducibility['exit_codes']) == 2
        assert all(code == 1 for code in reproducibility['exit_codes'])
        assert len(reproducibility['issues']) > 0


class TestBuildEnvironment:
    """Test build environment verification."""

    def test_verify_build_environment_basic(self):
        """Test basic build environment verification."""
        environment = build_verifier.verify_build_environment()

        assert 'python_version' in environment
        assert 'python_executable' in environment
        assert 'working_directory' in environment
        assert 'dependencies_available' in environment
        assert 'required_tools' in environment

    @patch('subprocess.run')
    def test_verify_build_environment_with_tools(self, mock_run):
        """Test environment verification with available tools."""
        # Mock successful tool detection
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.10.0"
        mock_run.return_value = mock_result

        environment = build_verifier.verify_build_environment()

        # Should detect at least some tools
        assert isinstance(environment['required_tools'], dict)


class TestBuildScriptValidation:
    """Test build script validation."""

    def test_validate_build_script_valid_script(self, tmp_path):
        """Test validation of valid build script."""
        script_file = tmp_path / "valid_script.sh"
        script_file.write_text("""#!/bin/bash
set -e
echo "Building project"
exit 0
""")
        script_file.chmod(0o755)

        validation = build_verifier.validate_build_process(script_file)

        assert validation['script_exists'] == True
        assert validation['is_executable'] == True
        assert validation['has_shebang'] == True
        assert validation['has_error_handling'] == True

    def test_validate_build_script_invalid_script(self, tmp_path):
        """Test validation of invalid build script."""
        script_file = tmp_path / "invalid_script.sh"
        script_file.write_text("echo 'No shebang or error handling'")

        validation = build_verifier.validate_build_process(script_file)

        assert validation['script_exists'] == True
        assert validation['is_executable'] == False  # Not executable
        assert validation['has_shebang'] == False
        assert validation['has_error_handling'] == False
        assert len(validation['recommendations']) > 0


class TestDependencyConsistency:
    """Test dependency consistency verification."""

    def test_verify_dependency_consistency_consistent(self, tmp_path):
        """Test verification of consistent dependencies."""
        req1 = tmp_path / "requirements1.txt"
        req2 = tmp_path / "requirements2.txt"

        req1.write_text("numpy==1.24.0\nmatplotlib==3.7.0\n")
        req2.write_text("numpy==1.24.0\nmatplotlib==3.7.0\n")

        consistency = build_verifier.verify_dependency_consistency([req1, req2])

        assert consistency['consistent_versions'] == True
        assert len(consistency['conflicting_versions']) == 0

    def test_verify_dependency_consistency_inconsistent(self, tmp_path):
        """Test verification of inconsistent dependencies."""
        req1 = tmp_path / "requirements1.txt"
        req2 = tmp_path / "requirements2.txt"

        req1.write_text("numpy==1.24.0\nmatplotlib==3.7.0\n")
        req2.write_text("numpy==1.25.0\nmatplotlib==3.7.0\n")

        consistency = build_verifier.verify_dependency_consistency([req1, req2])

        assert consistency['consistent_versions'] == False
        assert len(consistency['conflicting_versions']) > 0


class TestOutputDirectoryStructure:
    """Test output directory structure verification."""

    def test_verify_output_directory_structure_complete(self, tmp_path):
        """Test verification of complete directory structure."""
        # Create expected structure
        for dir_name in ['pdf', 'tex', 'data', 'figures']:
            (tmp_path / dir_name).mkdir()

        structure = build_verifier.verify_output_directory_structure(tmp_path)

        assert structure['directory_exists'] == True
        assert len(structure['expected_subdirectories']) == 4
        assert len(structure['missing_subdirectories']) == 0
        assert structure['structure_valid'] == True

    def test_verify_output_directory_structure_missing_dirs(self, tmp_path):
        """Test verification of incomplete directory structure."""
        # Create only some directories
        (tmp_path / "pdf").mkdir()

        structure = build_verifier.verify_output_directory_structure(tmp_path)

        assert structure['directory_exists'] == True
        assert len(structure['missing_subdirectories']) > 0
        assert structure['structure_valid'] == False


class TestBuildConfiguration:
    """Test build configuration validation."""

    def test_validate_build_configuration_basic(self):
        """Test basic build configuration validation."""
        config = build_verifier.validate_build_configuration()

        assert 'python_version_valid' in config
        assert 'dependencies_installed' in config
        assert 'build_tools_available' in config
        assert 'configuration_valid' in config
        assert 'issues' in config
        assert 'recommendations' in config


class TestBuildReportGeneration:
    """Test build report generation."""

    def test_generate_comprehensive_build_report(self):
        """Test generation of comprehensive build report."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'environment_valid': True,
            'reproducible': True,
            'issues': ["Minor warning"],
            'recommendations': ["Consider optimization"],
            'build_details': {
                'duration': 45.2,
                'exit_code': 0,
                'file_count': 15
            },
            'environment': {
                'dependencies_available': True,
                'issues': []
            },
            'artifacts': {
                'verification_passed': True,
                'file_count': 15
            },
            'reproducibility': {
                'consistent_results': True,
                'iterations_completed': 3
            }
        }

        report = build_verifier.create_comprehensive_build_report(build_results)

        assert "Comprehensive Build Verification Report" in report
        assert "Overall Status: ✅ SUCCESS" in report
        assert "45.2" in report
        assert "15" in report


class TestBuildIntegrityVerification:
    """Test build integrity verification against baselines."""

    def test_verify_integrity_against_manifest_identical(self, tmp_path):
        """Test integrity verification with identical manifests."""
        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        manifest1 = build_verifier.create_integrity_manifest(tmp_path)
        manifest2 = build_verifier.create_integrity_manifest(tmp_path)

        verification = build_verifier.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_changed'] == 0
        assert verification['files_added'] == 0
        assert verification['files_removed'] == 0

    def test_verify_integrity_against_manifest_modified(self, tmp_path):
        """Test integrity verification with modified manifest."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        manifest1 = build_verifier.create_integrity_manifest(tmp_path)

        test_file.write_text("Modified content")

        manifest2 = build_verifier.create_integrity_manifest(tmp_path)

        verification = build_verifier.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_changed'] == 1


class TestBuildVerificationScript:
    """Test build verification script creation."""

    def test_create_build_verification_script(self):
        """Test creation of build verification script."""
        script = build_verifier.create_build_verification_script()

        assert "build verification script" in script.lower()
        assert "verify_build_environment" in script
        assert "verify_build_artifacts" in script
        assert "verify_build_reproducibility" in script


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_run_build_command_nonexistent_command(self):
        """Test running nonexistent command."""
        exit_code, stdout, stderr = build_verifier.run_build_command(['nonexistent_command'])

        assert exit_code == -2
        assert "Command failed" in stderr

    def test_verify_build_artifacts_nonexistent_directory(self, tmp_path):
        """Test artifact verification for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        verification = build_verifier.verify_build_artifacts(nonexistent, {})

        assert verification['verification_passed'] == False
        assert len(verification['missing_files']) > 0

    def test_verify_dependency_consistency_empty_files(self):
        """Test dependency consistency with empty files."""
        consistency = build_verifier.verify_dependency_consistency([])

        assert consistency['files_checked'] == 0
        assert len(consistency['recommendations']) > 0


class TestBuildManifestOperations:
    """Test build manifest operations."""

    def test_create_integrity_manifest_with_files(self, tmp_path):
        """Test manifest creation with files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        manifest = build_verifier.create_integrity_manifest(tmp_path)

        assert manifest['file_count'] == 1
        assert manifest['total_size'] == len("Test content")
        assert 'test.txt' in manifest['file_hashes']

    def test_save_and_load_integrity_manifest(self, tmp_path):
        """Test saving and loading integrity manifests."""
        # Create and save manifest
        original_manifest = build_verifier.create_integrity_manifest(tmp_path)
        manifest_path = tmp_path / "manifest.json"
        build_verifier.save_integrity_manifest(original_manifest, manifest_path)

        # Load and verify
        loaded_manifest = build_verifier.load_integrity_manifest(manifest_path)

        assert loaded_manifest is not None
        assert loaded_manifest['file_count'] == original_manifest['file_count']


if __name__ == "__main__":
    pytest.main([__file__])
