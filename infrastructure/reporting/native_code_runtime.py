"""Exact CPython executable-code compatibility, separate from host identity.

Original sys.version remains retained provenance. This predicate neither admits
an installed SDK nor a runtime/kernel: those require the genuine current Source
and original supervisor capabilities. Every original Code/cache byte is checked.
"""

from __future__ import annotations

import importlib.util
import sys
from typing import Any

from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported

SCHEMA = "template-native-executed-code-runtime-v1"


def observe_native_code_runtime() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "python_version": sys.version,
        "implementation": sys.implementation.name,
        "release": list(sys.version_info),
        "optimize": sys.flags.optimize,
        "magic_hex": importlib.util.MAGIC_NUMBER.hex(),
        "cache_tag": sys.implementation.cache_tag,
    }


def validate_native_code_runtime(original: object) -> dict[str, Any]:
    current = observe_native_code_runtime()
    if not isinstance(original, dict) or set(original) != set(current):
        raise ProjectionSourceUnsupported("native original executed Code runtime inventory is incomplete")
    if not isinstance(original["python_version"], str) or not original["python_version"]:
        raise ValueError("native original full Python build/platform label is missing")
    release = original["release"]
    if (
        not isinstance(release, list)
        or len(release) != 5
        or any(type(item) is not int or item < 0 for item in (*release[:3], release[4]))
        or release[3] not in {"alpha", "beta", "candidate", "final"}
        or type(original["optimize"]) is not int
        or original["implementation"] != "cpython"
        or original["python_version"].split()[0] != current["python_version"].split()[0]
        or any(original[key] != current[key] for key in current if key != "python_version")
    ):
        raise ProjectionSourceUnsupported(
            "native retained Code requires the exact original CPython release/optimize/magic/cache-tag"
        )
    return original
