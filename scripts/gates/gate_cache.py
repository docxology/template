"""Gate cache runner with metrics instrumentation.

This module implements a gate that validates and populates a local cache of
Hermes plugin definitions and tool specifications. The gate checks whether
the cache is fresh and rebuilds it if stale or missing.

The gate runs as part of the template pipeline and ensures that subsequent
tool invocations have fast local access to plugin metadata without requiring
network calls to the Hermes registry.

Usage:
    python -m scripts.gates.gate_cache

Environment variables:
    HERMES_HOME: Root directory of Hermes installation (required)
    HERMES_CACHE_PATH: Cache directory path (default: /var/cache/template)
    CACHE_TTL_SECONDS: Cache freshness threshold in seconds (default: 3600)

Exit codes:
    0 - Gate succeeded (cache valid or rebuilt)
    1 - Gate failed (unrecoverable error)
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# --- Lightweight metrics stubs (Prometheus not available in template) ---

class _CounterStub:
    """Stub for a Prometheus Counter with label support."""

    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

    def labels(self, **kwargs: str) -> "_CounterStub":
        return self

    def inc(self, amount: float = 1.0) -> None:
        logger.debug("%s.inc(%.1f)", self._name, amount)


class _HistogramStub:
    """Stub for a Prometheus Histogram with label support."""

    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

    def labels(self, **kwargs: str) -> "_HistogramStub":
        return self

    def observe(self, value: float) -> None:
        logger.debug("%s.observe(%.4f)", self._name, value)


gate_runs_total = _CounterStub("gate_runs_total", "Total gate runs by name and outcome")
gate_duration_seconds = _HistogramStub("gate_duration_seconds", "Gate execution duration in seconds")


# Gate registry: defines available gates and their file-watch globs
# Each entry: (name, module, function, globs)
GATES = (
    {
        'name': 'cache',
        'module': 'scripts.gates.gate_cache',
        'function': 'run_gate',
        'globs': (),  # No specific file triggers; runs based on TTL
    },
    {
        'name': 'security',
        'module': 'scripts.gates.security_scan',
        'function': 'run_gate',
        'globs': ('src/**/*.py', 'pyproject.toml', 'tests/**/*.py'),
    },
    {
        'name': 'plugin-export-check',
        'module': 'scripts.gates.plugin_export_check',
        'function': 'run_gate',
        'globs': (
            'src/registrations.py',
            'src/hermes_plugin.py',
            'src/core/registry.py',
            '.hermes/plugins/template-plugin/**',
        ),
    },
    {
        'name': 'security-scan',
        'module': 'scripts.gates.security_scan',
        'function': 'run_gate',
        'globs': ('src/**/*.py', 'pyproject.toml', 'tests/**/*.py'),
    },
)

# Configuration from environment
HERMES_HOME = os.getenv('HERMES_HOME')
CACHE_PATH = Path(os.getenv('HERMES_CACHE_PATH', '/var/cache/template'))
CACHE_TTL = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
CACHE_MARKER = CACHE_PATH / '.cache_valid'


def _load_plugin_manifest(hermes_home: Path) -> Optional[Dict[str, Any]]:
    """Load the Hermes plugin manifest from the installation.
    
    Args:
        hermes_home: Path to Hermes installation root.
        
    Returns:
        Plugin manifest dict if found, None otherwise.
    """
    manifest_path = hermes_home / 'plugins' / 'manifest.json'
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid plugin manifest JSON: {e}")
        return None


def _is_cache_fresh(cache_marker: Path, ttl_seconds: int) -> bool:
    """Check if cache marker exists and is within TTL.
    
    Args:
        cache_marker: Path to cache validity marker file.
        ttl_seconds: Time-to-live threshold in seconds.
        
    Returns:
        True if cache is fresh, False otherwise.
    """
    if not cache_marker.exists():
        return False
    try:
        mtime = cache_marker.stat().st_mtime
        age = time.time() - mtime
        return age < ttl_seconds
    except Exception:
        return False


def _populate_cache(hermes_home: Path, cache_path: Path) -> bool:
    """Populate cache with plugin definitions and tool specs.
    
    Copies plugin files, tool schemas, and writes cache metadata.
    
    Args:
        hermes_home: Hermes installation root.
        cache_path: Target cache directory.
        
    Returns:
        True if cache populated successfully, False on error.
    """
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # Copy plugin definitions
        plugins_src = hermes_home / 'plugins'
        plugins_dst = cache_path / 'plugins'
        if plugins_src.exists():
            if plugins_dst.exists():
                shutil.rmtree(plugins_dst)
            shutil.copytree(plugins_src, plugins_dst)
        
        # Copy tool specifications
        tools_src = hermes_home / 'tools'
        tools_dst = cache_path / 'tools'
        if tools_src.exists():
            if tools_dst.exists():
                shutil.rmtree(tools_dst)
            shutil.copytree(tools_src, tools_dst)
        
        # Write cache metadata
        metadata = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'hermes_home': str(hermes_home),
            'version': '0.1.0'
        }
        with open(cache_path / 'cache_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Touch cache marker
        CACHE_MARKER.touch()
        
        print(f"Cache populated at {cache_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to populate cache: {e}")
        return False


def run_gate() -> int:
    """Execute the cache validation gate.
    
    Checks if cache exists and is fresh. Rebuilds cache if invalid.
    Records gate duration and outcome metrics.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
        
    Metrics recorded:
        - gate_duration_seconds: observed with gate execution time.
        - gate_runs_total: incremented with labels gate="cache", outcome="success"/"failure".
    """
    if not HERMES_HOME:
        print("ERROR: HERMES_HOME environment variable not set")
        gate_runs_total.labels(gate='cache', outcome='failure').inc()
        return 1
    
    hermes_home = Path(HERMES_HOME)
    if not hermes_home.exists():
        print(f"ERROR: Hermes home not found: {HERMES_HOME}")
        gate_runs_total.labels(gate='cache', outcome='failure').inc()
        return 1
    
    start_time = time.time()
    outcome = 'failure'  # default to failure, set to success on clean exit
    
    try:
        # Check cache freshness
        if _is_cache_fresh(CACHE_MARKER, CACHE_TTL):
            print(f"Cache is fresh (TTL: {CACHE_TTL}s). Skipping rebuild.")
            outcome = 'success'
            return 0
        
        print("Cache stale or missing. Rebuilding...")
        
        # Ensure cache directory exists
        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        
        # Populate cache
        if not _populate_cache(hermes_home, CACHE_PATH):
            outcome = 'failure'
            return 1
        
        outcome = 'success'
        return 0
        
    except KeyboardInterrupt:
        print("ERROR: Gate interrupted by user")
        outcome = 'error'
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error in cache gate: {e}")
        outcome = 'error'
        return 1
    finally:
        # Record metrics regardless of outcome
        duration = time.time() - start_time
        gate_duration_seconds.labels(gate='cache').observe(duration)
        gate_runs_total.labels(gate='cache', outcome=outcome).inc()


if __name__ == '__main__':
    exit_code = run_gate()
    exit(exit_code)
