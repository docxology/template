#!/usr/bin/env python3
"""01_validate_sources.py — Validate that all fonds, rules, and tools sources exist
and are well-formed.

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py
"""

from __future__ import annotations

import logging
import pathlib
import sys

# Ensure src/ is importable when running as a script
_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))

from src.fonds_reader import read_bibliography_fond, read_contacts_fond, read_datasets_fond
from src.rules_applier import validate_against_rules
from src.tools_invoker import discover_tools, validate_tool_scripts_exist

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_RULE_SETS = ["template_project_rules", "template_manuscript_rules"]


def main() -> int:
    """Validate all sources. Returns 0 on success, 1 if any validation fails."""
    errors: list[str] = []

    print("=" * 60)
    print("Validating fonds sources")
    print("=" * 60)

    # Bibliography
    bib = read_bibliography_fond()
    if bib is None:
        logger.warning("SKIP  template_bibliography — fond not found")
    else:
        count = len(bib["csv_rows"])
        print(f"  ✓  template_bibliography — {count} entries")

    # Contacts
    contacts = read_contacts_fond()
    if contacts is None:
        logger.warning("SKIP  template_contacts — fond not found")
    else:
        count = len(contacts["contacts"])
        print(f"  ✓  template_contacts — {count} contacts")

    # Datasets
    datasets = read_datasets_fond()
    if datasets is None:
        logger.warning("SKIP  template_datasets — fond not found")
    else:
        count = len(datasets["datasets"])
        print(f"  ✓  template_datasets — {count} datasets")

    print()
    print("=" * 60)
    print("Validating rules sources")
    print("=" * 60)

    for rule_set in _RULE_SETS:
        result = validate_against_rules(rule_set)
        status_sym = "✓" if result["status"] == "ok" else "⚠"
        print(
            f"  {status_sym}  {rule_set} — "
            f"status={result['status']}  "
            f"soft={result['soft_rules_count']}  "
            f"strong={result['strong_rules_count']}"
        )
        for w in result["warnings"]:
            logger.warning("     %s", w)
        if result["status"] == "missing":
            logger.warning("SKIP  %s — rule set not found", rule_set)

    print()
    print("=" * 60)
    print("Validating tools sources")
    print("=" * 60)

    tools = discover_tools()
    if not tools:
        logger.warning("SKIP  tools/templates/ — no tools discovered")
    else:
        for tool in tools:
            v = validate_tool_scripts_exist(tool["name"])
            sym = "✓" if v["valid"] else "✗"
            print(
                f"  {sym}  {tool['name']} — "
                f"entrypoints={len(v['entrypoints'])}  "
                f"missing={len(v['missing'])}"
            )
            if not v["valid"]:
                errors.append(f"tool {tool['name']}: missing scripts {v['missing']}")

    print()
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  ✗  {e}")
        return 1
    else:
        print("All sources validated successfully (or skipped if absent).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
