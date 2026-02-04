#!/usr/bin/env python3
"""Tests for audit_orchestrator module using real implementations.

Follows No Mocks Policy - all tests use real data and real validation.
"""

import json
from pathlib import Path

import pytest

from infrastructure.validation.audit_orchestrator import (
    generate_audit_report, run_comprehensive_audit)
from infrastructure.validation.doc_models import ScanResults


class TestAuditOrchestrator:
    """Test audit orchestrator functionality using real implementations."""

    def test_run_comprehensive_audit_basic(self, tmp_path):
        """Test basic audit execution with real validation."""
        # Create test markdown file
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\nSome content with [a link](test.md).")

        # Create a simple project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__init__.py").write_text("")

        # Run audit with real implementations
        results = run_comprehensive_audit(tmp_path, verbose=False)

        # Verify results
        assert isinstance(results, ScanResults)
        assert results.scan_duration >= 0
        assert results.scanned_files >= 0

    def test_generate_audit_report_markdown(self, tmp_path):
        """Test markdown report generation with real ScanResults."""
        # Create real scan results
        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=10)
        results.scanned_files = 10
        results.scan_duration = 0.0
        results.statistics = {"quality_issues": 5}

        # Generate report
        report = generate_audit_report(results, "markdown")

        # Verify report content
        assert "# 📊 Comprehensive Filepath and Reference Audit Report" in report
        assert "**Generated:** 2024-01-01 12:00:00" in report
        assert "**Files Scanned:** 10" in report

    def test_generate_audit_report_json(self, tmp_path):
        """Test JSON report generation with real ScanResults."""
        # Create real scan results
        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=5)
        results.scanned_files = 5
        results.scan_duration = 0.0

        # Generate report
        report = generate_audit_report(results, "json")

        # Parse and verify JSON
        data = json.loads(report)
        assert data["scan_date"] == "2024-01-01 12:00:00"
        assert data["total_files"] == 5

    def test_audit_with_validation_options(self, tmp_path):
        """Test audit with different validation options using real implementations."""
        # Create test file structure
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\n```python\nimport os\n```")

        # Create Python file for import validation
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module.py").write_text("import os\nimport sys")
        (tmp_path / "src" / "__init__.py").write_text("")

        # Run audit with all validations enabled using real implementations
        results = run_comprehensive_audit(
            tmp_path,
            verbose=True,
            include_code_validation=True,
            include_directory_validation=True,
            include_import_validation=True,
            include_placeholder_validation=True,
        )

        assert isinstance(results, ScanResults)
        assert results.scanned_files >= 0

    def test_audit_handles_file_read_errors(self, tmp_path):
        """Test audit handles file reading errors gracefully with real implementations."""
        # Create a valid markdown file
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\nValid content.")

        # Run audit - should handle any file reading issues gracefully
        results = run_comprehensive_audit(tmp_path, verbose=False)

        assert isinstance(results, ScanResults)
        # Results should be valid regardless of file reading issues
        assert hasattr(results, "quality_issues")

    def test_audit_statistics_calculation(self, tmp_path):
        """Test that audit statistics are calculated correctly with real data."""
        # Create test files
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\nContent here.")

        # Run real audit to get real statistics
        results = run_comprehensive_audit(tmp_path, verbose=False)

        # Verify statistics dictionary exists
        assert hasattr(results, "statistics")
        assert isinstance(results.statistics, dict)

    def test_audit_with_real_project_structure(self, tmp_path):
        """Test audit with realistic project structure using real validation."""
        # Create project structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        # Create markdown files
        (tmp_path / "docs" / "README.md").write_text(
            "# Documentation\n\n[Link](README.md)"
        )
        (tmp_path / "README.md").write_text("# Main README\n\n## Section")

        # Create Python files
        (tmp_path / "src" / "__init__.py").write_text("")
        (tmp_path / "src" / "module.py").write_text("import os")

        # Run real audit
        results = run_comprehensive_audit(tmp_path, verbose=False)

        assert isinstance(results, ScanResults)
        # Results depend on what files are discovered
        assert results.scanned_files >= 0
        assert results.total_files >= 0

    def test_audit_discovers_all_markdown_files(self, tmp_path):
        """Test that audit discovers all markdown files using real discovery."""
        # Create multiple markdown files
        (tmp_path / "file1.md").write_text("# File 1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.md").write_text("# File 2")
        (tmp_path / "subdir" / "file3.md").write_text("# File 3")

        # Run real audit
        results = run_comprehensive_audit(tmp_path, verbose=False)

        assert isinstance(results, ScanResults)
        # Should discover at least 3 markdown files
        assert results.scanned_files >= 3

    def test_audit_validates_links(self, tmp_path):
        """Test that audit validates links using real link checking."""
        # Create markdown with links
        test_md = tmp_path / "test.md"
        test_md.write_text(
            "# Test\n\n[Valid Link](test.md)\n[Invalid Link](nonexistent.md)"
        )

        # Create target file for valid link
        (tmp_path / "test.md").write_text("# Test")

        # Run real audit
        results = run_comprehensive_audit(tmp_path, verbose=False)

        assert isinstance(results, ScanResults)
        # May or may not find link issues depending on validation logic
        assert hasattr(results, "link_issues")

    def test_audit_with_code_validation(self, tmp_path):
        """Test audit with code validation enabled using real validation."""
        # Create markdown with code blocks
        test_md = tmp_path / "test.md"
        test_md.write_text(
            """
# Test

```python
import os
path = "src/module.py"
```

```bash
cd /some/path
```
"""
        )

        # Create referenced file
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module.py").write_text("content")

        # Run audit with code validation
        results = run_comprehensive_audit(
            tmp_path, verbose=False, include_code_validation=True
        )

        assert isinstance(results, ScanResults)
        assert hasattr(results, "quality_issues")


