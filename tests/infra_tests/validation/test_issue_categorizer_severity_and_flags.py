"""Issue severity assignment, false-positive detection, severity flags, and directory references."""

from infrastructure.validation.docs.models import (
    CompletenessGap,
    LinkIssue,
    QualityIssue,
)
from infrastructure.validation.repo.issue_categorizer import (
    assign_severity,
    get_severity_flag,
    is_directory_reference,
    is_false_positive,
)


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
