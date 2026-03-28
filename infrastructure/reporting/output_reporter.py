"""Output reporting utilities.

This module provides functions for generating output summaries and
collecting output statistics.

Implementation is split across focused submodules:
- ``output_statistics`` — file statistics collection and summary reporting
- ``log_analysis`` — log file parsing and summary generation
"""

from __future__ import annotations

# Re-export public API so all existing imports continue to work.
from .log_analysis import (
    generate_log_summary,
)
from .output_statistics import (
    collect_output_statistics,
    generate_detailed_output_report,
    log_output_summary,
)

__all__ = [
    "collect_output_statistics",
    "generate_detailed_output_report",
    "generate_log_summary",
    "log_output_summary",
]
