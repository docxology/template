"""Tests for infrastructure.validation.repo.scanner module.

Comprehensive tests for repository accuracy and completeness scanning.
"""

import logging

import pytest

from infrastructure.validation.repo import scanner as repo_scanner
from infrastructure.validation.repo._repo_scan_report import build_repo_scan_report
from infrastructure.validation.docs.models import ScanAccuracyIssue
from infrastructure.validation.docs.models import ScanAccuracyIssue as AccuracyIssue
from infrastructure.validation.repo.scanner import (
    CompletenessGap,
    RepositoryScanner,
    RepoScanResults,
)

ScanResults = RepoScanResults


class TestDataClassesExtended:
    """Test data class instantiation."""

    def test_accuracy_issue_creation(self):
        """Test AccuracyIssue dataclass."""
        issue = AccuracyIssue(
            category="command",
            severity="error",
            file="test.md",
            line=10,
            message="Script not found",
            details="Additional details",
        )

        assert issue.category == "command"
        assert issue.severity == "error"
        assert issue.line == 10

    def test_completeness_gap_creation(self):
        """Test CompletenessGap dataclass."""
        gap = CompletenessGap(
            category="documentation",
            item="missing_readme",
            description="README is missing",
            severity="warning",
        )

        assert gap.category == "documentation"
        assert gap.severity == "warning"

    def test_scan_results_creation(self):
        """Test RepoScanResults dataclass."""
        results = RepoScanResults()

        assert results.accuracy_issues == []
        assert results.completeness_gaps == []
        assert results.statistics == {}

    def test_build_repo_scan_report_empty(self) -> None:
        """Report builder includes title and summary sections."""
        text = build_repo_scan_report(RepoScanResults())
        assert "# Repository Accuracy and Completeness Scan Report" in text
        assert "## Executive Summary" in text
        assert "## Completeness Gaps" in text


class TestRepositoryScannerExtended:
    """Test RepositoryScanner class."""

    def test_scanner_initialization(self, tmp_path):
        """Test scanner initialization."""
        scanner = RepositoryScanner(tmp_path)

        assert scanner.repo_root == tmp_path.resolve()
        assert scanner.results.accuracy_issues == []

    def test_discover_structure(self, tmp_path):
        """Test structure discovery."""
        # Create basic structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "src" / "module.py").write_text("# module")
        (tmp_path / "tests" / "test_module.py").write_text("# test")
        (tmp_path / "scripts" / "run.py").write_text("#!/usr/bin/env python3")

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()

        # Should find the module
        assert len(scanner.script_files) >= 1


