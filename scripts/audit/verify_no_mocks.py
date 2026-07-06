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
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.validation.output.no_mock_enforcer import scan_test_roots, validate_no_mocks

logger = get_logger(__name__)


def main() -> int:
    """Main verification function."""
    repo_root = Path(__file__).resolve().parents[2]
    repo_tests_dir = repo_root / "tests"

    log_header("🔍 Verifying No Mocks Policy compliance...", logger)

    if not repo_tests_dir.exists():
        # The repo-level tests/ tree is load-bearing; a missing directory means
        # the check cannot run, so fail loudly rather than silently passing.
        logger.error(f"❌ FAILURE: Tests directory not found at {repo_tests_dir}")
        return 1

    violations: list[str] = []
    for tests_dir in scan_test_roots(repo_root):
        violations.extend(validate_no_mocks(tests_dir, repo_root))

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
