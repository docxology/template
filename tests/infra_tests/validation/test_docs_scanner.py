"""Tests for infrastructure.validation.docs.scanner — comprehensive coverage."""


from infrastructure.validation.docs.scanner import (
    AccuracyIssue,
    DocumentationScanner,
)
from infrastructure.validation.docs.models import ScanResults


def _setup_repo(tmp_path):
    """Create a minimal repo layout with docs for scanning."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "# User Guide\n\nThis is the main guide.\n\n## Installation\n\nRun `pip install`.\n"
    )
    (tmp_path / "docs" / "api.md").write_text(
        "# API Reference\n\nSee [guide](guide.md) for details.\n"
    )
    (tmp_path / "README.md").write_text("# Project\n\nSee [docs](docs/guide.md).\n")
    (tmp_path / "CLAUDE.md").write_text("# Claude\n\nInstructions.\n")
    return tmp_path


class TestAccuracyIssue:
    def test_backward_compat_init(self):
        issue = AccuracyIssue(
            file="test.md",
            line=10,
            issue_type="command",
            issue_message="Missing script",
        )
        assert issue.file == "test.md"
        assert issue.line == 10
        assert issue.issue_type == "command"
        assert issue.issue_message == "Missing script"
        assert issue.category == "command"
        assert issue.message == "Missing script"

    def test_severity_default(self):
        issue = AccuracyIssue(file="f", line=1, issue_type="t", issue_message="m")
        assert issue.severity == "warning"

    def test_custom_severity(self):
        issue = AccuracyIssue(file="f", line=1, issue_type="t", issue_message="m", severity="error")
        assert issue.severity == "error"


class TestDocumentationScanner:
    def test_init(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        assert scanner.repo_root == tmp_path.resolve()
        assert isinstance(scanner.results, ScanResults)

    def test_phase1_discovery(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        inventory = scanner.phase1_discovery()
        assert "markdown_files" in inventory
        assert inventory["markdown_files"] >= 2

    def test_phase2_accuracy(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        report = scanner.phase2_accuracy()
        assert "link_issues" in report
        assert "total_issues" in report

    def test_phase3_completeness(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        report = scanner.phase3_completeness()
        assert "total_gaps" in report

    def test_phase4_quality(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        report = scanner.phase4_quality()
        assert isinstance(report, dict)

    def test_phase5_improvements(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        report = scanner.phase5_improvements()
        assert "total_improvements" in report
        assert "link_fixes" in report

    def test_phase6_verification(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        report = scanner.phase6_verification()
        assert "link_checker" in report
        assert "cross_references" in report

    def test_phase7_reporting(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        report_text = scanner.phase7_reporting()
        assert isinstance(report_text, str)
        assert "Documentation Scan" in report_text

    def test_run_full_scan(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert isinstance(results, ScanResults)
        assert isinstance(report, str)
        assert len(report) > 100

    def test_identify_link_fixes(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        # Add a broken link issue
        from infrastructure.validation.docs.models import LinkIssue
        scanner.results.link_issues.append(
            LinkIssue(file="doc.md", line=5, link_text="x", target="missing.md",
                      issue_type="broken_file", issue_message="File not found")
        )
        fixes = scanner._identify_link_fixes()
        assert len(fixes) == 1
        assert fixes[0]["type"] == "link_fix"

    def test_identify_other_improvements(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        from infrastructure.validation.docs.models import QualityIssue
        scanner.results.quality_issues.append(
            QualityIssue(file="doc.md", line=1, issue_type="formatting",
                         issue_message="Heading hierarchy issue")
        )
        improvements = scanner._identify_other_improvements()
        assert len(improvements) == 1
        assert improvements[0]["type"] == "structural"

    def test_empty_repo(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert results.total_files == 0
        assert isinstance(report, str)
