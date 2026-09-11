"""Rules modules for the pools/rules/tools exemplar: soft/strong rule
loading and application, plus semantic evaluation of strong rule
constraints.

These modules are re-exported from ``template_pools_rules_tools`` for
backwards compatibility; import them from the package root.
"""

from .rules_applier import (
    get_rules_root,
    load_all_manuscript_rules,
    load_all_project_rules,
    load_soft_rules,
    load_strong_rules,
    validate_against_rules,
)
from .strong_rule_evaluator import (
    evaluate_strong_rules,
    load_rule_context_from_project,
)

__all__ = [
    "evaluate_strong_rules",
    "get_rules_root",
    "load_all_manuscript_rules",
    "load_all_project_rules",
    "load_rule_context_from_project",
    "load_soft_rules",
    "load_strong_rules",
    "validate_against_rules",
]
