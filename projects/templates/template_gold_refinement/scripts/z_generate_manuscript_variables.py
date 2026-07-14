#!/usr/bin/env python3
"""Thin orchestrator: generate and inject manuscript variables.

Reads config and refinery outputs, writes
``output/data/manuscript_variables.json``, and substitutes
``{{TOKEN}}`` markers in manuscript sections into
``output/manuscript/`` for PDF rendering.

All computation lives in ``src/manuscript_variables``;
all injection lives in ``infrastructure.rendering.manuscript_injection``.

Exit codes:
    0   variables written and injected successfully
    1   unexpected error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT.parents[2]))


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate manuscript variables for template_gold_refinement")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow N/A fallbacks when analysis outputs are missing (non-pipeline draft mode)",
    )
    args = parser.parse_args()

    from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree
    from config import load_gold_refinement_config
    from manuscript_variables import generate_variables, save_variables
    from seed_sensitivity import validate_seed_sensitivity_payload

    seed_report_path = _PROJECT_ROOT / "output" / "data" / "seed_sensitivity.json"
    if seed_report_path.exists():
        try:
            seed_payload = json.loads(seed_report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid seed sensitivity report: {seed_report_path}: {exc}") from exc
        seed_issues = validate_seed_sensitivity_payload(
            load_gold_refinement_config(_PROJECT_ROOT),
            seed_payload,
        )
        if seed_issues:
            raise ValueError("; ".join(seed_issues))

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
