"""Rules infrastructure — soft guidelines and strong formal constraints.

Provides rule discovery, validation, sidecar symlink sync, and public-scope
helpers for the ``rules/`` top-level directory, mirroring the architecture
of ``infrastructure/fonds/`` but for specifications rather than resource pools.

Rules are soft (markdown guidelines, prompt-style) or strong (yaml/json
formal constraints) specifications that govern projects, manuscripts, code,
or data.

Usage::

    from infrastructure.rules import (
        RuleInfo,
        discover_rules,
        resolve_rule_root,
        validate_rule_structure,
    )
"""

from infrastructure.rules.discovery import discover_rules, resolve_rule_root
from infrastructure.rules.rules_info import RuleInfo, build_rule_info
from infrastructure.rules.validation import validate_rule_structure

__all__ = [
    "RuleInfo",
    "build_rule_info",
    "discover_rules",
    "resolve_rule_root",
    "validate_rule_structure",
]
