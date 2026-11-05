"""Required SDK capabilities for analysis modules.

Import failures propagate: analysis cannot succeed without the supported SDK.
The standalone mathematical primitives live in ``core/``.
"""

from __future__ import annotations

from infrastructure.core import ProgressBar, SystemHealthChecker
from infrastructure.core.exceptions import ScriptExecutionError, TemplateError, ValidationError
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.documentation.figure_manager import FigureManager
from infrastructure.documentation.glossary_gen import build_api_index, generate_markdown_table
from infrastructure.publishing import generate_citation_apa, generate_citation_bibtex, generate_citation_mla
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.reporting.interactive_dashboard import InteractiveDashboard, Invariant, Panel
from infrastructure.scientific import benchmark_function, check_numerical_stability
from infrastructure.validation import verify_output_integrity


__all__ = [
    "FigureManager",
    "InteractiveDashboard",
    "Invariant",
    "Panel",
    "ProgressBar",
    "PublicationMetadata",
    "ScriptExecutionError",
    "SystemHealthChecker",
    "TemplateError",
    "ValidationError",
    "benchmark_function",
    "build_api_index",
    "check_numerical_stability",
    "generate_citation_apa",
    "generate_citation_bibtex",
    "generate_citation_mla",
    "generate_markdown_table",
    "get_logger",
    "log_success",
    "verify_output_integrity",
]
