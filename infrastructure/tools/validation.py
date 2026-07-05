"""Tool structure validation.

A valid tool requires:
- A tools.yaml manifest file
- A scripts/ directory with executable entry points

Unlike projects (which need src/ + tests/ for executable code) and fonds
(which need data/ for resource files), tools are executable entry points.
The validation reflects this: a scripts/ directory (not data/) is required.
"""

from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_tool_structure(tool_dir: Path) -> tuple[bool, str]:
    """Validate that a tool has the required structure.

    Required:
    - tools.yaml  — manifest file describing the tool
    - scripts/    — directory with executable entry points

    Optional:
    - tests/      — tool-level tests
    - docs/       — documentation

    Args:
        tool_dir: Path to tool directory.

    Returns:
        Tuple of (is_valid, message).

    Examples:
        >>> validate_tool_structure(Path("tools/templates/template_code_executor"))
        (True, "Valid tool structure")

        >>> validate_tool_structure(Path("tools/invalid"))
        (False, "Missing required file: tools.yaml")
    """
    if not tool_dir.exists():
        return False, f"Tool directory does not exist: {tool_dir}"

    if not tool_dir.is_dir():
        return False, f"Not a directory: {tool_dir}"

    # Check required manifest
    manifest = tool_dir / "tools.yaml"
    if not manifest.exists():
        return False, "Missing required file: tools.yaml"

    # Check required scripts directory
    scripts_dir = tool_dir / "scripts"
    if not scripts_dir.exists():
        return False, "Missing required directory: scripts"

    # Optional: check scripts/ has actual content
    script_files = list(scripts_dir.iterdir())
    if not script_files:
        logger.debug(f"{tool_dir.name}: scripts/ directory is empty")

    # Optional directories
    for opt_dir in ("tests", "docs"):
        if (tool_dir / opt_dir).exists():
            logger.debug(f"{tool_dir.name}: has optional {opt_dir}/ directory")

    return True, "Valid tool structure"


__all__ = ["validate_tool_structure"]
