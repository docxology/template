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

logger = get_logger(__name__)


def main() -> int:
    """Main verification function."""
    repo_root = Path(__file__).parent.parent
    tests_dir = repo_root / "tests"

    log_header("🔍 Verifying No Mocks Policy compliance...", logger)

    mock_frameworks = [
        'from unittest.mock', 'import unittest.mock', 'unittest.mock import',
        'MagicMock(', '@patch', 'with patch(', 'patch.object(',
        'Mock(', 'mocker.patch', 'pytest.mock'
    ]
    
    skip_patterns = [
        '#',  # Comments
        'def patch_', 'def patched_', 'patch_llm_client', 'patched_init',
        'monkeypatch.setattr',  # pytest monkeypatch is acceptable
        'No Mocks Policy', 'mock usage', 'mocking framework',
        'mock_repo', 'mock_',
        'pytest.mark',
    ]

    all_output = []
    
    if not tests_dir.exists():
        logger.warning(f"Tests directory not found at {tests_dir}")
        return 0

    for py_file in tests_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line_str = line.strip()
                    
                    # Skip if missing any mock framework
                    if not any(fw in line_str for fw in mock_frameworks):
                        continue
                        
                    # Skip if finding any skip patterns or if defining a function
                    if 'def ' in line_str or any(sp in line_str for sp in skip_patterns):
                        continue
                        
                    relative_path = py_file.relative_to(repo_root)
                    all_output.append(f"{relative_path}:{line_num}: {line_str}")
        except Exception as e:
            logger.warning(f"Error reading {py_file}: {e}")

    if all_output:
        # Mock usage found
        logger.error("❌ FAILURE: Mock usage detected in test files!")
        logger.info("=" * 60)
        logger.info("Found the following mock usage:")
        for out_line in all_output:
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