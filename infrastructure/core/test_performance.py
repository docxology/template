"""Backwards-compat shim: the module moved to ``infrastructure.core.testing.test_performance``.

Old import paths keep resolving (``CORE-TESTING-REHOME-1``); new code imports
from ``infrastructure.core.testing.test_performance`` directly.
"""

from infrastructure.core.testing.test_performance import (  # noqa: F401
    TEST_BENCHMARK_SCHEMA,
    TestBenchmarkError,
    TestPerformanceManifest,
    TestRunSummary,
    _redact_output_tail,
    build_test_command,
    build_test_performance_manifest,
    main,
    run_test_benchmark,
)

__all__ = [
    "TEST_BENCHMARK_SCHEMA",
    "TestBenchmarkError",
    "TestPerformanceManifest",
    "TestRunSummary",
    "_redact_output_tail",
    "build_test_command",
    "build_test_performance_manifest",
    "main",
    "run_test_benchmark",
]
