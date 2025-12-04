"""Comprehensive tests for infrastructure/validation/validate_pdf_cli.py.

Tests PDF validation CLI functionality thoroughly.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY
import pytest


class TestValidatePdfCliModule:
    """Test module-level functionality."""
    
    def test_module_imports(self):
        """Test module imports correctly."""
        from infrastructure.validation import validate_pdf_cli
        assert validate_pdf_cli is not None


class TestPrintValidationReport:
    """Test print_validation_report function."""
    
    def test_print_report_no_issues(self, capsys):
        """Test printing report with no issues."""
        from infrastructure.validation.validate_pdf_cli import print_validation_report
        
        report = {
            'pdf_path': '/path/to/test.pdf',
            'issues': {
                'total_issues': 0,
                'unresolved_references': 0,
                'warnings': 0,
                'errors': 0,
                'missing_citations': 0,
            },
            'summary': {
                'has_issues': False,
                'word_count': 100,
            },
            'first_words': 'This is the beginning...'
        }
        
        print_validation_report(report)
        
        captured = capsys.readouterr()
        assert 'No rendering issues detected' in captured.out
        assert 'test.pdf' in captured.out
    
    def test_print_report_with_issues(self, capsys):
        """Test printing report with issues."""
        from infrastructure.validation.validate_pdf_cli import print_validation_report
        
        report = {
            'pdf_path': '/path/to/test.pdf',
            'issues': {
                'total_issues': 5,
                'unresolved_references': 2,
                'warnings': 1,
                'errors': 1,
                'missing_citations': 1,
            },
            'summary': {
                'has_issues': True,
                'word_count': 100,
            },
            'first_words': 'Content with issues...'
        }
        
        print_validation_report(report)
        
        captured = capsys.readouterr()
        assert 'Found 5 rendering issue' in captured.out
        assert 'Unresolved references' in captured.out
        assert 'Warnings' in captured.out
        assert 'Errors' in captured.out
        assert 'Missing citations' in captured.out
    
    def test_print_report_verbose(self, capsys):
        """Test printing report with verbose flag."""
        from infrastructure.validation.validate_pdf_cli import print_validation_report
        
        report = {
            'pdf_path': '/path/to/test.pdf',
            'issues': {'total_issues': 0, 'unresolved_references': 0, 
                      'warnings': 0, 'errors': 0, 'missing_citations': 0},
            'summary': {'has_issues': False, 'word_count': 100},
            'first_words': 'Content...'
        }
        
        print_validation_report(report, verbose=True)
        
        captured = capsys.readouterr()
        assert 'Full Report Details' in captured.out
        assert 'PDF Path' in captured.out


class TestMainFunction:
    """Test main function."""
    
    def test_main_success(self, tmp_path, capsys):
        """Test main with successful validation."""
        from infrastructure.validation import validate_pdf_cli
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.return_value = {
                'pdf_path': str(pdf),
                'issues': {'total_issues': 0, 'unresolved_references': 0,
                          'warnings': 0, 'errors': 0, 'missing_citations': 0},
                'summary': {'has_issues': False, 'word_count': 50},
                'first_words': 'Test content'
            }
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf)
            
            assert exit_code == 0
    
    def test_main_with_issues(self, tmp_path, capsys):
        """Test main with validation issues."""
        from infrastructure.validation import validate_pdf_cli
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.return_value = {
                'pdf_path': str(pdf),
                'issues': {'total_issues': 2, 'unresolved_references': 2,
                          'warnings': 0, 'errors': 0, 'missing_citations': 0},
                'summary': {'has_issues': True, 'word_count': 50},
                'first_words': 'Test content'
            }
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf)
            
            assert exit_code == 1
    
    def test_main_file_not_found(self, tmp_path, capsys):
        """Test main with missing PDF."""
        from infrastructure.validation import validate_pdf_cli
        
        missing_pdf = tmp_path / "missing.pdf"
        
        exit_code = validate_pdf_cli.main(pdf_path=missing_pdf)
        
        assert exit_code == 2
        captured = capsys.readouterr()
        assert 'not found' in captured.out
    
    def test_main_validation_error(self, tmp_path, capsys):
        """Test main with validation error."""
        from infrastructure.validation import validate_pdf_cli
        from infrastructure.validation.pdf_validator import PDFValidationError
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.side_effect = PDFValidationError("Validation failed")
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf)
            
            assert exit_code == 2
            captured = capsys.readouterr()
            assert 'Validation Error' in captured.out
    
    def test_main_unexpected_error(self, tmp_path, capsys):
        """Test main with unexpected error."""
        from infrastructure.validation import validate_pdf_cli
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf)
            
            assert exit_code == 2
            captured = capsys.readouterr()
            assert 'Unexpected Error' in captured.out
    
    def test_main_verbose_with_error(self, tmp_path, capsys):
        """Test main verbose mode with error shows traceback."""
        from infrastructure.validation import validate_pdf_cli
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.side_effect = Exception("Test error")
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf, verbose=True)
            
            assert exit_code == 2


class TestDefaultPdfPath:
    """Test default PDF path handling."""
    
    def test_main_default_path(self, capsys):
        """Test main uses default path when none specified."""
        from infrastructure.validation import validate_pdf_cli
        
        # Without a real PDF, should return error
        exit_code = validate_pdf_cli.main()
        
        # Should try default path and fail (file not found)
        assert exit_code == 2


class TestValidatePdfCliIntegration:
    """Integration tests."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        from infrastructure.validation import validate_pdf_cli
        
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF")
        
        with patch('infrastructure.validation.validate_pdf_cli.validate_pdf_rendering') as mock_validate:
            mock_validate.return_value = {
                'pdf_path': str(pdf),
                'issues': {'total_issues': 0, 'unresolved_references': 0,
                          'warnings': 0, 'errors': 0, 'missing_citations': 0},
                'summary': {'has_issues': False, 'word_count': 100},
                'first_words': 'Full test content here...'
            }
            
            exit_code = validate_pdf_cli.main(pdf_path=pdf, n_words=100, verbose=True)
            
            assert exit_code == 0




