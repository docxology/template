"""Rule structure validation.

A valid rule requires:
- A rules.yaml manifest file
- At least one of:
  - soft/ directory — markdown guideline files (prose / prompt-style)
  - strong/ directory — yaml or json formal constraint files

Unlike projects (which need src/ + tests/ for executable code), rules are
passive specifications. The validation reflects this: no Python files are needed.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_rule_structure(rule_dir: Path) -> tuple[bool, str]:
    """Validate that a rule directory has the required structure.

    Required:
    - rules.yaml — manifest file describing the rule set
    - At least one of:
      - soft/   — markdown guideline documents
      - strong/ — yaml/json formal constraint files

    Optional:
    - scripts/    — optional processing or generation scripts
    - tests/      — optional rule integrity tests
    - examples/   — optional worked examples

    Args:
        rule_dir: Path to rule directory.

    Returns:
        Tuple of (is_valid, message).

    Examples:
        >>> validate_rule_structure(Path("rules/templates/template_project_rules"))
        (True, "Valid rule structure")

        >>> validate_rule_structure(Path("rules/invalid"))
        (False, "Missing required file: rules.yaml")
    """
    if not rule_dir.exists():
        return False, f"Rule directory does not exist: {rule_dir}"

    if not rule_dir.is_dir():
        return False, f"Not a directory: {rule_dir}"

    # Check required manifest
    manifest = rule_dir / "rules.yaml"
    if not manifest.exists():
        return False, "Missing required file: rules.yaml"

    # Check at least one specification directory exists
    has_soft = (rule_dir / "soft").exists()
    has_strong = (rule_dir / "strong").exists()
    if not has_soft and not has_strong:
        return False, "Missing required directory: at least one of soft/ or strong/ must exist"

    # Log optional directory presence
    for opt_dir in ("scripts", "tests", "examples"):
        if (rule_dir / opt_dir).exists():
            logger.debug(f"{rule_dir.name}: has optional {opt_dir}/ directory")

    if has_soft:
        soft_files = list((rule_dir / "soft").iterdir())
        if not soft_files:
            logger.debug(f"{rule_dir.name}: soft/ directory is empty")

    if has_strong:
        strong_files = list((rule_dir / "strong").iterdir())
        if not strong_files:
            logger.debug(f"{rule_dir.name}: strong/ directory is empty")

    return True, "Valid rule structure"


__all__ = ["validate_rule_structure"]
