"""Tests for infrastructure/core/health_check.py.

Tests SystemHealthChecker with real temp directories and actual system calls.
No mocks — uses real psutil, real filesystem, real dependency checks.
"""

from __future__ import annotations

import time
from pathlib import Path

from infrastructure.core.runtime.health_check import SystemHealthChecker


class TestSystemHealthCheckerInit:
    """Test SystemHealthChecker initialization."""

    def test_creates_with_checks_dict(self):
        """Checker initializes with a checks dict."""
        checker = SystemHealthChecker()
        assert isinstance(checker.checks, dict)
        assert len(checker.checks) > 0

    def test_has_expected_check_keys(self):
        """Checker has the expected check keys."""
        checker = SystemHealthChecker()
        expected = {"filesystem", "memory", "cpu", "disk", "network", "dependencies", "uptime"}
        assert expected.issubset(checker.checks.keys())

    def test_start_time_is_recent(self):
        """start_time is set to current time on creation."""
        before = time.time()
        checker = SystemHealthChecker()
        after = time.time()
        assert before <= checker.start_time <= after


class TestGetHealthStatus:
    """Test get_health_status() returns well-formed status dict."""

    def setup_method(self):
        self.checker = SystemHealthChecker()

    def test_returns_dict(self):
        """get_health_status returns a dict."""
        status = self.checker.get_health_status()
        assert isinstance(status, dict)

    def test_has_required_top_level_keys(self):
        """Status dict has timestamp, overall_status, checks, summary."""
        status = self.checker.get_health_status()
        assert "timestamp" in status
        assert "overall_status" in status
        assert "checks" in status
        assert "summary" in status

    def test_overall_status_is_string(self):
        """overall_status is a string."""
        status = self.checker.get_health_status()
        assert isinstance(status["overall_status"], str)

    def test_overall_status_valid_values(self):
        """overall_status is one of the expected values."""
        status = self.checker.get_health_status()
        assert status["overall_status"] in {"healthy", "degraded", "unhealthy"}

    def test_checks_is_dict(self):
        """checks sub-dict is a dict."""
        status = self.checker.get_health_status()
        assert isinstance(status["checks"], dict)

    def test_each_check_has_status_key(self):
        """Each check result has a 'status' key."""
        status = self.checker.get_health_status()
        for check_name, check_result in status["checks"].items():
            assert "status" in check_result, f"Check {check_name!r} missing 'status'"

    def test_each_check_status_is_valid(self):
        """Each check status is 'healthy' or 'unhealthy'."""
        status = self.checker.get_health_status()
        for check_name, check_result in status["checks"].items():
            assert check_result["status"] in {"healthy", "unhealthy"}, (
                f"Check {check_name!r} has unexpected status: {check_result['status']!r}"
            )

    def test_timestamp_is_numeric(self):
        """timestamp is a float/int."""
        status = self.checker.get_health_status()
        assert isinstance(status["timestamp"], (int, float))
        assert status["timestamp"] > 0

    def test_healthy_checks_have_details(self):
        """Healthy checks include a 'details' key."""
        status = self.checker.get_health_status()
        for check_name, check_result in status["checks"].items():
            if check_result["status"] == "healthy":
                assert "details" in check_result, (
                    f"Healthy check {check_name!r} missing 'details'"
                )

    def test_unhealthy_checks_have_error(self):
        """Unhealthy checks include an 'error' key."""
        status = self.checker.get_health_status()
        for check_name, check_result in status["checks"].items():
            if check_result["status"] == "unhealthy":
                assert "error" in check_result, (
                    f"Unhealthy check {check_name!r} missing 'error'"
                )

    def test_summary_is_dict(self):
        """summary is a dict."""
        status = self.checker.get_health_status()
        assert isinstance(status["summary"], dict)

    def test_multiple_calls_produce_fresh_timestamps(self):
        """Each call to get_health_status produces a new timestamp."""
        status1 = self.checker.get_health_status()
        time.sleep(0.01)
        status2 = self.checker.get_health_status()
        assert status2["timestamp"] >= status1["timestamp"]


