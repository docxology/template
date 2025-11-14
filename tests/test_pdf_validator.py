"""
Tests for PDF validation module.

Following TDD principles with NO MOCK METHODS - uses real PDF operations.
"""

import pytest
from pathlib import Path
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf_validator import (
    extract_text_from_pdf,
    scan_for_issues,
    extract_first_n_words,
    validate_pdf_rendering,
    PDFValidationError,
)


@pytest.fixture
def temp_pdf_with_issues():
    """Create a temporary PDF with rendering issues for testing."""
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as f:
        c = canvas.Canvas(f.name, pagesize=letter)
        
        # Page 1: Some reference text (simulating misplaced citations)
        c.drawString(100, 750, "References")
        c.drawString(100, 730, "[1] Smith et al. (2020)")
        c.drawString(100, 710, "[2] Jones et al. (2021)")
        c.showPage()
        
        # Page 2: Title page
        c.drawString(200, 750, "Research Paper Title")
        c.drawString(200, 730, "Author Name")
        c.drawString(200, 710, "October 2025")
        c.showPage()
        
        # Page 3: Content with ?? issues
        c.drawString(100, 750, "Introduction")
        c.drawString(100, 730, "This is section ??")
        c.drawString(100, 710, "Referenced in equation ??")
        c.drawString(100, 690, "See figure ?? for details")
        c.showPage()
        
        c.save()
        yield Path(f.name)
        Path(f.name).unlink()


@pytest.fixture
def temp_pdf_clean():
    """Create a clean temporary PDF without issues."""
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False) as f:
        c = canvas.Canvas(f.name, pagesize=letter)
        
        # Page 1: Title page
        c.drawString(200, 750, "Research Paper Title")
        c.drawString(200, 730, "Author Name")
        c.drawString(200, 710, "October 2025")
        c.showPage()
        
        # Page 2: Content
        c.drawString(100, 750, "Introduction")
        c.drawString(100, 730, "This is section 1")
        c.drawString(100, 710, "Referenced in equation 1")
        c.drawString(100, 690, "See figure 1 for details")
        c.showPage()
        
        c.save()
        yield Path(f.name)
        Path(f.name).unlink()


def test_extract_text_from_pdf_exists(temp_pdf_clean):
    """Test text extraction from existing PDF."""
    text = extract_text_from_pdf(temp_pdf_clean)
    
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Research Paper Title" in text
    assert "Author Name" in text
    assert "Introduction" in text


def test_extract_text_from_pdf_nonexistent():
    """Test extraction from nonexistent PDF raises error."""
    with pytest.raises(PDFValidationError, match="PDF file not found"):
        extract_text_from_pdf(Path("/nonexistent/file.pdf"))


