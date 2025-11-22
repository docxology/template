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
import infrastructure.build_verifier as build_verifier


class TestBuildVerificationReport:
    """Test BuildVerificationReport class."""

    def test_build_verification_report_init(self):
        """Test BuildVerificationReport initialization."""
        report = build_verifier.BuildVerificationReport()
        
        assert report.build_timestamp == ""
        assert report.build_duration == 0.0
        assert report.exit_code == 0
        assert report.output_files == []
        assert report.build_hash == ""
        assert report.dependency_hash == ""
        assert report.environment_hash == ""
        assert report.verification_passed == True
        assert report.issues == []
        assert report.warnings == []
        assert report.recommendations == []


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
    
    def test_verify_build_artifacts_file_not_exists(self, tmp_path):
        """Test verification when expected file doesn't exist (branch 174->172)."""
        expected_files = {
            'pdf': ['nonexistent.pdf']
        }
        
        verification = build_verifier.verify_build_artifacts(tmp_path, expected_files)
        
        # File doesn't exist, so it should be in missing_files
        assert 'nonexistent.pdf' in verification['missing_files']
        assert verification['verification_passed'] == False

    def test_verify_build_artifacts_empty(self, tmp_path):
        """Test verification of empty build artifacts."""
        expected_files = {
            'pdf': ['01_abstract.pdf']
        }

        verification = build_verifier.verify_build_artifacts(tmp_path, expected_files)

        assert len(verification['missing_files']) >= 1
        assert verification['verification_passed'] == False

    def test_verify_build_artifacts_unexpected_files(self, tmp_path):
        """Test verification with unexpected files."""
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir()
        (pdf_dir / "01_abstract.pdf").write_text("PDF content")
        (tmp_path / "unexpected_file.txt").write_text("Unexpected")

        expected_files = {
            'pdf': ['01_abstract.pdf']
        }

        verification = build_verifier.verify_build_artifacts(tmp_path, expected_files)

        assert len(verification.get('unexpected_files', [])) > 0


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

    @patch('build_verifier.run_build_command')
    @patch('build_verifier.calculate_file_hash')
    def test_verify_build_reproducibility_with_outputs(self, mock_hash, mock_run, tmp_path):
        """Test reproducibility verification with output file hashing."""
        mock_run.return_value = (0, "Build successful", "")
        output_file = tmp_path / "output.txt"
        output_file.write_text("Test output")
        mock_hash.return_value = "hash123"

        build_command = ['./test_build.sh']
        expected_outputs = {str(output_file): "expected content"}

        reproducibility = build_verifier.verify_build_reproducibility(
            build_command, expected_outputs, iterations=2
        )

        assert reproducibility['iterations_completed'] == 2
        assert mock_hash.called
    
    @patch('build_verifier.run_build_command')
    def test_verify_build_reproducibility_output_file_not_exists(self, mock_run, tmp_path):
        """Test reproducibility when expected output file doesn't exist (branch 174->172)."""
        mock_run.return_value = (0, "Build successful", "")
        build_command = ['./test_build.sh']
        
        # Create expected_outputs with a file that doesn't exist
        nonexistent_file = tmp_path / "nonexistent.txt"
        expected_outputs = {
            str(nonexistent_file): "expected content"
        }
        
        reproducibility = build_verifier.verify_build_reproducibility(
            build_command, expected_outputs=expected_outputs
        )
        
        # File doesn't exist, so it should skip hashing (branch 174->172)
        # The function should still complete successfully
        assert reproducibility['iterations_completed'] == 3
        # Since file doesn't exist, it won't be in output_hashes
        assert str(nonexistent_file) not in reproducibility.get('output_hashes', {})

    @patch('build_verifier.run_build_command')
    def test_verify_build_reproducibility_inconsistent_hashes(self, mock_run, tmp_path):
        """Test reproducibility with inconsistent output hashes."""
        mock_run.return_value = (0, "Build successful", "")
        
        output_file = tmp_path / "output.txt"
        output_file.write_text("Output 1")
        
        def hash_side_effect(path):
            # Return different hashes for different iterations
            if not hasattr(hash_side_effect, 'call_count'):
                hash_side_effect.call_count = 0
            hash_side_effect.call_count += 1
            return f"hash{hash_side_effect.call_count}"
        
        with patch('build_verifier.calculate_file_hash', side_effect=hash_side_effect):
            build_command = ['./test_build.sh']
            expected_outputs = {str(output_file): "content"}

            reproducibility = build_verifier.verify_build_reproducibility(
                build_command, expected_outputs, iterations=2
            )

            assert reproducibility['iterations_completed'] == 2
            assert reproducibility['consistent_results'] == False

    @patch('build_verifier.run_build_command')
    def test_verify_build_reproducibility_exception(self, mock_run):
        """Test reproducibility verification with exception."""
        def side_effect(*args, **kwargs):
            raise Exception("Build error")
        mock_run.side_effect = side_effect

        build_command = ['./test_build.sh']
        expected_outputs = {}

        reproducibility = build_verifier.verify_build_reproducibility(
            build_command, expected_outputs, iterations=1
        )

        assert reproducibility['iterations_completed'] >= 0
        assert reproducibility['consistent_results'] == False
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

    @patch('subprocess.run')
    def test_verify_build_environment_tool_exception(self, mock_run):
        """Test environment verification with tool exception."""
        mock_run.side_effect = Exception("Tool check failed")

        environment = build_verifier.verify_build_environment()

        assert 'required_tools' in environment
        assert environment['dependencies_available'] == False
        assert len(environment['issues']) > 0


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
    
    def test_validate_build_script_nonexistent(self, tmp_path):
        """Test validation of nonexistent build script (lines 476-477)."""
        nonexistent_script = tmp_path / "nonexistent.sh"
        
        validation = build_verifier.validate_build_process(nonexistent_script)
        
        assert validation['script_exists'] == False
        assert validation['validation_passed'] == False
        assert "Build script does not exist" in validation['recommendations']

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

    def test_validate_build_script_read_exception(self, tmp_path):
        """Test validation with read exception."""
        script_file = tmp_path / "script.sh"
        script_file.write_text("#!/bin/bash\necho test")
        
        with patch('builtins.open', side_effect=Exception("Read error")):
            validation = build_verifier.validate_build_process(script_file)
            
            assert "Failed to read script" in str(validation['recommendations'])

    def test_validate_build_script_no_logging(self, tmp_path):
        """Test validation of script without logging."""
        # Create script with no logging keywords (no 'log', 'echo', or 'print')
        script_file = tmp_path / "no_logging.sh"
        script_file.write_text("#!/bin/bash\nset -e\n# No output statements")
        script_file.chmod(0o755)

        validation = build_verifier.validate_build_process(script_file)

        # Script should not have logging (no 'log', 'echo', or 'print' in lowercase)
        # The word "logging" in comment doesn't count as it's not a command
        assert validation['has_logging'] == False
        assert any("logging" in rec.lower() for rec in validation['recommendations'])

    def test_validate_build_script_no_documentation(self, tmp_path):
        """Test validation of script without documentation."""
        script_file = tmp_path / "no_docs.sh"
        script_file.write_text("#!/bin/bash\nset -e\necho test")
        script_file.chmod(0o755)

        validation = build_verifier.validate_build_process(script_file)

        assert validation['has_documentation'] == False
        assert any("documentation" in rec.lower() for rec in validation['recommendations'])


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

    def test_verify_dependency_consistency_missing_file(self, tmp_path):
        """Test dependency consistency with missing file."""
        req1 = tmp_path / "requirements1.txt"
        req2 = tmp_path / "nonexistent.txt"
        req1.write_text("numpy==1.24.0\n")

        consistency = build_verifier.verify_dependency_consistency([req1, req2])

        assert req2.name in str(consistency['missing_files'])

    def test_verify_dependency_consistency_parse_exception(self, tmp_path):
        """Test dependency consistency with parse exception."""
        req1 = tmp_path / "requirements1.txt"
        req1.write_text("numpy==1.24.0\n")

        with patch('builtins.open', side_effect=Exception("Parse error")):
            consistency = build_verifier.verify_dependency_consistency([req1])
            
            assert len(consistency['recommendations']) > 0
            assert any("Failed to parse" in rec for rec in consistency['recommendations'])

    def test_verify_dependency_consistency_with_conflicts(self, tmp_path):
        """Test dependency consistency detection with conflicts."""
        req1 = tmp_path / "requirements1.txt"
        req2 = tmp_path / "requirements2.txt"
        req3 = tmp_path / "requirements3.txt"

        req1.write_text("numpy==1.24.0\n")
        req2.write_text("numpy==1.25.0\n")
        req3.write_text("numpy==1.24.0\n")

        consistency = build_verifier.verify_dependency_consistency([req1, req2, req3])

        assert consistency['consistent_versions'] == False
        assert len(consistency['conflicting_versions']) > 0
        assert any("Resolve version conflicts" in rec for rec in consistency['recommendations'])


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

    def test_verify_output_directory_structure_nonexistent(self, tmp_path):
        """Test verification of nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        structure = build_verifier.verify_output_directory_structure(nonexistent)

        assert structure['directory_exists'] == False
        assert structure['structure_valid'] == False

    def test_verify_output_directory_structure_unexpected_dirs(self, tmp_path):
        """Test verification with unexpected directories."""
        (tmp_path / "pdf").mkdir()
        (tmp_path / "unexpected").mkdir()

        structure = build_verifier.verify_output_directory_structure(tmp_path)

        assert len(structure['unexpected_subdirectories']) > 0
    
    def test_verify_output_directory_structure_with_files(self, tmp_path):
        """Test verification with files (not directories) in output (branch 664->663)."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create a file (not a directory) in output
        (output_dir / "some_file.txt").write_text("content")
        (output_dir / "pdf").mkdir()  # Also create a directory
        
        result = build_verifier.verify_output_directory_structure(output_dir)
        
        # Files should be ignored (not counted as directories)
        # The file should not appear in unexpected_dirs since it's not a dir
        assert 'some_file.txt' not in result.get('unexpected_subdirectories', [])


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

    def test_validate_build_configuration_old_python(self):
        """Test configuration validation with old Python version."""
        # Create a mock version_info that behaves like a tuple
        class MockVersionInfo:
            def __init__(self, major, minor):
                self.major = major
                self.minor = minor
            
            def __ge__(self, other):
                return (self.major, self.minor) >= other
        
        with patch('sys.version_info', MockVersionInfo(3, 9)):
            config = build_verifier.validate_build_configuration()

            assert config['python_version_valid'] == False
            assert len(config['issues']) > 0

    @patch('builtins.__import__')
    def test_validate_build_configuration_missing_deps(self, mock_import):
        """Test configuration validation with missing dependencies."""
        mock_import.side_effect = ImportError("No module named 'matplotlib'")

        config = build_verifier.validate_build_configuration()

        assert config['dependencies_installed'] == False
        assert len(config['issues']) > 0

    @patch('os.system')
    def test_validate_build_configuration_missing_tools(self, mock_system):
        """Test configuration validation with missing build tools."""
        mock_system.return_value = 1  # Tool not found

        config = build_verifier.validate_build_configuration()

        assert config['build_tools_available'] == False
        assert len(config['issues']) > 0


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
    
    def test_create_build_validation_report_with_issues(self):
        """Test creating report with issues (branch 616->622)."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'environment_valid': True,
            'reproducible': True,
            'issues': ['Issue 1', 'Issue 2']
        }
        
        report = build_verifier.create_build_validation_report(build_results)
        assert 'Issues' in report
        assert 'Issue 1' in report
    
    def test_create_build_validation_report_with_recommendations(self):
        """Test creating report with recommendations (branch 622->628)."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'environment_valid': True,
            'reproducible': True,
            'recommendations': ['Rec 1', 'Rec 2']
        }
        
        report = build_verifier.create_build_validation_report(build_results)
        assert 'Recommendations' in report
        assert 'Rec 1' in report
    
    def test_create_build_validation_report_with_performance(self):
        """Test creating report with performance metrics (branch 628->635)."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'environment_valid': True,
            'reproducible': True,
            'performance_metrics': {
                'duration': 10.5,
                'file_count': 5
            }
        }
        
        report = build_verifier.create_build_validation_report(build_results)
        assert 'Performance' in report
        assert '10.5' in report
        assert '5' in report

    def test_create_build_validation_report(self):
        """Test creation of build validation report."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'environment_valid': True,
            'reproducible': True,
            'issues': ["Issue 1"],
            'recommendations': ["Rec 1"],
            'performance_metrics': {
                'duration': 30.5,
                'file_count': 10
            }
        }

        report = build_verifier.create_build_validation_report(build_results)

        assert "Build Validation Report" in report
        assert "30.5" in report
        assert "10" in report
        assert "Issue 1" in report
        assert "Rec 1" in report

    def test_create_comprehensive_build_report_failure(self):
        """Test comprehensive report with failure status."""
        build_results = {
            'build_succeeded': False,
            'artifacts_verified': False,
            'environment': {
                'dependencies_available': False,
                'issues': ['Missing tool']
            },
            'artifacts': {
                'verification_passed': False,
                'missing_files': ['file1.pdf']
            },
            'reproducibility': {
                'consistent_results': False,
                'issues': ['Inconsistent output']
            }
        }

        report = build_verifier.create_comprehensive_build_report(build_results)

        assert "Overall Status: ❌ FAILURE" in report
        assert "Missing tool" in report
        assert "file1.pdf" in report
        assert "Inconsistent output" in report

    def test_create_comprehensive_build_report_partial(self):
        """Test comprehensive report with partial results."""
        build_results = {
            'build_succeeded': True,
            'artifacts_verified': True,
            'reproducible': False
        }

        report = build_verifier.create_comprehensive_build_report(build_results)

        assert "Overall Status: ❌ FAILURE" in report


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

    def test_verify_build_integrity_against_baseline_both_exist(self, tmp_path):
        """Test integrity verification when both baseline and current exist."""
        baseline_path = tmp_path / "baseline.json"
        current_path = tmp_path / "current.json"

        baseline_data = {'file_count': 10, 'total_size': 1000}
        current_data = {'file_count': 10, 'total_size': 1000}

        baseline_path.write_text(json.dumps(baseline_data))
        current_path.write_text(json.dumps(current_data))

        verification = build_verifier.verify_build_integrity_against_baseline(
            baseline_path, current_path
        )

        assert verification['baseline_exists'] == True
        assert verification['current_exists'] == True
        assert verification['integrity_maintained'] == True

    def test_verify_build_integrity_against_baseline_missing_baseline(self, tmp_path):
        """Test integrity verification with missing baseline."""
        baseline_path = tmp_path / "baseline.json"
        current_path = tmp_path / "current.json"
        current_path.write_text(json.dumps({'file_count': 10}))

        verification = build_verifier.verify_build_integrity_against_baseline(
            baseline_path, current_path
        )

        assert verification['baseline_exists'] == False
        assert "Create baseline" in str(verification['recommendations'])

    def test_verify_build_integrity_against_baseline_missing_current(self, tmp_path):
        """Test integrity verification with missing current."""
        baseline_path = tmp_path / "baseline.json"
        current_path = tmp_path / "current.json"
        baseline_path.write_text(json.dumps({'file_count': 10}))

        verification = build_verifier.verify_build_integrity_against_baseline(
            baseline_path, current_path
        )

        assert verification['current_exists'] == False
        assert "Current build results not found" in str(verification['recommendations'])

    def test_verify_build_integrity_against_baseline_differences(self, tmp_path):
        """Test integrity verification with differences."""
        baseline_path = tmp_path / "baseline.json"
        current_path = tmp_path / "current.json"

        baseline_data = {'file_count': 10, 'total_size': 1000}
        current_data = {'file_count': 12, 'total_size': 1200}

        baseline_path.write_text(json.dumps(baseline_data))
        current_path.write_text(json.dumps(current_data))

        verification = build_verifier.verify_build_integrity_against_baseline(
            baseline_path, current_path
        )

        assert verification['integrity_maintained'] == False
        assert len(verification['differences']) > 0

    def test_verify_build_integrity_against_baseline_exception(self, tmp_path):
        """Test integrity verification with exception."""
        baseline_path = tmp_path / "baseline.json"
        current_path = tmp_path / "current.json"

        baseline_path.write_text("invalid json")
        current_path.write_text("invalid json")

        verification = build_verifier.verify_build_integrity_against_baseline(
            baseline_path, current_path
        )

        assert "Failed to compare builds" in str(verification['recommendations'])

    def test_verify_integrity_against_manifest_added_files(self, tmp_path):
        """Test integrity verification with added files."""
        manifest1 = {'file_hashes': {'file1.txt': 'hash1'}}
        manifest2 = {'file_hashes': {'file1.txt': 'hash1', 'file2.txt': 'hash2'}}

        verification = build_verifier.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_added'] == 1
        assert verification['verification_passed'] == False

    def test_verify_integrity_against_manifest_removed_files(self, tmp_path):
        """Test integrity verification with removed files."""
        manifest1 = {'file_hashes': {'file1.txt': 'hash1', 'file2.txt': 'hash2'}}
        manifest2 = {'file_hashes': {'file1.txt': 'hash1'}}

        verification = build_verifier.verify_integrity_against_manifest(manifest1, manifest2)

        assert verification['files_removed'] == 1
        assert verification['verification_passed'] == False


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
    
    def test_verify_dependency_consistency_line_without_equals(self, tmp_path):
        """Test dependency consistency with line without == (branch 568->566)."""
        req_file = tmp_path / "requirements.txt"
        # Write a line that doesn't have '==' (should be skipped)
        req_file.write_text("some-package\n# comment\nanother-package==1.0\n")
        
        # Pass Path object, not string
        result = build_verifier.verify_dependency_consistency([req_file])
        # Should only parse lines with '==', so 'some-package' should be skipped
        # This covers branch 568->566 when line doesn't have '=='
        # Check consistent_versions instead of is_consistent
        assert result.get('consistent_versions', True) == True


