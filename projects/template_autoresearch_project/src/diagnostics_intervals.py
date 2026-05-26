"""Interval and paired-comparison diagnostic compatibility exports."""

from __future__ import annotations

from .diagnostics_reports import (
    bootstrap_intervals,
    candidate_accuracy_intervals,
    paired_comparison_report,
)

__all__ = [
    "bootstrap_intervals",
    "candidate_accuracy_intervals",
    "paired_comparison_report",
]
