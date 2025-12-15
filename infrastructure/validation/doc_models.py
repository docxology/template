"""Data models for documentation scanning."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    last_modified: Optional[str] = None


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
    """Represents an accuracy issue in documentation."""
    file: str
    line: int
    issue_type: str
    issue_message: str
    severity: str = "error"


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
    """Container for all scan results."""
    scan_date: str
    total_files: int = 0
    documentation_files: List[DocumentationFile] = field(default_factory=list)
    link_issues: List[LinkIssue] = field(default_factory=list)
    accuracy_issues: List[AccuracyIssue] = field(default_factory=list)
    completeness_gaps: List[CompletenessGap] = field(default_factory=list)
    quality_issues: List[QualityIssue] = field(default_factory=list)
    improvements_made: List[Dict] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)













