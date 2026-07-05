"""Public-repository rule scope helpers.

Runtime rule discovery intentionally includes local symlinked workspaces so
the orchestration CLI can operate on private rules. Public CI and generated docs
must stay narrower: only the tracked exemplar rules are part of the
public template repository.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rules.discovery import discover_rules
from infrastructure.rules.rules_info import RuleInfo

#: Canonical roster of git-tracked public exemplar rule names.
#: Each entry is qualified as ``<program>/<name>`` (e.g. ``templates/template_project_rules``).
PUBLIC_RULE_NAMES: tuple[str, ...] = (
    "templates/template_project_rules",
    "templates/template_manuscript_rules",
)


def public_rule_infos(repo_root: Path | str) -> list[RuleInfo]:
    """Return discovered rules that are part of the public template repo."""
    root = Path(repo_root)
    allowed = set(PUBLIC_RULE_NAMES)
    return [rule for rule in discover_rules(root) if rule.qualified_name in allowed]


def public_rule_names(repo_root: Path | str) -> list[str]:
    """Return public template rule names present in this checkout."""
    return sorted(rule.qualified_name for rule in public_rule_infos(repo_root))


__all__ = [
    "PUBLIC_RULE_NAMES",
    "public_rule_infos",
    "public_rule_names",
]
