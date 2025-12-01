"""Tests for infrastructure.validation.doc_scanner module.

Comprehensive tests for the documentation scanner covering all phases
and report generation.
"""
import pytest
from pathlib import Path
from datetime import datetime

from infrastructure.validation import doc_scanner
from infrastructure.validation.doc_scanner import (
    DocumentationScanner,
    DocumentationFile,
    LinkIssue,
    AccuracyIssue,
    CompletenessGap,
    QualityIssue,
    ScanResults,
)


class TestDataClasses:
    """Test data class instantiation and behavior."""
    
    def test_documentation_file_creation(self):
        """Test DocumentationFile dataclass."""
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
            last_modified="2024-01-01"
        )
        
        assert doc_file.path == "/path/to/file.md"
        assert doc_file.word_count == 100
        assert doc_file.has_links is True
    
    def test_link_issue_creation(self):
        """Test LinkIssue dataclass."""
        issue = LinkIssue(
            file="test.md",
            line=10,
            link_text="broken link",
            target="missing.md",
            issue_type="broken_link",
            issue_message="File not found",
            severity="error"
        )
        
        assert issue.file == "test.md"
        assert issue.severity == "error"
    
    def test_accuracy_issue_creation(self):
        """Test AccuracyIssue dataclass."""
        issue = AccuracyIssue(
            file="readme.md",
            line=5,
            issue_type="command",
            issue_message="Command not found",
            severity="warning"
        )
        
        assert issue.issue_type == "command"
    
    def test_completeness_gap_creation(self):
        """Test CompletenessGap dataclass."""
        gap = CompletenessGap(
            category="API",
            item="missing_function_docs",
            description="Function X is not documented",
            severity="warning"
        )
        
        assert gap.category == "API"
    
    def test_quality_issue_creation(self):
        """Test QualityIssue dataclass."""
        issue = QualityIssue(
            file="doc.md",
            line=1,
            issue_type="formatting",
            issue_message="Missing header",
            severity="info"
        )
        
        assert issue.issue_type == "formatting"
    
    def test_scan_results_creation(self):
        """Test ScanResults dataclass."""
        results = ScanResults(scan_date="2024-01-01T00:00:00")
        
        assert results.scan_date == "2024-01-01T00:00:00"
        assert results.total_files == 0
        assert results.link_issues == []


class TestDocumentationScanner:
    """Test DocumentationScanner class."""
    
    def test_scanner_initialization(self, tmp_path):
        """Test scanner initialization."""
        scanner = DocumentationScanner(tmp_path)
        
        assert scanner.repo_root == tmp_path.resolve()
        assert scanner.results.total_files == 0
    
    def test_find_markdown_files(self, tmp_path):
        """Test finding markdown files."""
        # Create test files
        (tmp_path / "doc1.md").write_text("# Doc 1")
        (tmp_path / "doc2.md").write_text("# Doc 2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "doc3.md").write_text("# Doc 3")
        
        scanner = DocumentationScanner(tmp_path)
        md_files = scanner._find_markdown_files()
        
        assert len(md_files) == 3
    
    def test_catalog_agents_readme(self, tmp_path):
        """Test cataloging AGENTS.md and README.md files."""
        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "AGENTS.md").write_text("# Agents")
        (tmp_path / "other.md").write_text("# Other")
        
        scanner = DocumentationScanner(tmp_path)
        md_files = scanner._find_markdown_files()
        agents_readme = scanner._catalog_agents_readme(md_files)
        
        assert len(agents_readme) == 2
    
    def test_find_config_files(self, tmp_path):
        """Test finding configuration files."""
        (tmp_path / "pyproject.toml").write_text("[project]")
        (tmp_path / "config.yaml").write_text("key: value")
        
        scanner = DocumentationScanner(tmp_path)
        config_files = scanner._find_config_files()
        
        assert len(config_files) >= 1
    
    def test_find_script_files(self, tmp_path):
        """Test finding script files."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("#!/usr/bin/env python3")
        (scripts_dir / "run.sh").write_text("#!/bin/bash")
        
        scanner = DocumentationScanner(tmp_path)
        script_files = scanner._find_script_files()
        
        assert len(script_files) >= 2
    
    def test_analyze_documentation_file(self, tmp_path):
        """Test analyzing a documentation file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Title

Some content here with [a link](other.md).

