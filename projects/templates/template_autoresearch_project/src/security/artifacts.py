"""Security artifact writer."""

from __future__ import annotations

from pathlib import Path

from src.config import AutoResearchLoopConfig
from src.ml.task import MLTaskResult
from src.writers.figure_dispatch import FigureRenderContext, render_security_figures
from src.writers.io import write_json, write_text

from .payloads import (
    integrity_attestation_payload,
    local_inventory_export_payload,
    security_profile_payload,
    supply_chain_inventory_payload,
    threat_model_payload,
)
from .render import render_security_review_markdown


def write_security_artifacts(
    project_root: Path,
    config: AutoResearchLoopConfig,
    output_paths: list[Path],
    *,
    generated_at: str,
    ml_result: MLTaskResult,
) -> list[Path]:
    """Write local security profile, threat model, inventory, attestation, report, and figures."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    profile = security_profile_payload(config, generated_at=generated_at)
    threat_model = threat_model_payload(config, generated_at=generated_at)
    inventory = supply_chain_inventory_payload(project_root, output_paths, generated_at=generated_at)
    inventory_export = local_inventory_export_payload(inventory, generated_at=generated_at)
    attestation = integrity_attestation_payload(project_root, inventory, generated_at=generated_at)
    review_markdown = render_security_review_markdown(profile, threat_model, inventory, attestation)

    paths = [
        write_json(data_dir / "autoresearch_security_profile.json", profile),
        write_json(data_dir / "autoresearch_threat_model.json", threat_model),
        write_json(data_dir / "autoresearch_supply_chain_inventory.json", inventory),
        write_json(data_dir / "autoresearch_inventory_export.json", inventory_export),
        write_json(data_dir / "autoresearch_integrity_attestation.json", attestation),
        write_text(reports_dir / "autoresearch_security_review.md", review_markdown),
    ]
    figure_ctx = FigureRenderContext(
        project_root=project_root,
        figures_dir=figures_dir,
        loop_result=None,
        ml_result=ml_result,
        diagnostics={},
    )
    paths.extend(render_security_figures(figure_ctx))
    return paths
