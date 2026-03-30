"""LaTeX executable discovery and per-package checking."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import NamedTuple

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class PackageStatus(NamedTuple):
    """Status of a LaTeX package.

    NamedTuple is intentional: package status is immutable once checked,
    and the fixed (name, installed, path) shape is used for hashable
    membership tests in sets and dict keys.
    """

    name: str
    installed: bool
    path: str | None = None


def find_kpsewhich() -> Path | None:
    """Locate kpsewhich executable.

    Returns:
        Path to kpsewhich or None if not found
    """
    # Try common locations
    common_paths = [
        "/usr/local/texlive/2025basic/bin/universal-darwin/kpsewhich",
        "/usr/local/texlive/2025/bin/universal-darwin/kpsewhich",
        "/Library/TeX/texbin/kpsewhich",
        "/usr/local/bin/kpsewhich",
        "/opt/homebrew/bin/kpsewhich",
    ]

    for path_str in common_paths:
        path = Path(path_str)
        if path.exists():
            return path

    # Try which command
    try:
        result = subprocess.run(
            ["which", "kpsewhich"], capture_output=True, text=True, check=False, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired) as e:  # noqa: BLE001 — kpsewhich lookup is optional; return None
        logger.debug(f"Failed to locate kpsewhich: {e}")

    return None


def check_latex_package(package_name: str, kpsewhich_path: Path | None = None) -> PackageStatus:
    """Check if a LaTeX package is installed.

    Args:
        package_name: Name of the package (without .sty extension)
        kpsewhich_path: Optional path to kpsewhich executable

    Returns:
        PackageStatus with installation information
    """
    if kpsewhich_path is None:
        kpsewhich_path = find_kpsewhich()

    if kpsewhich_path is None:
        logger.warning("kpsewhich not found - cannot verify LaTeX packages")
        return PackageStatus(name=package_name, installed=False, path=None)

    sty_file = f"{package_name}.sty"

    try:
        result = subprocess.run(
            [str(kpsewhich_path), sty_file],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode == 0 and result.stdout.strip():
            pkg_path = result.stdout.strip()
            logger.debug(f"Package {package_name} found: {pkg_path}")
            return PackageStatus(name=package_name, installed=True, path=pkg_path)
        else:
            logger.debug(f"Package {package_name} not found")
            return PackageStatus(name=package_name, installed=False, path=None)

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking package {package_name}")
        return PackageStatus(name=package_name, installed=False, path=None)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Error checking package {package_name}: {e}")
        return PackageStatus(name=package_name, installed=False, path=None)
