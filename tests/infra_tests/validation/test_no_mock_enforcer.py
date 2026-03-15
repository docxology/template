"""Tests for infrastructure/validation/no_mock_enforcer.py.

Tests the no-mock validation utility using real files.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

from infrastructure.validation.no_mock_enforcer import validate_no_mocks


class TestValidateNoMocks:
    """Test validate_no_mocks function."""

    def test_clean_test_file_has_no_violations(self, tmp_path):
        """Test that a clean test file returns no violations."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_clean.py").write_text(
            "def test_something():\n    result = 1 + 1\n    assert result == 2\n"
        )

        violations = validate_no_mocks(tests_dir, tmp_path)
        assert violations == []

    def test_file_with_mock_import_flagged(self, tmp_path):
        """Test that a file importing unittest.mock is flagged."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_bad.py").write_text(
            "from unittest.mock import MagicMock\n\ndef test_something():\n    m = MagicMock()\n"
        )

        violations = validate_no_mocks(tests_dir, tmp_path)
        assert len(violations) > 0
        assert any("test_bad.py" in v for v in violations)

    def test_magic_mock_usage_flagged(self, tmp_path):
        """Test that MagicMock( usage is flagged."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_bad.py").write_text(
            "import something\n\ndef test_something():\n    m = MagicMock()\n    assert True\n"
        )

        violations = validate_no_mocks(tests_dir, tmp_path)
        assert len(violations) > 0

    def test_empty_tests_dir_has_no_violations(self, tmp_path):
        """Test that an empty tests directory returns no violations."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        violations = validate_no_mocks(tests_dir, tmp_path)
        assert violations == []

    def test_returns_list(self, tmp_path):
        """Test that validate_no_mocks always returns a list."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        result = validate_no_mocks(tests_dir, tmp_path)
        assert isinstance(result, list)