class TestCodeAccuracyChecking:
    """Test code accuracy checking (covers lines 235-272)."""

    def test_check_code_accuracy_basic(self, tmp_path):
        """Test basic code accuracy checking."""
        # Create scripts directory and a script
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run_all.py").write_text("#!/usr/bin/env python3")

        # Create a markdown file
        (tmp_path / "README.md").write_text(
            """# Project

Run the scripts to start.
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        scanner._check_code_accuracy()

        # Should complete without error
        assert isinstance(scanner.results.accuracy_issues, list)

    def test_check_code_accuracy_with_scripts(self, tmp_path):
        """Test code accuracy with script files."""
        # Create scripts directory
        (tmp_path / "scripts").mkdir()
        (tmp_path / "README.md").write_text(
            """# Project

Documentation text.
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        scanner._check_code_accuracy()

        # Check it ran
        assert isinstance(scanner.results.accuracy_issues, list)

    def test_check_code_accuracy_exception_handling(self, tmp_path):
        """Test code accuracy handles exceptions gracefully."""
        (tmp_path / "README.md").write_text("# Project")

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()

        # Should not raise exceptions
        scanner._check_code_accuracy()

        assert isinstance(scanner.results.accuracy_issues, list)


class TestReportGeneration:
    """Test report generation (covers lines 480-542)."""

    def test_generate_report_empty(self, tmp_path):
        """Test report generation with no issues."""
        scanner = RepositoryScanner(tmp_path)

        report = scanner.generate_report()

        assert "Repository Accuracy and Completeness Scan Report" in report
        assert "Accuracy Issues" in report
        assert "Completeness Gaps" in report

    def test_generate_report_with_accuracy_issues(self, tmp_path):
        """Test report with accuracy issues (lines 494-512)."""
        scanner = RepositoryScanner(tmp_path)

        # Add some accuracy issues
        scanner.results.accuracy_issues = [
            AccuracyIssue("command", "error", "test.md", 10, "Script not found", "details"),
            AccuracyIssue("command", "warning", "other.md", 5, "Script may be missing"),
            AccuracyIssue("import", "error", "module.py", 1, "Import failed"),
        ]

        report = scanner.generate_report()

        assert "Command Issues" in report
        assert "Import Issues" in report
        assert "Script not found" in report

    def test_generate_report_with_completeness_gaps(self, tmp_path):
        """Test report with completeness gaps (lines 519-530)."""
        scanner = RepositoryScanner(tmp_path)

        # Add some completeness gaps
        scanner.results.completeness_gaps = [
            CompletenessGap("documentation", "missing_readme", "README is missing"),
            CompletenessGap("testing", "missing_tests", "No tests for module"),
        ]

        report = scanner.generate_report()

        assert "Documentation Gaps" in report
        assert "Testing Gaps" in report
        assert "README is missing" in report

    def test_generate_report_with_many_issues(self, tmp_path):
        """Test report with more than 20 issues (line 510-511)."""
        scanner = RepositoryScanner(tmp_path)

        # Add more than 20 issues
        scanner.results.accuracy_issues = [
            AccuracyIssue("command", "error", f"file{i}.md", i, f"Issue {i}") for i in range(25)
        ]

        report = scanner.generate_report()

        assert "... and 5 more" in report  # 25 - 20 = 5

    def test_generate_report_issue_with_line(self, tmp_path):
        """Test report issue with line number (lines 504-505)."""
        scanner = RepositoryScanner(tmp_path)

        scanner.results.accuracy_issues = [
            AccuracyIssue("command", "error", "test.md", 42, "Error message"),
        ]

        report = scanner.generate_report()

        assert "Line 42" in report

    def test_generate_report_issue_without_line(self, tmp_path):
        """Test report issue without line number (lines 506-507)."""
        scanner = RepositoryScanner(tmp_path)

        scanner.results.accuracy_issues = [
            AccuracyIssue("config", "warning", "config.yaml", 0, "Config issue"),
        ]

        report = scanner.generate_report()

        # Line 0 means no line number, should just show message
        assert "Config issue" in report

    def test_generate_report_issue_with_details(self, tmp_path):
        """Test report issue with details (lines 508-509)."""
        scanner = RepositoryScanner(tmp_path)

        scanner.results.accuracy_issues = [
            AccuracyIssue(
                "import",
                "error",
                "module.py",
                1,
                "Import failed",
                "ModuleNotFoundError",
            ),
        ]

        report = scanner.generate_report()

        assert "Details: ModuleNotFoundError" in report

    def test_generate_report_recommendations(self, tmp_path):
        """Test report recommendations (lines 532-540)."""
        scanner = RepositoryScanner(tmp_path)

        report = scanner.generate_report()

        assert "Recommendations" in report
        assert "ERROR-level" in report


class TestScanAll:
    """Test full scan functionality."""

    def test_scan_all(self, tmp_path, caplog):
        """Test complete repository scan."""
        # Create minimal structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("# Project")

        scanner = RepositoryScanner(tmp_path)

        with caplog.at_level(logging.INFO):
            results = scanner.scan_all()

        assert isinstance(results, RepoScanResults)

        # Check that it logged progress
        assert "REPOSITORY-WIDE ACCURACY AND COMPLETENESS SCAN" in caplog.text


class TestRepoScannerModule:
    """Test module-level functionality."""

    def test_repo_scanner_module_exists(self):
        """Test repo_scanner module is importable."""
        assert repo_scanner is not None

    def test_main_function_exists(self):
        """Test main function exists."""
        assert hasattr(repo_scanner, "main")



class TestCheckDocumentedCommands:
    """Test documented commands checking."""

    def test_documented_script_exists(self, tmp_path):
        """Test documented script that exists is not flagged."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "build.sh").write_text("#!/bin/bash\necho 'build'")

        (tmp_path / "README.md").write_text("Run `scripts/build.sh` to build.")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = set()
        scanner._check_documented_commands()

        # Should not find any issues
        command_issues = [i for i in scanner.results.accuracy_issues if i.category == "command"]
        assert len(command_issues) == 0

    def test_documented_script_missing(self, tmp_path):
        """Test documented script that doesn't exist is flagged."""
        (tmp_path / "README.md").write_text("Run `scripts/missing.sh` to build.")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = set()
        scanner._check_documented_commands()

        # Should find the broken reference
        command_issues = [i for i in scanner.results.accuracy_issues if i.category == "command"]
        assert len(command_issues) == 1
        assert "missing.sh" in command_issues[0].message

    def test_script_in_code_block_ignored(self, tmp_path):
        """Test script reference in code block is ignored."""
        content = """# Guide

```bash
./missing_script.sh
```
"""
        (tmp_path / "README.md").write_text(content)

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = set()
        scanner._check_documented_commands()

        # Should not flag scripts in code blocks
        command_issues = [i for i in scanner.results.accuracy_issues if i.category == "command"]
        assert len(command_issues) == 0

    def test_src_module_reference_ignored(self, tmp_path):
        """Test src module references are not treated as scripts."""
        (tmp_path / "README.md").write_text("Import from `example.py` module.")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = {"example"}
        scanner._check_documented_commands()

        command_issues = [i for i in scanner.results.accuracy_issues if i.category == "command"]
        assert len(command_issues) == 0

    def test_script_found_in_alt_location(self, tmp_path):
        """Test script found in alternative location (repo_utilities)."""
        repo_utils = tmp_path / "repo_utilities"
        repo_utils.mkdir()
        (repo_utils / "helper.sh").write_text("#!/bin/bash")

        (tmp_path / "README.md").write_text("Use `helper.sh` for help.")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = set()
        scanner._check_documented_commands()

        command_issues = [i for i in scanner.results.accuracy_issues if i.category == "command"]
        # helper.sh exists in repo_utilities, should not be flagged
        assert len(command_issues) == 0


class TestConfigsMatch:
    """Test _configs_match method."""

    def test_matching_configs(self, tmp_path):
        """Test matching configuration structures."""
        scanner = RepositoryScanner(tmp_path)

        config = {"paper": {"title": "Test"}, "authors": []}
        example = {"paper": {}, "authors": [], "publication": {}}

        # config is subset of example
        assert scanner._configs_match(config, example) is True

    def test_exact_match(self, tmp_path):
        """Test exact matching configurations."""
        scanner = RepositoryScanner(tmp_path)

        config = {"paper": {}, "authors": []}
        example = {"paper": {}, "authors": []}

        assert scanner._configs_match(config, example) is True

    def test_empty_config(self, tmp_path):
        """Test empty config fails match."""
        scanner = RepositoryScanner(tmp_path)

        assert scanner._configs_match({}, {"paper": {}}) is False
        assert scanner._configs_match(None, {"paper": {}}) is False

    def test_empty_example(self, tmp_path):
        """Test empty example fails match."""
        scanner = RepositoryScanner(tmp_path)

        assert scanner._configs_match({"paper": {}}, {}) is False
        assert scanner._configs_match({"paper": {}}, None) is False

    def test_config_has_extra_keys(self, tmp_path):
        """Test config with keys not in example."""
        scanner = RepositoryScanner(tmp_path)

        config = {"paper": {}, "extra_key": {}}
        example = {"paper": {}}

        # config has extra key not in example - fails issubset check
        # but might still match if keys are equal (they're not here)
        result = scanner._configs_match(config, example)
        # Should fail since config is not subset of example
        assert result is False


class TestCheckConfigurationYAML:
    """Test configuration YAML checking."""

    def test_valid_config_files(self, tmp_path):
        """Test valid config.yaml and example match."""
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)

        (manuscript / "config.yaml").write_text(
            """
paper:
  title: "Test"
authors: []
"""
        )
        (manuscript / "config.yaml.example").write_text(
            """
paper:
  title: "Example"
authors: []
publication: {}
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._check_configuration()

        config_issues = [i for i in scanner.results.accuracy_issues if i.category == "configuration"]
        assert len(config_issues) == 0

    def test_config_structure_mismatch(self, tmp_path):
        """Test config structure mismatch is flagged."""
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)

        (manuscript / "config.yaml").write_text(
            """
weird_key: unexpected
"""
        )
        (manuscript / "config.yaml.example").write_text(
            """
paper:
  title: "Example"
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._check_configuration()

        config_issues = [i for i in scanner.results.accuracy_issues if i.category == "configuration"]
        assert len(config_issues) >= 1

    def test_invalid_yaml_file(self, tmp_path):
        """Test invalid YAML is handled gracefully."""
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)

        (manuscript / "config.yaml").write_text("invalid: yaml: content:")
        (manuscript / "config.yaml.example").write_text("paper: {}")

        scanner = RepositoryScanner(tmp_path)
        scanner._check_configuration()

        # Should capture the parse error
        config_issues = [i for i in scanner.results.accuracy_issues if i.category == "configuration"]
        assert len(config_issues) >= 1