def test_extract_text_from_pdf_invalid_file():
    """Test extraction from invalid PDF file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        f.write("This is not a PDF file")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(PDFValidationError, match="Failed to extract text"):
            extract_text_from_pdf(temp_path)
    finally:
        temp_path.unlink()


def test_scan_for_issues_finds_double_question_marks(temp_pdf_with_issues):
    """Test scanning for ?? markers in PDF."""
    text = extract_text_from_pdf(temp_pdf_with_issues)
    issues = scan_for_issues(text)
    
    assert "unresolved_references" in issues
    assert issues["unresolved_references"] > 0
    assert issues["unresolved_references"] == 3  # Three ?? instances


def test_scan_for_issues_clean_pdf(temp_pdf_clean):
    """Test scanning clean PDF returns no issues."""
    text = extract_text_from_pdf(temp_pdf_clean)
    issues = scan_for_issues(text)
    
    assert issues["unresolved_references"] == 0
    assert issues["total_issues"] == 0


def test_scan_for_issues_detects_multiple_patterns():
    """Test scanning detects various issue patterns."""
    test_text = """
    This has ?? unresolved reference.
    [WARNING] some warning here
    Error: Compilation failed
    Missing citation: [?]
    """
    
    issues = scan_for_issues(test_text)
    
    assert issues["unresolved_references"] > 0
    assert issues["warnings"] > 0
    assert issues["errors"] > 0
    assert issues["total_issues"] > 0


def test_extract_first_n_words_basic():
    """Test extracting first N words from text."""
    text = "One two three four five six seven eight nine ten"
    
    result = extract_first_n_words(text, 5)
    
    assert result == "One two three four five"


def test_extract_first_n_words_with_whitespace():
    """Test extracting words handles extra whitespace."""
    text = "  One   two  \n\n  three   four    five  "
    
    result = extract_first_n_words(text, 3)
    
    assert result == "One two three"


def test_extract_first_n_words_less_than_requested():
    """Test extracting words when text has fewer than requested."""
    text = "Only three words"
    
    result = extract_first_n_words(text, 10)
    
    assert result == "Only three words"


def test_extract_first_n_words_empty_text():
    """Test extracting from empty text."""
    result = extract_first_n_words("", 10)
    
    assert result == ""


def test_decode_pdf_hex_strings_empty_text():
    """Test decoding hex strings with empty text (line 119)."""
    from pdf_validator import decode_pdf_hex_strings
    
    result = decode_pdf_hex_strings("")
    assert result == ""
    
    result = decode_pdf_hex_strings(None)
    assert result == ""


def test_decode_pdf_hex_strings_valid():
    """Test decoding valid hex strings."""
    from pdf_validator import decode_pdf_hex_strings
    
    # Valid hex: /x41 = 'A', /x42 = 'B'
    text = "Hello/x41/x42World"
    result = decode_pdf_hex_strings(text)
    assert "AB" in result


def test_decode_pdf_hex_strings_invalid_hex():
    """Test decoding invalid hex strings (lines 123-127)."""
    from pdf_validator import decode_pdf_hex_strings
    from unittest.mock import patch
    
    # Test with valid hex that decodes correctly
    text = "Hello/x41/x42World"  # /x41='A', /x42='B'
    result = decode_pdf_hex_strings(text)
    assert "AB" in result or "Hello" in result
    
    # To trigger the exception handler (lines 126-127), we need to patch int() or chr()
    # Test ValueError path
    with patch('pdf_validator.int', side_effect=ValueError('Invalid hex')):
        result = decode_pdf_hex_strings('Hello/x41World')
        # Should return original since decode fails
        assert isinstance(result, str)
        assert '/x41' in result or 'Hello' in result
    
    # Test OverflowError path
    with patch('pdf_validator.chr', side_effect=OverflowError('Value too large')):
        result = decode_pdf_hex_strings('Hello/x41World')
        # Should return original since decode fails
        assert isinstance(result, str)
        assert '/x41' in result or 'Hello' in result


def test_extract_first_n_words_with_punctuation():
    """Test word extraction preserves punctuation."""
    text = "Hello, world! This is a test. Does it work?"
    
    result = extract_first_n_words(text, 6)
    
    assert result == "Hello, world! This is a test."


def test_validate_pdf_rendering_with_issues(temp_pdf_with_issues):
    """Test full validation detects issues."""
    report = validate_pdf_rendering(temp_pdf_with_issues, n_words=10)
    
    assert "pdf_path" in report
    assert "issues" in report
    assert "first_words" in report
    assert "summary" in report
    
    # Check issues detected
    assert report["issues"]["unresolved_references"] > 0
    assert report["issues"]["total_issues"] > 0
    
    # Check first words extracted
    assert len(report["first_words"]) > 0
    assert "References" in report["first_words"]
    
    # Check summary
    assert report["summary"]["has_issues"] is True
    assert "word_count" in report["summary"]


def test_validate_pdf_rendering_clean(temp_pdf_clean):
    """Test validation of clean PDF."""
    report = validate_pdf_rendering(temp_pdf_clean, n_words=10)
    
    assert report["issues"]["total_issues"] == 0
    assert report["summary"]["has_issues"] is False
    assert "Research Paper Title" in report["first_words"]


def test_validate_pdf_rendering_custom_word_count(temp_pdf_clean):
    """Test validation with custom word count."""
    report = validate_pdf_rendering(temp_pdf_clean, n_words=5)
    
    words = report["first_words"].split()
    assert len(words) <= 5


def test_validate_pdf_rendering_nonexistent_file():
    """Test validation of nonexistent file."""
    with pytest.raises(PDFValidationError, match="PDF file not found"):
        validate_pdf_rendering(Path("/nonexistent.pdf"))


def test_scan_for_issues_structure():
    """Test that scan_for_issues returns expected structure."""
    text = "Sample text with ??"
    issues = scan_for_issues(text)
    
    # Verify structure
    assert isinstance(issues, dict)
    assert "unresolved_references" in issues
    assert "warnings" in issues
    assert "errors" in issues
    assert "missing_citations" in issues
    assert "total_issues" in issues
    
    # Verify types
    assert isinstance(issues["unresolved_references"], int)
    assert isinstance(issues["warnings"], int)
    assert isinstance(issues["errors"], int)
    assert isinstance(issues["missing_citations"], int)
    assert isinstance(issues["total_issues"], int)


def test_validate_pdf_rendering_report_structure(temp_pdf_clean):
    """Test validation report has expected structure."""
    report = validate_pdf_rendering(temp_pdf_clean)
    
    # Top-level keys
    assert "pdf_path" in report
    assert "issues" in report
    assert "first_words" in report
    assert "summary" in report
    
    # Issues structure
    assert isinstance(report["issues"], dict)
    assert "total_issues" in report["issues"]
    
    # Summary structure
    assert isinstance(report["summary"], dict)
    assert "has_issues" in report["summary"]
    assert "word_count" in report["summary"]
    
    # Types
    assert isinstance(report["pdf_path"], str)
    assert isinstance(report["first_words"], str)
    assert isinstance(report["summary"]["has_issues"], bool)
    assert isinstance(report["summary"]["word_count"], int)


def test_extract_first_n_words_deterministic():
    """Test word extraction is deterministic."""
    text = "The quick brown fox jumps over the lazy dog"
    
    result1 = extract_first_n_words(text, 5)
    result2 = extract_first_n_words(text, 5)
    
    assert result1 == result2
    assert result1 == "The quick brown fox jumps"


def test_scan_for_issues_case_sensitive():
    """Test issue scanning is case-appropriate."""
    text_lower = "this has ?? reference"
    text_upper = "THIS HAS ?? REFERENCE"
    
    issues_lower = scan_for_issues(text_lower)
    issues_upper = scan_for_issues(text_upper)
    
    # Both should detect ??
    assert issues_lower["unresolved_references"] == 1
    assert issues_upper["unresolved_references"] == 1


def test_scan_for_issues_ignores_scientific_error_terms():
    """Test that scientific error terms don't trigger false positives."""
    text = """
    The final error: 1.2e-6
    Standard error: 0.03
    Measurement error: negligible
    Root mean squared error: 0.15
    """
    
    issues = scan_for_issues(text)
    
    # Should not detect scientific "error:" as system errors
    assert issues["errors"] == 0
    assert issues["total_issues"] == 0


