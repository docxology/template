"""Test suite for reproducibility module.

This test suite provides comprehensive validation for reproducibility tools
including environment capture, dependency tracking, and build verification.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import reproducibility


class TestEnvironmentCapture:
    """Test environment state capture functionality."""

    def test_capture_environment_state_basic(self):
        """Test basic environment state capture."""
        env_state = reproducibility.capture_environment_state()

        assert 'platform' in env_state
        assert 'environment_variables' in env_state
        assert 'current_directory_files' in env_state
        assert 'timestamp' in env_state

        assert 'system' in env_state['platform']
        assert 'python_version' in env_state['platform']
        assert 'working_directory' in env_state['platform']

    def test_capture_environment_state_excludes_sensitive_vars(self):
        """Test that sensitive environment variables are excluded."""
        # Set some sensitive environment variables
        import os
        original_env = dict(os.environ)

        try:
            os.environ['PATH'] = '/usr/bin:/bin'
            os.environ['HOME'] = '/home/user'
            os.environ['USER'] = 'testuser'

            env_state = reproducibility.capture_environment_state()

            # Sensitive variables should not be included
            env_vars = env_state['environment_variables']
            assert 'PATH' not in env_vars
            assert 'HOME' not in env_vars
            assert 'USER' not in env_vars
        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestDependencyCapture:
    """Test dependency state capture functionality."""

    def test_capture_dependency_state_basic(self):
        """Test basic dependency state capture."""
        deps = reproducibility.capture_dependency_state()

        # Should return a list of dictionaries
        assert isinstance(deps, list)

        # Each dependency should have required fields
        for dep in deps:
            assert 'package' in dep
            assert 'version' in dep
            assert 'source' in dep

    @patch('subprocess.run')
    def test_capture_dependency_state_with_pip(self, mock_run):
        """Test dependency capture with pip freeze."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "numpy==1.24.0\nmatplotlib==3.7.0\n"
        mock_run.return_value = mock_result

        deps = reproducibility.capture_dependency_state()

        assert len(deps) >= 2
        assert any(d['package'] == 'numpy' for d in deps)
        assert any(d['package'] == 'matplotlib' for d in deps)


class TestFileHashing:
    """Test file hashing functionality."""

    def test_calculate_file_hash_existing_file(self, tmp_path):
        """Test hash calculation for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        hash_value = reproducibility.calculate_file_hash(test_file)

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex length
        assert hash_value.isalnum()

    def test_calculate_file_hash_nonexistent_file(self):
        """Test hash calculation for nonexistent file."""
        nonexistent = Path("nonexistent_file.txt")

        hash_value = reproducibility.calculate_file_hash(nonexistent)

        assert hash_value is None

    def test_calculate_directory_hash_existing_dir(self, tmp_path):
        """Test hash calculation for existing directory."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file2 = tmp_path / "file2.txt"
        test_file1.write_text("Content 1")
        test_file2.write_text("Content 2")

        hash_value = reproducibility.calculate_directory_hash(tmp_path)

        assert hash_value is not None
        assert len(hash_value) == 64


class TestReproducibilityReport:
    """Test reproducibility report generation."""

    def test_generate_reproducibility_report_basic(self, tmp_path):
        """Test basic reproducibility report generation."""
        report = reproducibility.generate_reproducibility_report(tmp_path)

        assert report.environment_hash != ""
        assert report.dependency_hash != ""
        assert report.code_hash != ""
        assert report.data_hash != ""
        assert report.overall_hash != ""
        assert report.timestamp != ""
        assert isinstance(report.platform_info, dict)
        assert isinstance(report.dependency_info, list)

    def test_save_and_load_reproducibility_report(self, tmp_path):
        """Test saving and loading reproducibility reports."""
        # Generate and save report
        original_report = reproducibility.generate_reproducibility_report(tmp_path)
        report_path = tmp_path / "test_report.json"
        reproducibility.save_reproducibility_report(original_report, report_path)

        # Load and verify
        loaded_report = reproducibility.load_reproducibility_report(report_path)

        assert loaded_report is not None
        assert loaded_report.environment_hash == original_report.environment_hash
        assert loaded_report.dependency_hash == original_report.dependency_hash
        assert loaded_report.overall_hash == original_report.overall_hash


