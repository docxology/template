#!/usr/bin/env python3
"""z_generate_manuscript_variables.py — Hydrate and inject manuscript tokens.

Invoked automatically by the rendering pipeline
(``infrastructure.rendering._manuscript_source.run_manuscript_variable_script``)
immediately before PDF rendering. Writes
``output/data/manuscript_variables.json`` and substitutes every
``{{UPPERCASE_KEY}}`` token in ``manuscript/*.md`` into
``output/manuscript/``, which the renderer then prefers over the raw
``manuscript/`` source (see
:func:`infrastructure.rendering._manuscript_source.resolve_manuscript_dir`).

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/z_generate_manuscript_variables.py
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys

_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))
# Repo root for `infrastructure.*` imports when the rendering pipeline invokes
# this script as a subprocess (sibling z_generate convention, e.g. gold_refinement).
sys.path.insert(0, str(_PROJECT_DIR.parents[2]))

from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree

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

    injected_dir = write_resolved_manuscript_tree(_PROJECT_DIR, variables)
    logger.info("Injected resolved manuscript into %s", injected_dir)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
