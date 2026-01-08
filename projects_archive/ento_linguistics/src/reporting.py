"""Automated report generation for scientific computing.

This module provides template-based report generation from simulation results,
summary statistics tables, key findings extraction, and comparison reports.
"""

# Re-export from utils.reporting to maintain backward compatibility
from utils.reporting import (
    ReportGenerator,
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
)


