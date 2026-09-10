"""Issue accessor extraction behaviors: type, file, target, and text."""

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
)
import pytest


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
