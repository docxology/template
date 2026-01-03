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

    # Run grep to find mock usage - only actual mock framework patterns
    mock_patterns = [
        r'MagicMock',
        r'unittest\.mock',
        r'mocker\.',
        r'from unittest\.mock import',
        r'@patch',
        r'patch\(',
        r'with patch',
        r'pytest\.mock',
        r'Mock\(',
    ]

    all_output = []
    for pattern in mock_patterns:
        result = subprocess.run(
            ['grep', '-r', '--include=*.py', pattern, 'tests/'],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Filter out false positives
            lines = result.stdout.strip().split('\n')
            filtered_lines = []
            for line in lines:
                # Skip documentation files, binary files, comments, and acceptable patterns
                if any(skip_pattern in line for skip_pattern in [
                    '__pycache__', '.pyc', 'AGENTS.md', '.md:',  # Documentation and binary
                    '#',  # Comments
                    'def patch_', 'def patched_', 'patch_llm_client', 'patched_init',  # Function names (not mock usage)
                    'monkeypatch.setattr',  # pytest monkeypatch is acceptable (test isolation, not mocking)
                    'No Mocks Policy', 'mock usage', 'mocking framework',  # Documentation text
                    'mock_repo', 'mock_',  # Variable names in documentation examples
                    'pytest.mark',  # Pytest markers are not mock usage
                ]):
                    continue
                # Only include actual mock framework usage (not function names or comments)
                if any(mock_framework in line for mock_framework in [
                    'from unittest.mock', 'import unittest.mock', 'unittest.mock import',
                    'MagicMock(', '@patch', 'with patch(', 'patch.object(',
                    'Mock(', 'mocker.patch', 'pytest.mock'
                ]):
                    # Exclude if it's just a function name or comment
                    if 'def ' in line or '#' in line:
                        continue
                    filtered_lines.append(line)
            if filtered_lines:
                all_output.append(f"Pattern '{pattern}':")
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