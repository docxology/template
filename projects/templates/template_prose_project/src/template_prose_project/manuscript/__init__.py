"""Manuscript-facing modules for the prose-review workflow: substitution
variables and markdown review-report assembly.

These modules are re-exported from ``template_prose_project`` for
backwards compatibility; import them from the package root.
"""

from .manuscript_variables import (
    ManuscriptVariables,
    compute_variables,
    load_report_payload,
    substitute_in_text,
    write_variables,
)
from .report import write_review_report

__all__ = [
    "ManuscriptVariables",
    "compute_variables",
    "load_report_payload",
    "substitute_in_text",
    "write_variables",
    "write_review_report",
]
