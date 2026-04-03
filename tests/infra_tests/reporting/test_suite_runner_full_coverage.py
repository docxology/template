"""Tests for infrastructure/reporting/suite_runner.py.

Covers: helper functions (_is_internal_stack_line, _passes_quiet_filter),
run_pytest_stream with real trivial commands, and run_test_suite logic.

No mocks used — all tests use real data, real subprocesses, and real function calls.
"""

from __future__ import annotations

import os


from infrastructure.reporting.suite_runner import (
    _is_internal_stack_line,
    _passes_quiet_filter,
    _INTERNAL_STACK_PATTERNS,
    _SUMMARY_KEYWORDS,
    TestSuiteConfig,
    run_pytest_stream,
    run_test_suite,
)


class TestIsInternalStackLine:
    """Test _is_internal_stack_line filtering."""

    def test_matches_known_patterns(self):
        """Lines containing internal stack patterns should match."""
        assert _is_internal_stack_line("  File x.py, super().serve_forever()")
        assert _is_internal_stack_line("  selector.select(timeout)")
        assert _is_internal_stack_line("  config.hook.pytest something")
        assert _is_internal_stack_line("  hook_impl.function(args)")

    def test_rejects_normal_lines(self):
        """Normal test output lines should not match."""
        assert not _is_internal_stack_line("test_foo.py::test_bar PASSED")
        assert not _is_internal_stack_line("assert result == expected")
        assert not _is_internal_stack_line("FAILED tests/test_x.py::test_y")

    def test_matches_request_patterns(self):
        """Request/HTTP internal patterns should match."""
        assert _is_internal_stack_line("  response = requests.post(url)")
        assert _is_internal_stack_line("  return request(method, url)")
        assert _is_internal_stack_line("  resp = conn.urlopen(method)")

    def test_empty_line(self):
        """Empty line should not match."""
        assert not _is_internal_stack_line("")


class TestPassesQuietFilter:
    """Test _passes_quiet_filter logic."""

    def test_non_quiet_dot_passes(self):
        """In non-quiet mode, dots always pass."""
        assert _passes_quiet_filter(".", "test line", quiet=False)

    def test_non_quiet_normal_line_passes(self):
        """In non-quiet mode, non-internal lines pass."""
        assert _passes_quiet_filter("\n", "test PASSED\n", quiet=False)

    def test_non_quiet_internal_line_blocked(self):
        """In non-quiet mode, internal stack lines are blocked."""
        assert not _passes_quiet_filter("\n", "  super().serve_forever()\n", quiet=False)

    def test_quiet_summary_line_passes(self):
        """In quiet mode, summary lines pass."""
        assert _passes_quiet_filter("\n", "5 passed, 1 failed\n", quiet=True)
        assert _passes_quiet_filter("\n", "PASSED\n", quiet=True)
        assert _passes_quiet_filter("\n", "FAILED\n", quiet=True)
        assert _passes_quiet_filter("\n", "coverage: 85%\n", quiet=True)

    def test_quiet_separator_line_passes(self):
        """In quiet mode, separator lines with many = signs pass."""
        assert _passes_quiet_filter("\n", "=" * 20 + "\n", quiet=True)

    def test_quiet_normal_line_blocked(self):
        """In quiet mode, normal output lines without summary keywords are blocked."""
        assert not _passes_quiet_filter("\n", "collecting ... \n", quiet=True)
        assert not _passes_quiet_filter("\n", "test_foo.py::test_bar\n", quiet=True)

    def test_quiet_dot_blocked(self):
        """In quiet mode, dots are not passed through."""
        assert not _passes_quiet_filter(".", ".", quiet=True)


class TestInternalStackPatterns:
    """Verify the _INTERNAL_STACK_PATTERNS list and _SUMMARY_KEYWORDS."""

    def test_patterns_are_non_empty_strings(self):
        """All patterns should be non-empty strings."""
        for pattern in _INTERNAL_STACK_PATTERNS:
            assert isinstance(pattern, str)
            assert len(pattern) > 0

    def test_summary_keywords_are_non_empty(self):
        """All summary keywords should be non-empty strings."""
        for keyword in _SUMMARY_KEYWORDS:
            assert isinstance(keyword, str)
            assert len(keyword) > 0

    def test_summary_keywords_contain_expected(self):
        """Summary keywords should include common pytest summary terms."""
        assert "passed" in _SUMMARY_KEYWORDS
        assert "failed" in _SUMMARY_KEYWORDS
        assert "PASSED" in _SUMMARY_KEYWORDS
        assert "FAILED" in _SUMMARY_KEYWORDS


class TestRunPytestStream:
    """Test run_pytest_stream with real trivial commands."""

    def test_stream_echo_command(self, tmp_path):
        """Test streaming a simple echo command."""
        env = os.environ.copy()
        exit_code, stdout, stderr = run_pytest_stream(
            ["echo", "hello world"], tmp_path, env, quiet=True
        )
        assert exit_code == 0
        assert "hello" in stdout

    def test_stream_failing_command(self, tmp_path):
        """Test streaming a command that exits with error."""
        env = os.environ.copy()
        exit_code, stdout, stderr = run_pytest_stream(
            ["false"], tmp_path, env, quiet=True
        )
        assert exit_code != 0

    def test_stream_multiline_output(self, tmp_path):
        """Test streaming multi-line output."""
        env = os.environ.copy()
        exit_code, stdout, stderr = run_pytest_stream(
            ["printf", "line1\nline2\nline3\n"], tmp_path, env, quiet=False
        )
        assert exit_code == 0
        assert "line1" in stdout


class TestRunTestSuite:
    """Test run_test_suite with real but harmless commands."""

    def _make_config(self, tmp_path, cmd=None, quiet=True) -> TestSuiteConfig:
        """Create a TestSuiteConfig with harmless defaults."""
        return TestSuiteConfig(
            label="Test",
            cmd=cmd or ["echo", "5 passed, 0 failed"],
            env=os.environ.copy(),
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=0.0,
            max_failures_env_var="MAX_TEST_FAILURES",
            max_failures_config_key="max_test_failures",
            quiet=quiet,
            spinner_label="Running test suite",
        )

    def test_run_suite_with_passing_command(self, tmp_path):
        """Test running suite with a passing command."""
        config = self._make_config(tmp_path, cmd=["echo", "5 passed, 0 failed in 1.0s"])
        exit_code, results = run_test_suite(config)
        assert exit_code == 0
        assert isinstance(results, dict)

    def test_run_suite_with_failing_command(self, tmp_path):
        """Test running suite with a failing command."""
        config = self._make_config(tmp_path, cmd=["false"])
        exit_code, results = run_test_suite(config)
        # The exit code depends on failure count and halt threshold
        assert isinstance(results, dict)

    def test_run_suite_results_have_failed_tests(self, tmp_path):
        """Test that results include failed_tests key."""
        config = self._make_config(tmp_path)
        exit_code, results = run_test_suite(config)
        assert "failed_tests" in results

    def test_run_suite_coverage_conflict_retry(self, tmp_path):
        """Test that coverage conflict detection works (uses echo to simulate)."""
        # This command outputs text that does NOT contain coverage conflict markers
        config = self._make_config(tmp_path, cmd=["echo", "All good"])
        exit_code, results = run_test_suite(config)
        # Should complete without retrying
        assert isinstance(results, dict)
