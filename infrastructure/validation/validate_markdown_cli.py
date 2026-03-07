#!/usr/bin/env python3
"""Markdown validation script - THIN ORCHESTRATOR

This script validates markdown files for integrity issues:
- Image references
- Cross-references
- Mathematical equations
- Links and URLs

All business logic is in infrastructure/markdown_validator.py
This script handles only CLI argument parsing and I/O.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Add infrastructure to path for imports BEFORE any infrastructure imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging_utils import get_logger  # noqa: E402

logger = get_logger(__name__)

try:
    from infrastructure.validation.markdown_validator import (
        collect_symbols,
        find_manuscript_directory,
        find_markdown_files,
        validate_images,
        validate_markdown,
        validate_math,
        validate_refs,
    )
except ImportError as e:
    # Store error for main() function to handle
    import_error = f"❌ Error: Failed to import from infrastructure/validation/markdown_validator.py\n   {e}\n   Ensure infrastructure/validation/markdown_validator.py exists and is properly formatted"  # noqa: E501
else:
    import_error = None  # type: ignore[assignment]


# Helper function for tests
def _repo_root() -> str:
    """Get repository root path (for testing).

    Returns:
        str: Path to repository root
    """
    return str(repo_root)


def main(manuscript_path: Optional[Path] = None, strict: bool = False) -> int:
    """Main function to run markdown validation.

    Args:
        manuscript_path: Path to markdown file or directory. If None, automatically
            detects manuscript directory from repository root.
        strict: Enable strict validation mode

    Returns:
        0 on success, 1 on failure or validation issues
    """
    # Handle import errors that should only occur at runtime
    if import_error:
        logger.error(import_error)
        return 1

    try:
        if manuscript_path is not None:
            # Use provided path (can be file or directory)
            manuscript_dir = Path(manuscript_path)
            # If it's a file, use its parent directory
            if manuscript_dir.is_file():
                manuscript_dir = manuscript_dir.parent
        else:
            # Find manuscript directory automatically
            manuscript_dir = find_manuscript_directory(repo_root)

        # Run validation
        problems, exit_code = validate_markdown(manuscript_dir, repo_root, strict=strict)

        # Print results
        if problems:
            header = (
                "Markdown validation issues (non-strict)"
                if not strict
                else "Validation issues found"
            )
            logger.warning(header + ":")
            for p in problems:
                logger.warning(f" - {p}")
        else:
            logger.info("Markdown validation passed: all images and references resolved.")

        return exit_code

    except FileNotFoundError as e:
        logger.error(f"❌ Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate markdown files for integrity issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "manuscript_path",
        nargs="?",
        type=Path,
        help="Path to markdown file or directory (default: auto-detect)",
    )
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")

    args = parser.parse_args()

    exit_code = main(manuscript_path=args.manuscript_path, strict=args.strict)

    sys.exit(exit_code)
