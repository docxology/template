"""LaTeX package validation and preamble checking."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.latex_discovery import (
    PackageStatus,
    check_latex_package,
    find_kpsewhich,
)

logger = get_logger(__name__)


@dataclass
class ValidationReport:
    """LaTeX package validation report."""

    required_packages: list[PackageStatus]
    optional_packages: list[PackageStatus]
    missing_required: list[str]
    missing_optional: list[str]
    all_required_available: bool

    def __str__(self) -> str:
        """Generate human-readable report."""
        lines = ["LaTeX Package Validation Report", "=" * 50]

        if self.all_required_available:
            lines.append("All required packages available")
        else:
            lines.append(f"Missing {len(self.missing_required)} required package(s)")
            for pkg in self.missing_required:
                lines.append(f"  - {pkg}")

        if self.missing_optional:
            lines.append(f"\nMissing {len(self.missing_optional)} optional package(s):")
            for pkg in self.missing_optional:
                lines.append(f"  - {pkg}")

        if self.missing_required or self.missing_optional:
            missing_all = self.missing_required + self.missing_optional
            lines.append("\nInstallation command:")
            lines.append(f"  sudo tlmgr install {' '.join(missing_all)}")

        return "\n".join(lines)


def validate_packages(
    required: list[str], optional: list[str], kpsewhich_path: Path | None = None
) -> ValidationReport:
    """Validate all required and optional LaTeX packages.

    Args:
        required: List of required package names
        optional: List of optional package names
        kpsewhich_path: Optional path to kpsewhich executable

    Returns:
        ValidationReport with detailed status
    """
    if kpsewhich_path is None:
        kpsewhich_path = find_kpsewhich()

    logger.info(
        f"Validating {len(required)} required and {len(optional)} optional LaTeX packages..."
    )

    def _bulk_check(packages: list[str]) -> list[PackageStatus]:
        """Check many packages with a single kpsewhich invocation (fast path)."""

        if not packages:
            return []
        if kpsewhich_path is None:
            return [PackageStatus(name=p, installed=False, path=None) for p in packages]

        sty_files = [f"{p}.sty" for p in packages]
        try:
            # kpsewhich supports multiple filenames; it prints one line per argument.
            # Using a single process is far faster than spawning N subprocesses.
            timeout_s = 8 if os.environ.get("PYTEST_CURRENT_TEST") else 20
            result = subprocess.run(
                [str(kpsewhich_path), *sty_files],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_s,
            )
            lines = result.stdout.splitlines()
            if len(lines) != len(packages):
                # Unexpected output shape; fall back to per-package checking.
                return [check_latex_package(p, kpsewhich_path) for p in packages]

            statuses: list[PackageStatus] = []
            for pkg, path_line in zip(packages, lines, strict=True):
                path_line = path_line.strip()
                if path_line:
                    statuses.append(PackageStatus(name=pkg, installed=True, path=path_line))
                else:
                    statuses.append(PackageStatus(name=pkg, installed=False, path=None))
            return statuses
        except subprocess.TimeoutExpired:
            logger.warning("Timeout checking LaTeX packages (bulk); falling back to per-package checks")
            return [check_latex_package(p, kpsewhich_path) for p in packages]

    # Check required/optional packages
    required_status = _bulk_check(required)
    optional_status = _bulk_check(optional)

    # Identify missing packages
    missing_required = [s.name for s in required_status if not s.installed]
    missing_optional = [s.name for s in optional_status if not s.installed]

    report = ValidationReport(
        required_packages=required_status,
        optional_packages=optional_status,
        missing_required=missing_required,
        missing_optional=missing_optional,
        all_required_available=(len(missing_required) == 0),
    )

    return report


def get_missing_packages_command(missing: list[str]) -> str:
    """Generate tlmgr install command for missing packages.

    Args:
        missing: List of missing package names

    Returns:
        Installation command string
    """
    if not missing:
        return ""

    return f"sudo tlmgr install {' '.join(missing)}"


def validate_preamble_packages(strict: bool = False) -> ValidationReport:
    """Validate packages used in the standard preamble.

    Args:
        strict: If True, treat optional packages as required

    Returns:
        ValidationReport

    Raises:
        ValidationError: If strict=True and required packages are missing
    """
    # Required packages for basic document rendering
    required = [
        "amsmath",
        "amssymb",
        "amsfonts",
        "amsthm",
        "graphicx",
        "geometry",
        "float",
        "booktabs",
        "longtable",
        "array",
        "hyperref",
        "natbib",
    ]

    # Optional packages that enhance functionality
    optional = [
        "multirow",
        "caption",
        "subcaption",
        "bm",
        "cleveref",
        "doi",
        "newunicodechar",
        "fancyvrb",
        "xcolor",
        "listings",
        "lmodern",
    ]

    if strict:
        required = required + optional
        optional = []

    report = validate_packages(required, optional)

    if strict and not report.all_required_available:
        raise ValidationError(
            f"Missing required LaTeX packages: {', '.join(report.missing_required)}",
            context={"missing": report.missing_required},
            suggestions=[
                get_missing_packages_command(report.missing_required),
                "Run: sudo tlmgr update --self",
                "Or install full MacTeX instead of BasicTeX",
            ],
        )

    return report
