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
    steganography: Optional secure PDF post-processing (overlays, barcodes, hashing)
"""

__version__ = "2.0.0"
__layer__ = "infrastructure"

# Import commonly-used items for convenient access
try:
    # Core
    from .core import (  # type: ignore
        BuildError,
        ConfigurationError,
        ProjectLogger,
        TemplateError,
        ValidationError,
        get_logger,
        get_project_logger,
        load_config,
        log_operation,
        log_timing,
        setup_logger,
        setup_project_logging,
    )

    # Documentation
    from .documentation import FigureManager, ImageManager, MarkdownIntegration

    # Publishing
    from .publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
        publish_to_zenodo,
    )

    # Reporting
    from .reporting import generate_pipeline_report, get_error_aggregator

    # Validation
    from .validation import validate_markdown, validate_pdf_rendering, verify_output_integrity
except ImportError as _e:
    import warnings
    warnings.warn(f"infrastructure convenience imports unavailable: {_e}", ImportWarning, stacklevel=2)

# Steganography — optional, only loaded when dependencies are available
try:
    from .steganography import SteganographyConfig, SteganographyProcessor, process_pdf
except ImportError:
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
    "steganography",
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