class TestFileHashCalculation:
    """Test file hash calculation."""

    def test_calculate_file_hash_success(self, tmp_path):
        """Test successful file hash calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash_value = build_verifier.calculate_file_hash(test_file)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex digest length

    def test_calculate_file_hash_nonexistent(self, tmp_path):
        """Test hash calculation for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        hash_value = build_verifier.calculate_file_hash(nonexistent)

        assert hash_value is None

    def test_calculate_file_hash_exception(self, tmp_path):
        """Test hash calculation with exception."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        with patch('builtins.open', side_effect=Exception("Read error")):
            hash_value = build_verifier.calculate_file_hash(test_file)

            assert hash_value is None


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

    def test_create_integrity_manifest_nonexistent_dir(self, tmp_path):
        """Test manifest creation with nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        manifest = build_verifier.create_integrity_manifest(nonexistent)

        assert manifest['file_count'] == 0
        assert manifest['total_size'] == 0

    def test_create_integrity_manifest_with_exception(self, tmp_path):
        """Test manifest creation with file exception."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # Patch calculate_file_hash to raise exception
        def mock_calculate_file_hash(path):
            raise Exception("Stat error")
        
        with patch('build_verifier.calculate_file_hash', side_effect=mock_calculate_file_hash):
            manifest = build_verifier.create_integrity_manifest(tmp_path)
            
            # Should handle exception gracefully (see line 950-951)
            assert 'file_hashes' in manifest
            # Exception should be stored as string in file_hashes
            assert any(isinstance(v, str) and "Stat error" in v for v in manifest['file_hashes'].values())

    def test_create_integrity_manifest_with_directories(self, tmp_path):
        """Test manifest creation with directory structure."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("Content")
        (tmp_path / "file2.txt").write_text("Content2")

        manifest = build_verifier.create_integrity_manifest(tmp_path)

        assert manifest['file_count'] == 2
        assert 'subdir' in manifest['directory_structure']

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

    def test_load_integrity_manifest_nonexistent(self, tmp_path):
        """Test loading nonexistent manifest."""
        nonexistent = tmp_path / "nonexistent.json"

        manifest = build_verifier.load_integrity_manifest(nonexistent)

        assert manifest is None

    def test_load_integrity_manifest_invalid_json(self, tmp_path):
        """Test loading invalid JSON manifest."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("invalid json")

        manifest = build_verifier.load_integrity_manifest(manifest_path)

        assert manifest is None


if __name__ == "__main__":
    pytest.main([__file__])