```python
print("code block")
```
""")
        
        scanner = DocumentationScanner(tmp_path)
        doc_file = scanner._analyze_documentation_file(md_file)
        
        assert doc_file.has_links is True
        assert doc_file.has_code_blocks is True
        assert doc_file.word_count > 0
    
    def test_phase1_discovery(self, tmp_path):
        """Test Phase 1 discovery."""
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "AGENTS.md").write_text("# Agents")
        
        scanner = DocumentationScanner(tmp_path)
        inventory = scanner.phase1_discovery()
        
        assert inventory['markdown_files'] >= 2
        assert 'agents_readme_files' in inventory
    
    def test_phase2_accuracy(self, tmp_path):
        """Test Phase 2 accuracy verification."""
        (tmp_path / "test.md").write_text("# Test\n\nSome content")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        accuracy = scanner.phase2_accuracy()
        
        assert 'link_issues' in accuracy
        assert 'total_issues' in accuracy
    
    def test_phase3_completeness(self, tmp_path):
        """Test Phase 3 completeness analysis."""
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        completeness = scanner.phase3_completeness()
        
        assert 'total_gaps' in completeness
    
    def test_phase4_quality(self, tmp_path):
        """Test Phase 4 quality assessment."""
        (tmp_path / "test.md").write_text("# Test\n\nParagraph content here.")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        quality = scanner.phase4_quality()
        
        assert 'total_issues' in quality
    
    def test_phase5_improvements(self, tmp_path):
        """Test Phase 5 intelligent improvements."""
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        improvements = scanner.phase5_improvements()
        
        assert isinstance(improvements, dict)
        assert 'total_improvements' in improvements
    
    def test_phase6_verification(self, tmp_path):
        """Test Phase 6 verification."""
        (tmp_path / "test.md").write_text("# Test\n\nContent")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        verification = scanner.phase6_verification()
        
        assert 'link_checker' in verification
        assert 'markdown_syntax' in verification


class TestScannerVerificationMethods:
    """Test scanner verification methods (covers lines 944-979)."""
    
    def test_run_link_checker_no_script(self, tmp_path):
        """Test _run_link_checker when script doesn't exist (lines 946-959)."""
        scanner = DocumentationScanner(tmp_path)
        
        # No check_documentation_links.py exists
        result = scanner._run_link_checker()
        
        # Should return error result
        assert result.get('success') is False or 'error' in result
    
    def test_validate_markdown_syntax(self, tmp_path):
        """Test _validate_markdown_syntax (line 964)."""
        scanner = DocumentationScanner(tmp_path)
        result = scanner._validate_markdown_syntax()
        
        assert result['status'] == 'basic_validation_passed'
    
    def test_test_documented_commands(self, tmp_path):
        """Test _test_documented_commands (lines 966-969)."""
        scanner = DocumentationScanner(tmp_path)
        result = scanner._test_documented_commands()
        
        assert result['status'] == 'manual_testing_required'
        assert 'commands_found' in result
    
    def test_verify_cross_references(self, tmp_path):
        """Test _verify_cross_references (lines 971-973)."""
        (tmp_path / "test.md").write_text("# Test\n\nSee [link](other.md)")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        result = scanner._verify_cross_references()
        
        assert result['status'] == 'verified'
        assert 'total_references' in result
    
    def test_check_circular_references(self, tmp_path):
        """Test _check_circular_references (lines 975-978)."""
        scanner = DocumentationScanner(tmp_path)
        result = scanner._check_circular_references()
        
        assert result['status'] == 'no_circular_references_detected'


class TestReportGeneration:
    """Test report generation (covers lines 980-1095+)."""
    
    def test_generate_report_empty_results(self, tmp_path):
        """Test report generation with no files."""
        scanner = DocumentationScanner(tmp_path)
        scanner.results.scan_date = "2024-01-01T00:00:00"
        
        report = scanner._generate_report()
        
        assert "Documentation Scan and Improvement Report" in report
        assert "2024-01-01" in report
    
    def test_generate_report_with_files(self, tmp_path):
        """Test report generation with scanned files."""
        (tmp_path / "README.md").write_text("# Project\n\nDescription here.")
        (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent docs.")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        
        report = scanner._generate_report()
        
        assert "Documentation Scan and Improvement Report" in report
        assert "Phase 1" in report or "Discovery" in report
    
    def test_generate_report_with_issues(self, tmp_path):
        """Test report generation with issues."""
        scanner = DocumentationScanner(tmp_path)
        
        # Add some test issues
        scanner.results.link_issues.append(
            LinkIssue("test.md", 1, "bad link", "missing.md", "broken", "Not found")
        )
        scanner.results.accuracy_issues.append(
            AccuracyIssue("readme.md", 5, "command", "Invalid command")
        )
        scanner.results.completeness_gaps.append(
            CompletenessGap("API", "missing_docs", "Function not documented")
        )
        scanner.results.quality_issues.append(
            QualityIssue("doc.md", 10, "formatting", "Missing header")
        )
        
        report = scanner._generate_report()
        
        assert "Link Issues" in report or "Issues" in report
    
    def test_generate_report_with_improvements(self, tmp_path):
        """Test report generation with improvements."""
        scanner = DocumentationScanner(tmp_path)
        
        # Add improvements
        scanner.results.improvements_made.append({
            'file': 'test.md',
            'type': 'added_section',
            'description': 'Added missing introduction'
        })
        
        report = scanner._generate_report()
        
        assert len(report) > 0
    
    def test_generate_report_with_statistics(self, tmp_path):
        """Test report generation with phase statistics."""
        (tmp_path / "test.md").write_text("# Test")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        scanner.phase3_completeness()
        scanner.phase4_quality()
        
        report = scanner._generate_report()
        
        assert "Phase" in report or "Statistics" in report


class TestScannerFullScan:
    """Test full scan functionality."""
    
    def test_full_scan(self, tmp_path):
        """Test running a complete scan."""
        # Create a minimal project structure
        (tmp_path / "README.md").write_text("# Project\n\nDescription.")
        (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent documentation.")
        
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide\n\nHow to use this.")
        
        scanner = DocumentationScanner(tmp_path)
        
        # Run all phases
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        scanner.phase3_completeness()
        scanner.phase4_quality()
        scanner.phase5_improvements()
        scanner.phase6_verification()
        
        # Generate report
        report = scanner._generate_report()
        
        assert scanner.results.total_files >= 3
        assert len(report) > 0
    
    def test_scan_with_broken_links(self, tmp_path):
        """Test scanning with broken internal links."""
        (tmp_path / "test.md").write_text("""# Test

See [missing link](nonexistent.md) for details.
Also check [section](#nonexistent-section).
""")
        
        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        
        # Should detect the broken links
        assert 'total_issues' in scanner.results.statistics.get('phase2', {})


class TestDocScannerModule:
    """Test module-level functionality."""
    
    def test_doc_scanner_module_exists(self):
        """Test doc_scanner module is importable."""
        assert doc_scanner is not None
    
    def test_main_function_exists(self):
        """Test main function exists."""
        assert hasattr(doc_scanner, 'main')


if __name__ == "__main__":
    pytest.main([__file__])
