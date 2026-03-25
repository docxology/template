"""Documentation validation subpackage."""

from infrastructure.validation.docs.accuracy import check_links, run_accuracy_phase, verify_commands
from infrastructure.validation.docs.completeness import run_completeness_phase
from infrastructure.validation.docs.discovery import discover_markdown_files, discover_project_documentation, run_discovery_phase
from infrastructure.validation.docs.models import DocumentationFile, ScanResults
from infrastructure.validation.docs.quality import run_quality_phase
from infrastructure.validation.docs.scanner import DocumentationScanner

__all__ = [
    "DocumentationFile",
    "DocumentationScanner",
    "ScanResults",
    "check_links",
    "discover_markdown_files",
    "discover_project_documentation",
    "run_accuracy_phase",
    "run_completeness_phase",
    "run_discovery_phase",
    "run_quality_phase",
    "verify_commands",
]
