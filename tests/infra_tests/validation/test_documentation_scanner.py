"""Tests for infrastructure.validation.docs.scanner and related modules."""

from datetime import datetime

import pytest

from infrastructure.validation.docs import scanner as doc_scanner
from infrastructure.validation.docs._docs_scan_report import build_documentation_scan_report
from infrastructure.validation.docs.accuracy import extract_headings
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.docs.discovery import (
    analyze_documentation_file,
    catalog_agents_readme,
    find_config_files,
    find_script_files,
)
from infrastructure.validation.docs.models import ScanAccuracyIssue
from infrastructure.validation.docs.scanner import (
    CompletenessGap,
    DocumentationFile,
    DocumentationScanner,
    LinkIssue,
    QualityIssue,
    ScanResults,
)
from infrastructure.validation.docs.verification import (
    run_link_audit,
    run_verification_checks,
    verify_cross_references,
)


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


def _make_rich_repo(tmp_path):
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


class TestDataClasses:
    """Test data class instantiation and behavior."""

    def test_documentation_file_creation(self):
        doc_file = DocumentationFile(
            path="/path/to/file.md",
            relative_path="file.md",
            directory="/path/to",
            name="file.md",
            category="docs",
            word_count=100,
            line_count=20,
            has_links=True,
            has_code_blocks=True,
            last_modified="2024-01-01",
        )
        assert doc_file.path == "/path/to/file.md"
        assert doc_file.word_count == 100
        assert doc_file.has_links is True

    def test_link_issue_creation(self):
        issue = LinkIssue(
            file="test.md",
            line=10,
            link_text="broken link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found",
            severity="error",
        )
        assert issue.file == "test.md"
        assert issue.severity == "error"

    def test_accuracy_issue_creation(self):
        issue = ScanAccuracyIssue(
            category="command",
            file="readme.md",
            line=5,
            message="Command not found",
            severity="warning",
        )
        assert issue.category == "command"

    def test_completeness_gap_creation(self):
        gap = CompletenessGap(
            category="API",
            item="missing_function_docs",
            description="Function X is not documented",
            severity="warning",
        )
        assert gap.category == "API"

    def test_quality_issue_creation(self):
        issue = QualityIssue(
            file="doc.md",
            line=1,
            issue_type="formatting",
            issue_message="Missing header",
            severity="info",
        )
        assert issue.issue_type == "formatting"

    def test_scan_results_creation(self):
        results = ScanResults(scan_date="2024-01-01T00:00:00")
        assert results.scan_date == "2024-01-01T00:00:00"
        assert results.total_files == 0
        assert results.link_issues == []


class TestScanAccuracyIssue:
    def test_basic_creation(self):
        issue = ScanAccuracyIssue(
            category="broken_ref",
            file="test.md",
            line=10,
            message="Reference not found",
            severity="warning",
            details="extra detail",
        )
        assert issue.category == "broken_ref"
        assert issue.message == "Reference not found"

    def test_default_severity(self):
        issue = ScanAccuracyIssue(
            category="test", file="t.md", line=1, message="msg",
        )
        assert issue.severity == "error"


