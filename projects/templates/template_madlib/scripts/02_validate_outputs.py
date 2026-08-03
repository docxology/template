#!/usr/bin/env python3
"""Project-local output validator for the Madlib exemplar.

Thin orchestrator: delegates all logic to
``src.output_validator.validate_generated_outputs`` and writes the
deterministic JSON report. Exits non-zero when a binding check fails so the
Stage 02 analysis pipeline treats drifted artifacts as a hard gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for candidate in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.core.logging.utils import get_logger, log_success  # noqa: E402
from src.output_validator import validate_generated_outputs, write_validation_report  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    """Validate regenerated outputs and exit 0 only when all checks pass."""
    result = validate_generated_outputs(PROJECT_ROOT)
    report = write_validation_report(PROJECT_ROOT, result=result)
    if result.passed:
        log_success("Madlib outputs validated", logger)
        print(str(report))
        return 0
    for issue in result.issues:
        logger.error("[%s] %s", issue.code, issue.message)
    print(str(report))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
