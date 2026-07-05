"""Fond structure validation.

A valid fond requires:
- A fonds.yaml manifest file
- A data/ directory with resource files

Unlike projects (which need src/ + tests/ for executable code), fonds are
passive data stores. The validation reflects this: no Python files are needed.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_fond_structure(fond_dir: Path) -> tuple[bool, str]:
    """Validate that fond has the required structure.

    Required:
    - fonds.yaml — manifest file describing the resource pool
    - data/     — directory with actual resource data

    Optional:
    - manuscript/ — cross-reference documentation
    - scripts/    — optional processing scripts
    - tests/      — optional data integrity tests

    Args:
        fond_dir: Path to fond directory.

    Returns:
        Tuple of (is_valid, message).

    Examples:
        >>> validate_fond_structure(Path("fonds/bibliography"))
        (True, "Valid fond structure")

        >>> validate_fond_structure(Path("fonds/invalid"))
        (False, "Missing required file: fonds.yaml")
    """
    if not fond_dir.exists():
        return False, f"Fond directory does not exist: {fond_dir}"

    if not fond_dir.is_dir():
        return False, f"Not a directory: {fond_dir}"

    # Check required files
    manifest = fond_dir / "fonds.yaml"
    if not manifest.exists():
        return False, "Missing required file: fonds.yaml"

    # Check required directory
    data_dir = fond_dir / "data"
    if not data_dir.exists():
        return False, "Missing required directory: data"

    # Optional: check data/ has actual content
    data_files = list(data_dir.iterdir())
    if not data_files:
        logger.debug(f"{fond_dir.name}: data/ directory is empty")

    # Optional directories
    for opt_dir in ("manuscript", "scripts", "tests"):
        if (fond_dir / opt_dir).exists():
            logger.debug(f"{fond_dir.name}: has optional {opt_dir}/ directory")

    return True, "Valid fond structure"


__all__ = ["validate_fond_structure"]
