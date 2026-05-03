"""TestPyPI upload and installation verification script.

This script builds the package, uploads to TestPyPI, and verifies installation
in a clean virtual environment by running the 'template doctor' command.

Environment:
    TEST_PYPI_API_TOKEN: Required. API token for TestPyPI upload.

Usage:
    uv run python scripts/publish/test_pypi.py
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


def build_package() -> Path:
    """Build the package distribution using uv."""
    print("\n=== Building package with uv build ===")
    dist_dir = Path("dist").absolute()
    if dist_dir.exists():
        for f in dist_dir.iterdir():
            f.unlink()
    run(["uv", "build"])
    wheels = list(Path("dist").glob("*.whl"))
    sdists = list(Path("dist").glob("*.tar.gz"))
    if not wheels and not sdists:
        raise RuntimeError("Build failed: no distribution files found in dist/")
    print(f"✓ Built {len(wheels)} wheel(s), {len(sdists)} sdist(s)")
    return dist_dir


def upload_to_testpypi(dist_dir: Path, token: str) -> None:
    """Upload distributions to TestPyPI using twine."""
    print("\n=== Uploading to TestPyPI ===")
    # Ensure twine is available
    run([sys.executable, "-m", "pip", "install", "twine", "-q"])

    # Upload using API token from environment
    run([
        "twine", "upload",
        "--repository", "testpypi",
        "--username", "__token__",
        "--password", token,
        str(dist_dir / "*")
    ])
    print("✓ Uploaded to TestPyPI")


def install_and_verify(package_name: str = "template") -> None:
    """Create fresh venv, install from TestPyPI, and run doctor."""
    print("\n=== Installing from TestPyPI in clean venv ===")
    with tempfile.TemporaryDirectory() as tmp:
        venv_path = Path(tmp) / "test_venv"
        # Create virtual environment
        run([sys.executable, "-m", "venv", str(venv_path)])
        # Determine pip path
        pip_path = venv_path / "bin" / "pip"
        if not pip_path.exists():
            pip_path = venv_path / "Scripts" / "pip.exe"  # Windows

        # Upgrade pip/setuptools/wheel
        run([str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel", "-q"])

        # Install from TestPyPI
        print(f"Installing '{package_name}' from TestPyPI...")
        run([
            str(pip_path), "install",
            "--index-url", "https://test.pypi.org/simple/",
            "--no-deps",  # let pip resolve deps from TestPyPI too
            package_name
        ])

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
            print("\n✓ Installation verification PASSED — template doctor succeeded")
        else:
            print("\n✗ Installation verification FAILED — template doctor returned non-zero exit code")
            sys.exit(1)


def main() -> None:
    token = os.environ.get("TEST_PYPI_API_TOKEN")
    if not token:
        print("ERROR: TEST_PYPI_API_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Build
        dist_dir = build_package()

        # Step 2: Upload to TestPyPI
        upload_to_testpypi(dist_dir, token)

        # Step 3: Install and verify
        install_and_verify()

        print("\n=== SUCCESS: Package is ready for PyPI release ===")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
