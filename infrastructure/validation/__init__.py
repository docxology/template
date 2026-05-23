"""Validation package — document, link, integrity, and output quality tools.

Import from submodules for new code; this module re-exports the stable
pipeline-facing surface documented in ``infrastructure/validation/AGENTS.md``.
"""

from .content import (
    extract_text_from_pdf,
    find_markdown_files,
    scan_for_issues,
    validate_citations,
    validate_figure_registry,
    validate_images,
    validate_markdown,
    validate_math,
    validate_pandoc_pitfalls,
    validate_pdf_rendering,
    validate_refs,
)
from .integrity import (
    LinkValidator,
    generate_integrity_report,
    verify_academic_standards,
    verify_cross_references,
    verify_data_consistency,
    verify_file_integrity,
    verify_output_integrity,
)
from .output import (
    validate_copied_outputs,
    validate_output_structure,
)
from .repo import (
    assign_severity,
    categorize_by_type,
    filter_false_positives,
    generate_audit_report,
    generate_issue_summary,
    group_related_issues,
    is_false_positive,
    prioritize_issues,
    run_comprehensive_audit,
)

__all__ = [
    "validate_pdf_rendering",
    "extract_text_from_pdf",
    "scan_for_issues",
    "validate_markdown",
    "find_markdown_files",
    "validate_images",
    "validate_refs",
    "validate_math",
    "validate_citations",
    "validate_pandoc_pitfalls",
    "validate_figure_registry",
    "verify_file_integrity",
    "verify_cross_references",
    "verify_data_consistency",
    "verify_academic_standards",
    "verify_output_integrity",
    "generate_integrity_report",
    "LinkValidator",
    "run_comprehensive_audit",
    "generate_audit_report",
    "categorize_by_type",
    "assign_severity",
    "is_false_positive",
    "filter_false_positives",
    "group_related_issues",
    "prioritize_issues",
    "generate_issue_summary",
    "validate_copied_outputs",
    "validate_output_structure",
]
