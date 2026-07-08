#!/usr/bin/env python3
"""Thin orchestrator: generate and inject manuscript variables.

Reads paper config and analysis outputs, writes
``output/data/manuscript_variables.json``, and substitutes
``{{TOKEN}}`` markers in manuscript sections into
``output/manuscript/`` for PDF rendering.

All computation lives in ``src.manuscript_variables``; all injection lives in
``infrastructure.rendering.manuscript_injection``.

Exit codes:
    0   variables written and injected successfully
    1   unexpected error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT.parents[2]))


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate manuscript variables for template_methods_paper")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow N/A fallbacks when analysis outputs are missing (non-pipeline draft mode)",
    )
    args = parser.parse_args()

    from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree
    from src.manuscript_variables import generate_variables, save_variables

    variables = generate_variables(
        _PROJECT_ROOT,
        require_analysis_outputs=not args.allow_draft,
    )
    out_path = _PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    save_variables(variables, out_path)
    write_resolved_manuscript_tree(_PROJECT_ROOT, variables)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
