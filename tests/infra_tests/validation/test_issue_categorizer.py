#!/usr/bin/env python3
"""Tests for issue_categorizer module."""

from infrastructure.validation.docs.models import (
    CompletenessGap,
    LinkIssue,
    QualityIssue,
    ScanAccuracyIssue,
)
from infrastructure.validation.repo.issue_categorizer import (
    ISSUE_TYPE_COMPLETENESS,
    _get_issue_file,
    _get_issue_target,
    _get_issue_text,
    _get_issue_type,
    assign_severity,
    categorize_by_type,
    filter_false_positives,
    generate_issue_summary,
    get_severity_flag,
    group_related_issues,
    is_directory_reference,
    is_false_positive,
    prioritize_issues,
    validate_issue_patterns,
)

import pytest


class TestIssueCategorizer:
    """Test issue categorization and filtering functionality."""

    def test_categorize_by_type_empty_list(self):
        """Test categorization with empty issue list."""
        result = categorize_by_type([])
        assert isinstance(result, dict)
        assert "critical" in result
        assert "error" in result
        assert "warning" in result
        assert "info" in result

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
                severity="error",
            ),
            ScanAccuracyIssue(
                category="accuracy",
                severity="warning",
                file="doc.md",
                line=1,
                message="Inaccurate information",
            ),
            QualityIssue(
                file="readme.md",
                line=1,
                issue_type="formatting",
                issue_message="Poor formatting",
                severity="info",
            ),
        ]

        result = categorize_by_type(issues)

        assert len(result["critical"]) == 1  # Link issue (severity='error' -> 'critical')
        assert len(result["warning"]) == 1  # Accuracy issue
        assert len(result["info"]) == 1  # Quality issue
        assert len(result["broken_links"]) == 1  # Link issue type maps to broken_links

    def test_assign_severity_critical(self):
        """Test critical severity assignment."""
        critical_issue = LinkIssue(
            file="test.md",
            line=1,
            link_text="link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found",
            severity="error",
        )

        severity = assign_severity(critical_issue)
        assert severity == "critical"

    def test_assign_severity_error(self):
        """Explicit severity='error' maps to 'critical' (error is promoted)."""
        error_issue = QualityIssue(
            file="test.md",
            line=1,
            issue_type="quality",
            issue_message="Invalid reference in document",
            severity="error",
        )
        severity = assign_severity(error_issue)
        assert severity == "critical"

    def test_assign_severity_warning(self):
        """Explicit severity='warning' passes through unchanged."""
        warning_issue = QualityIssue(
            file="test.md",
            line=1,
            issue_type="quality",
            issue_message="Code block path issue",
            severity="warning",
        )
        severity = assign_severity(warning_issue)
        assert severity == "warning"

    def test_assign_severity_info(self):
        """Test info severity assignment."""
        info_issue = QualityIssue(
            file="test.md",
            line=1,
            issue_type="minor",
            issue_message="Minor style issue",  # Avoid 'formatting' keyword
            severity="info",
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
            severity="error",
        )

        assert is_false_positive(mermaid_issue) is True

    def test_is_false_positive_latex_references(self):
        """Test false positive detection for LaTeX references."""
        latex_issue = QualityIssue(
            file="manuscript.md",
            line=1,
            issue_type="reference",
            issue_message="\\ref{fig:example} not found",
            severity="error",
        )

        assert is_false_positive(latex_issue) is True

    def test_is_false_positive_code_examples(self):
        """Test false positive detection for code examples."""
        code_issue = QualityIssue(
            file="readme.md",
            line=1,
            issue_type="path",
            issue_message="example.com not found",
            severity="error",
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
            severity="error",
        )

        assert is_false_positive(template_issue) is True

    def test_is_false_positive_virtual_env(self):
        """Test false positive detection for virtual environment paths."""
        venv_issue = QualityIssue(
            file="readme.md",
            line=1,
            issue_type="path",
            issue_message=".venv/lib/python not found",
            severity="error",
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
            severity="error",
        )

        assert is_false_positive(real_issue) is False

    def test_filter_false_positives(self):
        """Test filtering false positives from issue list."""
        issues = [
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="generic\nnode",
                issue_type="broken_link",
                issue_message="Mermaid artifact",
                severity="error",
            ),
            LinkIssue(
                file="readme.md",
                line=1,
                link_text="link",
                target="docs/missing.md",
                issue_type="broken_link",
                issue_message="Real missing file",
                severity="error",
            ),
            QualityIssue(
                file="manuscript.md",
                line=1,
                issue_type="reference",
                issue_message="\\ref{fig:example}",
                severity="error",
            ),
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
            QualityIssue(
                file="readme.md",
                line=10,
                issue_type="formatting",
                issue_message="Issue 1",
                severity="info",
            ),
            QualityIssue(
                file="readme.md",
                line=20,
                issue_type="formatting",
                issue_message="Issue 2",
                severity="info",
            ),
            LinkIssue(
                file="readme.md",
                line=1,
                link_text="link",
                target="missing.md",
                issue_type="broken_link",
                issue_message="Issue 3",
                severity="error",
            ),
        ]

        groups = group_related_issues(issues)

        # Should create groups by issue type within files
        assert len(groups) == 2  # Two different issue types
        assert len(groups[0]) == 2  # Two formatting issues
        assert len(groups[1]) == 1  # One link issue

    def test_prioritize_issues(self):
        """Test issue prioritization by severity."""
        issues = [
            QualityIssue(
                file="test.md",
                line=1,
                issue_type="minor",
                issue_message="Info issue",
                severity="info",
            ),
            QualityIssue(
                file="test.md",
                line=1,
                issue_type="formatting",
                issue_message="Warning issue",
                severity="warning",
            ),
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="missing.md",
                issue_type="broken_link",
                issue_message="Critical issue",
                severity="error",
            ),
        ]

        prioritized = prioritize_issues(issues)

        # Critical issues should come first
        assert prioritized[0].severity == "error"
        assert prioritized[1].severity == "warning"
        assert prioritized[2].severity == "info"

    def test_generate_issue_summary(self):
        """Test issue summary generation."""
        issues = [
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="missing.md",
                issue_type="broken_link",
                issue_message="Critical",
                severity="error",
            ),
            QualityIssue(
                file="test.md",
                line=1,
                issue_type="formatting",
                issue_message="Warning",
                severity="warning",
            ),
            QualityIssue(
                file="test.md",
                line=1,
                issue_type="minor",
                issue_message="Info",
                severity="info",
            ),
        ]

        summary = generate_issue_summary(issues)

        assert summary["total"] == 3
        assert summary["by_severity"]["critical"] == 1  # Link issue -> critical
        assert summary["by_severity"]["error"] == 0
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["info"] == 1
        assert summary["false_positives"] == 0  # No false positives in this set

    def test_generate_issue_summary_with_false_positives(self):
        """Test issue summary with false positives."""
        issues = [
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="generic\nnode",
                issue_type="broken_link",
                issue_message="Mermaid",
                severity="error",
            ),
            LinkIssue(
                file="test.md",
                line=1,
                link_text="link",
                target="missing.md",
                issue_type="broken_link",
                issue_message="Real issue",
                severity="error",
            ),
        ]

        summary = generate_issue_summary(issues)

        assert summary["total"] == 2
        assert summary["false_positives"] == 1

    def test_issue_text_extraction(self):
        """Test text extraction from different issue types."""
        from infrastructure.validation.repo.issue_categorizer import _get_issue_text

        # Test LinkIssue
        link_issue = LinkIssue(
            file="test.md",
            line=1,
            link_text="link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found",
        )
        assert _get_issue_text(link_issue) == "File not found"

        # Test QualityIssue without issue_message
        quality_issue = QualityIssue(file="test.md", line=1, issue_type="formatting", issue_message="Poor format")
        assert _get_issue_text(quality_issue) == "Poor format"

        # Test fallback
        class MockIssue:
            pass

        mock_issue = MockIssue()
        assert _get_issue_text(mock_issue) == str(mock_issue)


