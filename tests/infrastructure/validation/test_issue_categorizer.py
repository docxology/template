#!/usr/bin/env python3
"""Tests for issue_categorizer module."""

import pytest

from infrastructure.validation.issue_categorizer import (
    categorize_by_type,
    assign_severity,
    is_false_positive,
    filter_false_positives,
    group_related_issues,
    prioritize_issues,
    generate_issue_summary,
)
from infrastructure.validation.doc_models import (
    LinkIssue,
    AccuracyIssue,
    CompletenessGap,
    QualityIssue
)


class TestIssueCategorizer:
    """Test issue categorization and filtering functionality."""

    def test_categorize_by_type_empty_list(self):
        """Test categorization with empty issue list."""
        result = categorize_by_type([])
        assert isinstance(result, dict)
        assert 'critical' in result
        assert 'error' in result
        assert 'warning' in result
        assert 'info' in result

    def test_categorize_by_type_mixed_issues(self):
        """Test categorization with mixed issue types."""
        issues = [
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="missing.md",
                issue_type="broken_link",
                issue_message="File not found",
                severity="error"
            ),
            AccuracyIssue(
                file="doc.md",
                line=1,
                issue_type="accuracy",
                issue_message="Inaccurate information",
                severity="warning"
            ),
            QualityIssue(
                file="readme.md",
                line=1,
                issue_type="formatting",
                issue_message="Poor formatting",
                severity="info"
            )
        ]

        result = categorize_by_type(issues)

        assert len(result['critical']) == 1  # Link issue (severity='error' -> 'critical')
        assert len(result['warning']) == 1  # Accuracy issue
        assert len(result['info']) == 1  # Quality issue
        assert len(result['broken_links']) == 1  # Link issue type maps to broken_links

    def test_assign_severity_critical(self):
        """Test critical severity assignment."""
        critical_issue = LinkIssue(
            file="test.md",
            line=1,
            link_text="link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found",
            severity="error"
        )

        severity = assign_severity(critical_issue)
        assert severity == "critical"

    def test_assign_severity_error(self):
        """Test error severity assignment."""
        # Create issue without explicit severity to test content-based logic
        class TestIssue:
            def __init__(self):
                self.issue_message = "Invalid reference"

        error_issue = TestIssue()

        severity = assign_severity(error_issue)
        assert severity == "error"

    def test_assign_severity_warning(self):
        """Test warning severity assignment."""
        # Create issue without explicit severity to test content-based logic
        class TestIssue:
            def __init__(self):
                self.issue_message = "Code block path issue"

        warning_issue = TestIssue()

        severity = assign_severity(warning_issue)
        assert severity == "warning"

    def test_assign_severity_info(self):
        """Test info severity assignment."""
        info_issue = QualityIssue(
            file="test.md",
            line=1,
            issue_type="minor",
            issue_message="Minor style issue",  # Avoid 'formatting' keyword
            severity="info"
        )

        severity = assign_severity(info_issue)
        assert severity == "info"

    def test_is_false_positive_mermaid_syntax(self):
        """Test false positive detection for Mermaid diagrams."""
        mermaid_issue = LinkIssue(
            file="diagram.md",
            line=1,
            link_text="link",
            target="generic\nnode",
            issue_type="broken_link",
            issue_message="Invalid link",
            severity="error"
        )

        assert is_false_positive(mermaid_issue) is True

    def test_is_false_positive_latex_references(self):
        """Test false positive detection for LaTeX references."""
        latex_issue = QualityIssue(
            file="manuscript.md",
            line=1,
            issue_type="reference",
            issue_message="\\ref{fig:example} not found",
            severity="error"
        )

        assert is_false_positive(latex_issue) is True

    def test_is_false_positive_code_examples(self):
        """Test false positive detection for code examples."""
        code_issue = QualityIssue(
            file="readme.md",
            line=1,
            issue_type="path",
            issue_message="example.com not found",
            severity="error"
        )

        assert is_false_positive(code_issue) is True

    def test_is_false_positive_template_placeholders(self):
        """Test false positive detection for template placeholders."""
        template_issue = LinkIssue(
            file="template.md",
            line=1,
            link_text="link",
            target="{placeholder}",
            issue_type="broken_link",
            issue_message="Template placeholder",
            severity="error"
        )

        assert is_false_positive(template_issue) is True

    def test_is_false_positive_virtual_env(self):
        """Test false positive detection for virtual environment paths."""
        venv_issue = QualityIssue(
            file="readme.md",
            line=1,
            issue_type="path",
            issue_message=".venv/lib/python not found",
            severity="error"
        )

        assert is_false_positive(venv_issue) is True

    def test_is_false_positive_legitimate_issue(self):
        """Test that legitimate issues are not marked as false positives."""
        real_issue = LinkIssue(
            file="readme.md",
            line=1,
            link_text="link",
            target="docs/missing.md",
            issue_type="broken_link",
            issue_message="File docs/missing.md does not exist",
            severity="error"
        )

        assert is_false_positive(real_issue) is False

    def test_filter_false_positives(self):
        """Test filtering false positives from issue list."""
        issues = [
            LinkIssue(file="test.md", line=1, link_text="link", target="generic\nnode", issue_type="broken_link", issue_message="Mermaid artifact", severity="error"),
            LinkIssue(file="readme.md", line=1, link_text="link", target="docs/missing.md", issue_type="broken_link", issue_message="Real missing file", severity="error"),
            QualityIssue(file="manuscript.md", line=1, issue_type="reference", issue_message="\\ref{fig:example}", severity="error")
        ]

        filtered = filter_false_positives(issues)

        # Should only keep the real issue
        assert len(filtered) == 1
        assert "docs/missing.md" in filtered[0].target

    def test_group_related_issues_empty(self):
        """Test grouping with empty issue list."""
        result = group_related_issues([])
        assert result == []

    def test_group_related_issues_same_file(self):
        """Test grouping issues from same file."""
        issues = [
            QualityIssue(file="readme.md", line=10, issue_type="formatting", issue_message="Issue 1", severity="info"),
            QualityIssue(file="readme.md", line=20, issue_type="formatting", issue_message="Issue 2", severity="info"),
            LinkIssue(file="readme.md", line=1, link_text="link", target="missing.md", issue_type="broken_link", issue_message="Issue 3", severity="error")
        ]

        groups = group_related_issues(issues)

        # Should create groups by issue type within files
        assert len(groups) == 2  # Two different issue types
        assert len(groups[0]) == 2  # Two formatting issues
        assert len(groups[1]) == 1  # One link issue

    def test_prioritize_issues(self):
        """Test issue prioritization by severity."""
        issues = [
            QualityIssue(file="test.md", line=1, issue_type="minor", issue_message="Info issue", severity="info"),
            QualityIssue(file="test.md", line=1, issue_type="formatting", issue_message="Warning issue", severity="warning"),
            LinkIssue(file="test.md", line=1, link_text="link", target="missing.md", issue_type="broken_link", issue_message="Critical issue", severity="error")
        ]

        prioritized = prioritize_issues(issues)

        # Critical issues should come first
        assert prioritized[0].severity == "error"
        assert prioritized[1].severity == "warning"
        assert prioritized[2].severity == "info"

    def test_generate_issue_summary(self):
        """Test issue summary generation."""
        issues = [
            LinkIssue(file="test.md", line=1, link_text="link", target="missing.md", issue_type="broken_link", issue_message="Critical", severity="error"),
            QualityIssue(file="test.md", line=1, issue_type="formatting", issue_message="Warning", severity="warning"),
            QualityIssue(file="test.md", line=1, issue_type="minor", issue_message="Info", severity="info")
        ]

        summary = generate_issue_summary(issues)

        assert summary['total'] == 3
        assert summary['by_severity']['critical'] == 1  # Link issue -> critical
        assert summary['by_severity']['error'] == 0
        assert summary['by_severity']['warning'] == 1
        assert summary['by_severity']['info'] == 1
        assert summary['false_positives'] == 0  # No false positives in this set

    def test_generate_issue_summary_with_false_positives(self):
        """Test issue summary with false positives."""
        issues = [
            LinkIssue(file="test.md", line=1, link_text="link", target="generic\nnode", issue_type="broken_link", issue_message="Mermaid", severity="error"),
            LinkIssue(file="test.md", line=1, link_text="link", target="missing.md", issue_type="broken_link", issue_message="Real issue", severity="error")
        ]

        summary = generate_issue_summary(issues)

        assert summary['total'] == 2
        assert summary['false_positives'] == 1

    def test_issue_text_extraction(self):
        """Test text extraction from different issue types."""
        from infrastructure.validation.issue_categorizer import _get_issue_text

        # Test LinkIssue
        link_issue = LinkIssue(
            file="test.md",
            line=1,
            link_text="link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found"
        )
        assert _get_issue_text(link_issue) == "File not found"

        # Test QualityIssue without issue_message
        quality_issue = QualityIssue(
            file="test.md",
            line=1,
            issue_type="formatting",
            issue_message="Poor format"
        )
        assert _get_issue_text(quality_issue) == "Poor format"

        # Test fallback
        class MockIssue:
            pass

        mock_issue = MockIssue()
        assert _get_issue_text(mock_issue) == str(mock_issue)