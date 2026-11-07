"""Rule discovery for multi-rule support.

Scans the rules/ directory for valid rules (specifications — soft guidelines and
strong formal constraints) and returns RuleInfo objects. Follows the same
architecture as infrastructure/fonds/discovery.py but for specifications rather
than data resource pools.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.lifecycle_discovery import (
    POOL_NON_RENDERED_SUBDIRS,
    POOL_RENDERED_SUBDIRS,
    discover_lifecycle_items,
    resolve_pool_root,
)
from infrastructure.core.logging.utils import get_logger
from infrastructure.rules.rules_info import RuleInfo, build_rule_info
from infrastructure.rules.validation import validate_rule_structure

logger = get_logger(__name__)

#: Non-rendered lifecycle subdirectories under ``rules/``.
#: Only ``templates/`` is ever discovered and rendered (for public exemplars).
#: Working/ holds private sidecar mirrors; archive/ holds retired rules.
NON_RENDERED_RULE_SUBDIRS = POOL_NON_RENDERED_SUBDIRS

#: Rendered subdirectories under ``rules/``.
RENDERED_RULE_SUBDIRS = POOL_RENDERED_SUBDIRS

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
    return discover_lifecycle_items(
        Path(repo_root) / "rules",
        validate_rule_structure,
        build_rule_info,
        excluded=NON_RENDERED_RULE_SUBDIRS,
        kind="rule",
        logger=logger,
    )


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
    return resolve_pool_root(
        Path(repo_root) / "rules",
        rule_name,
        NON_RENDERED_RULE_SUBDIRS | RENDERED_RULE_SUBDIRS,
    )