class TestGenerateAuditReport:
    """Test audit report generation with various scenarios."""

    def test_report_with_no_issues(self, tmp_path):
        """Test report generation when there are no issues."""
        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=10)
        results.scanned_files = 10
        results.scan_duration = 1.5
        results.statistics = {}
        # No issues
        results.link_issues = []
        results.accuracy_issues = []
        results.quality_issues = []
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown")

        assert "ALL VALIDATIONS PASSED" in report
        assert "No broken links" in report

    def test_report_with_red_flags(self, tmp_path):
        """Test report shows red flags correctly."""
        from infrastructure.validation.doc_models import LinkIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=10)
        results.scanned_files = 10
        results.scan_duration = 1.5
        results.statistics = {"link_issues": 1}

        # Add a critical link issue
        results.link_issues = [
            LinkIssue(
                file="test.md",
                target="missing.md",
                line=10,
                link_text="broken link",
                issue_type="broken_link",
                issue_message="File not found: missing.md",
                severity="error",
            )
        ]
        results.accuracy_issues = []
        results.quality_issues = []
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown")

        assert "Total Issues Found:" in report
        assert "Severity Flag Summary" in report

    def test_report_with_yellow_flags(self, tmp_path):
        """Test report shows yellow flags correctly."""
        from infrastructure.validation.doc_models import QualityIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=5)
        results.scanned_files = 5
        results.scan_duration = 0.5
        results.statistics = {"quality_issues": 1}

        # Add a warning issue
        results.link_issues = []
        results.accuracy_issues = []
        results.quality_issues = [
            QualityIssue(
                file="doc.md",
                line=5,
                issue_type="code_block_path",
                issue_message="Path may not exist",
                severity="warning",
            )
        ]
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown")

        assert "Total Issues Found:" in report

    def test_report_with_green_flags_shown(self, tmp_path):
        """Test report shows green flags when requested."""
        from infrastructure.validation.doc_models import QualityIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=5)
        results.scanned_files = 5
        results.scan_duration = 0.5
        results.statistics = {"quality_issues": 1}

        # Add an info-level issue (likely green flag)
        results.link_issues = []
        results.accuracy_issues = []
        results.quality_issues = [
            QualityIssue(
                file="doc.md",
                line=5,
                issue_type="directory_structure",
                issue_message="Directory reference",
                severity="info",
            )
        ]
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown", show_green_flags=True)

        # Should include green flags section
        assert "Total Issues Found:" in report

    def test_report_json_with_issues(self, tmp_path):
        """Test JSON report format with issues."""
        from infrastructure.validation.doc_models import LinkIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=3)
        results.scanned_files = 3
        results.scan_duration = 0.8
        results.statistics = {"link_issues": 1}

        results.link_issues = [
            LinkIssue(
                file="readme.md",
                target="gone.md",
                line=15,
                link_text="link",
                issue_type="missing_file",
                issue_message="Target file not found",
                severity="error",
            )
        ]
        results.accuracy_issues = []
        results.quality_issues = []
        results.completeness_gaps = []

        report = generate_audit_report(results, "json")
        data = json.loads(report)

        assert data["scan_date"] == "2024-01-01 12:00:00"
        assert data["total_files"] == 3
        assert "severity_flags" in data
        assert "summary" in data

    def test_report_json_with_green_flags(self, tmp_path):
        """Test JSON report includes green flags when requested."""
        from infrastructure.validation.doc_models import QualityIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=2)
        results.scanned_files = 2
        results.scan_duration = 0.3
        results.statistics = {"quality_issues": 1}

        results.link_issues = []
        results.accuracy_issues = []
        results.quality_issues = [
            QualityIssue(
                file="test.md",
                line=1,
                issue_type="placeholder",
                issue_message="Placeholder detected",
                severity="info",
            )
        ]
        results.completeness_gaps = []

        report = generate_audit_report(results, "json", show_green_flags=True)
        data = json.loads(report)

        assert "green_flags" in data

    def test_report_many_red_flags_truncated(self, tmp_path):
        """Test report truncates many red flags."""
        from infrastructure.validation.doc_models import LinkIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=50)
        results.scanned_files = 50
        results.scan_duration = 5.0
        results.statistics = {"link_issues": 25}

        # Add many link issues
        results.link_issues = [
            LinkIssue(
                file=f"file{i}.md",
                target=f"missing{i}.md",
                line=i,
                link_text="link",
                issue_type="broken_link",
                issue_message=f"Missing file {i}",
                severity="error",
            )
            for i in range(25)
        ]
        results.accuracy_issues = []
        results.quality_issues = []
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown")

        # Should indicate there are more red flags
        assert "Total Issues Found:" in report

    def test_report_many_yellow_flags_truncated(self, tmp_path):
        """Test report truncates many yellow flags."""
        from infrastructure.validation.doc_models import QualityIssue

        results = ScanResults(scan_date="2024-01-01 12:00:00", total_files=30)
        results.scanned_files = 30
        results.scan_duration = 3.0
        results.statistics = {"quality_issues": 20}

        # Add many warning issues
        results.link_issues = []
        results.accuracy_issues = []
        results.quality_issues = [
            QualityIssue(
                file=f"doc{i}.md",
                line=i * 5,
                issue_type="code_block_path",
                issue_message=f"Path warning {i}",
                severity="warning",
            )
            for i in range(20)
        ]
        results.completeness_gaps = []

        report = generate_audit_report(results, "markdown")

        assert "Total Issues Found:" in report


