"""Shared bounded worker-count policy for pipeline and test runners."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

ENV_MULTI_PROJECT_WORKERS = "MULTI_PROJECT_MAX_WORKERS"
ENV_PROJECT_MATRIX_WORKERS = "TEMPLATE_PROJECT_WORKERS"
ENV_XDIST_WORKERS = "PYTEST_XDIST_WORKERS"
DEFAULT_PROJECT_MATRIX_MAX_WORKERS = 4

InvalidPolicy = Literal["raise", "fallback"]


def clamp_worker_count(requested: int, item_count: int | None = None) -> int:
    """Validate a positive worker request and cap it to available items."""
    if requested < 1:
        raise ValueError("workers must be positive")
    if item_count is None:
        return requested
    return min(requested, max(1, item_count))


def resolve_bounded_workers(
    *,
    env_name: str,
    env: Mapping[str, str] | None = None,
    item_count: int | None = None,
    default_cap: int | None = None,
    cpu_reserve: int = 0,
    invalid: InvalidPolicy = "raise",
) -> int:
    """Resolve an environment override or a CPU-bounded default.

    The helper deliberately owns only worker-count mechanics. Callers retain
    their public vocabulary (``auto``, ``serial``, or explicit integers) and
    any domain-specific safety checks such as macOS coverage limits.
    """
    source_env = os.environ if env is None else env
    configured = source_env.get(env_name, "").strip()
    if configured:
        try:
            requested = int(configured)
        except ValueError as exc:
            if invalid == "fallback":
                requested = 0
            else:
                raise ValueError(f"Invalid {env_name} value {configured!r}: use a positive integer") from exc
        if requested > 0:
            return clamp_worker_count(requested, item_count)
        if invalid == "raise":
            raise ValueError(f"Invalid {env_name} value {configured!r}: use a positive integer")

    available = max(1, (os.cpu_count() or 1) - max(0, cpu_reserve))
    if default_cap is not None:
        available = min(available, max(1, default_cap))
    return clamp_worker_count(available, item_count)


__all__ = [
    "DEFAULT_PROJECT_MATRIX_MAX_WORKERS",
    "ENV_MULTI_PROJECT_WORKERS",
    "ENV_PROJECT_MATRIX_WORKERS",
    "ENV_XDIST_WORKERS",
    "clamp_worker_count",
    "resolve_bounded_workers",
]
