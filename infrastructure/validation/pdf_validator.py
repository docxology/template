"""
PDF validation module for detecting rendering issues and verifying document structure.

This module provides functions to:
- Extract text from PDF files
- Scan for rendering issues (unresolved references, warnings, errors)
- Extract first N words to verify document structure
- Generate comprehensive validation reports

All functions are pure business logic with no I/O side effects.
"""

from pathlib import Path
from typing import Dict, Any
import re
import io
import contextlib
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import PDFValidationError


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text content from a PDF file with robust error handling and fallbacks.

    Performs comprehensive validation and uses multiple PDF libraries as fallbacks
    for maximum compatibility with different PDF formats and corruption levels.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a single string

    Raises:
        PDFValidationError: If file doesn't exist, is corrupted, or text extraction fails
    """
    if not pdf_path.exists():
        raise PDFValidationError(f"PDF file not found: {pdf_path}")

    logger = get_logger(__name__)

    # Validate PDF file size and basic integrity
    file_size = pdf_path.stat().st_size
    logger.debug(f"PDF file size: {file_size} bytes ({file_size/1024:.1f} KB)")

    if file_size < 1000:  # Less than 1KB
        raise PDFValidationError(
            f"PDF file is too small ({file_size} bytes) - likely corrupted or empty"
        )

    if file_size > 100 * 1024 * 1024:  # More than 100MB
        raise PDFValidationError(
            f"PDF file is too large ({file_size/1024/1024:.1f} MB) - exceeds safety limit"
        )

    # Try extraction with multiple libraries in order of preference
    extraction_methods = [
        ("pypdf", _extract_with_pypdf),
        ("pdfplumber", _extract_with_pdfplumber),
        ("PyPDF2", _extract_with_pypdf2),
    ]

    last_error = None
    for method_name, extract_func in extraction_methods:
        try:
            logger.debug(f"Attempting PDF text extraction with {method_name}")
            text = extract_func(pdf_path)
            if text and text.strip():
                logger.debug(f"Successfully extracted {len(text)} characters with {method_name}")
                return text
            else:
                logger.debug(f"{method_name} returned empty text, trying next method")
                continue
        except ImportError:
            logger.debug(f"{method_name} library not available, skipping")
            continue
        except Exception as e:
            error_msg = f"{method_name} extraction failed: {e}"
            logger.debug(error_msg)
            last_error = e
            continue

    # All methods failed
    error_details = []
    if last_error:
        error_details.append(f"Last error: {last_error}")

    # Try to provide additional diagnostics
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF-'):
                error_details.append("File does not have valid PDF header")
            else:
                error_details.append(f"PDF header detected: {header[:8]}")
    except Exception as diag_error:
        error_details.append(f"Could not read PDF header: {diag_error}")

    error_details.append(f"File size: {file_size} bytes")
    error_details.append("Tried extraction methods: pypdf, pdfplumber, PyPDF2")

    raise PDFValidationError(
        f"Failed to extract text from PDF after trying all available methods. "
        f"PDF may be corrupted, password-protected, or contain only images. "
        f"Details: {'; '.join(error_details)}"
    )


def _extract_with_pypdf(pdf_path: Path) -> str:
    """Extract text using pypdf library."""
    from pypdf import PdfReader
    import io
    import contextlib

    with open(pdf_path, 'rb') as file:
        # Capture stderr to suppress pypdf warnings
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            pdf_reader = PdfReader(file)
            text_parts = []

            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

        return '\n'.join(text_parts)


def _extract_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber library."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return '\n\n'.join(text_parts)


def _extract_with_pypdf2(pdf_path: Path) -> str:
    """Extract text using PyPDF2 library."""
    import PyPDF2

    text_parts = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return '\n\n'.join(text_parts)


def scan_for_issues(text: str) -> Dict[str, int]:
    """
    Scan extracted text for common rendering issues.
    
    Detects:
    - Unresolved references (??): LaTeX/Markdown reference that didn't resolve
    - Warnings: [WARNING] or Warning: patterns
    - Errors: Error: or [ERROR] patterns
    - Missing citations: [?] patterns
    
    Args:
        text: Extracted text from PDF
        
    Returns:
        Dictionary with issue counts:
        {
            'unresolved_references': int,
            'warnings': int,
            'errors': int,
            'missing_citations': int,
            'total_issues': int
        }
    """
    issues = {
        'unresolved_references': 0,
        'warnings': 0,
        'errors': 0,
        'missing_citations': 0,
    }
    
    # Count unresolved references (??)
    issues['unresolved_references'] = len(re.findall(r'\?\?', text))
    
    # Count warnings (case-insensitive)
    issues['warnings'] = len(re.findall(r'\[WARNING\]|Warning:', text, re.IGNORECASE))
    
    # Count errors (case-insensitive, but exclude common false positives)
    # Match [ERROR] or "Error:" only when it appears to be a system message
    # Exclude scientific terms like "standard error:", "final error:", "measurement error:"
    issues['errors'] = len(re.findall(r'\[ERROR\]|^\s*Error:\s|Error:\s+[A-Z]', text, re.MULTILINE))
    
    # Count missing citations [?]
    issues['missing_citations'] = len(re.findall(r'\[\?\]', text))
    
    # Total issues
    issues['total_issues'] = sum(issues.values())
    
    return issues


def decode_pdf_hex_strings(text: str) -> str:
    """
    Decode PDF hex-encoded strings (e.g., /x45/x78 -> Ex) to readable text.
    
    PDFs sometimes store text as hex sequences like /x45/x78/x61/x6D/x70/x6C/x65
    which should be decoded to "Example".
    
    Args:
        text: Text potentially containing hex-encoded strings
        
    Returns:
        Text with hex sequences decoded to readable characters
    """
    if not text:
        return ""
    
    # Pattern: /x followed by exactly 2 hex digits
    def decode_hex_match(match):
        hex_code = match.group(1)
        try:
            return chr(int(hex_code, 16))
        except (ValueError, OverflowError):
            return match.group(0)  # Return original if decode fails
    
    # Replace /xHH patterns with decoded characters
    decoded = re.sub(r'/x([0-9a-fA-F]{2})', decode_hex_match, text)
    
    return decoded


def extract_first_n_words(text: str, n: int = 200) -> str:
    """
    Extract the first N words from text, preserving punctuation.
    
    Handles multiple whitespace and newlines gracefully.
    Also decodes PDF hex-encoded strings for better readability.
    
    Args:
        text: Input text
        n: Number of words to extract (default: 200)
        
    Returns:
        String containing first N words
    """
    if not text:
        return ""
    
    # Decode hex-encoded strings first
    decoded_text = decode_pdf_hex_strings(text)
    
    # Split on whitespace and filter empty strings
    words = decoded_text.split()
    
    # Take first n words
    selected_words = words[:n]
    
    # Join back with single spaces
    return ' '.join(selected_words)


def validate_pdf_rendering(
    pdf_path: Path,
    n_words: int = 200
) -> Dict[str, Any]:
    """
    Perform comprehensive validation of PDF rendering.
    
    This function:
    1. Extracts text from the PDF
    2. Scans for rendering issues
    3. Extracts first N words to verify document structure
    4. Generates a comprehensive report
    
    Args:
        pdf_path: Path to PDF file to validate
        n_words: Number of words to extract for preview (default: 200)
        
    Returns:
        Validation report dictionary with structure:
        {
            'pdf_path': str,
            'issues': Dict[str, int],
            'first_words': str,
            'summary': {
                'has_issues': bool,
                'word_count': int
            }
        }
        
    Raises:
        PDFValidationError: If PDF cannot be read or validated
    """
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    
    # Scan for issues
    issues = scan_for_issues(text)
    
    # Extract first words
    first_words = extract_first_n_words(text, n_words)
    
    # Calculate word count
    word_count = len(first_words.split()) if first_words else 0
    
    # Build report
    report = {
        'pdf_path': str(pdf_path),
        'issues': issues,
        'first_words': first_words,
        'summary': {
            'has_issues': issues['total_issues'] > 0,
            'word_count': word_count
        }
    }
    
    return report

