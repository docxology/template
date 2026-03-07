"""Performance profiling and benchmarking — thin re-export of performance.py.

All implementations live in infrastructure.core.performance. This module exists
for backwards compatibility and delegates everything there.
"""

from __future__ import annotations

from infrastructure.core.performance import (  # noqa: F401
    CodeProfiler,
    ProfilingMetrics,
    benchmark_llm_query,
    get_performance_monitor,
    monitor_performance,
)
