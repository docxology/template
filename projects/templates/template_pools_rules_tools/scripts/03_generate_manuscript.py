#!/usr/bin/env python3
"""03_generate_manuscript.py — Generate manuscript variables for PDF rendering.

Reads the integration demo results and emits a manuscript_variables.json
file to output/data/ (created if absent). Token computation lives in
``src/manuscript_variables.py``, shared with
``scripts/z_generate_manuscript_variables.py`` (which additionally injects
the tokens into ``output/manuscript/`` before rendering).

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

from src.manuscript_variables import generate_variables

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_OUTPUT_DIR = _PROJECT_DIR / "output" / "data"


def main() -> int:
    """CLI entry point."""
    variables = generate_variables()

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
