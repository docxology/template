#!/usr/bin/env python3
"""Verify no mock usage in test files.

This script enforces the strict "No Mocks Policy" by checking that
test files do not contain any mock imports or usage.

Exit codes:
- 0: No mock usage found (success)
- 1: Mock usage detected (failure)
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Main verification function."""
    repo_root = Path(__file__).parent.parent

    print("🔍 Verifying No Mocks Policy compliance...")
    print("=" * 60)

    # Run grep to find mock usage
    result = subprocess.run(
        ['grep', '-r', r'MagicMock|unittest\.mock|mocker\.', 'tests/'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Mock usage found
        print("❌ FAILURE: Mock usage detected in test files!")
        print("=" * 60)
        print("Found the following mock usage:")
        print(result.stdout)
        print()
        print("🚫 No Mocks Policy Violation")
        print("All tests must use real data and real computations.")
        print("See AGENTS.md for implementation patterns.")
        return 1
    else:
        # No mock usage found
        print("✅ SUCCESS: No mock usage detected!")
        print("=" * 60)
        print("✓ All tests comply with No Mocks Policy")
        print("✓ Real data and computations used throughout")
        print("✓ Integration points properly tested")
        return 0


if __name__ == "__main__":
    sys.exit(main())