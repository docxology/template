"""Dataclasses for repository-wide scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from infrastructure.validation.docs.models import CompletenessGap, ScanAccuracyIssue


@dataclass
class RepoScanResults:
    """Container for repository scan results.

    Attributes:
        accuracy_issues: Import verification failures, missing commands, etc.
        completeness_gaps: Missing documentation, tests, or thin-orchestrator violations.
        statistics: Aggregate metrics produced by each scan phase.
    """

    accuracy_issues: list[ScanAccuracyIssue] = field(default_factory=list)
    completeness_gaps: list[CompletenessGap] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)