class TestDocumentationScannerDiscovery:
    """Inventory and discovery helpers."""

    def test_scanner_initialization(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        assert scanner.repo_root == tmp_path.resolve()
        assert scanner.results.total_files == 0

    def test_init_sets_defaults(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        assert scanner.results.scan_date is not None
        assert scanner.all_headings == {}
        assert scanner.script_files == []
        assert scanner.config_files == {}

    def test_discover_markdown_files(self, tmp_path):
        (tmp_path / "doc1.md").write_text("# Doc 1")
        (tmp_path / "doc2.md").write_text("# Doc 2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "doc3.md").write_text("# Doc 3")
        assert len(discover_markdown_files(tmp_path, scope="repo")) == 3

    def test_discover_markdown_files_skips_output(self, tmp_path):
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "skip.md").write_text("# Skip")
        files = discover_markdown_files(tmp_path, scope="repo")
        assert len(files) >= 2
        assert not any("output" in str(f) for f in files)

    def test_catalog_agents_readme(self, tmp_path):
        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "AGENTS.md").write_text("# Agents")
        (tmp_path / "other.md").write_text("# Other")
        md_files = discover_markdown_files(tmp_path, scope="repo")
        assert len(catalog_agents_readme(md_files, tmp_path)) == 2

    def test_find_config_files(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        (tmp_path / "config.yaml").write_text("key: value")
        assert len(find_config_files(tmp_path)) >= 1

    def test_find_script_files(self, tmp_path):
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("#!/usr/bin/env python3")
        (scripts_dir / "run.sh").write_text("#!/bin/bash")
        assert len(find_script_files(tmp_path)) >= 2

    def test_analyze_documentation_file(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Title

Some content here with [a link](other.md).

```python
print("code block")
```
"""
        )
        doc_file = analyze_documentation_file(md_file, tmp_path)
        assert doc_file.has_links is True
        assert doc_file.has_code_blocks is True
        assert doc_file.word_count > 0

    def test_discover_inventory(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "AGENTS.md").write_text("# Agents")
        scanner = DocumentationScanner(tmp_path)
        inventory = scanner.discover_inventory()
        assert inventory["markdown_files"] >= 2
        assert "agents_readme_files" in inventory
        assert "discovery" in scanner.results.statistics

    def test_discover_inventory_rich_repo(self, tmp_path):
        repo = _make_rich_repo(tmp_path)
        scanner = DocumentationScanner(repo)
        result = scanner.discover_inventory()
        assert result["markdown_files"] >= 2
        assert "hierarchy" in result
        assert scanner.results.total_files >= 2


class TestDocumentationScannerAccuracy:
    def test_verify_accuracy(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nSome content")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        accuracy = scanner.verify_accuracy()
        assert "link_issues" in accuracy
        assert "total_issues" in accuracy
        assert "accuracy" in scanner.results.statistics

    def test_verify_accuracy_with_links(self, tmp_path):
        (tmp_path / "README.md").write_text("# README\n\n[Link](existing.md)")
        (tmp_path / "existing.md").write_text("# Existing")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        result = scanner.verify_accuracy()
        assert "link_issues" in result

    def test_scan_with_broken_links(self, tmp_path):
        (tmp_path / "test.md").write_text(
            """# Test

See [missing link](nonexistent.md) for details.
Also check [section](#nonexistent-section).
"""
        )
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        scanner.verify_accuracy()
        assert "total_issues" in scanner.results.statistics.get("accuracy", {})


class TestDocumentationScannerCompleteness:
    def test_analyze_completeness(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        completeness = scanner.analyze_completeness()
        assert "total_gaps" in completeness
        assert "completeness" in scanner.results.statistics


class TestDocumentationScannerQuality:
    def test_assess_quality(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nParagraph content here.")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        quality = scanner.assess_quality()
        assert "total_issues" in quality
        assert "quality" in scanner.results.statistics


class TestDocumentationScannerImprovements:
    def test_identify_improvements(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        improvements = scanner.identify_improvements()
        assert isinstance(improvements, dict)
        assert "total_improvements" in improvements
        assert "improvements" in scanner.results.statistics

    def test_identify_link_fixes(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
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
        scanner = DocumentationScanner(tmp_path)
        scanner.results.quality_issues.append(
            QualityIssue(
                file="t.md", line=1, issue_type="formatting",
                issue_message="Heading level skip detected",
            )
        )
        improvements = scanner._identify_other_improvements()
        assert len(improvements) == 1
        assert improvements[0]["type"] == "structural"


class TestDocumentationScannerVerification:
    def test_run_verification_checks(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        verification = scanner.run_verification_checks()
        assert "link_checker" in verification
        assert "docs_lint" in verification
        assert "markdown_validation" in verification
        assert "commands_tested" in verification
        assert "circular_references" in verification
        assert "verification" in scanner.results.statistics

    def test_verification_includes_markdown_validation(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        (tmp_path / "test.md").write_text("# Test")
        result = scanner.run_verification_checks()
        assert "markdown_validation" in result
        assert result["markdown_validation"]["status"] in {"passed", "failed", "skipped"}

    def test_verification_includes_command_testing(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        (tmp_path / "test.md").write_text("# Test")
        result = scanner.run_verification_checks()
        assert "commands_tested" in result
        assert result["commands_tested"]["status"] in {"passed", "failed"}

    def test_verification_checks_circular_references(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        (tmp_path / "test.md").write_text("# Test")
        result = scanner.run_verification_checks()
        assert "circular_references" in result
        assert result["circular_references"]["status"] in {"passed", "failed"}

    def test_run_link_audit(self, tmp_path):
        result = run_link_audit(tmp_path)
        assert result["success"] is True
        assert result["exit_code"] == 0

    def test_verify_cross_references(self, tmp_path):
        (tmp_path / "test.md").write_text("# Test\n\nSee [link](other.md)")
        result = verify_cross_references(tmp_path)
        assert result["status"] == "verified"
        assert "total_references" in result

    def test_run_verification_checks_module(self, tmp_path):
        _setup_repo(tmp_path)
        result = run_verification_checks(tmp_path)
        assert "link_checker" in result
        assert "cross_references" in result


class TestDocumentationScannerReport:
    def test_build_scan_report_empty_results(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        scanner.results.scan_date = "2024-01-01T00:00:00"
        report = scanner.build_scan_report()
        assert "Documentation Scan and Improvement Report" in report
        assert "2024-01-01" in report

    def test_build_scan_report_with_files(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project\n\nDescription here.")
        (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent docs.")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        scanner.verify_accuracy()
        report = scanner.build_scan_report()
        assert "Documentation Scan and Improvement Report" in report
        assert "Discovery" in report

    def test_build_scan_report_with_issues(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        scanner.results.link_issues.append(
            LinkIssue("test.md", 1, "bad link", "missing.md", "broken", "Not found")
        )
        scanner.results.accuracy_issues.append(
            ScanAccuracyIssue(
                category="command",
                file="readme.md",
                line=5,
                message="Invalid command",
            )
        )
        scanner.results.completeness_gaps.append(
            CompletenessGap("API", "missing_docs", "Function not documented")
        )
        scanner.results.quality_issues.append(
            QualityIssue("doc.md", 10, "formatting", "Missing header")
        )
        report = scanner.build_scan_report()
        assert "Link Issues" in report or "Issues" in report

    def test_build_documentation_scan_report_core_sections(self):
        results = ScanResults(scan_date="2024-01-01T00:00:00", total_files=0)
        text = build_documentation_scan_report(results)
        assert "# Documentation Scan and Improvement Report" in text
        assert "## Executive Summary" in text
        assert "## Accuracy" in text


class TestDocumentationScannerFullRun:
    def test_run_full_scan(self, tmp_path):
        _setup_repo(tmp_path)
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert isinstance(results, ScanResults)
        assert isinstance(report, str)
        assert len(report) > 100
        assert "discovery" in results.statistics
        assert "accuracy" in results.statistics

    def test_full_scan_minimal_project(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project\n\nDescription.")
        (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent documentation.")
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide\n\nHow to use this.")
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert results.total_files >= 3
        assert len(report) > 0

    def test_empty_repo(self, tmp_path):
        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()
        assert results.total_files == 0
        assert isinstance(report, str)

    def test_statistics_populated(self, tmp_path):
        (tmp_path / "README.md").write_text("# README")
        scanner = DocumentationScanner(tmp_path)
        scanner.discover_inventory()
        scanner.verify_accuracy()
        scanner.analyze_completeness()
        scanner.assess_quality()
        assert "discovery" in scanner.results.statistics
        assert "accuracy" in scanner.results.statistics
        assert "completeness" in scanner.results.statistics
        assert "quality" in scanner.results.statistics


class TestDiscoveryModuleFunctions:
    def test_extract_headings(self):
        content = "# Title\n## Section\n### Subsection"
        headings = extract_headings(content)
        assert len(headings) >= 3

    def test_accuracy_issue_model(self):
        issue = ScanAccuracyIssue(
            category="command",
            file="doc.md",
            line=5,
            message="Command not found",
        )
        assert issue.category == "command"


class TestDocScannerModule:
    def test_doc_scanner_module_exists(self):
        assert doc_scanner is not None

    def test_main_function_exists(self):
        assert hasattr(doc_scanner, "main")
        assert callable(doc_scanner.main)


if __name__ == "__main__":
    pytest.main([__file__])
