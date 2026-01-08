"""Utility modules for the Ento-Linguistic Research Project."""

from .logging import get_logger, log_substep, log_progress_bar, log_stage
from .exceptions import ValidationError
from .figure_manager import FigureManager, FigureMetadata
from .validation import validate_markdown, validate_figure_registry, verify_output_integrity, IntegrityReport, validate_pdf_rendering
from .reporting import generate_pipeline_report, save_pipeline_report, get_error_aggregator, ReportGenerator
from .markdown_integration import MarkdownIntegration, ImageManager

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