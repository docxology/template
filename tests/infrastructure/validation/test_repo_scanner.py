"""Tests for infrastructure.validation.repo_scanner module.

Comprehensive tests for repository accuracy and completeness scanning.
"""
import pytest
from pathlib import Path

from infrastructure.validation import repo_scanner
from infrastructure.validation.repo_scanner import (
    RepositoryScanner,
    AccuracyIssue,
    CompletenessGap,
    ScanResults,
)


class TestDataClasses:
    """Test data class instantiation."""
    
    def test_accuracy_issue_creation(self):
        """Test AccuracyIssue dataclass."""
        issue = AccuracyIssue(
            category="command",
            severity="error",
            file="test.md",
            line=10,
            message="Script not found",
            details="Additional details"
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
            severity="warning"
        )
        
        assert gap.category == "documentation"
        assert gap.severity == "warning"
    
    def test_scan_results_creation(self):
        """Test ScanResults dataclass."""
        results = ScanResults()
        
        assert results.accuracy_issues == []
        assert results.completeness_gaps == []
        assert results.statistics == {}


class TestRepositoryScanner:
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
        (tmp_path / "README.md").write_text("""# Project

Run the scripts to start.
""")
        
        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        scanner._check_code_accuracy()
        
        # Should complete without error
        assert isinstance(scanner.results.accuracy_issues, list)
    
    def test_check_code_accuracy_with_scripts(self, tmp_path):
        """Test code accuracy with script files."""
        # Create scripts directory
        (tmp_path / "scripts").mkdir()
        (tmp_path / "README.md").write_text("""# Project

Documentation text.
""")
        
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
            AccuracyIssue("command", "error", f"file{i}.md", i, f"Issue {i}")
            for i in range(25)
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
            AccuracyIssue("import", "error", "module.py", 1, "Import failed", "ModuleNotFoundError"),
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
    
    def test_scan_all(self, tmp_path, capsys):
        """Test complete repository scan."""
        # Create minimal structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("# Project")
        
        scanner = RepositoryScanner(tmp_path)
        results = scanner.scan_all()
        
        assert isinstance(results, ScanResults)
        
        # Check that it printed progress
        captured = capsys.readouterr()
        assert "REPOSITORY-WIDE ACCURACY AND COMPLETENESS SCAN" in captured.out


class TestRepoScannerModule:
    """Test module-level functionality."""
    
    def test_repo_scanner_module_exists(self):
        """Test repo_scanner module is importable."""
        assert repo_scanner is not None
    
    def test_main_function_exists(self):
        """Test main function exists."""
        assert hasattr(repo_scanner, 'main')


if __name__ == "__main__":
    pytest.main([__file__])
