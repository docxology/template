"""Bind the actual generator and supervisor without inventing checkout files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .child_execution import ChildCapabilityBlocked

GENERATOR_CUSTODY_SCHEMA = "autopoiesis/active-generator-custody/1"


def capture_execution_custody(*, fresh_pycache_prefix: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Admit platform 4 and capture the imported generator's real source origin.

    A canonical ``src/template_autopoiesis`` checkout needs its own matching
    metadata and lock. Otherwise the selected installed distribution must bind
    the actual package directory through its genuine METADATA and RECORD.
    A fresh prefix is evidence only when the caller's launcher installed the
    shared pre-import bytecode audit; ordinary calls retain the weaker baseline.
    """
    try:
        from infrastructure import __version__
        from infrastructure.core.implementation_custody import (
            capture_dependency_custody,
            capture_implementation_custody,
        )
    except ImportError as exc:
        raise ChildCapabilityBlocked("child execution requires the installed or checkout platform 4.0.2") from exc
    if __version__ != "4.0.2":
        raise ChildCapabilityBlocked("child execution requires its bound platform version 4.0.2")

    import template_autopoiesis

    if not isinstance(template_autopoiesis.__file__, str):
        raise ValueError("actual generator package origin is unavailable")
    # Normalize import-path aliases such as tests/../src without resolving away
    # symlink ancestors, which the shared no-follow custody verifier rejects.
    package_root = Path(os.path.abspath(template_autopoiesis.__file__)).parent
    if package_root.name != "template_autopoiesis":
        raise ValueError("actual generator package origin has an unexpected identity")
    checkout_root = package_root.parent.parent if package_root.parent.name == "src" else None
    if checkout_root is not None and not all(
        (checkout_root / name).is_file() for name in ("pyproject.toml", "uv.lock")
    ):
        raise ValueError("generator checkout requires its actual package metadata and lock")

    platform = capture_implementation_custody(fresh_pycache_prefix=fresh_pycache_prefix)
    generator = capture_dependency_custody(
        "template_autopoiesis",
        package_root,
        checkout_root=checkout_root,
        fresh_pycache_prefix=fresh_pycache_prefix,
    )
    return {"schema_version": GENERATOR_CUSTODY_SCHEMA, **generator}, platform
