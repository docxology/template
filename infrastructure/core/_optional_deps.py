"""Optional dependency availability.

Single authoritative source for optional-dependency imports. Modules that need
psutil should import from here rather than each guarding the import themselves.

Usage:
    from infrastructure.core._optional_deps import psutil
    if psutil is None:
        return {}
"""

from __future__ import annotations

import types as _module_types

try:
    import psutil
except ImportError:
    psutil = None

np: _module_types.ModuleType | None = None
try:
    import numpy as np  # type: ignore[no-redef]
except ImportError:
    np = None  # numpy is optional

__all__ = ["psutil", "np"]
