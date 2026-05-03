#!/usr/bin/env python3
"""Install and validate pre-commit hooks.

This script performs the following:
1. Verifies that .pre-commit-config.yaml exists
2. Installs the pre-commit hook (for pre-commit stage)
3. Installs the pre-push hook (for pre-push stage)
4. Validates the configuration syntax
5. Runs a manual dry-run of all hooks on all files to ensure they work

Usage:
    python scripts/setup_pre_commit.py
    or
    uv run scripts/setup_pre_commit.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(command: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess command and handle errors."""
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        if capture:
            print(result.stdout)
            print(result.stderr)
        sys.exit(result.returncode)
    return result


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / ".pre-commit-config.yaml"

    if not config_path.is_file():
        print(f"ERROR: Missing {config_path}")
        sys.exit(1)

    print(f"Installing pre-commit hooks from {config_path}...")

    # Install the pre-commit git hook
    run(["pre-commit", "install"])

    # Install the pre-push git hook
    run(["pre-commit", "install", "--hook-type", "pre-push"])

    # Validate configuration syntax
    print("Validating configuration...")
    run(["pre-commit", "validate-config", str(config_path)])

    # Run a full dry-run of all hooks on all files (manual stage)
    print("Running full hook suite on all files (manual stage)...")
    result = run(
        ["pre-commit", "run", "--all-files", "--hook-stage", "manual"],
        check=False,  # Don't exit immediately; we'll report after
    )

    if result.returncode == 0:
        print("✅ All pre-commit hooks passed.")
        sys.exit(0)
    else:
        print("❌ Some pre-commit hooks failed. See output above for details.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
