"""Validation module - Quality & validation tools.

This module contains utilities for validating documents, PDFs, markdown files,
and ensuring data integrity across the research project.

Modules:
    pdf_validator: PDF rendering validation
    markdown_validator: Markdown file validation
    integrity: File integrity and cross-reference validation
    check_links: Documentation link verification
    doc_scanner: Comprehensive documentation scanning
    repo_scanner: Repository-wide accuracy and completeness scanning
"""

from .pdf_validator import validate_pdf_rendering, extract_text_from_pdf, scan_for_issues
from .markdown_validator import (
    validate_markdown,
    find_markdown_files,
    validate_images,
    validate_refs,
    validate_math,
)
from .integrity import (
    verify_file_integrity,
    verify_cross_references,
    verify_data_consistency,
    verify_academic_standards,
    verify_output_integrity,
    generate_integrity_report,
)
from .figure_validator import validate_figure_registry
from .output_validator import (
    validate_copied_outputs,
    validate_output_structure,
)
from .link_validator import LinkValidator

__all__ = [
    "validate_pdf_rendering",
    "extract_text_from_pdf",
    "scan_for_issues",
    "validate_markdown",
    "find_markdown_files",
    "validate_images",
    "validate_refs",
    "validate_math",
    "verify_file_integrity",
    "verify_cross_references",
    "verify_data_consistency",
    "verify_academic_standards",
    "verify_output_integrity",
    "generate_integrity_report",
    "validate_figure_registry",
    "validate_copied_outputs",
    "validate_output_structure",
    "LinkValidator",
]

