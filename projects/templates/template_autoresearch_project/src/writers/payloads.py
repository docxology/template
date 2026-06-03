"""Loop JSON and manuscript payload refresh writers."""

from __future__ import annotations

from pathlib import Path

from src.manuscript import compute_variables_from_payload, save_variables
from src.config import AutoResearchLoopConfig
from src.models import AutoResearchLoopResult, LoopStageResult
from src.reports import (
    build_review_packet,
    render_loop_markdown,
    render_review_packet_markdown,
    render_summary_markdown,
)

from .io import write_json, write_text
from .loop_artifacts import write_core_loop_artifacts


def refresh_loop_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Write or refresh loop JSON, review payloads, and manuscript variables."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    return [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_claims.json", [claim.to_dict() for claim in result.claims]),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
        save_variables(compute_variables_from_payload(loop_payload), data_dir / "manuscript_variables.json"),
    ]


def finalize_loop_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Compatibility alias for ``refresh_loop_payloads``."""
    return refresh_loop_payloads(project_root, result)


def update_result_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Compatibility alias for ``refresh_loop_payloads``."""
    return refresh_loop_payloads(project_root, result)


def write_loop_payloads(
    project_root: Path,
    plan_payload: dict[str, object],
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
    return [*core_paths, *refresh_loop_payloads(project_root, result)]
