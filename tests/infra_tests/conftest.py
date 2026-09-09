"""Pytest configuration for infrastructure layer tests.

Provides shared fixtures and utilities for testing infrastructure modules.
All fixtures use real implementations following the 'no mocks' policy.
"""

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
