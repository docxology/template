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

# Add infrastructure to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

try:
    from infrastructure.markdown_validator import (
        validate_markdown,
        find_manuscript_directory,
    )
except ImportError as e:
    print(f"❌ Error: Failed to import from infrastructure/markdown_validator.py")
    print(f"   {e}")
    print(f"   Ensure infrastructure/markdown_validator.py exists and is properly formatted")
    sys.exit(1)


def main() -> int:
    """Main function to run markdown validation.
    
    Returns:
        0 on success, 1 on failure or validation issues
    """
    strict = "--strict" in sys.argv
    
    try:
        # Find manuscript directory
        manuscript_dir = find_manuscript_directory(repo_root)
        
        # Run validation
        problems, exit_code = validate_markdown(manuscript_dir, repo_root, strict=strict)
        
        # Print results
        if problems:
            header = "Markdown validation issues (non-strict)" if not strict else "Validation issues found"
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
    raise SystemExit(main())
