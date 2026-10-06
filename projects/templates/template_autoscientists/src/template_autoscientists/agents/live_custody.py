"""Controller/worker custody for actual public implementation and selected runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from infrastructure.core.implementation_custody import (
    capture_implementation_custody,
    runtime_identity,
    source_file_manifest,
    verify_fresh_module_bytecode,
)
from .live_domain import CoordinationFailed


def _files(root: Path) -> dict[str, str]:
    return source_file_manifest(root, frozenset({".py"}))


_ACTIVE_ROOT = Path(__file__).absolute().parents[1]
_LOADED_ACTIVE_SOURCE = _files(_ACTIVE_ROOT)


def implementation_custody() -> dict[str, Any]:
    """Capture checkout or installed RECORD custody and an explicit launcher binding."""
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    return capture_implementation_custody(fresh_pycache_prefix=prefix)


def _platform_sources(custody: dict[str, Any]) -> dict[str, str]:
    """Project one freshly captured observation into its public source identity."""
    result = dict(custody["files"])
    if custody["distribution"] is not None:
        result["distribution/METADATA"] = custody["distribution"]["metadata_sha256"]
        result["distribution/RECORD"] = custody["distribution"]["record_sha256"]
    return result


def platform_sources() -> dict[str, str]:
    """Bind actual public source plus the selected distribution's metadata records."""
    return _platform_sources(implementation_custody())


def environment_identity() -> dict[str, Any]:
    """Identify only the selected installed runtime without dependency acquisition."""
    return runtime_identity()


def verify_custody(
    expected_sources: dict[str, str],
    expected_environment: dict[str, Any],
    custody: dict[str, Any] | None = None,
    *,
    fresh_prefix: Path | None = None,
) -> None:
    """Reject linked/stale loaded source, changed installed records, or runtime drift."""
    selected_prefix = fresh_prefix or (Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None)
    # WHY: all three evidence planes at this boundary must describe the same
    # fresh observation. Re-reading the full platform for each projection adds
    # work without adding a controller/worker boundary or an independent check.
    actual = capture_implementation_custody(fresh_pycache_prefix=selected_prefix)
    if custody is not None:
        expected = dict(custody, bytecode_binding="fresh-owned-prefix") if selected_prefix is not None else custody
        if actual != expected:
            raise ValueError("public implementation, distribution, bytecode binding or runtime changed")
    if selected_prefix is not None:
        verify_fresh_module_bytecode(_ACTIVE_ROOT, selected_prefix)
        project = _ACTIVE_ROOT.parent.parent
        if (project / "pyproject.toml").is_file() and (project / "scripts").is_dir():
            verify_fresh_module_bytecode(project / "scripts", selected_prefix)
    if (
        _files(_ACTIVE_ROOT) != _LOADED_ACTIVE_SOURCE
        or _platform_sources(actual) != expected_sources
        or actual["runtime_environment"] != expected_environment
    ):
        raise CoordinationFailed("trusted loaded source or runtime environment changed across workers")
