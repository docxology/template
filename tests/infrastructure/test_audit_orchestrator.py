#!/usr/bin/env python3
"""Tests for audit_orchestrator module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from infrastructure.validation.audit_orchestrator import (
    run_comprehensive_audit,
    generate_audit_report,
)
from infrastructure.validation.doc_models import ScanResults


class TestAuditOrchestrator:
    """Test audit orchestrator functionality."""

    @patch('infrastructure.validation.audit_orchestrator.find_markdown_files')
    @patch('infrastructure.validation.audit_orchestrator.extract_headings')
    @patch('infrastructure.validation.audit_orchestrator.check_links')
    @patch('infrastructure.validation.audit_orchestrator.validate_file_paths_in_code')
    @patch('infrastructure.validation.audit_orchestrator.validate_directory_structures')
    @patch('infrastructure.validation.audit_orchestrator.validate_python_imports')
    @patch('infrastructure.validation.audit_orchestrator.validate_placeholder_consistency')
    def test_run_comprehensive_audit_basic(
        self,
        mock_placeholder,
        mock_imports,
        mock_directory,
        mock_code,
        mock_links,
        mock_headings,
        mock_find_md,
        tmp_path
    ):
        """Test basic audit execution."""
        # Setup mocks
        mock_find_md.return_value = [tmp_path / "test.md"]
        mock_headings.return_value = set()
        mock_links.return_value = []
        mock_code.return_value = []
        mock_directory.return_value = []
        mock_imports.return_value = []
        mock_placeholder.return_value = []

        # Create test markdown file
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\nSome content.")

        # Run audit
        results = run_comprehensive_audit(tmp_path, verbose=False)

        # Verify results
        assert isinstance(results, ScanResults)
        assert results.scan_duration >= 0
        assert results.scanned_files >= 0

    def test_generate_audit_report_markdown(self, tmp_path):
        """Test markdown report generation."""
        # Create mock scan results
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
        """Test JSON report generation."""
        import json

        # Create mock scan results
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

    @patch('infrastructure.validation.audit_orchestrator.logger')
    def test_audit_with_validation_options(self, mock_logger, tmp_path):
        """Test audit with different validation options."""
        # Create test file
        test_md = tmp_path / "test.md"
        test_md.write_text("# Test\n\n```python\nimport os\n```")

        # Mock all validation functions to return empty results
        with patch('infrastructure.validation.audit_orchestrator.find_markdown_files', return_value=[test_md]), \
             patch('infrastructure.validation.audit_orchestrator.extract_headings', return_value=set()), \
             patch('infrastructure.validation.audit_orchestrator.check_links', return_value=[]), \
             patch('infrastructure.validation.audit_orchestrator.validate_file_paths_in_code', return_value=[]), \
             patch('infrastructure.validation.audit_orchestrator.validate_directory_structures', return_value=[]), \
             patch('infrastructure.validation.audit_orchestrator.validate_python_imports', return_value=[]), \
             patch('infrastructure.validation.audit_orchestrator.validate_placeholder_consistency', return_value=[]):

            # Run audit with all validations enabled
            results = run_comprehensive_audit(
                tmp_path,
                verbose=True,
                include_code_validation=True,
                include_directory_validation=True,
                include_import_validation=True,
                include_placeholder_validation=True
            )

            assert isinstance(results, ScanResults)
            mock_logger.info.assert_called()

    def test_audit_handles_file_read_errors(self, tmp_path):
        """Test audit handles file reading errors gracefully."""
        # Create a file that will cause read error
        test_md = tmp_path / "bad.md"

        with patch('infrastructure.validation.audit_orchestrator.find_markdown_files', return_value=[test_md]), \
             patch.object(Path, 'read_text', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):

            # Should not raise exception
            results = run_comprehensive_audit(tmp_path, verbose=False)

            assert isinstance(results, ScanResults)
            # Should have recorded quality issues for the problematic file
            assert len(results.quality_issues) > 0

    def test_audit_statistics_calculation(self, tmp_path):
        """Test that audit statistics are calculated correctly."""
        # Create mock scan results with known issue counts
        results = ScanResults(
            scan_date="2024-01-01 12:00:00",
            total_files=10
        )
        results.quality_issues = ['issue1', 'issue2', 'issue3']

        # Simulate the _calculate_statistics function being called
        from infrastructure.validation.audit_orchestrator import _calculate_statistics
        _calculate_statistics(results)

        # Verify statistics dictionary exists
        assert hasattr(results, 'statistics')
        assert isinstance(results.statistics, dict)
        assert 'quality_issues' in results.statistics