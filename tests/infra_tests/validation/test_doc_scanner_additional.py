"""Tests for infrastructure.validation.docs.scanner — additional coverage for phases."""


from infrastructure.validation.docs.scanner import (
    AccuracyIssue,
    DocumentationScanner,
)


class TestAccuracyIssueCompat:
    def test_basic_creation(self):
        issue = AccuracyIssue(
            file="test.md",
            line=10,
            issue_type="broken_ref",
            issue_message="Reference not found",
            severity="warning",
            details="extra detail",
        )
        assert issue.issue_type == "broken_ref"
        assert issue.issue_message == "Reference not found"
        assert issue.category == "broken_ref"
        assert issue.message == "Reference not found"
        assert issue.file == "test.md"
        assert issue.line == 10
        assert issue.severity == "warning"
        assert issue.details == "extra detail"

    def test_default_severity(self):
        issue = AccuracyIssue(
            file="t.md", line=1, issue_type="test", issue_message="msg",
        )
        assert issue.severity == "warning"


class TestScannerPhases:
    def _make_repo(self, tmp_path):
        (tmp_path / "README.md").write_text(
            "# Project\n\nSee [guide](docs/guide.md) for details.\n"
        )
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text(
            "# Guide\n\n## Section\n\nContent with [back](../README.md).\n"
        )
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]\n")
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('hello')\n")
        return tmp_path

    def test_phase1_discovery(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        result = scanner.phase1_discovery()
        assert result["markdown_files"] >= 2
        assert "hierarchy" in result
        assert scanner.results.total_files >= 2

    def test_phase2_accuracy(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        scanner.phase1_discovery()
        result = scanner.phase2_accuracy()
        assert isinstance(result, dict)
        assert "phase2" in scanner.results.statistics

    def test_phase3_completeness(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        scanner.phase1_discovery()
        result = scanner.phase3_completeness()
        assert isinstance(result, dict)
        assert "phase3" in scanner.results.statistics

    def test_phase4_quality(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        scanner.phase1_discovery()
        result = scanner.phase4_quality()
        assert isinstance(result, dict)
        assert "phase4" in scanner.results.statistics

    def test_phase5_improvements(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        scanner.phase4_quality()
        result = scanner.phase5_improvements()
        assert "total_improvements" in result
        assert "link_fixes" in result
        assert "content_updates" in result
        assert "structural_changes" in result
        assert "phase5" in scanner.results.statistics

    def test_phase6_verification(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        result = scanner.phase6_verification()
        assert "link_checker" in result
        assert "cross_references" in result

    def test_phase7_reporting(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        scanner.phase1_discovery()
        report = scanner.phase7_reporting()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_run_full_scan(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        results, report = scanner.run_full_scan()
        assert results.total_files >= 2
        assert isinstance(report, str)
        assert "phase1" in results.statistics
        assert "phase2" in results.statistics

    def test_identify_link_fixes(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        from infrastructure.validation.docs.models import LinkIssue

        scanner.results.link_issues.append(
            LinkIssue(
                file="t.md", line=1, link_text="x", target="missing.md",
                issue_type="broken_file", issue_message="File not found",
            )
        )
        scanner.results.link_issues.append(
            LinkIssue(
                file="t.md", line=2, link_text="y", target="#missing",
                issue_type="broken_anchor", issue_message="Anchor not found",
            )
        )
        fixes = scanner._identify_link_fixes()
        assert len(fixes) == 2
        assert fixes[0]["type"] == "link_fix"

    def test_identify_other_improvements(self, tmp_path):
        repo = self._make_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        from infrastructure.validation.docs.models import QualityIssue

        scanner.results.quality_issues.append(
            QualityIssue(
                file="t.md", line=1, issue_type="formatting",
                issue_message="Heading level skip detected",
            )
        )
        improvements = scanner._identify_other_improvements()
        assert len(improvements) == 1
        assert improvements[0]["type"] == "structural"

    def test_validate_markdown_syntax(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        result = scanner._validate_markdown_syntax()
        assert result["status"] == "basic_validation_passed"

    def test_test_documented_commands(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        result = scanner._test_documented_commands()
        assert result["status"] == "manual_testing_required"

    def test_check_circular_references(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        result = scanner._check_circular_references()
        assert result["status"] == "no_circular_references_detected"

    def test_verify_cross_references(self, tmp_path):
        (tmp_path / "test.md").write_text("[link](other.md)")
        scanner = DocumentationScanner(tmp_path)
        result = scanner._verify_cross_references()
        assert result["status"] == "verified"
        assert "total_references" in result


class TestScannerInitialization:
    def test_init_sets_defaults(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        assert scanner.repo_root == tmp_path.resolve()
        assert scanner.results.scan_date is not None
        assert scanner.all_headings == {}
        assert scanner.script_files == []
        assert scanner.config_files == {}

    def test_empty_repo(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert results.total_files == 0
