"""Tests for infrastructure/core/health_check.py.

Tests SystemHealthChecker with real temp directories and actual system calls.
No mocks — uses real psutil, real filesystem, real dependency checks.
"""

from __future__ import annotations

import time

from infrastructure.core.health_check import SystemHealthChecker


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
