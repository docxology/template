#!/usr/bin/env python3
"""04_validate_strong_rules.py — Semantic evaluation of strong rule schemas.

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py
"""

from __future__ import annotations

import logging
import pathlib
import sys

_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))

from src.strong_rule_evaluator import (  # noqa: E402
    evaluate_strong_rules,
    load_rule_context_from_project,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_RULE_SETS = ["template_project_rules", "template_manuscript_rules"]


def main() -> int:
    """CLI entry point."""
    context = load_rule_context_from_project(_PROJECT_DIR)
    errors: list[str] = []

    print("=" * 60)
    print("Strong rule semantic evaluation")
    print("=" * 60)

    for rule_set in _RULE_SETS:
        result = evaluate_strong_rules(rule_set, context)
        sym = "✓" if result["passed"] else "✗"
        print(
            f"  {sym}  {rule_set} — "
            f"evaluations={len(result['evaluations'])}  "
            f"violations={result['violation_count']}"
        )
        for evaluation in result["evaluations"]:
            if evaluation["passed"]:
                continue
            for violation in evaluation["violations"]:
                message = f"{rule_set}/{evaluation['rule_name']}: {violation['message']}"
                logger.warning("     %s", message)
                errors.append(message)

    print()
    if errors:
        print("Strong rule violations:")
        for error in errors:
            print(f"  ✗  {error}")
        return 1

    print("All strong rules passed semantic evaluation (or were skipped without context).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
