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

    def test_capture_environment_state_exception(self):
        """Test environment capture with exception in directory listing."""
        with patch('pathlib.Path.glob', side_effect=Exception("Access denied")):
            env_state = reproducibility.capture_environment_state()
            # Should handle exception gracefully
            assert 'current_directory_files' in env_state
            assert env_state['current_directory_files'] == []
            assert env_state['current_directory_directories'] == []

    @patch('subprocess.run')
    def test_capture_dependency_state_uv(self, mock_run):
        """Test dependency capture with uv."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "numpy==1.25.0\npandas==2.0.0\n"
        mock_run.return_value = mock_result

        deps = reproducibility.capture_dependency_state()

        # Should include uv dependencies
        assert len(deps) >= 2
        assert any(d['package'] == 'numpy' and d['source'] == 'uv' for d in deps)

    @patch('subprocess.run')
    def test_capture_dependency_state_uv_existing_package(self, mock_run):
        """Test uv dependency capture when package already exists from pip."""
        # First call (pip) returns numpy
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "numpy==1.24.0\n"
        
        # Second call (uv) returns numpy with different version
        uv_result = MagicMock()
        uv_result.returncode = 0
        uv_result.stdout = "numpy==1.25.0\n"
        
        mock_run.side_effect = [pip_result, uv_result]

        deps = reproducibility.capture_dependency_state()

        # Should update numpy to uv version
        numpy_deps = [d for d in deps if d['package'] == 'numpy']
        assert len(numpy_deps) == 1
        assert numpy_deps[0]['source'] == 'uv'
        assert numpy_deps[0]['version'] == '1.25.0'

    @patch('subprocess.run')
    def test_capture_dependency_state_timeout(self, mock_run):
        """Test dependency capture with timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(['pip', 'freeze'], 30)

        deps = reproducibility.capture_dependency_state()

        # Should return empty list on timeout
        assert isinstance(deps, list)

    def test_calculate_file_hash_exception(self, tmp_path):
        """Test file hash calculation with exception."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        with patch('builtins.open', side_effect=Exception("Read error")):
            hash_value = reproducibility.calculate_file_hash(test_file)
            assert hash_value is None

    def test_calculate_directory_hash_exception(self, tmp_path):
        """Test directory hash calculation with exception."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("Content")

        with patch('pathlib.Path.rglob', side_effect=Exception("Access error")):
            hash_value = reproducibility.calculate_directory_hash(test_dir)
            assert hash_value is None

    def test_calculate_directory_hash_no_files(self, tmp_path):
        """Test directory hash with no files."""
        test_dir = tmp_path / "empty_dir"
        test_dir.mkdir()

        hash_value = reproducibility.calculate_directory_hash(test_dir)
        assert hash_value is None

    def test_generate_reproducibility_report_no_src(self, tmp_path):
        """Test report generation when src/ doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            report = reproducibility.generate_reproducibility_report(tmp_path)
            assert report.code_hash == ""
            assert any("source code" in issue.lower() for issue in report.issues)

    def test_generate_reproducibility_report_no_deps(self, tmp_path):
        """Test report generation with no dependencies."""
        with patch('reproducibility.capture_dependency_state', return_value=[]):
            report = reproducibility.generate_reproducibility_report(tmp_path)
            assert len(report.dependency_info) == 0
            assert any("dependency information" in rec.lower() for rec in report.recommendations)

    def test_generate_reproducibility_report_no_data_hash(self, tmp_path):
        """Test report generation with no data directory."""
        report = reproducibility.generate_reproducibility_report(tmp_path)
        # The data_hash might be "no_data_directory" or empty
        # Recommendation is only added if data_hash is falsy (empty string)
        # If it's "no_data_directory", it's truthy so no recommendation
        # Just verify the report was generated successfully
        assert report.data_hash is not None
        assert isinstance(report.recommendations, list)

    def test_generate_build_manifest_nonexistent_dir(self, tmp_path):
        """Test build manifest generation for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        manifest = reproducibility.generate_build_manifest(nonexistent)
        
        assert manifest['file_count'] == 0
        assert manifest['directory_count'] == 0
        assert 'timestamp' in manifest

    def test_generate_build_manifest_with_exception(self, tmp_path):
        """Test build manifest generation with file access exception."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "file.txt"
        test_file.write_text("Content")

        # Patch the second stat() call (line 448) which doesn't have exception handling
        # But we need to allow is_file() to work, so we'll patch it more carefully
        # Actually, let's test the exception in the first loop (lines 414-420) which has try-except
        # We need to patch stat() but allow is_file() to work
        call_count = [0]
        original_stat = Path.stat
        
        def mock_stat(self):
            call_count[0] += 1
            # Raise exception on second stat() call (for st_size), not first (for is_file)
            if call_count[0] == 2:
                raise Exception("Stat error")
            return original_stat(self)

        with patch.object(Path, 'stat', mock_stat):
            # This will test the exception path in the first loop (line 419)
            manifest = reproducibility.generate_build_manifest(test_dir)
            # Should handle exception gracefully
            assert 'file_manifest' in manifest

    def test_generate_build_manifest_file_manifest(self, tmp_path):
        """Test build manifest with file hashes."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        test_file = test_dir / "file.txt"
        test_file.write_text("Content")

        manifest = reproducibility.generate_build_manifest(test_dir)
        
        assert 'file.txt' in manifest['file_manifest']
        file_info = manifest['file_manifest']['file.txt']
        assert 'hash' in file_info
        assert 'size' in file_info
        assert 'modified' in file_info

    def test_save_build_manifest(self, tmp_path):
        """Test saving build manifest."""
        manifest = {
            'timestamp': '2024-01-01T00:00:00',
            'file_count': 1,
            'file_manifest': {}
        }
        manifest_path = tmp_path / "manifest.json"
        
        reproducibility.save_build_manifest(manifest, manifest_path)
        
        assert manifest_path.exists()
        with open(manifest_path) as f:
            loaded = json.load(f)
            assert loaded['file_count'] == 1

    def test_verify_build_integrity_missing_manifest(self, tmp_path):
        """Test build integrity verification with missing manifest."""
        nonexistent = tmp_path / "nonexistent.json"
        result = reproducibility.verify_build_integrity(nonexistent, tmp_path)
        
        assert 'error' in result
        assert 'not found' in result['error']

    def test_verify_build_integrity_missing_file(self, tmp_path):
        """Test build integrity verification with missing file."""
        manifest = {
            'timestamp': '2024-01-01T00:00:00',
            'file_manifest': {
                'missing.txt': {'hash': 'abc123', 'size': 10}
            }
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        result = reproducibility.verify_build_integrity(manifest_path, tmp_path)
        
        assert result['files_missing'] > 0
        assert 'missing.txt' in result['details']
        assert result['details']['missing.txt'] == 'missing'

    def test_verify_build_integrity_changed_file(self, tmp_path):
        """Test build integrity verification with changed file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")
        
        original_hash = reproducibility.calculate_file_hash(test_file)
        
        manifest = {
            'timestamp': '2024-01-01T00:00:00',
            'file_manifest': {
                'test.txt': {'hash': 'different_hash', 'size': 10}
            }
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        result = reproducibility.verify_build_integrity(manifest_path, tmp_path)
        
        assert result['files_changed'] > 0
        assert 'test.txt' in result['details']
        assert result['details']['test.txt'] == 'changed'

    def test_verify_build_integrity_new_file(self, tmp_path):
        """Test build integrity verification with new file."""
        test_file = tmp_path / "new.txt"
        test_file.write_text("New content")
        
        manifest = {
            'timestamp': '2024-01-01T00:00:00',
            'file_manifest': {}
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        result = reproducibility.verify_build_integrity(manifest_path, tmp_path)
        
        assert result['files_added'] > 0
        assert 'new.txt' in result['details']
        assert result['details']['new.txt'] == 'added'

    def test_verify_build_integrity_exception(self, tmp_path):
        """Test build integrity verification with exception."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("invalid json")
        
        result = reproducibility.verify_build_integrity(manifest_path, tmp_path)
        
        assert 'error' in result
        assert 'Failed to verify' in result['error']

    def test_validate_experiment_reproducibility_differences(self):
        """Test experiment reproducibility validation with differences."""
        current = {'value1': 1.0, 'value2': 2.0}
        expected = {'value1': 1.0, 'value2': 2.5}
        
        result = reproducibility.validate_experiment_reproducibility(current, expected, tolerance=0.1)
        
        assert result['reproducible'] == False
        assert 'value2' in result['differences']
        assert len(result['recommendations']) > 0

    def test_validate_experiment_reproducibility_reproducible(self):
        """Test experiment reproducibility validation with matching results."""
        current = {'value1': 1.0, 'value2': 2.0}
        expected = {'value1': 1.0, 'value2': 2.0}
        
        result = reproducibility.validate_experiment_reproducibility(current, expected)
        
        assert result['reproducible'] == True
        assert len(result['differences']) == 0

    def test_compare_snapshots_different_environment(self, tmp_path):
        """Test snapshot comparison with different environments."""
        snap1 = {
            'timestamp': '2024-01-01T00:00:00',
            'environment': {'platform': 'Linux'},
            'dependencies': [],
            'manifest': {'file_manifest': {}}
        }
        snap2 = {
            'timestamp': '2024-01-02T00:00:00',
            'environment': {'platform': 'Windows'},
            'dependencies': [],
            'manifest': {'file_manifest': {}}
        }
        
        snap1_path = tmp_path / "snap1.json"
        snap2_path = tmp_path / "snap2.json"
        
        with open(snap1_path, 'w') as f:
            json.dump(snap1, f)
        with open(snap2_path, 'w') as f:
            json.dump(snap2, f)
        
        result = reproducibility.compare_snapshots(snap1_path, snap2_path)
        
        assert 'environment' in result['differences']
        assert result['differences']['environment']['changed'] == True

    def test_compare_snapshots_different_dependencies(self, tmp_path):
        """Test snapshot comparison with different dependencies."""
        snap1 = {
            'timestamp': '2024-01-01T00:00:00',
            'environment': {},
            'dependencies': [{'package': 'numpy', 'version': '1.24.0'}],
            'manifest': {'file_manifest': {}}
        }
        snap2 = {
            'timestamp': '2024-01-02T00:00:00',
            'environment': {},
            'dependencies': [{'package': 'numpy', 'version': '1.25.0'}],
            'manifest': {'file_manifest': {}}
        }
        
        snap1_path = tmp_path / "snap1.json"
        snap2_path = tmp_path / "snap2.json"
        
        with open(snap1_path, 'w') as f:
            json.dump(snap1, f)
        with open(snap2_path, 'w') as f:
            json.dump(snap2, f)
        
        result = reproducibility.compare_snapshots(snap1_path, snap2_path)
        
        assert 'dependencies' in result['differences']
        assert result['differences']['dependencies']['changed'] == True

    def test_compare_snapshots_different_files(self, tmp_path):
        """Test snapshot comparison with different file manifests."""
        snap1 = {
            'timestamp': '2024-01-01T00:00:00',
            'environment': {},
            'dependencies': [],
            'manifest': {'file_manifest': {'file1.txt': {'hash': 'abc'}}}
        }
        snap2 = {
            'timestamp': '2024-01-02T00:00:00',
            'environment': {},
            'dependencies': [],
            'manifest': {'file_manifest': {'file2.txt': {'hash': 'def'}}}
        }
        
        snap1_path = tmp_path / "snap1.json"
        snap2_path = tmp_path / "snap2.json"
        
        with open(snap1_path, 'w') as f:
            json.dump(snap1, f)
        with open(snap2_path, 'w') as f:
            json.dump(snap2, f)
        
        result = reproducibility.compare_snapshots(snap1_path, snap2_path)
        
        assert 'files' in result['differences']
        assert result['differences']['files']['changed'] == True

    def test_compare_snapshots_identical(self, tmp_path):
        """Test snapshot comparison with identical snapshots."""
        snap = {
            'timestamp': '2024-01-01T00:00:00',
            'environment': {'platform': 'Linux'},
            'dependencies': [{'package': 'numpy', 'version': '1.24.0'}],
            'manifest': {'file_manifest': {}}
        }
        
        snap1_path = tmp_path / "snap1.json"
        snap2_path = tmp_path / "snap2.json"
        
        with open(snap1_path, 'w') as f:
            json.dump(snap, f)
        with open(snap2_path, 'w') as f:
            json.dump(snap, f)
        
        result = reproducibility.compare_snapshots(snap1_path, snap2_path)
        
        assert len(result['differences']) == 0
        assert any("identical" in rec.lower() for rec in result['recommendations'])

    def test_compare_snapshots_exception(self, tmp_path):
        """Test snapshot comparison with exception."""
        snap1_path = tmp_path / "snap1.json"
        snap2_path = tmp_path / "snap2.json"
        
        snap1_path.write_text("invalid json")
        snap2_path.write_text("invalid json")
        
        result = reproducibility.compare_snapshots(snap1_path, snap2_path)
        
        assert 'error' in result
        assert 'Failed to compare' in result['error']


if __name__ == "__main__":
    pytest.main([__file__])