class TestGetIssueType:
    def test_link_issue(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="y",
            issue_type="broken_link",
            issue_message="msg",
        )
        assert _get_issue_type(issue) == "broken_link"

    def test_quality_issue(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="formatting",
            issue_message="msg",
        )
        assert _get_issue_type(issue) == "formatting"

    def test_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="accuracy",
            severity="warning",
            file="t.md",
            line=1,
            message="msg",
        )
        assert _get_issue_type(issue) == "accuracy"

    def test_completeness_gap(self):
        issue = CompletenessGap(
            category="docs",
            item="README",
            description="Missing README",
        )
        assert _get_issue_type(issue) == ISSUE_TYPE_COMPLETENESS

    def test_unexpected_type_raises(self):
        with pytest.raises(TypeError, match="Unexpected issue type"):
            _get_issue_type("not an issue")  # type: ignore[arg-type]


class TestGetIssueFile:
    def test_link_issue(self):
        issue = LinkIssue(
            file="readme.md",
            line=1,
            link_text="x",
            target="y",
            issue_type="broken",
            issue_message="msg",
        )
        assert _get_issue_file(issue) == "readme.md"

    def test_quality_issue(self):
        issue = QualityIssue(file="q.md", line=1, issue_type="t", issue_message="m")
        assert _get_issue_file(issue) == "q.md"

    def test_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="c",
            severity="w",
            file="a.md",
            line=1,
            message="m",
        )
        assert _get_issue_file(issue) == "a.md"

    def test_completeness_gap(self):
        issue = CompletenessGap(category="docs", item="README", description="d")
        assert _get_issue_file(issue) == "unknown"


