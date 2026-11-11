"""Shared tool-lookup helpers for runtime subprocess orchestration.

Centralizes ``shutil.which``-based resolution of external tools so callers
do not each re-implement fallback handling. Import sites keep their own
policy (raise vs. fall back); this module only owns *where* the tool is.
"""

from __future__ import annotations

import shutil


def find_uv() -> str | None:
    """Return the absolute path to the ``uv`` executable, or ``None``.

    Single canonical lookup point for uv-resolution across the runtime,
    pytest-orchestration, doctor, and export-smoke paths. Behavior is
    identical to ``shutil.which("uv")``; the value of this helper is that
    future changes (e.g. env-var overrides) have exactly one home.
    """
    return shutil.which("uv")
