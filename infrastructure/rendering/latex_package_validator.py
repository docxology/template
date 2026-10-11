"""Executable LaTeX package validation command."""

from infrastructure.core.logging.constants import BANNER_WIDTH
from infrastructure.rendering.latex_discovery import find_kpsewhich as _find_kpsewhich
from infrastructure.rendering.latex_validation import validate_preamble_packages as _validate_preamble_packages

__all__ = ["main"]


def main() -> None:
    """CLI entry point for package validation."""
    print("LaTeX Package Validator")
    print("=" * BANNER_WIDTH)

    # Check for kpsewhich
    kpsewhich = _find_kpsewhich()
    if kpsewhich:
        print(f"Found kpsewhich: {kpsewhich}")
    else:
        print("kpsewhich not found - cannot validate packages")
        print("   Please install BasicTeX or MacTeX")
        raise SystemExit(1)

    print()

    # Validate preamble packages
    report = _validate_preamble_packages(strict=False)
    print(report)

    # Exit with error if required packages are missing
    if not report.all_required_available:
        raise SystemExit(1)

    raise SystemExit(0)


if __name__ == "__main__":
    main()