class TestGetIssueTarget:
    def test_link_issue(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="docs/guide.md",
            issue_type="broken",
            issue_message="msg",
        )
        assert _get_issue_target(issue) == "docs/guide.md"

    def test_non_link_issue(self):
        issue = QualityIssue(file="t.md", line=1, issue_type="t", issue_message="m")
        assert _get_issue_target(issue) == ""


class TestGetIssueText:
    def test_scan_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="c",
            severity="w",
            file="f.md",
            line=1,
            message="the error message",
        )
        assert _get_issue_text(issue) == "the error message"

    def test_completeness_gap(self):
        issue = CompletenessGap(category="docs", item="README", description="missing docs")
        assert _get_issue_text(issue) == "missing docs"


class TestAssignSeverity:
    def test_explicit_critical(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="t",
            issue_message="msg",
            severity="critical",
        )
        assert assign_severity(issue) == "critical"

    def test_content_based_critical_via_completeness(self):
        # CompletenessGap has severity="warning" by default but assign_severity
        # maps it through the explicit severity check. Test content-based by
        # using a completeness gap with severity not in the explicit map.
        issue = CompletenessGap(
            category="docs",
            item="README",
            description="syntax error in file",
            severity="unknown",
        )
        assert assign_severity(issue) == "critical"

    def test_content_based_error_via_completeness(self):
        issue = CompletenessGap(
            category="docs",
            item="x",
            description="broken link found",
            severity="unknown",
        )
        assert assign_severity(issue) == "error"

    def test_content_based_warning_via_completeness(self):
        issue = CompletenessGap(
            category="docs",
            item="x",
            description="placeholder value found",
            severity="unknown",
        )
        assert assign_severity(issue) == "warning"

    def test_content_based_info_fallback(self):
        issue = CompletenessGap(
            category="docs",
            item="x",
            description="some normal text",
            severity="unknown",
        )
        assert assign_severity(issue) == "info"

    def test_quality_issue_default_severity_info(self):
        # QualityIssue default severity is "info"
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="t",
            issue_message="some text",
        )
        assert assign_severity(issue) == "info"

    def test_completeness_gap_default_severity_warning(self):
        issue = CompletenessGap(category="docs", item="README", description="missing docs")
        assert assign_severity(issue) == "warning"


