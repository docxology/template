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

# Add infrastructure to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from infrastructure.validation.markdown_validator import (
        find_manuscript_directory, validate_markdown)
except ImportError as e:
    # Store error for main() function to handle
    import_error = f"❌ Error: Failed to import from infrastructure/validation/markdown_validator.py\n   {e}\n   Ensure infrastructure/validation/markdown_validator.py exists and is properly formatted"
else:
    import_error = None


# Helper function for tests
def _repo_root() -> str:
    """Get repository root path (for testing).

    Returns:
        str: Path to repository root
    """
    return str(repo_root)


# Re-export functions from infrastructure for tests
def find_markdown_files(directory: str) -> list:
    """Find all markdown files in directory (for testing).

    Args:
        directory: Directory to search

    Returns:
        list: List of markdown file paths sorted numerically
    """
    import os
    from pathlib import Path

    md_files = []
    for f in os.listdir(directory):
        if f.endswith(".md"):
            md_files.append(os.path.join(directory, f))

    # Sort numerically
    return sorted(
        md_files,
        key=lambda x: (
            "".join(filter(str.isalpha, os.path.basename(x))),
            (
                int("".join(filter(str.isdigit, os.path.basename(x))))
                if any(c.isdigit() for c in os.path.basename(x))
                else 0
            ),
        ),
    )


def collect_symbols(md_files: list) -> tuple:
    """Collect symbols from markdown files (for testing).

    Args:
        md_files: List of markdown file paths

    Returns:
        tuple: (labels, anchors) dictionaries
    """
    labels = {}
    anchors = {}

    for file_path in md_files:
        with open(file_path, "r") as f:
            content = f.read()
            # Collect labels from {#label} syntax
            import re

            for match in re.finditer(r"\{#([^}]+)\}", content):
                labels[match.group(1)] = file_path
            # Collect anchors from [anchor]: url syntax
            for match in re.finditer(r"^\[([^\]]+)\]:\s*(.+)$", content, re.MULTILINE):
                anchors[match.group(1)] = match.group(2)

    return labels, anchors


def validate_images(md_files: list, repo_root_str: str) -> list:
    """Validate image references (for testing).

    Args:
        md_files: List of markdown file paths
        repo_root_str: Repository root path

    Returns:
        list: List of issues found
    """
    issues = []
    import os
    import re

    for file_path in md_files:
        with open(file_path, "r") as f:
            content = f.read()
            # Find image references ![alt](path)
            for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", content):
                image_path = match.group(2)
                if not image_path.startswith("http"):
                    full_path = os.path.join(os.path.dirname(file_path), image_path)
                    if not os.path.exists(full_path):
                        issues.append(f"Image not found: {image_path} in {file_path}")

    return issues


def validate_refs(
    md_files: list, labels: dict, anchors: dict, repo_root_str: str
) -> list:
    """Validate cross-references (for testing).

    Args:
        md_files: List of markdown file paths
        labels: Dictionary of labels
        anchors: Dictionary of anchors
        repo_root_str: Repository root path

    Returns:
        list: List of issues found
    """
    issues = []
    import re

    for file_path in md_files:
        with open(file_path, "r") as f:
            content = f.read()
            # Find references [text](#label)
            for match in re.finditer(r"\[([^\]]+)\]\(#([^)]+)\)", content):
                label = match.group(2)
                if label not in labels:
                    issues.append(f"Reference not found: #{label} in {file_path}")

    return issues


def validate_math(md_files: list, repo_root_str: str) -> list:
    """Validate math equations (for testing).

    Args:
        md_files: List of markdown file paths
        repo_root_str: Repository root path

    Returns:
        list: List of issues found
    """
    issues = []
    import re

    for file_path in md_files:
        with open(file_path, "r") as f:
            content = f.read()
            # Check for unmatched brackets
            open_count = content.count("$")
            if open_count % 2 != 0:
                issues.append(f"Unmatched $ symbols in {file_path}")

    return issues


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
        print(import_error)
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
        problems, exit_code = validate_markdown(
            manuscript_dir, repo_root, strict=strict
        )

        # Print results
        if problems:
            header = (
                "Markdown validation issues (non-strict)"
                if not strict
                else "Validation issues found"
            )
            print(header + ":")
            for p in problems:
                print(" -", p)
        else:
            print("Markdown validation passed: all images and references resolved.")

        return exit_code

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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
    parser.add_argument(
        "--strict", action="store_true", help="Enable strict validation mode"
    )

    args = parser.parse_args()

    exit_code = main(manuscript_path=args.manuscript_path, strict=args.strict)

    sys.exit(exit_code)
