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

# Core utilities — always available, used throughout the codebase
try:
    from .core.exceptions import (  # type: ignore
        BuildError,
        ConfigurationError,
        TemplateError,
        ValidationError,
    )
    from .core.config_loader import load_config  # type: ignore
    from .core.logging_utils import get_logger  # type: ignore
except ImportError as _core_e:
    raise RuntimeError(f"infrastructure core import failed: {_core_e}") from _core_e

# All other symbols should be imported from their subpackages directly:
#   from infrastructure.reporting import generate_pipeline_report
#   from infrastructure.validation import validate_pdf_rendering
#   from infrastructure.documentation import FigureManager

__all__ = [
    "TemplateError",
    "ConfigurationError",
    "ValidationError",
    "BuildError",
    "load_config",
    "get_logger",
]
