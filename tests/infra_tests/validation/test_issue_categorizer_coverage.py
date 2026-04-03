"""Tests for infrastructure.validation.repo.issue_categorizer — additional coverage."""

from infrastructure.validation.docs.models import (
    CompletenessGap,
    LinkIssue,
    QualityIssue,
    ScanAccuracyIssue,
)
from infrastructure.validation.repo.issue_categorizer import (
    _get_issue_file,
    _get_issue_target,
    _get_issue_text,
    _get_issue_type,
    assign_severity,
    categorize_by_type,
    generate_issue_summary,
    get_severity_flag,
    group_related_issues,
    is_directory_reference,
    is_false_positive,
    prioritize_issues,
    validate_issue_patterns,
    ISSUE_TYPE_COMPLETENESS,
)

import pytest


class TestGetIssueType:
    def test_link_issue(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="y",
            issue_type="broken_link", issue_message="msg",
        )
        assert _get_issue_type(issue) == "broken_link"

    def test_quality_issue(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="formatting", issue_message="msg",
        )
        assert _get_issue_type(issue) == "formatting"

    def test_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="accuracy", severity="warning", file="t.md", line=1, message="msg",
        )
        assert _get_issue_type(issue) == "accuracy"

    def test_completeness_gap(self):
        issue = CompletenessGap(
            category="docs", item="README", description="Missing README",
        )
        assert _get_issue_type(issue) == ISSUE_TYPE_COMPLETENESS

    def test_unexpected_type_raises(self):
        with pytest.raises(TypeError, match="Unexpected issue type"):
            _get_issue_type("not an issue")  # type: ignore[arg-type]


class TestGetIssueFile:
    def test_link_issue(self):
        issue = LinkIssue(
            file="readme.md", line=1, link_text="x", target="y",
            issue_type="broken", issue_message="msg",
        )
        assert _get_issue_file(issue) == "readme.md"

    def test_quality_issue(self):
        issue = QualityIssue(file="q.md", line=1, issue_type="t", issue_message="m")
        assert _get_issue_file(issue) == "q.md"

    def test_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="c", severity="w", file="a.md", line=1, message="m",
        )
        assert _get_issue_file(issue) == "a.md"

    def test_completeness_gap(self):
        issue = CompletenessGap(category="docs", item="README", description="d")
        assert _get_issue_file(issue) == "unknown"


class TestGetIssueTarget:
    def test_link_issue(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="docs/guide.md",
            issue_type="broken", issue_message="msg",
        )
        assert _get_issue_target(issue) == "docs/guide.md"

    def test_non_link_issue(self):
        issue = QualityIssue(file="t.md", line=1, issue_type="t", issue_message="m")
        assert _get_issue_target(issue) == ""


class TestGetIssueText:
    def test_scan_accuracy_issue(self):
        issue = ScanAccuracyIssue(
            category="c", severity="w", file="f.md", line=1, message="the error message",
        )
        assert _get_issue_text(issue) == "the error message"

    def test_completeness_gap(self):
        issue = CompletenessGap(category="docs", item="README", description="missing docs")
        assert _get_issue_text(issue) == "missing docs"


class TestAssignSeverity:
    def test_explicit_critical(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="t", issue_message="msg", severity="critical",
        )
        assert assign_severity(issue) == "critical"

    def test_content_based_critical_via_completeness(self):
        # CompletenessGap has severity="warning" by default but assign_severity
        # maps it through the explicit severity check. Test content-based by
        # using a completeness gap with severity not in the explicit map.
        issue = CompletenessGap(
            category="docs", item="README",
            description="syntax error in file", severity="unknown",
        )
        assert assign_severity(issue) == "critical"

    def test_content_based_error_via_completeness(self):
        issue = CompletenessGap(
            category="docs", item="x",
            description="broken link found", severity="unknown",
        )
        assert assign_severity(issue) == "error"

    def test_content_based_warning_via_completeness(self):
        issue = CompletenessGap(
            category="docs", item="x",
            description="placeholder value found", severity="unknown",
        )
        assert assign_severity(issue) == "warning"

    def test_content_based_info_fallback(self):
        issue = CompletenessGap(
            category="docs", item="x",
            description="some normal text", severity="unknown",
        )
        assert assign_severity(issue) == "info"

    def test_quality_issue_default_severity_info(self):
        # QualityIssue default severity is "info"
        issue = QualityIssue(
            file="t.md", line=1, issue_type="t", issue_message="some text",
        )
        assert assign_severity(issue) == "info"

    def test_completeness_gap_default_severity_warning(self):
        issue = CompletenessGap(category="docs", item="README", description="missing docs")
        assert assign_severity(issue) == "warning"


