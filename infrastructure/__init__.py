"""Infrastructure layer - Modular build, validation, and development tools.

This package contains reusable infrastructure modules for building, validating, and
managing research projects. Organized by functionality into submodules.

Modules:
    core: Foundation utilities (config, logging, exceptions)
    validation: Quality & validation tools (PDF, Markdown, integrity)
    documentation: Documentation & figure management
    build: Build & reproducibility verification
    scientific: Scientific computing utilities
    literature: Literature search and reference management
    llm: Local LLM integration for research assistance
    rendering: Multi-format output generation
    publishing: Academic publishing & dissemination
"""

__version__ = "2.0.0"
__layer__ = "infrastructure"

# Import commonly-used items for convenient access
try:
    # Core
    from .core import (
        get_logger, setup_logger, log_operation, log_timing,
        TemplateError, ConfigurationError, ValidationError, BuildError,
        load_config
    )
    # Validation
    from .validation import (
        validate_pdf_rendering,
        validate_markdown,
        verify_output_integrity
    )
    # Documentation
    from .documentation import (
        FigureManager,
        ImageManager,
        MarkdownIntegration
    )
    # Build
    from .build import (
        verify_build_artifacts,
        analyze_document_quality,
        generate_reproducibility_report
    )
    # Publishing
    from .publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
        publish_to_zenodo
    )
except ImportError:
    # Graceful fallback if imports fail
    pass

__all__ = [
    # Modules
    "core",
    "validation",
    "documentation",
    "build",
    "scientific",
    "literature",
    "llm",
    "rendering",
    "publishing",
    # Core conveniences
    "get_logger",
    "setup_logger",
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
    # Build conveniences
    "verify_build_artifacts",
    "analyze_document_quality",
    "generate_reproducibility_report",
    # Publishing conveniences
    "extract_publication_metadata",
    "generate_citation_bibtex",
    "publish_to_zenodo",
]