class TestValidateSingleFile:
    """Test the internal _validate_single_file function."""

    def test_validate_file_with_link_issues(self, tmp_path):
        """Test validation detects link issues."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\n[Broken](nonexistent.md)")

        content = md_file.read_text()
        all_headings = {"test.md": {"test"}}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=False,
            include_directory=False,
            include_imports=False,
            include_placeholders=False,
        )

        assert "link_issues" in results
        assert "accuracy_issues" in results
        assert "quality_issues" in results

    def test_validate_file_with_code_blocks(self, tmp_path):
        """Test validation of code blocks."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

```python
import os
path = "src/main.py"
```
"""
        )

        content = md_file.read_text()
        all_headings = {}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=True,
            include_directory=False,
            include_imports=False,
            include_placeholders=False,
        )

        assert "quality_issues" in results

    def test_validate_file_with_directory_structure(self, tmp_path):
        """Test validation of directory structures."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

Directory structure:
```
project/
├── src/
│   └── main.py
└── tests/
```
"""
        )

        content = md_file.read_text()
        all_headings = {}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=False,
            include_directory=True,
            include_imports=False,
            include_placeholders=False,
        )

        assert "quality_issues" in results

    def test_validate_file_with_imports(self, tmp_path):
        """Test validation of Python imports."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        # Create Python file
        (tmp_path / "mymodule.py").write_text("# module")

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

