#!/usr/bin/env python3
"""Issue categorization and filtering for audit results.

This module provides intelligent categorization of audit issues, severity assignment,
false positive filtering, and issue grouping for better analysis and reporting.
"""

from __future__ import annotations

import re
from typing import Dict, List, Union

from infrastructure.validation.doc_models import (
    LinkIssue,
    AccuracyIssue,
    CompletenessGap,
    QualityIssue
)

# Type alias for any issue type
Issue = Union[LinkIssue, AccuracyIssue, CompletenessGap, QualityIssue]


def categorize_by_type(issues: List[Issue]) -> Dict[str, List[Issue]]:
    """Categorize issues by their type and severity.

    Args:
        issues: List of issues from any validation module

    Returns:
        Dictionary mapping category names to lists of issues
    """
    categories = {
        'critical': [],
        'error': [],
        'warning': [],
        'info': [],
        'broken_links': [],
        'missing_files': [],
        'invalid_references': [],
        'code_issues': [],
        'formatting_issues': [],
        'false_positives': []
    }

    for issue in issues:
        # Categorize by severity first
        severity = assign_severity(issue)
        categories[severity].append(issue)

        # Then categorize by type
        issue_type = _get_issue_type(issue)
        # Map issue types to category names
        type_mapping = {
            'link_issue': 'broken_links',
            'broken_link': 'broken_links',  # Also map the actual issue_type from LinkIssue
            'accuracy_issue': 'invalid_references',
            'quality_issue': 'code_issues',
            'completeness_gap': 'missing_files'
        }
        category_key = type_mapping.get(issue_type, issue_type)
        if category_key in categories:
            categories[category_key].append(issue)

        # Check for false positives
        if is_false_positive(issue):
            categories['false_positives'].append(issue)

    return categories


def assign_severity(issue: Issue) -> str:
    """Assign severity level to an issue.

    Args:
        issue: Issue to evaluate

    Returns:
        Severity level: 'critical', 'error', 'warning', or 'info'
    """
    # Check explicit severity first (respect user's explicit settings)
    if hasattr(issue, 'severity'):
        severity = issue.severity.lower()
        if severity == 'error':
            return 'critical'  # Map error to critical for consistency
        elif severity in ['critical', 'warning', 'info']:
            return severity

    # Fallback to content-based severity analysis
    issue_text = _get_issue_text(issue).lower()

    # Critical issues
    if any(keyword in issue_text for keyword in [
        'file not found', 'does not exist', 'critical', 'broken import',
        'module not found', 'syntax error'
    ]):
        return 'critical'

    # Error issues
    if any(keyword in issue_text for keyword in [
        'invalid reference', 'broken link', 'anchor not found',
        'missing file', 'path error', 'import error'
    ]):
        return 'error'

    # Warning issues
    if any(keyword in issue_text for keyword in [
        'code block', 'directory structure', 'placeholder',
        'formatting', 'consistency', 'recommendation'
    ]):
        return 'warning'

    # Info issues - minor or informational
    return 'info'


def is_false_positive(issue: Issue) -> bool:
    """Determine if an issue is likely a false positive.

    Args:
        issue: Issue to evaluate

    Returns:
        True if issue appears to be a false positive
    """
    issue_text = _get_issue_text(issue).lower()
    target = _get_issue_target(issue).lower() if hasattr(issue, 'target') else ''

    # Mermaid diagram artifacts (common false positive)
    if '\\n' in target or 'generic' in target:
        return True

    # LaTeX cross-references (valid in manuscripts)
    if any(ref in issue_text for ref in ['\\ref{fig:', '\\ref{sec:', '\\ref{eq:', '\\eqref{']):
        return True

    # Markdown table formatting artifacts
    if 'infrastructure/agents.md]' in target or 'infrastructure/readme.md]' in target:
        return True

    # Virtual environment references
    if '.venv/' in target or '/.venv/' in target or '.venv/' in issue_text:
        return True

    # Code block examples that are intentionally generic
    if any(example in issue_text for example in [
        'example.com', 'your-domain.com', 'path/to/',
        'placeholder', 'template', 'sample', 'your_'
    ]):
        return True

    # Template placeholders that can't be resolved
    if '{' in target and '}' in target:
        return True

    # Common documentation patterns that are valid
    if target in ['infrastructure/', 'scripts/', 'projects/project/']:
        return True

    return False


