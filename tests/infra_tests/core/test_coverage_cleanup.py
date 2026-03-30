"""Tests for infrastructure/core/coverage_cleanup.py.

Tests coverage file cleanup utilities using real files.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.core.files.coverage_cleanup import clean_coverage_files


class TestCleanCoverageFiles:
    """Test clean_coverage_files function."""

    def test_returns_true_on_empty_dir(self, tmp_path):
        """Test that clean_coverage_files returns True when no files to clean."""
        result = clean_coverage_files(tmp_path)
        assert result is True

    def test_removes_coverage_file(self, tmp_path):
        """Test that .coverage file is removed."""
        coverage_file = tmp_path / ".coverage"
        coverage_file.write_text("coverage data")

        result = clean_coverage_files(tmp_path)

        assert result is True
        assert not coverage_file.exists()

    def test_removes_coverage_json_file(self, tmp_path):
        """Test that coverage_*.json files are removed."""
        json_file = tmp_path / "coverage_results.json"
        json_file.write_text("{}")

        result = clean_coverage_files(tmp_path)

        assert result is True
        assert not json_file.exists()

    def test_custom_patterns(self, tmp_path):
        """Test that custom patterns are respected."""
        keep_file = tmp_path / ".coverage"
        keep_file.write_text("coverage data")
        remove_file = tmp_path / "remove_me.txt"
        remove_file.write_text("to remove")

        result = clean_coverage_files(tmp_path, patterns=["remove_me.txt"])

        assert result is True
        assert keep_file.exists()  # Not in custom patterns
        assert not remove_file.exists()

    def test_returns_bool(self, tmp_path):
        """Test that the function always returns a boolean."""
        result = clean_coverage_files(tmp_path)
        assert isinstance(result, bool)
