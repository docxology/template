"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.pytest_profiles``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.pytest_profiles`` directly.
"""

from infrastructure.core.testing.pytest_profiles import (  # noqa: F401
    DEFAULT_PROJECT_MATRIX_MAX_WORKERS,
    DEFAULT_PUBLIC_PROJECT_TEST_TIMEOUT_SECONDS,
    DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
    DEFAULT_TEST_PROFILE,
    ENV_PROJECT_MATRIX_WORKERS,
    ENV_XDIST_WORKERS,
    MACOS_COVERAGE_XDIST_MAX_WORKERS,
    TEST_PROFILE_NAMES,
    TEST_PROFILE_REGISTRY,
    TEST_RUNNER_BASE_DEPS,
    TestProfileName,
    TestProfileSpec,
    XDIST_DISTRIBUTION,
    XdistWorkerConfig,
    build_profile_marker_expression,
    parse_project_workers,
    resolve_project_matrix_workers,
    resolve_test_profile,
    resolve_xdist_args,
    resolve_xdist_worker_config,
    test_runner_dependency_specs,
    validate_coverage_parallel,
    validate_project_matrix_concurrency,
)

__all__ = [
    "DEFAULT_PROJECT_MATRIX_MAX_WORKERS",
    "DEFAULT_PUBLIC_PROJECT_TEST_TIMEOUT_SECONDS",
    "DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS",
    "DEFAULT_TEST_PROFILE",
    "ENV_PROJECT_MATRIX_WORKERS",
    "ENV_XDIST_WORKERS",
    "MACOS_COVERAGE_XDIST_MAX_WORKERS",
    "TEST_PROFILE_NAMES",
    "TEST_PROFILE_REGISTRY",
    "TEST_RUNNER_BASE_DEPS",
    "TestProfileName",
    "TestProfileSpec",
    "XDIST_DISTRIBUTION",
    "XdistWorkerConfig",
    "build_profile_marker_expression",
    "parse_project_workers",
    "resolve_project_matrix_workers",
    "resolve_test_profile",
    "resolve_xdist_args",
    "resolve_xdist_worker_config",
    "test_runner_dependency_specs",
    "validate_coverage_parallel",
    "validate_project_matrix_concurrency",
]
