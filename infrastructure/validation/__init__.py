"""Validation module - Quality & validation tools.

This module contains utilities for validating documents, PDFs, markdown files,
and ensuring data integrity across the research project.

## Module groups (22 files — logical namespaces within the flat package)

**Content validators** (validate specific file types):
    pdf_validator: PDF rendering validation
    markdown_validator: Markdown file validation
    figure_validator: Figure registry validation

**Integrity & links**:
    integrity: File integrity and cross-reference validation
    link_validator: Markdown link resolution and checking
    check_links: Documentation link verification CLI

**Documentation scanning**:
    doc_scanner: Comprehensive documentation scanning
    doc_discovery: Documentation file discovery utilities
    doc_models: Data models for documentation scanning

**Repository-wide scanning**:
    repo_scanner: Repository accuracy and completeness scanning
    audit_orchestrator: Comprehensive multi-module audit coordination
    issue_categorizer: Issue categorization and filtering

**CLI entry points**:
    cli: Unified validation CLI interface
    validate_markdown_cli: Standalone markdown validation script
    validate_pdf_cli: Standalone PDF validation script

**Output validation**:
    output_validator: Pipeline output validation
    (output statistics live in infrastructure/reporting/output_reporter.py)
"""

from __future__ import annotations

# Content validators
from .figure_validator import validate_figure_registry
from .markdown_validator import (
    find_markdown_files,
    validate_images,
    validate_markdown,
    validate_math,
    validate_refs,
)
from .pdf_validator import extract_text_from_pdf, scan_for_issues, validate_pdf_rendering

# Integrity & links
from .integrity import (
    generate_integrity_report,
    verify_academic_standards,
    verify_cross_references,
    verify_data_consistency,
    verify_file_integrity,
    verify_output_integrity,
)
from .link_validator import LinkValidator

# Repository-wide scanning
from .audit_orchestrator import generate_audit_report, run_comprehensive_audit
from .issue_categorizer import (
    assign_severity,
    categorize_by_type,
    filter_false_positives,
    generate_issue_summary,
    group_related_issues,
    is_false_positive,
    prioritize_issues,
)

# Output validation
from .output_validator import validate_copied_outputs, validate_output_structure

# The validation package intentionally exports a broad surface because pipeline scripts
# import a variety of validators from a single entry point rather than from individual
# submodules. Sibling packages (rendering, documentation) have narrower entry points
# because their callers use more targeted imports.
__all__ = [
    # Content validators
    "validate_pdf_rendering",
    "extract_text_from_pdf",
    "scan_for_issues",
    "validate_markdown",
    "find_markdown_files",
    "validate_images",
    "validate_refs",
    "validate_math",
    "validate_figure_registry",
    # Integrity & links
    "verify_file_integrity",
    "verify_cross_references",
    "verify_data_consistency",
    "verify_academic_standards",
    "verify_output_integrity",
    "generate_integrity_report",
    "LinkValidator",
    # Repository-wide scanning
    "run_comprehensive_audit",
    "generate_audit_report",
    "categorize_by_type",
    "assign_severity",
    "is_false_positive",
    "filter_false_positives",
    "group_related_issues",
    "prioritize_issues",
    "generate_issue_summary",
    # Output validation
    "validate_copied_outputs",
    "validate_output_structure",
]