class TestIsFalsePositive:
    def test_directory_reference(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="infrastructure/",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_pure_number(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="42",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_double_quoted_string(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target='"hello"',
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_single_quoted_string(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="'test'",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_short_target(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="ab",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_file_does_not_exist_with_slash(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="somedir/",
            issue_type="broken",
            issue_message="file does not exist",
        )
        assert is_false_positive(issue) is True

    def test_code_block_path_artifact(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="```python\nimport os",
            issue_type="code_block_path",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_table_artifact(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="| Column |",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_markdown_table_special_pattern(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="infrastructure/agents.md]",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_false_positive(issue) is True


class TestGetSeverityFlag:
    def test_false_positive_is_green(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="{placeholder}",
            issue_type="broken",
            issue_message="msg",
        )
        assert get_severity_flag(issue) == "green"

    def test_critical_is_red(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="docs/missing.md",
            issue_type="broken",
            issue_message="file not found",
            severity="error",
        )
        assert get_severity_flag(issue) == "red"

    def test_warning_is_yellow(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="t",
            issue_message="code block issue",
            severity="warning",
        )
        assert get_severity_flag(issue) == "yellow"

    def test_info_is_green(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="t",
            issue_message="minor note",
            severity="info",
        )
        assert get_severity_flag(issue) == "green"


class TestIsDirectoryReference:
    def test_link_with_directory_target(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="infrastructure/",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_directory_reference(issue) is True

    def test_non_link_issue(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="t",
            issue_message="msg",
        )
        assert is_directory_reference(issue) is False

    def test_file_not_dir(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="docs/guide.md",
            issue_type="broken",
            issue_message="msg",
        )
        assert is_directory_reference(issue) is False

    def test_file_does_not_exist_trailing_slash(self):
        issue = LinkIssue(
            file="t.md",
            line=1,
            link_text="x",
            target="somedir/",
            issue_type="broken",
            issue_message="file does not exist",
        )
        assert is_directory_reference(issue) is True


class TestValidateIssuePatterns:
    def test_returns_dict(self):
        patterns = validate_issue_patterns()
        assert isinstance(patterns, dict)
        assert "broken_links" in patterns
        assert "file_references" in patterns
        assert "latex_references" in patterns
        assert "anchor_links" in patterns

    def test_patterns_are_valid_regex(self):
        import re

        patterns = validate_issue_patterns()
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                re.compile(pattern)  # Should not raise


class TestCategorizeByTypeCompleteness:
    def test_completeness_gap_categorized(self):
        issue = CompletenessGap(category="docs", item="README", description="missing docs")
        result = categorize_by_type([issue])
        assert len(result["missing_files"]) == 1

    def test_accuracy_issue_categorized(self):
        issue = ScanAccuracyIssue(
            category="accuracy_issue",
            severity="warning",
            file="t.md",
            line=1,
            message="inaccurate info",
        )
        result = categorize_by_type([issue])
        assert len(result["invalid_references"]) == 1

    def test_quality_issue_categorized(self):
        issue = QualityIssue(
            file="t.md",
            line=1,
            issue_type="quality_issue",
            issue_message="poor quality",
        )
        result = categorize_by_type([issue])
        assert len(result["code_issues"]) == 1


class TestGroupRelatedIssuesDifferentFiles:
    def test_different_files_different_groups(self):
        issues = [
            QualityIssue(file="a.md", line=1, issue_type="fmt", issue_message="m1"),
            QualityIssue(file="b.md", line=1, issue_type="fmt", issue_message="m2"),
        ]
        groups = group_related_issues(issues)
        assert len(groups) == 2

    def test_same_file_different_types(self):
        issues = [
            QualityIssue(file="a.md", line=1, issue_type="fmt", issue_message="m1"),
            QualityIssue(file="a.md", line=2, issue_type="quality", issue_message="m2"),
        ]
        groups = group_related_issues(issues)
        assert len(groups) == 2


class TestPrioritizeIssuesEdgeCases:
    def test_same_severity_sorted_by_type_and_file(self):
        issues = [
            QualityIssue(file="z.md", line=1, issue_type="z_type", issue_message="info msg"),
            QualityIssue(file="a.md", line=1, issue_type="a_type", issue_message="info msg"),
        ]
        result = prioritize_issues(issues)
        # Both are info severity, so sorted by type then file
        assert _get_issue_file(result[0]) == "a.md"
        assert _get_issue_file(result[1]) == "z.md"


class TestGenerateIssueSummaryFlags:
    def test_severity_flags(self):
        issues = [
            LinkIssue(
                file="t.md",
                line=1,
                link_text="x",
                target="docs/missing.md",
                issue_type="broken",
                issue_message="file not found",
                severity="error",
            ),
            QualityIssue(
                file="t.md",
                line=1,
                issue_type="t",
                issue_message="code block issue",
                severity="warning",
            ),
        ]
        summary = generate_issue_summary(issues)
        assert summary["by_severity_flag"]["red"] >= 1
        assert summary["by_severity_flag"]["yellow"] >= 1

    def test_by_type_counts(self):
        issues = [
            LinkIssue(
                file="t.md",
                line=1,
                link_text="x",
                target="y",
                issue_type="broken_link",
                issue_message="msg",
            ),
            LinkIssue(
                file="t.md",
                line=2,
                link_text="x",
                target="z",
                issue_type="broken_link",
                issue_message="msg",
            ),
        ]
        summary = generate_issue_summary(issues)
        assert summary["by_type"]["broken_link"] == 2
