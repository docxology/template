"""Pytest configuration for infrastructure layer tests.

Provides shared fixtures and utilities for testing infrastructure modules.
All fixtures use real implementations following the 'no mocks' policy.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(scope="module", autouse=True)
def explicit_disposable_build_epoch() -> Iterator[None]:
    """Supply an explicit reference clock for non-Git test projects.

    This is a declared test input, not publication or candidate-commit evidence.
    Negative clock controls remove/replace it explicitly. Production callers
    receive no fallback from this fixture.
    """
    # Module evidence fixtures launch real children before function fixtures.
    # Give both scopes the same explicit input, restoring it at module teardown.
    with pytest.MonkeyPatch.context() as environment_inputs:
        if "SOURCE_DATE_EPOCH" not in os.environ:
            environment_inputs.setenv("SOURCE_DATE_EPOCH", "1700000000")
        yield


# =============================================================================
# Centralized Fixtures
# =============================================================================
#
# Environment defaults (headless matplotlib backend, Git overrides, sys.path
# insertion) and the
# ``repo_root`` / ``ensure_ollama_for_tests`` fixtures live in tests/conftest.py
# (the root) so every suite inherits one definition. Do not redefine them here.
#
# IMPORTANT: Do NOT add tests/infra_tests to sys.path - it would shadow
# infrastructure.* imports with tests/infra_tests/* packages.
#
# Helper functions (scaffolding, ``safe_network_test``) live in real helper
# modules under ``tests/helpers/``; tests import them directly rather than
# through conftest re-exports.
