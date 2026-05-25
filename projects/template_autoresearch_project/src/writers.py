"""Artifact writers for the AutoResearch loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256

from .config import AutoResearchLoopConfig
from .figures import figure_registry_payload, write_stage_matrix_figure
from .manuscript_variables import compute_variables_from_payload, save_variables
from .models import AutoResearchLoopResult, LoopStageResult
from .reports import (
    build_review_packet,
    render_loop_markdown,
    render_review_packet_markdown,
    render_stage_matrix_csv,
    render_summary_markdown,
)

_VOLATILE_VALIDATION_REPORTS = frozenset(
    {
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
        "output/reports/evidence_registry.json",
    }
)


def write_json(path: Path, payload: object) -> Path:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    """Write text payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def relative_path(project_root: Path, path: Path) -> str:
    """Return a project-relative path string when possible."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def write_artifact_manifest(project_root: Path, paths: list[Path]) -> Path:
    """Write the artifact manifest for declared loop outputs."""
    manifest_path = (project_root / "output" / "reports" / "artifact_manifest.json").resolve()
    entries = []
    for index, path in enumerate(
        sorted(
            {
                path.resolve()
                for path in paths
                if path.exists()
                and path.resolve() != manifest_path
                and relative_path(project_root, path) not in _VOLATILE_VALIDATION_REPORTS
            }
        ),
        start=1,
    ):
        entries.append(
            ArtifactManifestEntry(
                path=relative_path(project_root, path),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=index,
                stage_name="AutoResearch loop",
                contract_match=True,
            )
        )
    manifest = ArtifactManifest(entries=tuple(entries), issues=())
    return write_json(manifest_path, manifest.to_dict())


def write_core_loop_artifacts(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    generated_at: str,
    project_name: str,
) -> list[Path]:
    """Write plan, loop markdown, figure, and stage matrix before readiness is known."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    provisional = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )
    figure_path = write_stage_matrix_figure(figures_dir, provisional)
    return [
        write_json(data_dir / "autoresearch_plan.json", plan_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(provisional)),
        write_text(data_dir / "autoresearch_stage_matrix.csv", render_stage_matrix_csv(provisional)),
        figure_path,
        write_json(figures_dir / "figure_registry.json", figure_registry_payload()),
    ]


def finalize_loop_payloads(
    project_root: Path,
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write JSON payloads and reports that depend on final readiness and claims."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    paths = [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_claims.json", [claim.to_dict() for claim in result.claims]),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
    ]
    variables = compute_variables_from_payload(loop_payload)
    paths.append(save_variables(variables, data_dir / "manuscript_variables.json"))
    return paths


def update_result_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Refresh loop JSON and review payloads after output paths are finalized."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    return [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
        save_variables(
            compute_variables_from_payload(loop_payload),
            data_dir / "manuscript_variables.json",
        ),
    ]


def write_loop_payloads(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write all loop outputs once using core and finalize phases."""
    core_paths = write_core_loop_artifacts(
        project_root,
        plan_payload,
        config,
        stage_results,
        result.generated_at,
        result.project_name,
    )
    return [*core_paths, *finalize_loop_payloads(project_root, result)]
