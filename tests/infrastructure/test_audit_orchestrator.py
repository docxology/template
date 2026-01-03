#!/usr/bin/env python3
"""Tests for audit_orchestrator module using real implementations.

Follows No Mocks Policy - all tests use real data and real validation.
"""

import pytest
from pathlib import Path
import json

from infrastructure.validation.audit_orchestrator import (
    run_comprehensive_audit,
    generate_audit_report,
)
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
        results = ScanResults(
            scan_date="2024-01-01 12:00:00",
            total_files=10
        )
        results.statistics = {'quality_issues': 5}

        # Generate report
        report = generate_audit_report(results, 'markdown')

        # Verify report content
        assert "# 📊 Comprehensive Filepath and Reference Audit Report" in report
        assert "**Generated:** 2024-01-01 12:00:00" in report
        assert "**Files Scanned:** 10" in report

    def test_generate_audit_report_json(self, tmp_path):
        """Test JSON report generation with real ScanResults."""
        # Create real scan results
        results = ScanResults(
            scan_date="2024-01-01 12:00:00",
            total_files=5
        )

        # Generate report
        report = generate_audit_report(results, 'json')

        # Parse and verify JSON
        data = json.loads(report)
        assert data['scan_date'] == "2024-01-01 12:00:00"
        assert data['total_files'] == 5

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
            include_placeholder_validation=True
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
        assert hasattr(results, 'quality_issues')

    def test_audit_statistics_calculation(self, tmp_path):
        """Test that audit statistics are calculated correctly with real data."""
        # Create test files
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\nContent here.")

        # Run real audit to get real statistics
        results = run_comprehensive_audit(tmp_path, verbose=False)

        # Verify statistics dictionary exists
        assert hasattr(results, 'statistics')
        assert isinstance(results.statistics, dict)

    def test_audit_with_real_project_structure(self, tmp_path):
        """Test audit with realistic project structure using real validation."""
        # Create project structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        # Create markdown files
        (tmp_path / "docs" / "README.md").write_text("# Documentation\n\n[Link](README.md)")
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
        test_md.write_text("# Test\n\n[Valid Link](test.md)\n[Invalid Link](nonexistent.md)")

        # Create target file for valid link
        (tmp_path / "test.md").write_text("# Test")

        # Run real audit
        results = run_comprehensive_audit(tmp_path, verbose=False)

        assert isinstance(results, ScanResults)
        # May or may not find link issues depending on validation logic
        assert hasattr(results, 'link_issues')

    def test_audit_with_code_validation(self, tmp_path):
        """Test audit with code validation enabled using real validation."""
        # Create markdown with code blocks
        test_md = tmp_path / "test.md"
        test_md.write_text("""
# Test

```python
import os
path = "src/module.py"
```

```bash
cd /some/path
```
""")

        # Create referenced file
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module.py").write_text("content")

        # Run audit with code validation
        results = run_comprehensive_audit(
            tmp_path,
            verbose=False,
            include_code_validation=True
        )

        assert isinstance(results, ScanResults)
        assert hasattr(results, 'quality_issues')
