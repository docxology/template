"""Test summary generator — re-export shim for backwards compatibility.

All implementations live in infrastructure.reporting.suite_summary_generator.
"""

from __future__ import annotations

from infrastructure.reporting.suite_summary_generator import (  # noqa: F401

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)
    discover_active_projects,
    generate_markdown_report,
    generate_summary_report,
    load_infrastructure_results,
    load_test_results,
    run_test_summary_generation,
)