class TestSystemHealthChecker:
    def test_init_defaults(self):
        checker = SystemHealthChecker()
        assert checker.repo_root == Path.cwd()
        assert checker._network_dns_host == "google.com"
        assert checker._network_tcp_host == "1.1.1.1"

    def test_init_custom(self, tmp_path):
        checker = SystemHealthChecker(
            repo_root=tmp_path,
            start_time=100.0,
            network_test_hosts=("example.com", "8.8.8.8"),
        )
        assert checker.repo_root == tmp_path
        assert checker.start_time == 100.0
        assert checker._network_dns_host == "example.com"
        assert checker._network_tcp_host == "8.8.8.8"

    def test_get_health_status(self, tmp_path):
        checker = SystemHealthChecker(repo_root=tmp_path)
        status = checker.get_health_status()
        assert "timestamp" in status
        assert "overall_status" in status
        assert "checks" in status
        assert "summary" in status

    def test_check_filesystem(self, tmp_path):
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects").mkdir()
        checker = SystemHealthChecker(repo_root=tmp_path)
        result = checker._check_filesystem()
        assert "write_permissions" in result
        assert result["write_permissions"] is True
        assert "directories" in result

    def test_check_filesystem_with_projects(self, tmp_path):
        (tmp_path / "infrastructure").mkdir()
        proj_dir = tmp_path / "projects" / "myproj"
        (proj_dir / "src").mkdir(parents=True)
        (proj_dir / "output").mkdir(parents=True)
        checker = SystemHealthChecker(repo_root=tmp_path)
        result = checker._check_filesystem()
        dirs = result["directories"]
        assert any("myproj" in k for k in dirs)

    def test_check_memory(self):
        checker = SystemHealthChecker()
        result = checker._check_memory()
        # psutil may or may not be available
        if "psutil_unavailable" not in result:
            assert "total_mb" in result
            assert "available_mb" in result
            assert "percent_used" in result

    def test_check_cpu(self):
        checker = SystemHealthChecker()
        result = checker._check_cpu()
        if "psutil_unavailable" not in result:
            assert "cpu_count" in result

    def test_check_disk(self):
        checker = SystemHealthChecker()
        result = checker._check_disk()
        if "psutil_unavailable" not in result:
            assert "total_gb" in result
            assert "free_gb" in result

    def test_check_network(self):
        checker = SystemHealthChecker()
        result = checker._check_network()
        assert "dns_resolution" in result
        assert "http_connectivity" in result

    def test_check_dependencies(self):
        checker = SystemHealthChecker()
        result = checker._check_dependencies()
        # numpy should be available in this environment
        assert "numpy" in result
        assert "optional" in result

    def test_check_uptime(self):
        checker = SystemHealthChecker(start_time=100.0)
        result = checker._check_uptime()
        assert "process_uptime_seconds" in result
        assert result["process_uptime_seconds"] > 0

    def test_is_healthy(self, tmp_path):
        checker = SystemHealthChecker(repo_root=tmp_path)
        result = checker.is_healthy()
        assert isinstance(result, bool)

    def test_get_metrics(self, tmp_path):
        checker = SystemHealthChecker(repo_root=tmp_path)
        metrics = checker.get_metrics()
        assert "health_status" in metrics
        assert "timestamp" in metrics
        assert metrics["health_status"] in (0, 1)

    def test_generate_summary(self):
        checker = SystemHealthChecker()
        status = {
            "checks": {
                "fs": {"status": "healthy", "details": {}},
                "mem": {"status": "unhealthy", "error": "low memory"},
            }
        }
        summary = checker._generate_summary(status)
        assert summary["total_checks"] == 2
        assert summary["healthy_checks"] == 1
        assert summary["unhealthy_checks"] == 1

    def test_generate_summary_with_warnings(self):
        checker = SystemHealthChecker()
        status = {
            "checks": {
                "memory": {"status": "healthy", "details": {"is_critical": True}},
                "disk": {"status": "healthy", "details": {"is_critical": True}},
            }
        }
        summary = checker._generate_summary(status)
        assert "warnings" in summary
        assert len(summary["warnings"]) == 2
