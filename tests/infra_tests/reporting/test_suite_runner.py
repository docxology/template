"""Tests for infrastructure/reporting/suite_runner.py.

Tests test suite runner infrastructure using real instantiation.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

from infrastructure.reporting.suite_runner import TestSuiteConfig


class TestTestSuiteConfig:
    """Test TestSuiteConfig dataclass."""

    def test_construction_with_required_fields(self, tmp_path):
        """Test TestSuiteConfig can be constructed with required fields."""
        config = TestSuiteConfig(
            label="infra",
            cmd=["uv", "run", "pytest", "tests/"],
            env={"PYTHONPATH": str(tmp_path)},
            repo_root=tmp_path,
            coverage_json_paths=[tmp_path / "coverage.json"],
            coverage_threshold=60.0,
            max_failures_env_var="MAX_FAILURES",
            max_failures_config_key="max_failures",
        )
        assert config.label == "infra"
        assert config.coverage_threshold == 60.0
        assert config.quiet is True  # default

    def test_spinner_label_auto_populated(self, tmp_path):
        """Test that spinner_label is auto-populated when empty."""
        config = TestSuiteConfig(
            label="Project",
            cmd=["pytest"],
            env={},
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=90.0,
            max_failures_env_var="MAX",
            max_failures_config_key="max",
        )
        assert config.spinner_label == "Running project tests"

    def test_custom_spinner_label(self, tmp_path):
        """Test that custom spinner_label is preserved."""
        config = TestSuiteConfig(
            label="infra",
            cmd=["pytest"],
            env={},
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=60.0,
            max_failures_env_var="MAX",
            max_failures_config_key="max",
            spinner_label="Custom spinner label",
        )
        assert config.spinner_label == "Custom spinner label"

    def test_repo_root_is_path(self, tmp_path):
        """Test that repo_root is stored as a Path."""
        config = TestSuiteConfig(
            label="test",
            cmd=["pytest"],
            env={},
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=80.0,
            max_failures_env_var="MAX",
            max_failures_config_key="max",
        )
        assert isinstance(config.repo_root, Path)
