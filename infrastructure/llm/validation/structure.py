"""Structure validation functions for LLM output validation."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def validate_section_completeness(
    response: str,
    required_headers: List[str],
    flexible: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate that all required sections are present in the response.
    
    Args:
        response: Response text to validate
        required_headers: List of required section headers (e.g., ["## Overview", "## Results"])
        flexible: If True, accepts semantic equivalents (e.g., "overview" matches "## Overview")
        
    Returns:
        Tuple of (is_complete, missing_sections, details)
    """
    found_headers = []
    missing_headers = []
    details: Dict[str, Any] = {
        "required": required_headers,
        "found": [],
        "missing": [],
    }
    
    response_lower = response.lower()
    
    for header in required_headers:
        # Extract header text without markdown
        header_text = header.replace("##", "").replace("#", "").strip().lower()
        
        # Check for exact match
        if header in response:
            found_headers.append(header)
            details["found"].append(header)
            continue
        
        # Check for flexible match
        if flexible:
            # Check for header text anywhere (case-insensitive)
            if header_text in response_lower:
                # Find the actual header used
                pattern = rf"#+\s*{re.escape(header_text)}"
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    found_headers.append(match.group(0))
                    details["found"].append(match.group(0))
                    continue
        
        missing_headers.append(header)
        details["missing"].append(header)
    
    is_complete = len(missing_headers) == 0
    return is_complete, missing_headers, details


def extract_structured_sections(response: str) -> Dict[str, str]:
    """Extract markdown sections from response into structured data.
    
    Args:
        response: Response text with markdown headers
        
    Returns:
        Dict mapping section headers to section content
    """
    sections: Dict[str, str] = {}
    
    # Pattern to match markdown headers (## Header or # Header)
    header_pattern = r'^(#{1,6})\s+(.+)$'
    
    lines = response.split('\n')
    current_header = None
    current_content: List[str] = []
    
    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # Save previous section
            if current_header:
                sections[current_header] = '\n'.join(current_content).strip()
            
            # Start new section
            current_header = match.group(2).strip()
            current_content = []
        else:
            if current_header:
                current_content.append(line)
    
    # Save last section
    if current_header:
        sections[current_header] = '\n'.join(current_content).strip()
    
    return sections


def validate_response_structure(
    response: str,
    required_headers: List[str],
    min_word_count: Optional[int] = None,
    max_word_count: Optional[int] = None,
    flexible_headers: bool = True
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Comprehensive structure validation for LLM responses.
    
    Args:
        response: Response text to validate
        required_headers: List of required section headers
        min_word_count: Minimum word count (optional)
        max_word_count: Maximum word count (optional)
        flexible_headers: If True, accepts semantic equivalents
        
    Returns:
        Tuple of (is_valid, list of issues, details dict)
    """
    issues = []
    details: Dict[str, Any] = {
        "word_count": len(response.split()),
        "sections": {},
    }
    
    # Check word count
    word_count = len(response.split())
    if min_word_count and word_count < min_word_count:
        issues.append(f"Response too short: {word_count} < {min_word_count} words")
    if max_word_count and word_count > max_word_count:
        issues.append(f"Response too long: {word_count} > {max_word_count} words")
    
    # Check section completeness
    is_complete, missing, section_details = validate_section_completeness(
        response, required_headers, flexible_headers
    )
    details["sections"] = section_details
    
    if not is_complete:
        issues.append(f"Missing required sections: {', '.join(missing)}")
    
    # Extract sections for analysis
    sections = extract_structured_sections(response)
    details["extracted_sections"] = list(sections.keys())
    
    is_valid = len(issues) == 0
    return is_valid, issues, details










