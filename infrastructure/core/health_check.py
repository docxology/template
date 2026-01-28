"""System health monitoring and status checks.

This module provides comprehensive health monitoring for all system components,
including dependencies, filesystem, network, and performance metrics.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class SystemHealthChecker:
    """Comprehensive system health monitoring."""

    def __init__(self):
        self.start_time = time.time()
        self.checks = {
            "filesystem": self._check_filesystem,
            "memory": self._check_memory,
            "cpu": self._check_cpu,
            "disk": self._check_disk,
            "network": self._check_network,
            "dependencies": self._check_dependencies,
            "uptime": self._check_uptime,
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status.

        Returns:
            Dictionary containing health status for all components
        """
        status = {
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
            except Exception as e:
                logger.warning(f"Health check failed for {check_name}: {e}")
                status["checks"][check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
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

    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health and permissions."""
        import tempfile

        results = {}

        # Check write permissions
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
                f.write("health_check_test")
            results["write_permissions"] = True
        except (OSError, IOError):
            results["write_permissions"] = False

        # Check critical directories
        critical_dirs = [
            Path("projects"),
            Path("projects/project"),
            Path("projects/project/src"),
            Path("projects/project/output"),
            Path("infrastructure"),
        ]

        results["directories"] = {}
        for dir_path in critical_dirs:
            results["directories"][str(dir_path)] = {
                "exists": dir_path.exists(),
                "readable": dir_path.exists() and dir_path.is_dir(),
                "writable": dir_path.exists() and os.access(dir_path, os.W_OK),
            }

        return results

    def _check_memory(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_mb": memory.total // (1024 * 1024),
                "available_mb": memory.available // (1024 * 1024),
                "used_mb": memory.used // (1024 * 1024),
                "percent_used": memory.percent,
                "critical_threshold": 95.0,  # Consider critical if > 95% used
                "is_critical": memory.percent > 95.0,
            }
        except ImportError:
            return {"psutil_unavailable": True}

    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage and load."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
                ),
            }
        except ImportError:
            return {"psutil_unavailable": True}

    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage("/")
            return {
                "total_gb": disk.total // (1024**3),
                "used_gb": disk.used // (1024**3),
                "free_gb": disk.free // (1024**3),
                "percent_used": disk.percent,
                "critical_threshold": 95.0,
                "is_critical": disk.percent > 95.0,
            }
        except ImportError:
            return {"psutil_unavailable": True}

    def _check_network(self) -> Dict[str, Any]:
        """Check network connectivity."""
        import socket

        results = {}

        # Test DNS resolution
        try:
            socket.gethostbyname("google.com")
            results["dns_resolution"] = True
        except socket.gaierror:
            results["dns_resolution"] = False

        # Test basic connectivity (if requests available)
        try:
            import requests

            response = requests.get("https://httpbin.org/status/200", timeout=5)
            results["http_connectivity"] = response.status_code == 200
        except (ImportError, requests.RequestException):
            results["http_connectivity"] = None  # Not available or failed

        return results

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical Python dependencies."""
        critical_deps = [
            "numpy",
            "matplotlib",
            "requests",
            "pyyaml",
            "psutil",  # For monitoring
        ]

        results = {}
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

    def _check_uptime(self) -> Dict[str, Any]:
        """Check system uptime and process runtime."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
        except (FileNotFoundError, OSError):
            # Fallback for systems without /proc/uptime
            uptime_seconds = (
                time.time() - psutil.boot_time()
                if hasattr(psutil, "boot_time")
                else None
            )

        process_uptime = time.time() - self.start_time

        return {
            "system_uptime_seconds": uptime_seconds,
            "system_uptime_hours": uptime_seconds / 3600 if uptime_seconds else None,
            "process_uptime_seconds": process_uptime,
            "process_uptime_hours": process_uptime / 3600,
        }

    def _generate_summary(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary metrics from health status."""
        checks = status["checks"]

        summary = {
            "total_checks": len(checks),
            "healthy_checks": sum(
                1 for c in checks.values() if c["status"] == "healthy"
            ),
            "unhealthy_checks": sum(
                1 for c in checks.values() if c["status"] == "unhealthy"
            ),
        }

        # Add critical resource warnings
        warnings = []

        if "memory" in checks and checks["memory"].get("details", {}).get(
            "is_critical"
        ):
            warnings.append("High memory usage detected")

        if "disk" in checks and checks["disk"].get("details", {}).get("is_critical"):
            warnings.append("Low disk space detected")

        if warnings:
            summary["warnings"] = warnings

        return summary


class HealthCheckAPI:
    """REST-like API for health check endpoints."""

    def __init__(self):
        self.checker = SystemHealthChecker()

    def get_status(self) -> Dict[str, Any]:
        """Get system health status."""
        return self.checker.get_health_status()

    def get_status_summary(self) -> Dict[str, Any]:
        """Get simplified health status summary."""
        full_status = self.get_status()

        return {
            "status": full_status["overall_status"],
            "timestamp": full_status["timestamp"],
            "checks_summary": full_status["summary"],
            "unhealthy_checks": [
                name
                for name, check in full_status["checks"].items()
                if check["status"] == "unhealthy"
            ],
        }

    def is_healthy(self) -> bool:
        """Quick health check - returns True if system is healthy."""
        status = self.get_status()
        return status["overall_status"] == "healthy"

    def get_metrics(self) -> Dict[str, Any]:
        """Get health metrics in a format suitable for monitoring systems."""
        status = self.get_status()

        metrics = {
            "health_status": 1 if status["overall_status"] == "healthy" else 0,
            "timestamp": status["timestamp"],
        }

        # Add individual check metrics
        for check_name, check_data in status["checks"].items():
            metrics[f"{check_name}_status"] = (
                1 if check_data["status"] == "healthy" else 0
            )

        # Add resource metrics
        if "memory" in status["checks"]:
            mem_details = status["checks"]["memory"].get("details", {})
            if "percent_used" in mem_details:
                metrics["memory_percent_used"] = mem_details["percent_used"]

        if "cpu" in status["checks"]:
            cpu_details = status["checks"]["cpu"].get("details", {})
            if "cpu_percent" in cpu_details:
                metrics["cpu_percent_used"] = cpu_details["cpu_percent"]

        if "disk" in status["checks"]:
            disk_details = status["checks"]["disk"].get("details", {})
            if "percent_used" in disk_details:
                metrics["disk_percent_used"] = disk_details["percent_used"]

        return metrics


# Global instances
_health_api = HealthCheckAPI()


def get_health_api() -> HealthCheckAPI:
    """Get the global health check API instance."""
    return _health_api


def quick_health_check() -> bool:
    """Perform a quick health check.

    Returns:
        True if system is healthy, False otherwise
    """
    return _health_api.is_healthy()


def get_health_status() -> Dict[str, Any]:
    """Get detailed health status."""
    return _health_api.get_status()


def get_health_metrics() -> Dict[str, Any]:
    """Get health metrics for monitoring systems."""
    return _health_api.get_metrics()
