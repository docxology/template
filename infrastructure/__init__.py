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

from __future__ import annotations

__version__ = "2.0.0"
__layer__ = "infrastructure"

# Import commonly-used items for convenient access
# Core utilities are mandatory — everything else degrades gracefully
try:
    # Core (always available) — import from submodules directly
    from .core.exceptions import (  # type: ignore
        BuildError,
        ConfigurationError,
        TemplateError,
        ValidationError,
    )
    from .core.config_loader import load_config  # type: ignore
    from .core.logging_utils import (  # type: ignore
        get_logger,
        log_operation,
        log_timing,
        setup_logger,
    )
except ImportError as _core_e:
    raise RuntimeError(f"infrastructure core import failed: {_core_e}") from _core_e

# Optional subpackages — imported for convenience but not required
import warnings as _warnings

try:
    from .documentation import FigureManager, ImageManager, MarkdownIntegration
except ImportError as _doc_e:
    _warnings.warn(f"Documentation subpackage unavailable: {_doc_e}", ImportWarning, stacklevel=2)

try:
    from .publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
        publish_to_zenodo,
    )
except ImportError as _pub_e:
    _warnings.warn(f"Publishing subpackage unavailable: {_pub_e}", ImportWarning, stacklevel=2)

try:
    from .reporting import generate_pipeline_report, get_error_aggregator
except ImportError as _rep_e:
    _warnings.warn(f"Reporting subpackage unavailable: {_rep_e}", ImportWarning, stacklevel=2)

try:
    from .validation import validate_markdown, validate_pdf_rendering, verify_output_integrity
except ImportError as _val_e:
    _warnings.warn(f"Validation subpackage unavailable: {_val_e}", ImportWarning, stacklevel=2)

# Steganography — optional, only loaded when dependencies are available
try:
    from .steganography import SteganographyConfig, SteganographyProcessor, process_pdf
except ImportError as _steg_e:
    import warnings
    warnings.warn(f"Steganography dependencies unavailable: {_steg_e}", ImportWarning, stacklevel=2)

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
