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


class PDFValidationError(Exception):
    """Raised when PDF validation encounters an error."""
    pass


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text content from a PDF file.

    Suppresses harmless pypdf warnings (e.g., "Ignoring wrong pointing object")
    that occur during PDF parsing of malformed objects.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a single string

    Raises:
        PDFValidationError: If file doesn't exist or text extraction fails
    """
    if not pdf_path.exists():
        raise PDFValidationError(f"PDF file not found: {pdf_path}")

    logger = get_logger(__name__)

    try:
        from pypdf import PdfReader

        with open(pdf_path, 'rb') as file:
            # Capture stderr to suppress pypdf warnings (e.g., "Ignoring wrong pointing object")
            # These are harmless and indicate pypdf is gracefully handling malformed PDF objects
            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                pdf_reader = PdfReader(file)
                text_parts = []

                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

            # Log suppressed warnings at DEBUG level for troubleshooting
            captured_warnings = stderr_capture.getvalue().strip()
            if captured_warnings:
                logger.debug(f"Suppressed pypdf warnings for {pdf_path.name}: {captured_warnings}")

            return '\n'.join(text_parts)

    except Exception as e:
        raise PDFValidationError(f"Failed to extract text from PDF: {e}")


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

