"""Optional dependency availability.

Single authoritative source for optional-dependency imports. Modules that need
psutil should import from here rather than each guarding the import themselves.

Usage:
    from infrastructure.core._optional_deps import psutil
    if psutil is None:
        return {}
"""
from __future__ import annotations

try:
    import psutil  # type: ignore[import-untyped]
except ImportError:
    psutil = None  # type: ignore[assignment]

__all__ = ["psutil"]
