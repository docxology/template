"""Infrastructure layer - Modular build, validation, and development tools.

This package contains reusable infrastructure modules for building, validating, and
managing research projects. Organized by functionality into submodules.

Modules:
    core: Foundation utilities (config, logging, exceptions, progress, checkpoint)
    validation: Quality & validation tools (PDF, Markdown, integrity)
    documentation: Documentation & figure management
    scientific: Scientific computing utilities
    llm: Local LLM integration for research assistance
    rendering: Multi-format output generation
    publishing: Academic publishing & dissemination
    reporting: Pipeline reporting & error aggregation
"""

__version__ = "2.0.0"
__layer__ = "infrastructure"

# Import commonly-used items for convenient access
try:
    # Core
    from .core import (BuildError, ConfigurationError, ProjectLogger,
                       TemplateError, ValidationError, get_logger,
                       get_project_logger, load_config, log_operation,
                       log_timing, setup_logger, setup_project_logging)
    # Documentation
    from .documentation import FigureManager, ImageManager, MarkdownIntegration
    # Publishing
    from .publishing import (extract_publication_metadata,
                             generate_citation_bibtex, publish_to_zenodo)
    # Reporting
    from .reporting import generate_pipeline_report, get_error_aggregator
    # Validation
    from .validation import (validate_markdown, validate_pdf_rendering,
                             verify_output_integrity)
except ImportError:
    # Graceful fallback if imports fail
    pass

__all__ = [
    # Modules
    "core",
    "validation",
    "documentation",
    "scientific",
    "llm",
    "rendering",
    "publishing",
    "reporting",
    # Core conveniences
    "get_logger",
    "setup_logger",
    "get_project_logger",
    "setup_project_logging",
    "ProjectLogger",
    "log_operation",
    "log_timing",
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "load_config",
    # Validation conveniences
    "validate_pdf_rendering",
    "validate_markdown",
    "verify_output_integrity",
    # Documentation conveniences
    "FigureManager",
    "ImageManager",
    "MarkdownIntegration",
    # Publishing conveniences
    "extract_publication_metadata",
    "generate_citation_bibtex",
    "publish_to_zenodo",
    # Reporting conveniences
    "generate_pipeline_report",
    "get_error_aggregator",
]
