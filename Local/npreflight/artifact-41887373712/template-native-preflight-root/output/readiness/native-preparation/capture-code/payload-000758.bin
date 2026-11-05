"""Rule discovery for multi-rule support.

Scans the rules/ directory for valid rules (specifications — soft guidelines and
strong formal constraints) and returns RuleInfo objects. Follows the same
architecture as infrastructure/fonds/discovery.py but for specifications rather
than data resource pools.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rules.rules_info import RuleInfo, build_rule_info
from infrastructure.rules.validation import validate_rule_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``rules/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired rules.
NON_RENDERED_RULE_SUBDIRS: frozenset[str] = frozenset({"working", "archive"})

#: Rendered subdirectories under ``rules/``.
RENDERED_RULE_SUBDIRS: frozenset[str] = frozenset({"templates"})

#: Public API of this module.
__all__ = [
    "NON_RENDERED_RULE_SUBDIRS",
    "RENDERED_RULE_SUBDIRS",
    "discover_rules",
    "resolve_rule_root",
]


def discover_rules(
    repo_root: Path | str,
) -> list[RuleInfo]:
    """Discover all valid rules in the rules/ directory.

    Args:
        repo_root: Repository root directory.

    Returns:
        List of RuleInfo objects for valid rules.

    The lifecycle subfolders in :data:`NON_RENDERED_RULE_SUBDIRS`
    (``working``/``archive``) are deliberately excluded from discovery.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)
    rules_dir_path = repo_root / "rules"

    if not rules_dir_path.exists():
        logger.warning(f"Rules directory not found: {rules_dir_path}")
        return []

    rules: list[RuleInfo] = []

    for child_dir in sorted(rules_dir_path.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        # Non-rendered lifecycle mirrors are never discovered
        if child_dir.name in NON_RENDERED_RULE_SUBDIRS:
            logger.debug(f"Skipping non-rendered lifecycle subfolder: {child_dir.name}")
            continue

        # First, check if this is a valid standalone rule
        is_valid, _ = validate_rule_structure(child_dir)

        if is_valid:
            rule_info = build_rule_info(child_dir)
            rules.append(rule_info)
            logger.debug(f"Discovered standalone rule: {rule_info.name} at {rule_info.path}")
        else:
            # Not a valid rule — check if it's a program directory containing rules
            nested = _discover_nested_rules(child_dir, program_name=child_dir.name)
            if nested:
                rules.extend(nested)
                logger.debug(f"Discovered program directory: {child_dir.name} with {len(nested)} rules")
            else:
                logger.debug(f"Skipping {child_dir.name}: not a valid rule or program directory")

    return rules


def _discover_nested_rules(
    program_dir: Path,
    program_name: str,
    *,
    _allow_category: bool = True,
) -> list[RuleInfo]:
    """Discover rules nested within a program directory.

    A program directory is a folder that contains multiple related rules,
    but is not a rule itself. A child directory whose name starts with
    ``_`` is a category grouping — its own direct children are the actual
    rules, discovered with the compound qualified name ``<program>/_<category>/<name>``.
    Category nesting is exactly one level deep.
    """
    nested = []
    for child_dir in sorted(program_dir.iterdir()):
        if not child_dir.is_dir():
            continue

        if child_dir.name.startswith("."):
            continue

        is_valid, _ = validate_rule_structure(child_dir)

        if is_valid:
            rule_info = build_rule_info(child_dir, program=program_name)
            nested.append(rule_info)
            logger.debug(f"Discovered nested rule: {rule_info.qualified_name} at {rule_info.path}")
        elif _allow_category and child_dir.name.startswith("_"):
            nested.extend(
                _discover_nested_rules(
                    child_dir,
                    program_name=f"{program_name}/{child_dir.name}",
                    _allow_category=False,
                )
            )

    return nested


def resolve_rule_root(repo_root: Path | str, rule_name: str) -> Path:
    """Resolve a rule directory by qualified name.

    A qualified ``<subfolder>/<name>`` path (head in ``templates/``, ``working/``,
    or ``archive/``) resolves directly under ``rules/<subfolder>/<name>``. A bare
    name prefers ``rules/templates/<name>``, then a flat standalone ``rules/<name>``.

    Args:
        repo_root: Repository root directory.
        rule_name: Rule name or qualified path.

    Returns:
        Absolute resolved path to the rule directory.
    """
    if isinstance(repo_root, str):
        repo_root = Path(repo_root)

    valid_heads = NON_RENDERED_RULE_SUBDIRS | RENDERED_RULE_SUBDIRS

    head = rule_name.replace("\\", "/").split("/", 1)[0]
    if head in valid_heads:
        qualified = repo_root / "rules" / rule_name
        if qualified.is_dir():
            return qualified.resolve()
        return qualified

    # Try templates first, then flat
    for candidate in [
        repo_root / "rules" / "templates" / rule_name,
        repo_root / "rules" / rule_name,
    ]:
        if candidate.is_dir():
            return candidate.resolve()

    return repo_root / "rules" / rule_name
