#!/usr/bin/env python3
"""Verify no mock usage in test files.

This script enforces the strict "No Mocks Policy" by checking that
test files do not contain any mock imports or usage.

Exit codes:
- 0: No mock usage found (success)
- 1: Mock usage detected (failure)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.validation.no_mock_enforcer import validate_no_mocks

logger = get_logger(__name__)


def main() -> int:
    """Main verification function."""
    repo_root = Path(__file__).parent.parent
    tests_dir = repo_root / "tests"

    log_header("🔍 Verifying No Mocks Policy compliance...", logger)

    if not tests_dir.exists():
        logger.warning(f"Tests directory not found at {tests_dir}")
        return 0

    violations = validate_no_mocks(tests_dir, repo_root)

    if violations:
        # Mock usage found
        logger.error("❌ FAILURE: Mock usage detected in test files!")
        logger.info("=" * 60)
        logger.info("Found the following mock usage:")
        for out_line in violations:
            logger.info(out_line)
        logger.info("")
        logger.info("🚫 No Mocks Policy Violation")
        logger.info("All tests must use real data and real computations.")
        logger.info("See AGENTS.md for implementation patterns.")
        return 1
    else:
        # No mock usage found
        log_success("✅ SUCCESS: No mock usage detected!", logger)
        logger.info("=" * 60)
        logger.info("✓ All tests comply with No Mocks Policy")
        logger.info("✓ Real data and computations used throughout")
        logger.info("✓ Integration points properly tested")
        return 0


if __name__ == "__main__":
    sys.exit(main())
