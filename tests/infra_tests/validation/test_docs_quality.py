"""Tests for infrastructure.validation.docs.quality — comprehensive coverage."""


from infrastructure.validation.docs.quality import (
    assess_actionability,
    assess_clarity,
    assess_maintainability,
    check_formatting,
    group_quality_by_severity,
    group_quality_by_type,
    run_quality_phase,
)
from infrastructure.validation.docs.models import QualityIssue


class TestAssessClarity:
    def test_short_lines_no_issues(self, tmp_path):
        md_file = tmp_path / "short.md"
        content = "Short line\nAnother short line\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_clarity(content, md_file, lines, tmp_path)
        assert result == []

    def test_long_line_flagged(self, tmp_path):
        md_file = tmp_path / "long.md"
        long_line = "x" * 121
        content = f"Short line\n{long_line}\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_clarity(content, md_file, lines, tmp_path)
        assert len(result) == 1
        assert result[0].issue_type == "clarity"
        assert result[0].line == 2
        assert "120 characters" in result[0].issue_message

    def test_code_block_line_not_flagged(self, tmp_path):
        md_file = tmp_path / "code.md"
        long_code = "```" + "x" * 200
        content = f"{long_code}\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_clarity(content, md_file, lines, tmp_path)
        assert result == []

    def test_exactly_120_chars_not_flagged(self, tmp_path):
        md_file = tmp_path / "exact.md"
        content = "x" * 120 + "\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_clarity(content, md_file, lines, tmp_path)
        assert result == []

    def test_multiple_long_lines(self, tmp_path):
        md_file = tmp_path / "multi.md"
        content = ("y" * 130 + "\n") * 3
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_clarity(content, md_file, lines, tmp_path)
        assert len(result) == 3


class TestAssessActionability:
    def test_imperative_bullet_no_issue(self, tmp_path):
        md_file = tmp_path / "action.md"
        content = "- Run the tests\n- Install dependencies\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert result == []

    def test_non_imperative_bullet_flagged(self, tmp_path):
        md_file = tmp_path / "passive.md"
        content = "- The system should handle errors\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert len(result) == 1
        assert result[0].issue_type == "actionability"
        assert "the" in result[0].issue_message.lower()

    def test_numbered_list_imperative(self, tmp_path):
        md_file = tmp_path / "numbered.md"
        content = "1. Run the pipeline\n2. Check the output\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert result == []

    def test_code_block_skipped(self, tmp_path):
        md_file = tmp_path / "codeblock.md"
        content = "```\n- The passive item inside code\n```\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert result == []

    def test_inline_code_bullet_skipped(self, tmp_path):
        md_file = tmp_path / "inline.md"
        content = "- `some_command --flag`\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert result == []

    def test_non_list_items_ignored(self, tmp_path):
        md_file = tmp_path / "nonlist.md"
        content = "This is a paragraph with no list items.\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_actionability(content, md_file, lines, tmp_path)
        assert result == []


class TestAssessMaintainability:
    def test_no_duplicates(self, tmp_path):
        md_file = tmp_path / "unique.md"
        content = "Line one\nLine two\nLine three\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert result == []

    def test_three_duplicates_flagged(self, tmp_path):
        md_file = tmp_path / "dupes.md"
        content = "Duplicate line\nDuplicate line\nDuplicate line\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert len(result) == 1
        assert result[0].issue_type == "maintainability"
        assert "3 times" in result[0].issue_message

    def test_two_duplicates_not_flagged(self, tmp_path):
        md_file = tmp_path / "two.md"
        content = "Repeat\nRepeat\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert result == []

    def test_headings_ignored(self, tmp_path):
        md_file = tmp_path / "headings.md"
        content = "# Title\n# Title\n# Title\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert result == []

    def test_code_blocks_ignored(self, tmp_path):
        md_file = tmp_path / "code.md"
        content = "```\nrepeat\nrepeat\nrepeat\n```\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert result == []

    def test_blank_lines_ignored(self, tmp_path):
        md_file = tmp_path / "blank.md"
        content = "\n\n\n\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = assess_maintainability(content, md_file, lines, tmp_path)
        assert result == []


class TestCheckFormatting:
    def test_valid_heading_hierarchy(self, tmp_path):
        md_file = tmp_path / "valid.md"
        content = "# H1\n## H2\n### H3\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = check_formatting(content, md_file, lines, tmp_path)
        assert result == []

    def test_skipped_heading_level(self, tmp_path):
        md_file = tmp_path / "skip.md"
        content = "# H1\n### H3\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = check_formatting(content, md_file, lines, tmp_path)
        assert len(result) == 1
        assert result[0].issue_type == "formatting"
        assert "jumps from 1 to 3" in result[0].issue_message

    def test_no_headings(self, tmp_path):
        md_file = tmp_path / "none.md"
        content = "Just text\nMore text\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = check_formatting(content, md_file, lines, tmp_path)
        assert result == []

    def test_multiple_skips(self, tmp_path):
        md_file = tmp_path / "multi.md"
        content = "# H1\n#### H4\n"
        md_file.write_text(content)
        lines = content.split("\n")
        result = check_formatting(content, md_file, lines, tmp_path)
        assert len(result) == 1
        assert "jumps from 1 to 4" in result[0].issue_message


class TestGroupQualityByType:
    def test_groups_correctly(self):
        issues = [
            QualityIssue(file="a.md", line=1, issue_type="clarity", issue_message="too long"),
            QualityIssue(file="b.md", line=2, issue_type="clarity", issue_message="too long 2"),
            QualityIssue(file="c.md", line=3, issue_type="formatting", issue_message="heading skip"),
        ]
        result = group_quality_by_type(issues)
        assert result["clarity"] == 2
        assert result["formatting"] == 1

    def test_empty_list(self):
        assert group_quality_by_type([]) == {}


class TestGroupQualityBySeverity:
    def test_groups_correctly(self):
        issues = [
            QualityIssue(file="a.md", line=1, issue_type="clarity", issue_message="msg", severity="info"),
            QualityIssue(file="b.md", line=2, issue_type="clarity", issue_message="msg", severity="warning"),
            QualityIssue(file="c.md", line=3, issue_type="clarity", issue_message="msg", severity="info"),
        ]
        result = group_quality_by_severity(issues)
        assert result["info"] == 2
        assert result["warning"] == 1

    def test_empty_list(self):
        assert group_quality_by_severity([]) == {}


class TestRunQualityPhase:
    def test_runs_on_markdown_files(self, tmp_path):
        md1 = tmp_path / "good.md"
        md1.write_text("# Title\n## Subtitle\nShort content.\n")

        md2 = tmp_path / "bad.md"
        long_line = "x" * 130
        md2.write_text(f"# Title\n### Skip\n{long_line}\n")

        report, issues = run_quality_phase([md1, md2], tmp_path)
        assert report["total_issues"] >= 2  # at least heading skip + long line
        assert "by_type" in report
        assert "severity_breakdown" in report
        assert len(issues) >= 2

    def test_empty_file_list(self, tmp_path):
        report, issues = run_quality_phase([], tmp_path)
        assert report["total_issues"] == 0
        assert issues == []
