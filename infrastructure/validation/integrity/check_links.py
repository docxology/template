#!/usr/bin/env python3
"""Check documentation links and references for accuracy.

Dual role: (1) library — re-exports from :mod:`check_links_lib` for programmatic use;
(2) standalone CLI — ``python -m infrastructure.validation.integrity.check_links``.

This module validates:
- Internal markdown links resolve correctly
- File references point to existing files
- Anchor links match actual headings
- External links are accessible
- File path patterns in code blocks
- Directory structure examples against actual filesystem
- Python import statements
- Consistency of {name} placeholders vs actual project names
"""

from __future__ import annotations

import sys
from pathlib import Path

from infrastructure.validation.docs.accuracy import extract_headings
from infrastructure.validation.integrity.check_links_lib import (
    LinkCheckResult,
    _get_actual_project_names,
    _is_real_path_item,
    _resolve_template_path,
    _should_validate_path,
    _validate_import_path,
    check_file_reference,
    extract_code_blocks,
    extract_links,
    find_all_markdown_files,
    generate_comprehensive_report,
    run_link_audit,
    validate_directory_structures,
    validate_file_paths_in_code,
    validate_placeholder_consistency,
    validate_python_imports,
)

__all__ = [
    "LinkCheckResult",
    "check_file_reference",
    "extract_code_blocks",
    "extract_headings",
    "extract_links",
    "find_all_markdown_files",
    "generate_comprehensive_report",
    "run_link_audit",
    "validate_directory_structures",
    "validate_file_paths_in_code",
    "validate_placeholder_consistency",
    "validate_python_imports",
]


def main() -> int:
    """Main function to check all documentation links and references comprehensively."""
    # Repo root: .../infrastructure/validation/integrity/check_links.py → four parents
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    return run_link_audit(repo_root)


if __name__ == "__main__":
    sys.exit(main())