class TestIsFalsePositive:
    def test_directory_reference(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="infrastructure/",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_pure_number(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="42",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_double_quoted_string(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target='"hello"',
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_single_quoted_string(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="'test'",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_short_target(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="ab",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_file_does_not_exist_with_slash(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="somedir/",
            issue_type="broken", issue_message="file does not exist",
        )
        assert is_false_positive(issue) is True

    def test_code_block_path_artifact(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="```python\nimport os",
            issue_type="code_block_path", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_table_artifact(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="| Column |",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True

    def test_markdown_table_special_pattern(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x",
            target="infrastructure/agents.md]",
            issue_type="broken", issue_message="msg",
        )
        assert is_false_positive(issue) is True


class TestGetSeverityFlag:
    def test_false_positive_is_green(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="{placeholder}",
            issue_type="broken", issue_message="msg",
        )
        assert get_severity_flag(issue) == "green"

    def test_critical_is_red(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="docs/missing.md",
            issue_type="broken", issue_message="file not found",
            severity="error",
        )
        assert get_severity_flag(issue) == "red"

    def test_warning_is_yellow(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="t",
            issue_message="code block issue", severity="warning",
        )
        assert get_severity_flag(issue) == "yellow"

    def test_info_is_green(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="t",
            issue_message="minor note", severity="info",
        )
        assert get_severity_flag(issue) == "green"


class TestIsDirectoryReference:
    def test_link_with_directory_target(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="infrastructure/",
            issue_type="broken", issue_message="msg",
        )
        assert is_directory_reference(issue) is True

    def test_non_link_issue(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="t", issue_message="msg",
        )
        assert is_directory_reference(issue) is False

    def test_file_not_dir(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="docs/guide.md",
            issue_type="broken", issue_message="msg",
        )
        assert is_directory_reference(issue) is False

    def test_file_does_not_exist_trailing_slash(self):
        issue = LinkIssue(
            file="t.md", line=1, link_text="x", target="somedir/",
            issue_type="broken", issue_message="file does not exist",
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
            category="accuracy_issue", severity="warning",
            file="t.md", line=1, message="inaccurate info",
        )
        result = categorize_by_type([issue])
        assert len(result["invalid_references"]) == 1

    def test_quality_issue_categorized(self):
        issue = QualityIssue(
            file="t.md", line=1, issue_type="quality_issue",
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
                file="t.md", line=1, link_text="x", target="docs/missing.md",
                issue_type="broken", issue_message="file not found", severity="error",
            ),
            QualityIssue(
                file="t.md", line=1, issue_type="t",
                issue_message="code block issue", severity="warning",
            ),
        ]
        summary = generate_issue_summary(issues)
        assert summary["by_severity_flag"]["red"] >= 1
        assert summary["by_severity_flag"]["yellow"] >= 1

    def test_by_type_counts(self):
        issues = [
            LinkIssue(
                file="t.md", line=1, link_text="x", target="y",
                issue_type="broken_link", issue_message="msg",
            ),
            LinkIssue(
                file="t.md", line=2, link_text="x", target="z",
                issue_type="broken_link", issue_message="msg",
            ),
        ]
        summary = generate_issue_summary(issues)
        assert summary["by_type"]["broken_link"] == 2
