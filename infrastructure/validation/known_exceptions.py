#!/usr/bin/env python3
"""Known exception patterns for audit tool false positive filtering.

This module defines patterns that are known to be valid exceptions and should
not be flagged as issues by the audit tool.
"""
from __future__ import annotations

from typing import List, Set

# Valid directory references (these are directories, not files)
VALID_DIRECTORY_REFERENCES: Set[str] = {
    'infrastructure/',
    'scripts/',
    'docs/',
    'projects/',
    'tests/',
    'output/',
    'projects_archive/',
    'projects/code_project/',
    'projects/active_inference_meta_pragmatic/',
    'projects/ento_linguistics/',
}

# Template patterns (placeholders that can't be resolved)
TEMPLATE_PATTERNS: List[str] = [
    r'\{[^}]+\}',  # {name}, {project}, etc.
    r'<[^>]+>',    # <module>, <name>, etc.
]

# Code example patterns (intentional examples, not real paths)
CODE_EXAMPLE_PATTERNS: List[str] = [
    'your_project',
    'example.com',
    'your-domain.com',
    'path/to/',
    'placeholder',
    'template',
    'sample',
    'your_',
    'my_project',
    'new_project',
    'custom_project',
]

# Numeric or quoted strings (code examples, not file paths)
CODE_LITERAL_PATTERNS: List[str] = [
    r'^\d+$',  # Pure numbers like "42"
    r'^"[^"]+"$',  # Quoted strings like "hello"
    r"^'[^']+'$",  # Single-quoted strings
]

# Mermaid diagram patterns (formatting artifacts)
MERMAID_PATTERNS: List[str] = [
    r'\\n',  # Newline in mermaid
    r'<br/>',  # Line break in mermaid
    r'<br>',  # Line break in mermaid
    r'\|',  # Table separator in mermaid
]

# Table formatting artifacts
TABLE_ARTIFACTS: List[str] = [
    r'\]',  # Closing bracket from markdown table
    r'\)',  # Closing paren from markdown table
    r'\`',  # Backtick from markdown table
]

# Code block formatting artifacts
CODE_BLOCK_ARTIFACTS: List[str] = [
    r'\n',  # Newline in code block
    r'\|',  # Pipe character (often from tables)
    r'`',   # Backtick
    r'\)',  # Closing paren
    r'\]',  # Closing bracket
    r'\}',  # Closing brace
]

# LaTeX references (valid in manuscripts)
LATEX_PATTERNS: List[str] = [
    r'\\ref\{',
    r'\\eqref\{',
    r'\\cite\{',
    r'\\label\{',
]

# Virtual environment patterns
VENV_PATTERNS: List[str] = [
    '.venv/',
    '/.venv/',
    'venv/',
    '/venv/',
    'site-packages/',
]

def is_valid_directory_reference(target: str) -> bool:
    """Check if target is a valid directory reference.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target is a known valid directory reference
    """
    target_clean = target.strip()
    # Check exact matches
    if target_clean in VALID_DIRECTORY_REFERENCES:
        return True
    # Check if it ends with / and matches a known directory pattern
    if target_clean.endswith('/'):
        base_dir = target_clean.rstrip('/')
        if base_dir in [d.rstrip('/') for d in VALID_DIRECTORY_REFERENCES]:
            return True
        # Check if it's a subdirectory of a known directory
        for valid_dir in VALID_DIRECTORY_REFERENCES:
            if target_clean.startswith(valid_dir):
                return True
    return False


def is_template_pattern(target: str) -> bool:
    """Check if target contains template placeholders.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target contains template patterns
    """
    import re
    for pattern in TEMPLATE_PATTERNS:
        if re.search(pattern, target):
            return True
    return False


def is_code_example(target: str) -> bool:
    """Check if target is a code example pattern.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target matches code example patterns
    """
    import re
    
    # Check for numeric or quoted string literals (code examples)
    for pattern in CODE_LITERAL_PATTERNS:
        if re.match(pattern, target.strip()):
            return True
    
    target_lower = target.lower()
    for pattern in CODE_EXAMPLE_PATTERNS:
        if pattern in target_lower:
            return True
    return False


def is_mermaid_artifact(target: str) -> bool:
    """Check if target contains Mermaid diagram artifacts.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target contains Mermaid formatting artifacts
    """
    import re
    for pattern in MERMAID_PATTERNS:
        if re.search(pattern, target):
            return True
    # Check for common mermaid keywords
    if any(keyword in target.lower() for keyword in ['generic', 'br/', 'subgraph']):
        return True
    return False


def is_table_artifact(target: str) -> bool:
    """Check if target is a table formatting artifact.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target appears to be a table formatting artifact
    """
    import re
    for pattern in TABLE_ARTIFACTS:
        if re.search(pattern, target):
            return True
    # Check for markdown table patterns
    if target.endswith((']', ')', '`')):
        return True
    return False


def is_code_block_artifact(target: str) -> bool:
    """Check if target is a code block formatting artifact.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target appears to be a code block formatting artifact
    """
    import re
    # Check for newlines or special formatting chars
    if '\n' in target or '\r' in target:
        return True
    for pattern in CODE_BLOCK_ARTIFACTS:
        if re.search(pattern, target):
            return True
    # Check if it ends with formatting characters
    if target.rstrip().endswith((')', ']', '}', '`', '|', '\\n')):
        return True
    return False


def is_latex_reference(target: str) -> bool:
    """Check if target is a LaTeX reference.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target is a LaTeX reference
    """
    import re
    for pattern in LATEX_PATTERNS:
        if re.search(pattern, target):
            return True
    return False


def is_venv_reference(target: str) -> bool:
    """Check if target is a virtual environment reference.
    
    Args:
        target: Path target to check
        
    Returns:
        True if target references a virtual environment
    """
    for pattern in VENV_PATTERNS:
        if pattern in target:
            return True
    return False
