"""Pipeline reporter for generating consolidated reports.

Generates comprehensive reports in multiple formats (JSON, HTML, Markdown)
from pipeline execution data.

This module re-exports from focused submodules for backwards compatibility.
"""

from __future__ import annotations

# Re-export data model and report generation
from .pipeline_report_model import (
    PipelineReport,
    _StageResultDict,
    generate_pipeline_report,
)

# Re-export markdown generation
from .pipeline_markdown import _generate_pipeline_markdown

# Re-export HTML generation
from .pipeline_html import generate_html_report

# Re-export I/O and serialization utilities
from .pipeline_io import (
    _atomic_write_json,
    _atomic_write_text,
    generate_error_markdown,
    generate_performance_report,
    generate_validation_markdown,
    generate_validation_report,
    save_error_summary,
    save_pipeline_report,
    save_test_results,
)

__all__ = [
    "PipelineReport",
    "generate_pipeline_report",
    "generate_html_report",
    "generate_error_markdown",
    "generate_performance_report",
    "generate_validation_markdown",
    "generate_validation_report",
    "save_error_summary",
    "save_pipeline_report",
    "save_test_results",
]
