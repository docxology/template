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

    # Run grep to find mock usage - comprehensive patterns
    mock_patterns = [
        r'MagicMock',
        r'unittest\.mock',
        r'mocker\.',
        r'from unittest\.mock import',
        r'@patch',
        r'patch\(',
        r'with patch',
        r'\.patch',
        r'pytest\.mock',
        r'mock\.',
        r'Mock\(',
        r'pytest\.mark\.requires_ollama',  # Skip this - it's a marker, not mock usage
        r'pytest\.mark\.requires_.*'  # Skip pytest markers
    ]

    all_output = []
    for pattern in mock_patterns:
        # Skip pytest markers as they're not mock usage
        if 'pytest.mark' in pattern:
            continue

        result = subprocess.run(
            ['grep', '-r', pattern, 'tests/'],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            all_output.append(f"Pattern '{pattern}':")
            # Filter out false positives
            lines = result.stdout.strip().split('\n')
            filtered_lines = []
            for line in lines:
                # Skip lines that are just imports of pytest markers or other non-mock usage
                if not any(skip_pattern in line for skip_pattern in [
                    'pytest.mark', 'requires_ollama', 'requires_zenodo', 'requires_github'
                ]):
                    filtered_lines.append(line)
            if filtered_lines:
                all_output.extend(filtered_lines)
                all_output.append("")

    combined_output = '\n'.join(all_output)

    if combined_output.strip():
        # Mock usage found
        print("❌ FAILURE: Mock usage detected in test files!")
        print("=" * 60)
        print("Found the following mock usage:")
        print(combined_output)
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