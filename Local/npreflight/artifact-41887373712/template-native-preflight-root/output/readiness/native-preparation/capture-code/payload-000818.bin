"""Validation package — document, link, integrity, and output quality tools.

Import from submodules for new code; this module re-exports the stable
pipeline-facing surface documented in ``infrastructure/validation/AGENTS.md``.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

# Resolve each stable export only when requested; submodule imports stay composable.
_EXPORTS = {
    "discover_markdown_files": (".content", "discover_markdown_files"),
    "extract_text_from_pdf": (".content", "extract_text_from_pdf"),
    "scan_for_issues": (".content", "scan_for_issues"),
    "validate_citations": (".content", "validate_citations"),
    "validate_figure_registry": (".content", "validate_figure_registry"),
    "validate_images": (".content", "validate_images"),
    "validate_markdown": (".content", "validate_markdown"),
    "validate_math": (".content", "validate_math"),
    "validate_pandoc_pitfalls": (".content", "validate_pandoc_pitfalls"),
    "validate_pdf_rendering": (".content", "validate_pdf_rendering"),
    "validate_refs": (".content", "validate_refs"),
    "LinkValidator": (".integrity", "LinkValidator"),
    "generate_integrity_report": (".integrity", "generate_integrity_report"),
    "verify_academic_standards": (".integrity", "verify_academic_standards"),
    "verify_cross_references": (".integrity", "verify_cross_references"),
    "verify_data_consistency": (".integrity", "verify_data_consistency"),
    "verify_file_integrity": (".integrity", "verify_file_integrity"),
    "verify_output_integrity": (".integrity", "verify_output_integrity"),
    "validate_copied_outputs": (".output", "validate_copied_outputs"),
    "validate_output_structure": (".output", "validate_output_structure"),
    "assign_severity": (".repo", "assign_severity"),
    "categorize_by_type": (".repo", "categorize_by_type"),
    "filter_false_positives": (".repo", "filter_false_positives"),
    "generate_audit_report": (".repo", "generate_audit_report"),
    "generate_issue_summary": (".repo", "generate_issue_summary"),
    "group_related_issues": (".repo", "group_related_issues"),
    "is_false_positive": (".repo", "is_false_positive"),
    "prioritize_issues": (".repo", "prioritize_issues"),
    "run_comprehensive_audit": (".repo", "run_comprehensive_audit"),
}

if TYPE_CHECKING:
    from .content import (
        discover_markdown_files,
        extract_text_from_pdf,
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
    "discover_markdown_files",
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


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXPORTS.keys())