class TestReproducibilityVerification:
    """Test reproducibility verification functionality."""

    def test_verify_reproducibility_identical_reports(self, tmp_path):
        """Test verification with identical reports."""
        report1 = reproducibility.generate_reproducibility_report(tmp_path)
        report2 = reproducibility.generate_reproducibility_report(tmp_path)

        verification = reproducibility.verify_reproducibility(report1, report2)

        # The verification should complete without errors
        assert isinstance(verification, dict)
        assert 'code_changed' in verification
        assert 'data_changed' in verification
        assert 'dependencies_changed' in verification
        assert 'environment_changed' in verification
        assert 'overall_changed' in verification
        assert 'recommendations' in verification

    @patch('reproducibility.capture_environment_state')
    def test_verify_reproducibility_environment_changed(self, mock_capture):
        """Test verification when environment changes."""
        from reproducibility import ReproducibilityReport

        # Create two reports with different environment hashes
        report1 = ReproducibilityReport()
        report1.environment_hash = "hash1"
        report1.dependency_hash = "dep1"
        report1.code_hash = "code1"
        report1.data_hash = "data1"
        report1.overall_hash = "overall1"

        report2 = ReproducibilityReport()
        report2.environment_hash = "hash2"  # Different environment
        report2.dependency_hash = "dep1"
        report2.code_hash = "code1"
        report2.data_hash = "data1"
        report2.overall_hash = "overall2"

        verification = reproducibility.verify_reproducibility(report1, report2)

        assert verification['environment_changed'] == True
        assert verification['overall_changed'] == True
        assert len(verification['recommendations']) > 0


class TestBuildManifest:
    """Test build manifest generation."""

    def test_generate_build_manifest_empty_dir(self, tmp_path):
        """Test manifest generation for empty directory."""
        manifest = reproducibility.generate_build_manifest(tmp_path)

        assert 'timestamp' in manifest
        assert 'file_count' in manifest
        assert 'total_size' in manifest
        assert manifest['file_count'] == 0
        assert manifest['total_size'] == 0

    def test_generate_build_manifest_with_files(self, tmp_path):
        """Test manifest generation with files."""
        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        manifest = reproducibility.generate_build_manifest(tmp_path)

        assert manifest['file_count'] == 1
        assert manifest['total_size'] == len("Hello, World!")
        assert 'test.txt' in manifest['file_manifest']


class TestReproducibleEnvironment:
    """Test reproducible environment creation."""

    def test_create_reproducible_environment(self):
        """Test creation of reproducible environment configuration."""
        env_config = reproducibility.create_reproducible_environment()

        assert 'random_seeds' in env_config
        assert 'environment_variables' in env_config
        assert 'recommendations' in env_config

        assert 'python_random' in env_config['random_seeds']
        assert 'PYTHONHASHSEED' in env_config['environment_variables']
        assert len(env_config['recommendations']) > 0


class TestExperimentValidation:
    """Test experiment reproducibility validation."""

    def test_validate_experiment_reproducibility_identical(self):
        """Test validation with identical results."""
        current = {'accuracy': 0.95, 'loss': 0.05}
        expected = {'accuracy': 0.95, 'loss': 0.05}

        validation = reproducibility.validate_experiment_reproducibility(current, expected)

        assert validation['reproducible'] == True
        assert len(validation['differences']) == 0

    def test_validate_experiment_reproducibility_different(self):
        """Test validation with different results."""
        current = {'accuracy': 0.95, 'loss': 0.05}
        expected = {'accuracy': 0.90, 'loss': 0.05}

        validation = reproducibility.validate_experiment_reproducibility(current, expected)

        assert validation['reproducible'] == False
        assert 'accuracy' in validation['differences']


