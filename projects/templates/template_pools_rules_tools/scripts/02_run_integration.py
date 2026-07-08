#!/usr/bin/env python3
"""02_run_integration.py — Run the full fonds/rules/tools integration demo.

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys

_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))

from src.integration import run_integration_demo

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def _serialisable(obj: object) -> object:
    """Convert pathlib.Path objects to strings for JSON serialisation."""
    if isinstance(obj, pathlib.Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


def main() -> int:
    """CLI entry point."""
    print("Running integration demo …")
    results = run_integration_demo()

    summary = results["summary"]
    print()
    print("=" * 60)
    print("Integration Summary")
    print("=" * 60)
    print(f"  Fonds loaded:        {summary['fonds_loaded']} / 3")
    print(f"  Rules sets OK:       {summary['rules_sets_ok']} / {summary['rules_sets_total']}")
    print(f"  Tools discovered:    {summary['tools_discovered']}")
    print(f"  Tools valid:         {summary['tools_valid']}")
    print(f"  Bib entries:         {summary['bib_entries']}")
    print(f"  Contacts:            {summary['contacts']}")
    print(f"  Datasets:            {summary['datasets']}")

    # Pretty-print the full results (omit 'tools' path objects for clarity)
    printable = {
        "summary": summary,
        "rules_statuses": {
            k: {
                "status": v["status"],
                "soft": v["soft_rules_count"],
                "strong": v["strong_rules_count"],
            }
            for k, v in results["rules"].items()
        },
        "tools": [
            {
                "name": t["name"],
                "type": (t["manifest"] or {}).get("type"),
                "valid": t["validation"]["valid"],
                "missing": t["validation"]["missing"],
            }
            for t in results["tools"]
        ],
    }

    print()
    print(json.dumps(printable, indent=2, default=_serialisable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
