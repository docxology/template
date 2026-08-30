"""Tests for infrastructure/reporting/suite_runner.py.

Covers: helper functions (_is_internal_stack_line, _passes_quiet_filter),
run_pytest_stream with real trivial commands, and run_test_suite logic.

No mocks used — all tests use real data, real subprocesses, and real function calls.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.reporting.suite_runner import (
    _INTERNAL_STACK_PATTERNS,
    _SUMMARY_KEYWORDS,
    DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
    DEFAULT_TEST_SUITE_TIMEOUT_SECONDS,
    TestSuiteConfig as SuiteConfig,
    _is_internal_stack_line,
    _passes_quiet_filter,
    _remaining_attempt_timeout_seconds,
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

    def test_quiet_coverage_line_passes(self):
        """In quiet mode, coverage summary lines pass."""
        assert _passes_quiet_filter("\n", "TOTAL coverage 80%\n", quiet=True)


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
        exit_code, stdout, stderr = run_pytest_stream(["echo", "hello world"], tmp_path, env, quiet=True)
        assert exit_code == 0
        assert "hello" in stdout

    def test_stream_failing_command(self, tmp_path):
        """Test streaming a command that exits with error."""
        env = os.environ.copy()
        exit_code, stdout, stderr = run_pytest_stream(["false"], tmp_path, env, quiet=True)
        assert exit_code != 0

    def test_stream_multiline_output(self, tmp_path):
        """Test streaming multi-line output."""
        env = os.environ.copy()
        exit_code, stdout, stderr = run_pytest_stream(["printf", "line1\nline2\nline3\n"], tmp_path, env, quiet=False)
        assert exit_code == 0
        assert "line1" in stdout

    def test_stream_timeout_kills_descendants(self, tmp_path):
        """A quiet parent/child hang must return within the declared deadline."""
        marker = tmp_path / "child-finished"
        child_code = "import time; time.sleep(5); open(%r, 'w').write('late')" % str(marker)
        parent_code = (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]]); "
            "time.sleep(5)"
        )
        started = time.monotonic()
        exit_code, _stdout, stderr = run_pytest_stream(
            [sys.executable, "-c", parent_code, child_code, str(marker)],
            tmp_path,
            os.environ.copy(),
            quiet=True,
            timeout_seconds=0.2,
        )
        elapsed = time.monotonic() - started
        assert exit_code == 124
        assert "timed out" in stderr
        # Cleanup includes the bounded-run guardian handshake plus repeated
        # process-table scans (~1s idle, multi-second on a loaded host). Assert
        # the kill landed well before the workload's natural 5s exit rather
        # than pinning an absolute wall clock that flakes under load.
        assert elapsed < 5.0
        time.sleep(0.1)
        assert not marker.exists()

    @pytest.mark.skipif(os.name == "nt", reason="detached POSIX session regression")
    def test_stream_timeout_kills_descendants_that_start_new_sessions(self, tmp_path):
        """A nested bounded runner cannot outlive the outer output lock."""
        marker = tmp_path / "detached-child-finished"
        pid_file = tmp_path / "detached-child.pid"
        child_code = (
            "import pathlib,time; "
            "time.sleep(3.0); "
            f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
        )
        parent_code = (
            "import pathlib,subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable, '-c', sys.argv[1]], start_new_session=True); "
            "pathlib.Path(sys.argv[2]).write_text(str(child.pid), encoding='utf-8'); "
            "time.sleep(30)"
        )
        child_pid: int | None = None
        try:
            exit_code, _stdout, stderr = run_pytest_stream(
                [sys.executable, "-c", parent_code, child_code, str(pid_file)],
                tmp_path,
                os.environ.copy(),
                quiet=True,
                timeout_seconds=1.5,
            )
            assert exit_code == 124
            assert "timed out" in stderr
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            time.sleep(1.8)
            assert not marker.exists()
        finally:
            if child_pid is not None:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(child_pid, signal.SIGKILL)

    @pytest.mark.skipif(os.name == "nt", reason="detached POSIX session regression")
    def test_stream_success_cleans_reparented_detached_child(self, tmp_path):
        """An early successful root exit cannot release a live child writer."""
        marker = tmp_path / "reparented-child-finished"
        child_code = (
            "import pathlib,time; "
            "time.sleep(1.5); "
            f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
        )
        parent_code = (
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable, '-c', sys.argv[1]], "
            "start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"
        )

        exit_code, _stdout, _stderr = run_pytest_stream(
            [sys.executable, "-c", parent_code, child_code],
            tmp_path,
            os.environ.copy(),
            quiet=True,
            timeout_seconds=0.3,
        )

        assert exit_code == 0
        time.sleep(1.6)
        assert not marker.exists()

    @pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
    def test_stream_guardian_cleans_while_calling_process_is_stopped(self, tmp_path):
        """Streaming cleanup proceeds while its orchestration process is stalled."""
        marker = tmp_path / "stalled-stream-child-finished"
        root_ready = tmp_path / "stream-root-ready"
        child_code = (
            "import pathlib,time; "
            "time.sleep(1.0); "
            f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
        )
        root_code = (
            "import pathlib,subprocess,sys,time; "
            "subprocess.Popen([sys.executable, '-c', sys.argv[1]], "
            "start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            "pathlib.Path(sys.argv[2]).write_text('ready', encoding='utf-8'); "
            "time.sleep(0.25)"
        )
        helper_code = (
            "import os,pathlib,sys; "
            "from infrastructure.reporting.suite_runner import run_pytest_stream; "
            "cwd=pathlib.Path(sys.argv[1]); "
            "code,_,_=run_pytest_stream([sys.executable, '-c', sys.argv[2], sys.argv[3], sys.argv[4]], "
            "cwd, os.environ.copy(), quiet=True, timeout_seconds=10); "
            "raise SystemExit(0 if code == 0 else 71)"
        )
        repo_root = Path(__file__).resolve().parents[3]
        helper = subprocess.Popen(
            [
                sys.executable,
                "-c",
                helper_code,
                str(tmp_path),
                root_code,
                child_code,
                str(root_ready),
            ],
            cwd=repo_root,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        stopped = False
        try:
            deadline = time.monotonic() + 10
            while not root_ready.is_file():
                if helper.poll() is not None:
                    pytest.fail(f"stream helper exited before its root was ready: {helper.returncode}")
                if time.monotonic() >= deadline:
                    pytest.fail("timed out waiting for streaming root readiness")
                time.sleep(0.01)

            os.kill(helper.pid, signal.SIGSTOP)
            stopped = True
            time.sleep(1.3)
            assert not marker.exists()
        finally:
            if stopped:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(helper.pid, signal.SIGCONT)
            try:
                helper.wait(timeout=10)
            except subprocess.TimeoutExpired:
                helper.kill()
                helper.wait(timeout=5)
        assert helper.returncode == 0
        assert not marker.exists()


class TestSuiteConfigModel:
    """TestSuiteConfig defaults and overrides."""

    def test_construction_with_required_fields(self, tmp_path):
        """Test TestSuiteConfig can be constructed with required fields."""
        config = SuiteConfig(
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
        assert config.quiet is True
        assert config.timeout_seconds == DEFAULT_TEST_SUITE_TIMEOUT_SECONDS == 1800.0
        assert config.total_timeout_seconds is None
        assert config.coverage_cleanup_scope_dir is None
        assert config.coverage_cleanup_recursive is True

    def test_rejects_nonpositive_opt_in_total_timeout(self, tmp_path):
        with pytest.raises(ValueError, match="total_timeout_seconds must be positive"):
            SuiteConfig(
                label="Project",
                cmd=["pytest"],
                env={},
                repo_root=tmp_path,
                coverage_json_paths=[],
                coverage_threshold=90.0,
                max_failures_env_var="MAX",
                max_failures_config_key="max",
                total_timeout_seconds=0.0,
            )

    def test_default_spinner_label(self):
        config = SuiteConfig(
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

    def test_spinner_label_auto_populated(self, tmp_path):
        """Test that spinner_label is auto-populated when empty."""
        config = SuiteConfig(
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
        config = SuiteConfig(
            label="Project",
            cmd=["pytest"],
            env={},
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=90.0,
            max_failures_env_var="MAX_PROJ_FAILURES",
            max_failures_config_key="max_proj_failures",
            spinner_label="Custom label",
        )
        assert config.spinner_label == "Custom label"

    def test_quiet_default(self):
        config = SuiteConfig(
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

    def test_repo_root_is_path(self, tmp_path):
        """Test that repo_root is stored as a Path."""
        config = SuiteConfig(
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


class TestRunTestSuite:
    """Test run_test_suite with real but harmless commands."""

    def _make_config(self, tmp_path, cmd=None, quiet=True) -> SuiteConfig:
        """Create a TestSuiteConfig with harmless defaults."""
        return SuiteConfig(
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

    def test_passing_suite_clears_timeout_parser_false_positives(self, tmp_path):
        """A green run cannot persist diagnostic timeout text as failures."""
        config = self._make_config(
            tmp_path,
            cmd=["bash", "-c", "printf 'tests/test_ok.py::test_ok PASSED\\npytest_timeout: configured\\n1 passed\\n'"],
        )
        exit_code, results = run_test_suite(config)
        assert exit_code == 0
        assert results["failed"] == 0
        assert results["failed_tests"] == []

    def test_run_suite_with_failing_command(self, tmp_path):
        """Test running suite with a failing command."""
        config = self._make_config(tmp_path, cmd=["false"])
        exit_code, results = run_test_suite(config)
        assert isinstance(results, dict)

    def test_nonpositive_per_attempt_timeout_keeps_fail_fast_semantics(self, tmp_path):
        """The opt-in total budget does not reinterpret an invalid attempt budget."""
        config = self._make_config(tmp_path)
        config.timeout_seconds = 0.0
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            run_test_suite(config)

    def test_run_suite_results_have_failed_tests(self, tmp_path):
        """Test that results include failed_tests key."""
        config = self._make_config(tmp_path)
        exit_code, results = run_test_suite(config)
        assert "failed_tests" in results

    def test_run_suite_coverage_conflict_retry(self, tmp_path):
        """Test that coverage conflict detection works (uses echo to simulate)."""
        config = self._make_config(tmp_path, cmd=["echo", "All good"])
        exit_code, results = run_test_suite(config)
        assert isinstance(results, dict)

    def _run_real_coverage_conflict_retry(self, tmp_path, config):
        attempts_path = tmp_path / "cleanup-attempts.txt"
        retry_probe = tmp_path / "cleanup_retry_probe.py"
        retry_probe.write_text(
            "import pathlib\n"
            f"attempts = pathlib.Path({str(attempts_path)!r})\n"
            "count = int(attempts.read_text(encoding='utf-8')) + 1 if attempts.exists() else 1\n"
            "attempts.write_text(str(count), encoding='utf-8')\n"
            "if count == 1:\n"
            "    print('coverage.exceptions.DataError: retry required', flush=True)\n"
            "    raise SystemExit(1)\n"
            "print('1 passed in 0.01s', flush=True)\n",
            encoding="utf-8",
        )
        config.cmd = [sys.executable, str(retry_probe)]

        exit_code, results = run_test_suite(config)

        assert attempts_path.read_text(encoding="utf-8") == "2"
        assert exit_code == results["exit_code"] == 0

    def test_project_scoped_retry_cleanup_preserves_sibling_coverage(self, tmp_path):
        """A real generic-project retry removes only the selected project's data."""
        selected_root = tmp_path / "projects" / "selected"
        sibling_root = tmp_path / "projects" / "sibling"
        selected_root.mkdir(parents=True)
        sibling_root.mkdir(parents=True)
        selected_coverage = selected_root / ".coverage.project"
        sibling_coverage = sibling_root / ".coverage.project"
        selected_coverage.write_text("selected", encoding="utf-8")
        sibling_coverage.write_text("sibling", encoding="utf-8")
        config = self._make_config(tmp_path)
        config.coverage_cleanup_scope_dir = selected_root
        config.coverage_cleanup_recursive = True

        self._run_real_coverage_conflict_retry(tmp_path, config)

        assert not selected_coverage.exists()
        assert sibling_coverage.read_text(encoding="utf-8") == "sibling"

    def test_nonrecursive_retry_cleanup_preserves_nested_project_coverage(self, tmp_path):
        """A real infrastructure retry removes root data but not project data."""
        project_root = tmp_path / "projects" / "selected"
        project_root.mkdir(parents=True)
        infrastructure_coverage = tmp_path / ".coverage.infra"
        project_coverage = project_root / ".coverage.project"
        infrastructure_coverage.write_text("infrastructure", encoding="utf-8")
        project_coverage.write_text("project", encoding="utf-8")
        config = self._make_config(tmp_path)
        config.coverage_cleanup_scope_dir = None
        config.coverage_cleanup_recursive = False

        self._run_real_coverage_conflict_retry(tmp_path, config)

        assert not infrastructure_coverage.exists()
        assert project_coverage.read_text(encoding="utf-8") == "project"

    def test_attempt_budget_is_bounded_by_remaining_total(self):
        """The source-owned deadline calculation preserves and bounds both modes."""
        assert _remaining_attempt_timeout_seconds(12.0, None, now_seconds=100.0) == 12.0
        assert _remaining_attempt_timeout_seconds(12.0, 110.0, now_seconds=103.5) == 6.5
        assert _remaining_attempt_timeout_seconds(12.0, 110.0, now_seconds=110.0) == 0.0
        assert _remaining_attempt_timeout_seconds(12.0, 110.0, now_seconds=111.0) == 0.0

    @pytest.mark.timeout(20)
    def test_total_budget_bounds_coverage_retry_and_cleans_descendant(self, tmp_path):
        """A real retry receives only remaining time and kills its detached child."""
        attempts_path = tmp_path / "attempts.txt"
        second_started_path = tmp_path / "second-started.txt"
        descendant_marker_path = tmp_path / "descendant-finished.txt"
        descendant = tmp_path / "descendant.py"
        descendant.write_text(
            "import pathlib, sys, time\n"
            "time.sleep(4.0)\n"
            "pathlib.Path(sys.argv[1]).write_text('survived', encoding='utf-8')\n",
            encoding="utf-8",
        )
        retry_probe = tmp_path / "retry_probe.py"
        retry_probe.write_text(
            "import pathlib, subprocess, sys, time\n"
            f"attempts = pathlib.Path({str(attempts_path)!r})\n"
            "count = int(attempts.read_text(encoding='utf-8')) + 1 if attempts.exists() else 1\n"
            "attempts.write_text(str(count), encoding='utf-8')\n"
            "if count == 1:\n"
            "    time.sleep(1.0)\n"
            "    print('coverage.exceptions.DataError: retry required', flush=True)\n"
            "    raise SystemExit(1)\n"
            f"pathlib.Path({str(second_started_path)!r}).write_text('started', encoding='utf-8')\n"
            f"subprocess.Popen([sys.executable, {str(descendant)!r}, {str(descendant_marker_path)!r}], "
            "start_new_session=True)\n"
            "time.sleep(10.0)\n"
            "print('1 passed in 10.0s', flush=True)\n",
            encoding="utf-8",
        )
        config = SuiteConfig(
            label="Project",
            cmd=[sys.executable, str(retry_probe)],
            env=os.environ.copy(),
            repo_root=tmp_path,
            coverage_json_paths=[],
            coverage_threshold=0.0,
            max_failures_env_var="MAX_PROJECT_TEST_FAILURES",
            max_failures_config_key="max_project_test_failures",
            quiet=True,
            streaming_subprocess=True,
            timeout_seconds=10.0,
            total_timeout_seconds=4.0,
        )

        started_at = time.monotonic()
        exit_code, results = run_test_suite(config)
        elapsed = time.monotonic() - started_at
        time.sleep(1.5)

        assert attempts_path.read_text(encoding="utf-8") == "2"
        assert second_started_path.is_file()
        assert not descendant_marker_path.exists()
        assert exit_code == results["exit_code"] == 124
        assert elapsed < 8.0
        assert config.total_timeout_seconds == 4.0
        assert config.timeout_seconds == 10.0
        assert DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS == 6900.0

    def test_coverage_floor_failure_is_not_green_washed(self, tmp_path):
        """Regression: a non-zero exit with ZERO test failures (the signature of a
        ``--cov-fail-under`` coverage-floor failure: every test passes, pytest still
        exits 1) must NOT be suppressed to 0. Suppressing it green-washes a failed
        coverage gate. Pins suite_runner.run_test_suite against that latent defect."""
        config = self._make_config(
            tmp_path,
            # All tests pass (failed==0) but the process exits non-zero, exactly as
            # pytest does when coverage is below --cov-fail-under.
            cmd=["bash", "-c", "echo '10 passed in 1.0s'; exit 1"],
        )
        exit_code, results = run_test_suite(config)
        assert results.get("failed", 0) == 0
        assert exit_code == 1, "coverage-floor failure (exit 1, 0 failed) was green-washed to 0"

    def test_tolerated_test_failures_are_still_suppressed(self, tmp_path, monkeypatch):
        """Companion control: a non-zero exit WITH test failures that are within the
        configured tolerance is still suppressed to 0 (the legitimate path the fix
        must preserve). Uses a real env var, not a mock."""
        monkeypatch.setenv("MAX_TEST_FAILURES", "5")
        config = self._make_config(
            tmp_path,
            cmd=["bash", "-c", "echo '2 failed, 8 passed in 1.0s'; exit 1"],
        )
        exit_code, results = run_test_suite(config)
        assert results.get("failed", 0) == 2
        assert exit_code == 0, "tolerated test failures (2 <= max 5) should be suppressed"
