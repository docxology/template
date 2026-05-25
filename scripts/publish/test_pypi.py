"""TestPyPI upload and installation verification orchestrator."""

from __future__ import annotations

import os
import sys

from infrastructure.publishing.test_pypi import run_test_pypi_release


def main() -> None:
    """Run the TestPyPI release verification flow."""
    token = os.environ.get("TEST_PYPI_API_TOKEN")
    if not token:
        print("ERROR: TEST_PYPI_API_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)
    try:
        run_test_pypi_release(token)
    except Exception as exc:
        print(f"\nTEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
