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


def _is_non_imrad_manuscript(context: dict[str, object]) -> bool:
    """Check whether the manuscript uses a non-IMRaD structure intentionally.

    This project demonstrates pools/rules/tools architecture rather than a
    standard research paper, so IMRaD section requirements are advisory.
    """
    sections = context.get("manuscript_sections")
    if not isinstance(sections, list):
        return False
    imrad_sections = {"Related Work", "Methods", "Results", "Discussion", "References"}
    return not imrad_sections.intersection(sections)


def main() -> int:
    """CLI entry point."""
    context = load_rule_context_from_project(_PROJECT_DIR)
    errors: list[str] = []
    warnings: list[str] = []

    non_imrad = _is_non_imrad_manuscript(context)

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
                # Section schema violations are advisory for non-IMRaD manuscripts
                if non_imrad and evaluation["rule_name"] == "section_schema":
                    logger.warning("     %s (advisory: non-IMRaD manuscript)", message)
                    warnings.append(message)
                else:
                    logger.warning("     %s", message)
                    errors.append(message)

    print()
    if warnings:
        print("Advisory warnings (non-blocking):")
        for warning in warnings:
            print(f"  ⚠  {warning}")
    if errors:
        print("Strong rule violations:")
        for error in errors:
            print(f"  ✗  {error}")
        return 1

    print(
        "All strong rules passed semantic evaluation (or were advisory for non-IMRaD manuscripts)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
