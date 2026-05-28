"""Phase-ledger payloads for the deterministic AutoResearch loop."""

from __future__ import annotations

import json
from pathlib import Path

from .models import AutoResearchLoopResult

PHASE_LEDGER_SCHEMA = "template-autoresearch-phase-ledger-v1"


def phase_ledger_payload(
    project_root: Path,
    result: AutoResearchLoopResult,
    output_paths: list[Path],
    *,
    generated_at: str,
    settlement_pass_count: int,
) -> dict[str, object]:
    """Return the deterministic loop phase ledger."""
    phase_specs = (
        ("intrinsic_readiness", "readiness", "validate configured project-intrinsic contracts"),
        ("core_artifacts", "loop", "write plan, stage matrix, and provisional loop outputs"),
        ("evidence_registry", "evidence", "write local evidence registry"),
        ("ml_task", "ml", "run fixed-seed bounded candidate evaluation"),
        ("method_contract", "governance", "write program, idea, run, review, and benchmark ledgers"),
        ("provisional_payloads", "settlement", "refresh loop payloads before extrinsic validation"),
        ("security_artifacts", "security", "write local security and integrity evidence"),
        ("final_visuals", "figures", "write final registry-backed figures"),
        ("manuscript_hydration", "manuscript", "write variables, provenance, and figure blocks"),
        ("readiness_manifest", "settlement", "refresh checksum manifest before extrinsic validation"),
        ("schema_manifest", "schema", "write generated JSON schema-version manifest"),
        ("research_object_manifest", "packaging", "write local research-object manifest"),
        ("extrinsic_readiness", "readiness", "validate generated artifacts and extrinsic contracts"),
        ("final_schema_manifest", "schema", "refresh schema manifest after final payload updates"),
        ("final_research_object_manifest", "packaging", "refresh local research-object manifest"),
        ("artifact_manifest", "settlement", "write final artifact checksum manifest"),
    )
    rel_paths = [_relative_path(project_root, path) for path in output_paths if path.exists()]
    phases = [
        {
            "order": index,
            "phase": phase,
            "artifact_group": group,
            "description": description,
            "observed_artifact_count": _artifact_count_for_group(rel_paths, group),
        }
        for index, (phase, group, description) in enumerate(phase_specs, start=1)
    ]
    return {
        "schema": PHASE_LEDGER_SCHEMA,
        "generated_at": generated_at,
        "project_name": result.project_name,
        "settlement_pass_count": settlement_pass_count,
        "readiness_valid": result.readiness_valid,
        "publication_approved": result.config.human_review.publication_approved,
        "phases": phases,
        "claim_boundary": (
            "Phase ledger records deterministic artifact-settlement order only; it is not runtime autonomy, "
            "self-approval, or external workflow certification."
        ),
    }


def write_phase_ledger(
    path: Path,
    project_root: Path,
    result: AutoResearchLoopResult,
    output_paths: list[Path],
    *,
    generated_at: str,
    settlement_pass_count: int,
) -> Path:
    """Write the deterministic loop phase ledger."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            phase_ledger_payload(
                project_root,
                result,
                output_paths,
                generated_at=generated_at,
                settlement_pass_count=settlement_pass_count,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _artifact_count_for_group(paths: list[str], group: str) -> int:
    if group == "ml":
        return sum(path.startswith("output/data/ml_") or path.startswith("output/figures/ml_") for path in paths)
    if group == "figures":
        return sum(path.startswith("output/figures/") for path in paths)
    if group == "security":
        return sum(
            "security" in path or "integrity" in path or "inventory" in path or "threat_model" in path for path in paths
        )
    if group == "manuscript":
        return sum("manuscript" in path for path in paths)
    if group == "schema":
        return sum("schema" in path for path in paths)
    if group == "packaging":
        return sum("research_object" in path for path in paths)
    if group == "readiness":
        return sum("readiness" in path for path in paths)
    if group == "evidence":
        return sum("evidence_registry" in path for path in paths)
    if group == "governance":
        return sum(path.endswith(("review_decisions.json", "run_ledger.json", "idea_ledger.json")) for path in paths)
    if group == "settlement":
        return sum("artifact_manifest" in path or "autoresearch_loop" in path for path in paths)
    return 0


def _relative_path(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
