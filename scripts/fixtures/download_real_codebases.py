#!/usr/bin/env python3
"""Download real codebases for fixture testing.

Shallow clones (--depth=1) GitHub repositories and uses git sparse-checkout
to materialize only the requested subdirectory. Clones into:
    tests/fixtures/real_codebases/requests
    tests/fixtures/real_codebases/fastapi

Resumable: skips cloning if target directory already exists and is non-empty.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Repository root (where pyproject.toml resides)
ROOT = Path(__file__).parent.parent.parent.resolve()

# Target fixtures directory
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "real_codebases"

# Codebase definitions: name -> (repo_url, subdirectory_to_checkout)
CODEBASES = {
    "requests": (
        "https://github.com/psf/requests.git",
        "src/requests",  # Only the library source
    ),
    "fastapi": (
        "https://github.com/tiangolo/fastapi.git",
        "fastapi",  # Main package directory
    ),
}


def run_command(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a shell command and raise on failure."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    return result


def clone_subdirectory(repo_url: str, subdir: str, target_dir: Path) -> None:
    """Clone the repository shallowly and checkout only the specified subdirectory.

    Uses git's sparse-checkout feature to limit working tree size.

    Args:
        repo_url: GitHub repository URL.
        subdir: Relative path within the repo to include (e.g., 'src/requests').
        target_dir: Destination path (must not exist; git clone will create it).
    """
    # Ensure target_dir parent exists
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Shallow clone without checkout
    run_command(["git", "clone", "--depth=1", "--no-checkout", repo_url, str(target_dir)])

    # Step 2: Enable and configure sparse checkout to include only the desired subdir
    run_command(["git", "config", "core.sparseCheckout", "true"], cwd=target_dir)
    sparse_info = target_dir / ".git" / "info" / "sparse-checkout"
    sparse_info.write_text(f"{subdir}/\n")

    # Step 3: Checkout HEAD (default branch) respecting sparse pattern
    run_command(["git", "checkout", "-f", "HEAD"], cwd=target_dir)

    print(f"✓ Cloned {repo_url} → {target_dir} (sparse: {subdir}/)")


def main() -> None:
    """Entry point: download all configured codebases."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    for name, (repo_url, subdir) in CODEBASES.items():
        target = FIXTURES_DIR / name

        if target.exists():
            if any(target.iterdir()):
                print(f"⊘ {name}: already exists at {target}, skipping")
                continue
            else:
                # Remove empty directory left from a failed attempt
                subprocess.run(["rm", "-rf", str(target)], check=False)

        try:
            print(f"⬇ Downloading {name}...")
            clone_subdirectory(repo_url, subdir, target)
        except Exception as e:
            print(f"✗ Failed to download {name}: {e}", file=sys.stderr)
            # Clean up partial directory if created
            if target.exists():
                subprocess.run(["rm", "-rf", str(target)], check=False)
            sys.exit(1)

    print("\nAll codebases downloaded.")


if __name__ == "__main__":
    main()
