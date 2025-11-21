"""Infrastructure layer - Build, validation, and development tools.

This package contains reusable infrastructure for building, validating, and
managing research projects. These are generic utilities that apply to any
project using this template.

Modules:
    build_verifier: Build process verification and artifact validation
    integrity: File integrity checking and cross-reference validation
    quality_checker: Document quality metrics and academic standards
    reproducibility: Build reproducibility tracking and environment capture
    publishing: Academic publishing workflow assistance
    pdf_validator: PDF rendering quality validation
    glossary_gen: Automatic API documentation generation
    markdown_integration: Figure insertion and cross-reference management
    figure_manager: Automatic figure numbering and LaTeX generation
    image_manager: Image file management and insertion
    markdown_validator: Markdown validation utilities (NEW)
    config_loader: Configuration loading and formatting (NEW)
"""

__version__ = "1.0.0"
__layer__ = "infrastructure"

# Import core functions for convenient access
try:
    from .build_verifier import verify_build_artifacts, verify_build_reproducibility
    from .integrity import verify_file_integrity, verify_cross_references
    from .quality_checker import analyze_document_quality
    from .pdf_validator import validate_pdf_rendering
except ImportError:
    # Graceful fallback if imports fail
    pass

__all__ = [
    "build_verifier",
    "integrity",
    "quality_checker",
    "reproducibility",
    "publishing",
    "pdf_validator",
    "glossary_gen",
    "markdown_integration",
    "figure_manager",
    "image_manager",
    "markdown_validator",
    "config_loader",
]

