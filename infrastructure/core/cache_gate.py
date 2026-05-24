"""Hermes plugin cache validation gate (opt-in; not part of default template pipeline).

Requires ``HERMES_HOME`` and a Hermes plugin tree. Invoked only via
``scripts/gates/gate_cache.py`` — not wired into ``./run.sh`` or CI.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class _NoOpMetrics:
    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

    def labels(self, **_kwargs: str) -> "_NoOpMetrics":
        return self

    def inc(self, amount: float = 1.0) -> None:
        logger.debug("%s.inc(%.1f)", self._name, amount)


class _NoOpHistogram:
    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

    def labels(self, **_kwargs: str) -> "_NoOpHistogram":
        return self

    def observe(self, value: float) -> None:
        logger.debug("%s.observe(%.4f)", self._name, value)


gate_runs_total = _NoOpMetrics("gate_runs_total", "Total gate runs by name and outcome")
gate_duration_seconds = _NoOpHistogram("gate_duration_seconds", "Gate execution duration in seconds")

GATES = (
    {
        "name": "cache",
        "module": "infrastructure.core.cache_gate",
        "function": "run_cache_gate",
        "globs": (),
    },
    {
        "name": "security",
        "module": "scripts.gates.security_scan",
        "function": "main",
        "globs": ("src/**/*.py", "pyproject.toml", "tests/**/*.py"),
    },
    {
        "name": "plugin-export-check",
        "module": "scripts.gates.plugin_export_check",
        "function": "run_plugin_export_check",
        "globs": (
            "src/registrations.py",
            "src/hermes_plugin.py",
            "src/core/registry.py",
            ".hermes/plugins/template-plugin/**",
        ),
    },
    {
        "name": "security-scan",
        "module": "scripts.gates.security_scan",
        "function": "main",
        "globs": ("src/**/*.py", "pyproject.toml", "tests/**/*.py"),
    },
)


def _load_plugin_manifest(hermes_home: Path) -> dict[str, Any] | None:
    manifest_path = hermes_home / "plugins" / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid plugin manifest JSON: {exc}")
        return None


def _is_cache_fresh(cache_marker: Path, ttl_seconds: int) -> bool:
    if not cache_marker.exists():
        return False
    try:
        age = time.time() - cache_marker.stat().st_mtime
        return age < ttl_seconds
    except OSError:
        return False


def _populate_cache(hermes_home: Path, cache_path: Path, cache_marker: Path) -> bool:
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        plugins_src = hermes_home / "plugins"
        plugins_dst = cache_path / "plugins"
        if plugins_src.exists():
            if plugins_dst.exists():
                shutil.rmtree(plugins_dst)
            shutil.copytree(plugins_src, plugins_dst)
        tools_src = hermes_home / "tools"
        tools_dst = cache_path / "tools"
        if tools_src.exists():
            if tools_dst.exists():
                shutil.rmtree(tools_dst)
            shutil.copytree(tools_src, tools_dst)
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hermes_home": str(hermes_home),
            "version": "0.1.0",
        }
        (cache_path / "cache_metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        cache_marker.touch()
        print(f"Cache populated at {cache_path}")
        return True
    except OSError as exc:
        print(f"ERROR: Failed to populate cache: {exc}")
        return False


def run_cache_gate() -> int:
    hermes_home_env = os.getenv("HERMES_HOME")
    cache_path = Path(os.getenv("HERMES_CACHE_PATH", "/var/cache/template"))
    cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    cache_marker = cache_path / ".cache_valid"

    if not hermes_home_env:
        print("ERROR: HERMES_HOME environment variable not set")
        gate_runs_total.labels(gate="cache", outcome="failure").inc()
        return 1

    hermes_home = Path(hermes_home_env)
    if not hermes_home.exists():
        print(f"ERROR: Hermes home not found: {hermes_home_env}")
        gate_runs_total.labels(gate="cache", outcome="failure").inc()
        return 1

    start_time = time.time()
    outcome = "failure"
    try:
        if _is_cache_fresh(cache_marker, cache_ttl):
            print(f"Cache is fresh (TTL: {cache_ttl}s). Skipping rebuild.")
            outcome = "success"
            return 0
        print("Cache stale or missing. Rebuilding...")
        cache_path.mkdir(parents=True, exist_ok=True)
        if not _populate_cache(hermes_home, cache_path, cache_marker):
            return 1
        outcome = "success"
        return 0
    except KeyboardInterrupt:
        print("ERROR: Gate interrupted by user")
        outcome = "error"
        return 1
    except OSError as exc:
        print(f"ERROR: Unexpected error in cache gate: {exc}")
        outcome = "error"
        return 1
    finally:
        gate_duration_seconds.labels(gate="cache").observe(time.time() - start_time)
        gate_runs_total.labels(gate="cache", outcome=outcome).inc()
