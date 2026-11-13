"""Optional dependency availability.

Single authoritative source for optional-dependency imports. Modules that need
psutil should import from here rather than each guarding the import themselves.
NumPy resolves only when a scientific consumer requests ``np``; psutil-only
logging and resource monitoring do not load numerical providers.

Usage:
    from infrastructure.core._optional_deps import psutil
    if psutil is None:
        return {}
"""

import types as _module_types
from importlib import import_module
from typing import TYPE_CHECKING

try:
    import psutil
except ImportError:
    psutil = None

if TYPE_CHECKING:
    np: _module_types.ModuleType | None


def __getattr__(name: str) -> _module_types.ModuleType | None:
    if name != "np":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value: _module_types.ModuleType | None
    try:
        value = import_module("numpy")
    except ImportError:
        value = None

    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


__all__ = ["psutil", "np"]