def filter_false_positives(issues: List[Issue]) -> List[Issue]:
    """Filter out false positive issues from the list.

    Args:
        issues: List of issues to filter

    Returns:
        List with false positives removed
    """
    return [issue for issue in issues if not is_false_positive(issue)]


def group_related_issues(issues: List[Issue]) -> List[List[Issue]]:
    """Group related issues together for better analysis.

    Args:
        issues: List of issues to group

    Returns:
        List of issue groups (each group is a list of related issues)
    """
    if not issues:
        return []

    # Group by file first
    file_groups = {}
    for issue in issues:
        file_key = _get_issue_file(issue)
        if file_key not in file_groups:
            file_groups[file_key] = []
        file_groups[file_key].append(issue)

    # Within each file, group by issue type
    groups = []
    for file_issues in file_groups.values():
        type_groups = {}
        for issue in file_issues:
            issue_type = _get_issue_type(issue)
            if issue_type not in type_groups:
                type_groups[issue_type] = []
            type_groups[issue_type].append(issue)

        groups.extend(type_groups.values())

    return groups


def prioritize_issues(issues: List[Issue]) -> List[Issue]:
    """Sort issues by priority (severity, then type).

    Args:
        issues: List of issues to prioritize

    Returns:
        Sorted list with highest priority issues first
    """
    def sort_key(issue: Issue) -> tuple:
        severity = assign_severity(issue)
        severity_order = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}
        issue_type = _get_issue_type(issue)

        return (severity_order.get(severity, 4), issue_type, _get_issue_file(issue))

    return sorted(issues, key=sort_key)


def generate_issue_summary(issues: List[Issue]) -> Dict[str, int]:
    """Generate a summary of issues by category and severity.

    Args:
        issues: List of issues to summarize

    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total': len(issues),
        'by_severity': {'critical': 0, 'error': 0, 'warning': 0, 'info': 0},
        'by_type': {},
        'false_positives': 0
    }

    for issue in issues:
        severity = assign_severity(issue)
        summary['by_severity'][severity] += 1

        issue_type = _get_issue_type(issue)
        summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1

        if is_false_positive(issue):
            summary['false_positives'] += 1

    return summary


def _get_issue_text(issue: Issue) -> str:
    """Extract text content from any issue type."""
    if hasattr(issue, 'issue_message'):
        return issue.issue_message
    elif hasattr(issue, 'description'):
        return issue.description
    elif hasattr(issue, 'text'):
        return issue.text
    return str(issue)


def _get_issue_target(issue: Issue) -> str:
    """Extract target/path from any issue type."""
    if hasattr(issue, 'target'):
        return issue.target
    return ""


def _get_issue_file(issue: Issue) -> str:
    """Extract file path from any issue type."""
    if hasattr(issue, 'file'):
        return issue.file
    elif hasattr(issue, 'source_file'):
        return issue.source_file
    return "unknown"


def _get_issue_type(issue: Issue) -> str:
    """Extract issue type from any issue type."""
    if hasattr(issue, 'issue_type'):
        return issue.issue_type
    elif isinstance(issue, LinkIssue):
        return 'link_issue'
    elif isinstance(issue, AccuracyIssue):
        return 'accuracy_issue'
    elif isinstance(issue, CompletenessGap):
        return 'completeness_gap'
    elif isinstance(issue, QualityIssue):
        return 'quality_issue'
    return 'unknown'


def validate_issue_patterns() -> Dict[str, List[str]]:
    """Return validation patterns for different issue types.

    Returns:
        Dictionary mapping issue types to lists of validation patterns
    """
    return {
        'broken_links': [
            r'\[([^\]]+)\]\(([^)]+)\)',  # Markdown links
            r'<a href="([^"]+)">',        # HTML links
        ],
        'file_references': [
            r'`([^`]+)`',                 # Inline code
            r'```[\s\S]*?```',           # Code blocks
            r"'([^']+)'",                # Single quotes
            r'"([^"]+)"',                # Double quotes
        ],
        'latex_references': [
            r'\\ref\{([^}]+)\}',          # LaTeX references
            r'\\eqref\{([^}]+)\}',        # LaTeX equation references
            r'\\cite\{([^}]+)\}',         # LaTeX citations
        ],
        'anchor_links': [
            r'#([a-zA-Z][\w-]*)',       # Markdown anchors
        ]
    }