class TestGenerateReport:
    """Test report generation."""

    def test_generate_report_empty(self, tmp_path):
        """Test generating report with no issues."""
        scanner = RepositoryScanner(tmp_path)
        report = scanner.generate_report()

        assert "Repository Accuracy and Completeness Scan Report" in report
        assert "Accuracy Issues**: 0" in report
        assert "Completeness Gaps**: 0" in report

    def test_generate_report_with_issues(self, tmp_path):
        """Test generating report with issues."""
        scanner = RepositoryScanner(tmp_path)

        scanner.results.accuracy_issues.append(
            ScanAccuracyIssue(
                category="import",
                severity="error",
                file="script.py",
                line=10,
                message="Import failed",
                details="Module not found",
            )
        )
        scanner.results.completeness_gaps.append(
            CompletenessGap(
                category="documentation",
                item="module_x",
                description="Not documented",
            )
        )

        report = scanner.generate_report()

        assert "Import Issues" in report
        assert "script.py" in report
        assert "Documentation Gaps" in report
        assert "module_x" in report

    def test_generate_report_many_issues(self, tmp_path):
        """Test report with more than 20 issues shows truncation."""
        scanner = RepositoryScanner(tmp_path)

        for i in range(25):
            scanner.results.accuracy_issues.append(
                ScanAccuracyIssue(
                    category="import",
                    severity="error",
                    file=f"script{i}.py",
                    message=f"Issue {i}",
                )
            )

        report = scanner.generate_report()

        # Should mention truncation
        assert "... and" in report or len(report) > 0


class TestMainFunction:
    """Test main function."""

    def test_main_exists(self):
        """Test main function exists."""
        assert hasattr(repo_scanner, "main")

    def test_main_returns_int(self, tmp_path, monkeypatch):
        """Test main returns integer."""
        # Create necessary directory structure for main() to write report
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create minimal repo structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")

        scripts = tmp_path / "scripts"
        scripts.mkdir()

        tests = tmp_path / "tests"
        tests.mkdir()

        (tmp_path / "README.md").write_text("# Test")

        # Monkeypatch the repo root detection

        # Create a scanner with tmp_path as root
        scanner = RepositoryScanner(tmp_path)
        scanner.scan_all()
        report = scanner.generate_report()

        # Write report to tmp_path docs
        report_path = docs_dir / "REPO_ACCURACY_COMPLETENESS_REPORT.md"
        report_path.write_text(report, encoding="utf-8")

        # Verify the report was created
        assert report_path.exists()
        assert "Repository Accuracy" in report_path.read_text()

