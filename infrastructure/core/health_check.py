"""System health monitoring and status checks.

This module provides comprehensive health monitoring for all system components,
including dependencies, filesystem, network, and performance metrics.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from infrastructure.core._optional_deps import psutil
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class SystemHealthChecker:
    """Comprehensive system health monitoring."""

    def __init__(self, repo_root: Path | None = None, start_time: float | None = None) -> None:
        self.start_time = start_time if start_time is not None else time.time()
        self.repo_root = repo_root or Path.cwd()
        self.checks = {
            "filesystem": self._check_filesystem,
            "memory": self._check_memory,
            "cpu": self._check_cpu,
            "disk": self._check_disk,
            "network": self._check_network,
            "dependencies": self._check_dependencies,
            "uptime": self._check_uptime,
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status."""
        status: dict[str, Any] = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "checks": {},
            "summary": {},
        }

        unhealthy_checks = []

        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                status["checks"][check_name] = {
                    "status": "healthy",
                    "details": result,
                    "timestamp": time.time(),
                }
            except Exception as e:  # noqa: BLE001 — intentional: check functions are arbitrary; must not propagate
                logger.warning(f"Health check failed for {check_name}: {e}")
                status["checks"][check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": time.time(),
                }
                unhealthy_checks.append(check_name)

        # Determine overall status
        if unhealthy_checks:
            status["overall_status"] = (
                "degraded" if len(unhealthy_checks) < len(self.checks) else "unhealthy"
            )
            status["summary"]["unhealthy_checks"] = unhealthy_checks

        # Add summary metrics
        status["summary"].update(self._generate_summary(status))

        return status

    def _check_filesystem(self) -> dict[str, Any]:
        import tempfile

        results: dict[str, Any] = {}

        # Check write permissions
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
                f.write("health_check_test")
            results["write_permissions"] = True
        except (OSError, IOError):
            results["write_permissions"] = False

        # Check critical directories (discover project dirs dynamically)
        projects_root = self.repo_root / "projects"
        critical_dirs = [projects_root, self.repo_root / "infrastructure"]
        if projects_root.exists():
            for p in sorted(projects_root.iterdir()):
                if p.is_dir() and not p.name.startswith((".", "_")):
                    critical_dirs.append(p / "src")
                    critical_dirs.append(p / "output")

        results["directories"] = {}
        for dir_path in critical_dirs:
            results["directories"][str(dir_path)] = {
                "exists": dir_path.exists(),
                "readable": dir_path.exists() and dir_path.is_dir(),
                "writable": dir_path.exists() and os.access(dir_path, os.W_OK),
            }

        return results

    def _check_memory(self) -> dict[str, Any]:
        if psutil is None:
            return {"psutil_unavailable": True}
        memory = psutil.virtual_memory()
        return {
            "total_mb": memory.total // (1024 * 1024),
            "available_mb": memory.available // (1024 * 1024),
            "used_mb": memory.used // (1024 * 1024),
            "percent_used": memory.percent,
            "critical_threshold": 95.0,
            "is_critical": memory.percent > 95.0,
        }

    def _check_cpu(self) -> dict[str, Any]:
        if psutil is None:
            return {"psutil_unavailable": True}
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "load_average": (psutil.getloadavg() if hasattr(psutil, "getloadavg") else None),
        }

    def _check_disk(self) -> dict[str, Any]:
        if psutil is None:
            return {"psutil_unavailable": True}
        disk = psutil.disk_usage("/")
        return {
            "total_gb": disk.total // (1024**3),
            "used_gb": disk.used // (1024**3),
            "free_gb": disk.free // (1024**3),
            "percent_used": disk.percent,
            "critical_threshold": 95.0,
            "is_critical": disk.percent > 95.0,
        }

    def _check_network(self) -> dict[str, Any]:
        import socket

        results: dict[str, Any] = {}

        # Test DNS resolution
        try:
            socket.gethostbyname("google.com")
            results["dns_resolution"] = True
        except socket.gaierror:
            results["dns_resolution"] = False

        # Test basic TCP connectivity via socket (no external HTTP dependency)
        try:
            with socket.create_connection(("1.1.1.1", 80), timeout=5):
                results["http_connectivity"] = True
        except OSError:
            results["http_connectivity"] = False

        return results

    def _check_dependencies(self) -> dict[str, Any]:
        critical_deps = [
            "numpy",
            "matplotlib",
            "requests",
            "pyyaml",
            "psutil",  # For monitoring
        ]

        results: dict[str, Any] = {}
        for dep in critical_deps:
            try:
                __import__(dep)
                results[dep] = "available"
            except ImportError:
                results[dep] = "missing"

        # Check optional dependencies
        optional_deps = ["ollama", "scikit-learn", "reportlab"]
        results["optional"] = {}
        for dep in optional_deps:
            try:
                __import__(dep)
                results["optional"][dep] = "available"
            except ImportError:
                results["optional"][dep] = "missing"

        return results

    def _check_uptime(self) -> dict[str, Any]:
        """Return system and process uptime; falls back from /proc/uptime to psutil.boot_time()."""
        uptime_seconds: float | None = None
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
        except (FileNotFoundError, OSError):
            # Fallback for systems without /proc/uptime
            uptime_seconds = (
                time.time() - psutil.boot_time()
                if psutil is not None and hasattr(psutil, "boot_time")
                else None
            )

        process_uptime = time.time() - self.start_time

        return {
            "system_uptime_seconds": uptime_seconds,
            "system_uptime_hours": uptime_seconds / 3600 if uptime_seconds else None,
            "process_uptime_seconds": process_uptime,
            "process_uptime_hours": process_uptime / 3600,
        }

    def is_healthy(self) -> bool:
        """Return True if all health checks pass."""
        return bool(self.get_health_status()["overall_status"] == "healthy")

    def get_metrics(self) -> dict[str, Any]:
        """Return health metrics in a format suitable for monitoring systems."""
        status = self.get_health_status()

        metrics: dict[str, Any] = {
            "health_status": 1 if status["overall_status"] == "healthy" else 0,
            "timestamp": status["timestamp"],
        }

        for check_name, check_data in status["checks"].items():
            metrics[f"{check_name}_status"] = 1 if check_data["status"] == "healthy" else 0

        for check_key, detail_key, metric_key in [
            ("memory", "percent_used", "memory_percent_used"),
            ("cpu", "cpu_percent", "cpu_percent_used"),
            ("disk", "percent_used", "disk_percent_used"),
        ]:
            if check_key in status["checks"]:
                details = status["checks"][check_key].get("details", {})
                if detail_key in details:
                    metrics[metric_key] = details[detail_key]

        return metrics

    def _generate_summary(self, status: dict[str, Any]) -> dict[str, Any]:
        checks = status["checks"]

        summary: dict[str, Any] = {
            "total_checks": len(checks),
            "healthy_checks": sum(1 for c in checks.values() if c["status"] == "healthy"),
            "unhealthy_checks": sum(1 for c in checks.values() if c["status"] == "unhealthy"),
        }

        # Add critical resource warnings
        warnings: list[str] = []

        if "memory" in checks and checks["memory"].get("details", {}).get("is_critical"):
            warnings.append("High memory usage detected")

        if "disk" in checks and checks["disk"].get("details", {}).get("is_critical"):
            warnings.append("Low disk space detected")

        if warnings:
            summary["warnings"] = warnings

        return summary


