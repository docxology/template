"""TestPyPI upload and installation verification orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# This repo sets [tool.uv] package=false, so it is never installed into the
# venv; each script must put the repo root on sys.path before importing
# `infrastructure`. This file lives two levels below the root (scripts/publish/).
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.publishing.pypi_release import run_test_pypi_release  # noqa: E402


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
