"""Utility modules for the Ento-Linguistic Research Project."""

from .exceptions import ValidationError
from .figure_manager import FigureManager, FigureMetadata
from .logging import get_logger, log_progress_bar, log_stage, log_substep
from .markdown_integration import ImageManager, MarkdownIntegration
from .reporting import (ReportGenerator, generate_pipeline_report,
                        get_error_aggregator, save_pipeline_report)
from .validation import (IntegrityReport, validate_figure_registry,
                         validate_markdown, validate_pdf_rendering,
                         verify_output_integrity)

__all__ = [
    "get_logger",
    "log_substep",
    "log_progress_bar",
    "log_stage",
    "ValidationError",
    "FigureManager",
    "FigureMetadata",
    "validate_markdown",
    "validate_figure_registry",
    "verify_output_integrity",
    "IntegrityReport",
    "validate_pdf_rendering",
    "generate_pipeline_report",
    "save_pipeline_report",
    "get_error_aggregator",
    "ReportGenerator",
    "MarkdownIntegration",
    "ImageManager",
]
