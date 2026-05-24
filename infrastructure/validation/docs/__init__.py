"""Documentation validation subpackage."""

from infrastructure.validation.docs.accuracy import check_links, verify_commands, verify_documentation_accuracy
from infrastructure.validation.docs.completeness import analyze_documentation_completeness
from infrastructure.validation.docs.discovery import (
    discover_documentation,
    discover_project_documentation,
)
from infrastructure.validation.docs.models import DocumentationFile, ScanResults
from infrastructure.validation.docs.quality import assess_documentation_quality
from infrastructure.validation.docs.scanner import DocumentationScanner
from infrastructure.validation.docs.verification import run_verification_checks

__all__ = [
    "DocumentationFile",
    "DocumentationScanner",
    "ScanResults",
    "analyze_documentation_completeness",
    "assess_documentation_quality",
    "check_links",
    "discover_documentation",
    "discover_project_documentation",
    "run_verification_checks",
    "verify_commands",
    "verify_documentation_accuracy",
]
