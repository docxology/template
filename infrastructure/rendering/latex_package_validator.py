"""LaTeX package validation utilities.

This module serves as the entry point, re-exporting from focused submodules:
- latex_discovery: kpsewhich location and per-package checking
- latex_validation: Bulk validation, preamble checking, reports
"""

from __future__ import annotations

# Re-exports for backwards compatibility
from infrastructure.rendering.latex_discovery import (  # noqa: F401
    PackageStatus,
    check_latex_package,
    find_kpsewhich,
)
from infrastructure.rendering.latex_validation import (  # noqa: F401
    ValidationReport,
    get_missing_packages_command,
    validate_packages,
    validate_preamble_packages,
)


def main() -> None:
    """CLI entry point for package validation."""
    print("LaTeX Package Validator")
    print("=" * 60)

    # Check for kpsewhich
    kpsewhich = find_kpsewhich()
    if kpsewhich:
        print(f"Found kpsewhich: {kpsewhich}")
    else:
        print("kpsewhich not found - cannot validate packages")
        print("   Please install BasicTeX or MacTeX")
        raise SystemExit(1)

    print()

    # Validate preamble packages
    report = validate_preamble_packages(strict=False)
    print(report)

    # Exit with error if required packages are missing
    if not report.all_required_available:
        raise SystemExit(1)

    raise SystemExit(0)


if __name__ == "__main__":
    main()
