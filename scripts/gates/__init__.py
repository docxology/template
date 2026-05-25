"""Gate execution scripts.

This package contains gate scripts that run as part of the template pipeline.
Gates are atomic validation or transformation steps that record metrics
and determine pipeline progression.

Modules:
    gate_cache: Cache validation and population gate.
    security_scan: Security scanning gate (bandit, safety, pip-audit).
    plugin_export_check: Plugin export verification gate.
"""

__all__ = ["gate_cache", "security_scan", "plugin_export_check"]