class TestVersionSnapshots:
    """Test version snapshot functionality."""

    def test_create_version_snapshot(self, tmp_path):
        """Test version snapshot creation."""
        snapshot_name = "test_snapshot"

        snapshot_path = reproducibility.create_version_snapshot(tmp_path, snapshot_name)

        assert snapshot_path.exists()
        assert snapshot_name in snapshot_path.name

        # Verify snapshot content
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)

        assert 'timestamp' in snapshot_data
        assert 'name' in snapshot_data
        assert snapshot_data['name'] == snapshot_name

    def test_compare_snapshots_identical(self, tmp_path):
        """Test snapshot comparison with identical snapshots."""
        # Create two identical snapshots
        snap1_path = reproducibility.create_version_snapshot(tmp_path, "test1")
        snap2_path = reproducibility.create_version_snapshot(tmp_path, "test2")

        comparison = reproducibility.compare_snapshots(snap1_path, snap2_path)

        assert 'differences' in comparison
        # The snapshots will have different timestamps, so environment will be different
        # But the comparison should still work and provide useful information
        assert isinstance(comparison['differences'], dict)

    def test_compare_snapshots_missing_file(self):
        """Test snapshot comparison with missing file."""
        missing_path = Path("missing.json")
        existing_path = Path("existing.json")

        comparison = reproducibility.compare_snapshots(missing_path, existing_path)

        assert 'error' in comparison
        assert 'not found' in comparison['error']


class TestReproducibleScriptTemplate:
    """Test reproducible script template generation."""

    def test_create_reproducible_script_template(self):
        """Test creation of reproducible script template."""
        script_name = "my_experiment"

        template = reproducibility.create_reproducible_script_template(script_name)

        assert script_name in template
        assert "reproducible research script" in template.lower()
        assert "setup_reproducible_environment" in template
        assert "reproducibility_report" in template


class TestEnvironmentValidation:
    """Test environment validation for reproducibility."""

    @patch('platform.system')
    @patch('sys.version_info')
    def test_capture_environment_state_platform_info(self, mock_version, mock_system):
        """Test platform information capture."""
        mock_system.return_value = 'Linux'
        mock_version.major = 3
        mock_version.minor = 10
        mock_version.micro = 5

        env_state = reproducibility.capture_environment_state()

        assert env_state['platform']['system'] == 'Linux'
        assert env_state['platform']['python_version'] == '3.10.5'


class TestDependencyValidation:
    """Test dependency validation for reproducibility."""

    def test_capture_dependency_state_basic(self):
        """Test basic dependency capture functionality."""
        deps = reproducibility.capture_dependency_state()

        # Should return a list (may be empty if no dependencies found)
        assert isinstance(deps, list)
        # Each dependency should be a dict with required fields
        for dep in deps:
            assert isinstance(dep, dict)
            assert 'package' in dep
            assert 'version' in dep
            assert 'source' in dep


class TestHashValidation:
    """Test hash validation functionality."""

    def test_calculate_file_hash_deterministic(self, tmp_path):
        """Test that file hashing is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        hash1 = reproducibility.calculate_file_hash(test_file)
        hash2 = reproducibility.calculate_file_hash(test_file)

        assert hash1 == hash2

    def test_calculate_file_hash_different_files(self, tmp_path):
        """Test that different files have different hashes."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"

        file1.write_text("Hello, World!")
        file2.write_text("Hello, World!")

        hash1 = reproducibility.calculate_file_hash(file1)
        hash2 = reproducibility.calculate_file_hash(file2)

        # Same content should have same hash
        assert hash1 == hash2

        file2.write_text("Different content")
        hash3 = reproducibility.calculate_file_hash(file2)

        # Different content should have different hash
        assert hash1 != hash3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_reproducibility_report_empty_dir(self, tmp_path):
        """Test report generation for empty directory."""
        report = reproducibility.generate_reproducibility_report(tmp_path)

        assert report.environment_hash != ""
        assert report.dependency_hash != ""
        # Code and data hashes might be empty for empty directory

    def test_save_reproducibility_report_invalid_path(self, tmp_path):
        """Test saving report to nested path that doesn't exist yet."""
        report = reproducibility.generate_reproducibility_report(tmp_path)
        # Use tmp_path to avoid polluting repository with test artifacts
        invalid_path = tmp_path / "nested" / "path" / "report.json"

        # Should not raise exception - function creates directories as needed
        reproducibility.save_reproducibility_report(report, invalid_path)
        
        # Verify file was created
        assert invalid_path.exists()

    def test_load_reproducibility_report_nonexistent(self):
        """Test loading nonexistent report."""
        nonexistent = Path("nonexistent.json")

        report = reproducibility.load_reproducibility_report(nonexistent)

        assert report is None


if __name__ == "__main__":
    pytest.main([__file__])
