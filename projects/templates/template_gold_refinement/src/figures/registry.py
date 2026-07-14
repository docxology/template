"""Figure registry, quality report, and the all-figures orchestrator.

Serializes the :data:`FIGURE_SPECS` registry, scores rendered PNG/SVG pairs
into a quality report, and drives ``generate_all_figures`` — the single entry
point that renders every chart and diagram and then writes both reports.

All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._common import (
    FIGURE_SPECS,
    _load_json_object,
    _quality_record,
    logger,
)
from .charts import (
    generate_karat_grading_chart,
    generate_purity_progression,
    generate_seed_sensitivity,
    generate_token_density_chart,
)
from .diagrams import (
    generate_claim_evidence_assay,
    generate_evidence_tier_ladder,
    generate_formalism_traceability,
    generate_implementation_circuit,
    generate_integrity_gate_matrix,
    generate_integrity_risk_matrix,
    generate_provenance_sankey,
    generate_purity_claim_scatter,
    generate_token_heatmap,
)


def figure_registry_payload() -> dict[str, Any]:
    """Process figure registry payload."""
    return {"figures": [spec.registry_record() for spec in FIGURE_SPECS]}


def write_figure_registry(output_dir: Path) -> Path:
    """Write the figure registry to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir / "figure_registry.json"
    registry_path.write_text(
        json.dumps(figure_registry_payload(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote %s", registry_path)
    return registry_path


def write_figure_quality_report(project_root: Path) -> Path:
    """Write figure quality report to the output path."""
    output_dir = project_root / "output" / "figures"
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    records = [_quality_record(output_dir, spec) for spec in FIGURE_SPECS]
    registry = _load_json_object(output_dir / "figure_registry.json")
    registry_labels = {str(item.get("label", "")) for item in registry.get("figures", []) if isinstance(item, dict)}
    spec_labels = {spec.label for spec in FIGURE_SPECS}
    payload = {
        "schema": "template-gold-refinement-figure-quality-v1",
        "figure_count": len(FIGURE_SPECS),
        "png_count": sum(1 for record in records if record["png_exists"]),
        "svg_count": sum(1 for record in records if record["svg_exists"]),
        "passing_count": sum(1 for record in records if record["passes_quality"]),
        "registry_parity": registry_labels == spec_labels,
        "records": records,
    }
    path = reports_dir / "figure_quality_report.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s", path)
    return path


def generate_all_figures(project_root: Path) -> list[Path]:
    """Generate all figures for the gold-refinement exemplar.

    Returns the list of generated figure paths.
    """
    output_dir = project_root / "output" / "figures"
    paths = [
        generate_purity_progression(output_dir, project_root=project_root),
        generate_karat_grading_chart(output_dir, project_root=project_root),
        generate_token_density_chart(output_dir, project_root=project_root),
        generate_provenance_sankey(output_dir, project_root=project_root),
        generate_purity_claim_scatter(output_dir, project_root=project_root),
        generate_token_heatmap(output_dir, project_root=project_root),
        generate_seed_sensitivity(output_dir, project_root=project_root),
        generate_integrity_gate_matrix(output_dir, project_root=project_root),
        generate_formalism_traceability(output_dir, project_root=project_root),
        generate_implementation_circuit(output_dir, project_root=project_root),
        generate_claim_evidence_assay(output_dir, project_root=project_root),
        generate_integrity_risk_matrix(output_dir, project_root=project_root),
        generate_evidence_tier_ladder(output_dir, project_root=project_root),
    ]
    write_figure_registry(output_dir)
    write_figure_quality_report(project_root)
    return paths
