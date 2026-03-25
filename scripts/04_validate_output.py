#!/usr/bin/env python3
"""Output validation orchestrator script.

This thin orchestrator coordinates the validation stage:
1. Validates generated PDFs
2. Checks markdown formatting
3. Verifies file integrity
4. Generates validation report

Stage 5 of the pipeline orchestration.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging.utils import get_logger, log_header
from infrastructure.validation.output.pipeline import execute_validation_pipeline

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute validation orchestration."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate output")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 04: Validate Output (Project: {args.project})", logger)

    return execute_validation_pipeline(args.project)


if __name__ == "__main__":
    sys.exit(main())
