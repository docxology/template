"""Tests for infrastructure.core.runtime.health_check — comprehensive coverage."""

from pathlib import Path

from infrastructure.core.runtime.health_check import SystemHealthChecker


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
