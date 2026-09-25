"""Compatibility facade for orchestration analysis entrypoints.

Prefer ``from orchestration.analysis import ...`` in new code.
"""

from orchestration.analysis import (
    run_analysis,
    summarize_sweep,
    write_analysis_statistics,
    write_invariants_report,
    write_parameter_sweep,
)

__all__ = [
    "run_analysis",
    "summarize_sweep",
    "write_analysis_statistics",
    "write_invariants_report",
    "write_parameter_sweep",
]
