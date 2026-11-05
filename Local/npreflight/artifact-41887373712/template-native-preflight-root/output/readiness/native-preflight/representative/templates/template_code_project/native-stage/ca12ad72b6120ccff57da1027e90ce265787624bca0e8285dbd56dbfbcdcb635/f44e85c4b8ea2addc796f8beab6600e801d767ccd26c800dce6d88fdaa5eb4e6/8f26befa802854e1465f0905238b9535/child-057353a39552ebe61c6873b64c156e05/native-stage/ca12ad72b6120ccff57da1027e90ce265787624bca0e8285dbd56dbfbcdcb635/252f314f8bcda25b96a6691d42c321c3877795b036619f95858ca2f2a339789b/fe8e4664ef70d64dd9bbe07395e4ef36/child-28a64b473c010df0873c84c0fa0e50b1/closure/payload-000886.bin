"""RuleInfo dataclass for representing discovered rules (specifications).

A rule is a specification — soft (prompt-like guidelines) or strong (formal
constraints) — that applies to projects, subsets, or parts of individual
projects. Distinct from fonds (resource pools) and projects (executable code).

Rules live in a ``rules/`` directory, with:
- ``soft/``   — markdown guideline files (prose / prompt-style)
- ``strong/`` — yaml or json formal constraint files
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RuleInfo:
    """Information about a discovered rule.

    Attributes:
        name: Rule directory name
        path: Absolute path to rule directory
        rule_type: Specification domain (project|manuscript|code|data)
        has_soft: Whether rule has soft/ directory (markdown guidelines)
        has_strong: Whether rule has strong/ directory (yaml/json formal specs)
        metadata: Raw metadata dict from rules.yaml
        program: Parent program directory name (empty for standalone rules)
    """

    name: str
    path: Path
    rule_type: str = "project"
    has_soft: bool = False
    has_strong: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    program: str = ""

    @property
    def qualified_name(self) -> str:
        """Full path-like name for display and selection."""
        if self.program:
            return f"{self.program}/{self.name}"
        return self.name

    @property
    def is_valid(self) -> bool:
        """Rule is valid if it has at least one of soft/ or strong/."""
        return self.has_soft or self.has_strong


def build_rule_info(rule_dir: Path, program: str = "") -> RuleInfo:
    """Build a RuleInfo from a validated rule directory.

    Args:
        rule_dir: Path to the rule directory.
        program: Parent program directory name (empty for standalone rules).

    Returns:
        Populated RuleInfo instance.
    """
    metadata = _load_rules_manifest(rule_dir)
    return RuleInfo(
        name=rule_dir.name,
        path=rule_dir,
        rule_type=metadata.get("type", "project") if metadata else "project",
        has_soft=(rule_dir / "soft").exists(),
        has_strong=(rule_dir / "strong").exists(),
        metadata=metadata or {},
        program=program,
    )


def _load_rules_manifest(rule_dir: Path) -> dict[str, Any] | None:
    """Load rules.yaml if present.

    Args:
        rule_dir: Path to the rule directory.

    Returns:
        Parsed YAML dict or None if the file is absent or unreadable.
    """
    manifest_path = rule_dir / "rules.yaml"
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                return loaded if isinstance(loaded, dict) else None
        except Exception:  # noqa: BLE001
            return None
    return None


__all__ = [
    "RuleInfo",
    "build_rule_info",
]
