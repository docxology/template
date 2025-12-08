"""LaTeX package validation utilities."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Dict, NamedTuple, Optional
from dataclasses import dataclass

from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import ValidationError

logger = get_logger(__name__)


class PackageStatus(NamedTuple):
    """Status of a LaTeX package."""
    name: str
    installed: bool
    path: Optional[str] = None


@dataclass
class ValidationReport:
    """LaTeX package validation report."""
    required_packages: List[PackageStatus]
    optional_packages: List[PackageStatus]
    missing_required: List[str]
    missing_optional: List[str]
    all_required_available: bool
    
    def __str__(self) -> str:
        """Generate human-readable report."""
        lines = ["LaTeX Package Validation Report", "=" * 50]
        
        if self.all_required_available:
            lines.append("✅ All required packages available")
        else:
            lines.append(f"❌ Missing {len(self.missing_required)} required package(s)")
            for pkg in self.missing_required:
                lines.append(f"  - {pkg}")
        
        if self.missing_optional:
            lines.append(f"\n⚠️  Missing {len(self.missing_optional)} optional package(s):")
            for pkg in self.missing_optional:
                lines.append(f"  - {pkg}")
        
        if self.missing_required or self.missing_optional:
            missing_all = self.missing_required + self.missing_optional
            lines.append(f"\nInstallation command:")
            lines.append(f"  sudo tlmgr install {' '.join(missing_all)}")
        
        return "\n".join(lines)


def find_kpsewhich() -> Optional[Path]:
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
            ["which", "kpsewhich"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    
    return None


def check_latex_package(package_name: str, kpsewhich_path: Optional[Path] = None) -> PackageStatus:
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
            timeout=5
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
    except Exception as e:
        logger.warning(f"Error checking package {package_name}: {e}")
        return PackageStatus(name=package_name, installed=False, path=None)


def validate_packages(
    required: List[str],
    optional: List[str],
    kpsewhich_path: Optional[Path] = None
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
    
    logger.info(f"Validating {len(required)} required and {len(optional)} optional LaTeX packages...")
    
    # Check required packages
    required_status = [
        check_latex_package(pkg, kpsewhich_path) for pkg in required
    ]
    
    # Check optional packages
    optional_status = [
        check_latex_package(pkg, kpsewhich_path) for pkg in optional
    ]
    
    # Identify missing packages
    missing_required = [s.name for s in required_status if not s.installed]
    missing_optional = [s.name for s in optional_status if not s.installed]
    
    report = ValidationReport(
        required_packages=required_status,
        optional_packages=optional_status,
        missing_required=missing_required,
        missing_optional=missing_optional,
        all_required_available=(len(missing_required) == 0)
    )
    
    return report


def get_missing_packages_command(missing: List[str]) -> str:
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
                "Or install full MacTeX instead of BasicTeX"
            ]
        )
    
    return report


def main():
    """CLI entry point for package validation."""
    import sys
    
    print("LaTeX Package Validator")
    print("=" * 60)
    
    # Check for kpsewhich
    kpsewhich = find_kpsewhich()
    if kpsewhich:
        print(f"✅ Found kpsewhich: {kpsewhich}")
    else:
        print("❌ kpsewhich not found - cannot validate packages")
        print("   Please install BasicTeX or MacTeX")
        sys.exit(1)
    
    print()
    
    # Validate preamble packages
    report = validate_preamble_packages(strict=False)
    print(report)
    
    # Exit with error if required packages are missing
    if not report.all_required_available:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

