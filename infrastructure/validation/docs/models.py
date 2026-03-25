"""Data models for documentation scanning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class DocumentationFile:
    """Represents a documentation file with metadata."""

    path: str
    relative_path: str
    directory: str
    name: str
    category: str = ""
    word_count: int = 0
    line_count: int = 0
    has_links: bool = False
    has_code_blocks: bool = False
    last_modified: str | None = None


@dataclass
class LinkIssue:
    """Represents a link or reference issue."""

    file: str
    line: int
    link_text: str
    target: str
    issue_type: str
    issue_message: str
    severity: str = "error"


@dataclass
class AccuracyIssue:
    """Represents an accuracy issue in documentation.

    .. deprecated::
        Legacy shape — new code should use ``ScanAccuracyIssue`` from repo_scanner.
        Planned for removal: 2026-09-01. Migrate callers in doc_accuracy.py,
        audit_orchestrator.py, and issue_categorizer.py to ScanAccuracyIssue.
    """

    file: str
    line: int
    issue_type: str
    issue_message: str
    severity: str = "error"


@dataclass
class ScanAccuracyIssue:
    """Accuracy issue found during repository-wide scanning (repo_scanner)."""

    category: str
    severity: str
    file: str
    line: int = 0
    message: str = ""
    details: str = ""

@dataclass
class CompletenessGap:
    """Represents a documentation completeness gap."""

    category: str
    item: str
    description: str
    severity: str = "warning"


@dataclass
class QualityIssue:
    """Represents a documentation quality issue."""

    file: str
    line: int
    issue_type: str
    issue_message: str
    severity: str = "info"


@dataclass
class ScanResults:
    """Container for doc-scanner scan results (doc_scanner.py output only).

    Note: This is distinct from ``RepoScanResults`` (``repo/models.py``), which
    holds accuracy and completeness results from repository-wide scanning.
    Use ``ScanResults`` for documentation file enumeration; use
    ``RepoScanResults`` for accuracy/completeness audit results.
    """

    scan_date: str
    total_files: int = 0
    documentation_files: list[DocumentationFile] = field(default_factory=list)
    link_issues: list[LinkIssue] = field(default_factory=list)
    accuracy_issues: list[AccuracyIssue] = field(default_factory=list)
    completeness_gaps: list[CompletenessGap] = field(default_factory=list)
    quality_issues: list[QualityIssue] = field(default_factory=list)
    improvements_made: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
    scanned_files: int = 0
    scan_duration: float = 0.0
