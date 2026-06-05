"""Documentation validation subpackage."""

from infrastructure.validation.docs.accuracy import check_links, verify_commands, verify_documentation_accuracy
from infrastructure.validation.docs.completeness import analyze_documentation_completeness
from infrastructure.validation.docs.discovery import (
    discover_documentation,
    discover_project_documentation,
)
from infrastructure.validation.docs.models import DocumentationFile, ScanResults
from infrastructure.validation.docs.public_audit import (
    build_public_documentation_audit,
    format_audit_json,
    format_audit_markdown,
)
from infrastructure.validation.docs.quality import assess_documentation_quality
from infrastructure.validation.docs.scanner import DocumentationScanner
from infrastructure.validation.docs.verification import run_verification_checks

__all__ = [
    "DocumentationFile",
    "DocumentationScanner",
    "ScanResults",
    "analyze_documentation_completeness",
    "assess_documentation_quality",
    "build_public_documentation_audit",
    "check_links",
    "discover_documentation",
    "discover_project_documentation",
    "format_audit_json",
    "format_audit_markdown",
    "run_verification_checks",
    "verify_commands",
    "verify_documentation_accuracy",
]