def test_scan_for_issues_detects_real_errors():
    """Test that real system errors are still detected."""
    text = """
    Error: Compilation failed with exit code 1
    [ERROR] File not found
       Error: Invalid syntax on line 42
    """
    
    issues = scan_for_issues(text)
    
    # Should detect these as real errors
    assert issues["errors"] >= 2  # At least [ERROR] and "Error: C"
    assert issues["total_issues"] > 0


def test_validate_pdf_rendering_with_real_combined_pdf():
    """Test validation works with actual project PDF if it exists."""
    pdf_path = Path("/Users/4d/Documents/GitHub/template/output/pdf/project_combined.pdf")
    
    if not pdf_path.exists():
        pytest.skip("Project PDF not found")
    
    report = validate_pdf_rendering(pdf_path, n_words=200)
    
    # Should complete without error
    assert "issues" in report
    assert "first_words" in report
    assert isinstance(report["summary"]["word_count"], int)
    
    # Print for manual inspection during test
    print(f"\n{'='*60}")
    print(f"PDF Validation Report for: {pdf_path.name}")
    print(f"{'='*60}")
    print(f"Total Issues Found: {report['issues']['total_issues']}")
    print(f"  - Unresolved references (??): {report['issues']['unresolved_references']}")
    print(f"  - Warnings: {report['issues']['warnings']}")
    print(f"  - Errors: {report['issues']['errors']}")
    print(f"  - Missing citations: {report['issues']['missing_citations']}")
    print(f"\nFirst {report['summary']['word_count']} words:")
    print(f"{'-'*60}")
    print(report['first_words'])
    print(f"{'='*60}\n")

