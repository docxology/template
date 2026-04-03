"""Tests for infrastructure.reporting.suite_runner — testable helper functions."""

from infrastructure.reporting.suite_runner import (
    _is_internal_stack_line,
    _passes_quiet_filter,
    TestSuiteConfig,
)
from pathlib import Path


class TestIsInternalStackLine:
    def test_matches_super_serve_forever(self):
        assert _is_internal_stack_line("    super().serve_forever()") is True

    def test_matches_selector_select(self):
        assert _is_internal_stack_line("    selector.select(timeout)") is True

    def test_matches_config_hook(self):
        assert _is_internal_stack_line("    config.hook.pytest") is True

    def test_matches_requests_post(self):
        assert _is_internal_stack_line("    response = requests.post(url)") is True

    def test_no_match(self):
        assert _is_internal_stack_line("    assert result == expected") is False

    def test_empty_string(self):
        assert _is_internal_stack_line("") is False

    def test_matches_hook_impl(self):
        assert _is_internal_stack_line("    hook_impl.function(args)") is True


class TestPassesQuietFilter:
    def test_dot_in_normal_mode(self):
        assert _passes_quiet_filter(".", "some line", quiet=False) is True

    def test_normal_line_not_internal(self):
        assert _passes_quiet_filter("\n", "PASSED in 5s\n", quiet=False) is True

    def test_internal_line_filtered(self):
        assert _passes_quiet_filter("\n", "super().serve_forever()\n", quiet=False) is False

    def test_quiet_summary_line_passes(self):
        assert _passes_quiet_filter("\n", "5 passed, 1 failed\n", quiet=True) is True

    def test_quiet_separator_passes(self):
        assert _passes_quiet_filter("\n", "=" * 20, quiet=True) is True

    def test_quiet_normal_line_filtered(self):
        assert _passes_quiet_filter("\n", "collecting tests\n", quiet=True) is False

    def test_quiet_dot_filtered(self):
        assert _passes_quiet_filter(".", ".", quiet=True) is False

    def test_quiet_coverage_line_passes(self):
        assert _passes_quiet_filter("\n", "TOTAL coverage 80%\n", quiet=True) is True


class TestTestSuiteConfig:
    def test_default_spinner_label(self):
        config = TestSuiteConfig(
            label="Infrastructure",
            cmd=["pytest", "tests/"],
            env={},
            repo_root=Path("/tmp"),
            coverage_json_paths=[],
            coverage_threshold=60.0,
            max_failures_env_var="MAX_INFRA_FAILURES",
            max_failures_config_key="max_infra_failures",
        )
        assert config.spinner_label == "Running infrastructure tests"

    def test_custom_spinner_label(self):
        config = TestSuiteConfig(
            label="Project",
            cmd=["pytest"],
            env={},
            repo_root=Path("/tmp"),
            coverage_json_paths=[],
            coverage_threshold=90.0,
            max_failures_env_var="MAX_PROJ_FAILURES",
            max_failures_config_key="max_proj_failures",
            spinner_label="Custom label",
        )
        assert config.spinner_label == "Custom label"

    def test_quiet_default(self):
        config = TestSuiteConfig(
            label="Test",
            cmd=[],
            env={},
            repo_root=Path("/tmp"),
            coverage_json_paths=[],
            coverage_threshold=0,
            max_failures_env_var="",
            max_failures_config_key="",
        )
        assert config.quiet is True
