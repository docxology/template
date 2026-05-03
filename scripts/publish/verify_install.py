"""Post-publish installation verification script.

This script verifies that the package can be installed and run correctly
in a clean virtual environment from PyPI (production, not TestPyPI).

Usage:
    uv run python scripts/publish/verify_install.py

Optional:
    PACKAGE_NAME: Override package name (default: template)
    INDEX_URL: Use custom package index (default: pypi.org)
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and stream output."""
    print(f"→ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def verify_install(package_name: str = "template", index_url: str = "https://pypi.org/simple/") -> None:
    """Create fresh venv, install from PyPI, and run doctor."""
    print(f"\n=== Verifying installation of '{package_name}' from {index_url} ===")
    with tempfile.TemporaryDirectory() as tmp:
        venv_path = Path(tmp) / "verify_venv"
        # Create virtual environment
        run([sys.executable, "-m", "venv", str(venv_path)])
        # Determine pip path
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_path / "Scripts" / "pip.exe"  # Windows

        # Upgrade pip/setuptools/wheel
        run([str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel", "-q"])

        # Install from PyPI
        print(f"Installing '{package_name}'...")
        run([
            str(pip_path), "install",
            "--index-url", index_url,
            package_name
        ])

        # Verify import works
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"

        print("\nChecking import...")
        result = subprocess.run(
            [str(python_path), "-c", f"import {package_name}; print({package_name}.__version__)"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✓ Import successful — version: {result.stdout.strip()}")
        else:
            print(f"✗ Import failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Run template doctor
        cli_path = venv_path / "bin" / "template"
        if not cli_path.exists():
            cli_path = venv_path / "Scripts" / "template.exe"

        print(f"\nRunning: {cli_path} doctor")
        result = subprocess.run([str(cli_path), "doctor"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("\n✓ Post-publish verification PASSED")
        else:
            print("\n✗ Post-publish verification FAILED — template doctor returned non-zero exit code")
            sys.exit(1)


def main() -> None:
    package_name = os.environ.get("PACKAGE_NAME", "template")
    index_url = os.environ.get("INDEX_URL", "https://pypi.org/simple/")
    try:
        verify_install(package_name, index_url)
        print("\n=== SUCCESS: Package is live and functional on PyPI ===")
    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
