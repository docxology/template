"""Manuscript cluster: ``{{SIA_*}}`` token computation (core + metric tables),
render-time variable merging/hydration, and loop summary reports."""

from .manuscript_tokens_core import (
    compute_core_variables,
    format_metric,
)
from .manuscript_tokens_metrics import (
    compute_metrics_variables,
)
from .manuscript_variables import (
    compute_variables,
    save_variables,
)
from .reports import (
    write_loop_report,
    write_manuscript_variables,
)

__all__ = [
    "compute_core_variables",
    "format_metric",
    "compute_metrics_variables",
    "compute_variables",
    "save_variables",
    "write_loop_report",
    "write_manuscript_variables",
]
