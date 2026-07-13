#!/usr/bin/env python3
"""Thin orchestrator: run the gold-refinery analysis pipeline.

Executes the refinery stages, generates the token plan, writes
``output/data/refinery_results.json`` and ``output/reports/token_plan.json``,
and logs the purity progression.

All computation lives in ``src/``; this script only coordinates I/O.

Exit codes:
    0   analysis completed successfully
    1   unexpected error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT.parents[2]))

CLAIM_SUPPORT_REGISTRY_NAME = "claim_support_registry.json"


def main() -> int:
    """CLI entry point."""
    from composition import generate_token_plan
    from config import load_gold_refinement_config
    from refinery import run_refinery

    root = _PROJECT_ROOT

    # Run the refinery
    result = run_refinery()

    # Generate the token plan
    gr_config = load_gold_refinement_config(root)
    token_plan = generate_token_plan(gr_config)

    # Write refinery results
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    refinery_data = {
        "stage_count": result.stage_count,
        "final_purity": result.final_purity,
        "final_karat": result.final_karat.label,
        "total_purity_gain": result.total_purity_gain,
        "is_nine_nines_certified": result.is_nine_nines_certified,
        "purity_sequence": list(result.purity_sequence),
        "stages": [
            {
                "order": s.order,
                "name": s.name,
                "input_purity": s.input_purity,
                "output_purity": s.output_purity,
                "karat": s.karat_grade.label,
                "metallurgical_operation": s.metallurgical_operation,
                "manuscript_operation": s.manuscript_operation,
            }
            for s in result.stages
        ],
    }
    refinery_path = data_dir / "refinery_results.json"
    refinery_path.write_text(json.dumps(refinery_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {refinery_path}")

    # Write token plan
    reports_dir = root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    plan_data = {
        "seed": token_plan.seed,
        "total_tokens": len(token_plan.choices),
        "category_counts": token_plan.category_counts,
        "section_counts": token_plan.section_counts,
        "choices": [c.as_dict() for c in token_plan.choices],
    }
    plan_path = reports_dir / "token_plan.json"
    plan_path.write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {plan_path}")

    # Generate figures
    from figures import generate_all_figures

    figure_paths = generate_all_figures(root)
    for fp in figure_paths:
        print(f"Wrote {fp}")

    # Build evidence registry
    from evidence import build_evidence_registry, write_evidence_registry

    registry = build_evidence_registry(gr_config, root)
    registry_path = reports_dir / CLAIM_SUPPORT_REGISTRY_NAME
    write_evidence_registry(registry, registry_path)
    print(f"Wrote {registry_path}")
    print(f"  Evidence: {registry.supported_claims}/{registry.total_claims} claims supported")

    # Build dashboard
    from dashboard import write_dashboard

    dashboard_path = write_dashboard(root)
    print(f"Wrote {dashboard_path}")

    # Summary
    print("\nRefinery pipeline complete:")
    print(f"  Stages: {result.stage_count}")
    print(f"  Final purity: {result.final_purity:.10f}")
    print(f"  Final karat: {result.final_karat.label}")
    print(f"  Nine-nines certified: {result.is_nine_nines_certified}")
    print(f"  Tokens generated: {len(token_plan.choices)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
