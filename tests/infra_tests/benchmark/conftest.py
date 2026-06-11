"""Pytest configuration for benchmark tests.

Registers the ``bench`` marker so ``--strict-markers`` does not reject
the per-test ``@pytest.mark.bench`` decoration. The marker is also declared
in the root ``pyproject.toml#[tool.pytest.ini_options].markers``; this
``conftest`` provides a local affordance so the bench tree stays
self-contained when invoked directly with ``pytest tests/infra_tests/benchmark/``.
"""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``bench`` marker locally (idempotent with root config)."""
    config.addinivalue_line(
        "markers",
        "bench: performance benchmark tests",
    )