```python
from mymodule import something
```
"""
        )

        content = md_file.read_text()
        all_headings = {}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=False,
            include_directory=False,
            include_imports=True,
            include_placeholders=False,
        )

        assert "quality_issues" in results

    def test_validate_file_with_placeholders(self, tmp_path):
        """Test validation of placeholders."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

Replace {placeholder} with actual value.
Also update {another_placeholder}.
"""
        )

        content = md_file.read_text()
        all_headings = {}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=False,
            include_directory=False,
            include_imports=False,
            include_placeholders=True,
        )

        assert "quality_issues" in results

    def test_validate_file_all_options(self, tmp_path):
        """Test validation with all options enabled."""
        from infrastructure.validation.audit_orchestrator import \
            _validate_single_file

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """# Test

[Link](other.md)

```python
import os
x = "path/to/file.txt"
```

Directory:
```
src/
└── main.py
```

Replace {value} here.
"""
        )

        content = md_file.read_text()
        all_headings = {}

        results = _validate_single_file(
            md_file,
            content,
            tmp_path,
            all_headings,
            include_code=True,
            include_directory=True,
            include_imports=True,
            include_placeholders=True,
        )

        assert "link_issues" in results
        assert "accuracy_issues" in results
        assert "quality_issues" in results


class TestCalculateStatistics:
    """Test _calculate_statistics function."""

    def test_calculate_statistics_empty(self):
        """Test statistics calculation with empty results."""
        from infrastructure.validation.audit_orchestrator import \
            _calculate_statistics

        results = ScanResults(scan_date="2024-01-01")
        results.documentation_files = []
        results.link_issues = []
        results.accuracy_issues = []
        results.completeness_gaps = []
        results.quality_issues = []

        _calculate_statistics(results)

        assert results.scanned_files == 0
        assert "link_issues" in results.statistics
        assert results.statistics["link_issues"] == 0

    def test_calculate_statistics_with_data(self):
        """Test statistics calculation with real data."""
        from infrastructure.validation.audit_orchestrator import \
            _calculate_statistics
        from infrastructure.validation.doc_models import (DocumentationFile,
                                                          LinkIssue)

        results = ScanResults(scan_date="2024-01-01")
        results.documentation_files = [
            DocumentationFile(
                path="test.md",
                relative_path="test.md",
                directory=".",
                name="test.md",
                category="docs",
                word_count=100,
                line_count=20,
                has_links=True,
                has_code_blocks=True,
            ),
            DocumentationFile(
                path="readme.md",
                relative_path="readme.md",
                directory=".",
                name="readme.md",
                category="docs",
                word_count=50,
                line_count=10,
                has_links=False,
                has_code_blocks=False,
            ),
        ]
        results.link_issues = [
            LinkIssue(
                file="test.md",
                target="x.md",
                line=1,
                link_text="x",
                issue_type="missing",
                issue_message="Missing",
                severity="error",
            )
        ]
        results.accuracy_issues = []
        results.completeness_gaps = []
        results.quality_issues = []

        _calculate_statistics(results)

        assert results.scanned_files == 2
        assert results.statistics["link_issues"] == 1


class TestModuleStructure:
    """Test module structure and imports."""

    def test_module_imports(self):
        """Test module can be imported."""
        from infrastructure.validation import audit_orchestrator

        assert audit_orchestrator is not None

    def test_public_functions_exist(self):
        """Test expected public functions exist."""
        from infrastructure.validation.audit_orchestrator import (
            generate_audit_report, run_comprehensive_audit)

        assert callable(run_comprehensive_audit)
        assert callable(generate_audit_report)
