#!/usr/bin/env python3
"""03_generate_manuscript.py — Generate manuscript variables for PDF rendering.

Reads the integration demo results and emits a manuscript_variables.json
file to output/data/ (created if absent).

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/03_generate_manuscript.py
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
logger = logging.getLogger(__name__)

_OUTPUT_DIR = _PROJECT_DIR / "output" / "data"


def generate_manuscript_variables() -> dict[str, object]:
    """Derive manuscript token values from the integration demo results."""
    results = run_integration_demo()
    summary = results["summary"]

    variables: dict[str, object] = {
        "FONDS_LOADED": summary["fonds_loaded"],
        "RULES_SETS_OK": summary["rules_sets_ok"],
        "RULES_SETS_TOTAL": summary["rules_sets_total"],
        "TOOLS_DISCOVERED": summary["tools_discovered"],
        "TOOLS_VALID": summary["tools_valid"],
        "BIB_ENTRIES": summary["bib_entries"],
        "CONTACTS_COUNT": summary["contacts"],
        "DATASETS_COUNT": summary["datasets"],
        "STRONG_RULES_PROJECT": (
            results["rules"].get("template_project_rules", {}).get("strong_rules_count", 0)
        ),
        "STRONG_RULES_MANUSCRIPT": (
            results["rules"].get("template_manuscript_rules", {}).get("strong_rules_count", 0)
        ),
        "TOOL_NAMES": ", ".join(t["name"] for t in results["tools"]),
    }

    return variables


def main() -> int:
    """CLI entry point."""
    variables = generate_manuscript_variables()

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / "manuscript_variables.json"
    out_path.write_text(json.dumps(variables, indent=2), encoding="utf-8")
    logger.info("Wrote %d variables to %s", len(variables), out_path)

    print("Manuscript variables:")
    for k, v in variables.items():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
