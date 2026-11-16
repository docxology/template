"""Final-byte settlement shared by the loop and standalone hydration entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from infrastructure.autoresearch import (
    AutoResearchPlan,
    AutoResearchReport,
    build_autoresearch_plan,
    validate_autoresearch_plan,
    write_autoresearch_report,
)
from infrastructure.autoresearch.models import AutoResearchIssue
from infrastructure.core.files.portability import sanitize_machine_local_paths
from infrastructure.core.pipeline.artifacts import (
    artifact_manifest_from_payload,
    collect_stable_output_inventory,
    output_inventory_mode_for_project,
    validate_artifact_manifest,
)


def terminal_readiness(plan: AutoResearchPlan, project_root: Path) -> AutoResearchReport:
    """Read-only validation of actual terminal bytes; never refresh a failed snapshot."""
    intrinsic = validate_autoresearch_plan(plan, project_root, phase="intrinsic")
    extrinsic = validate_autoresearch_plan(plan, project_root, phase="extrinsic")
    manifest_path = project_root / "output/reports/artifact_manifest.json"
    manifest = artifact_manifest_from_payload(json.loads(manifest_path.read_text(encoding="utf-8")))
    primary = validate_artifact_manifest(
        manifest,
        project_dir=project_root,
        expected_inventory_mode=output_inventory_mode_for_project(plan.repo_root, project_root),
    )
    issues = (
        *intrinsic.issues,
        *extrinsic.issues,
        *(
            AutoResearchIssue(severity="error", code="AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE", message=message)
            for message in primary.issues
        ),
    )
    return AutoResearchReport(
        project_name=plan.project_name,
        valid=intrinsic.valid and extrinsic.valid and not primary.issues,
        issues=issues,
        plan=plan,
    )


def invalidate_settlement(project_root: Path, plan: AutoResearchPlan, report: AutoResearchReport) -> None:
    """Revoke reusable readiness before any failure-path snapshot or exception escape."""
    from ..writers.io import write_json

    write_autoresearch_report(project_root, report)
    for relative in ("output/data/autoresearch_loop.json", "output/reports/autoresearch_loop.json"):
        path = project_root / relative
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.setdefault("metrics", {})["readiness_valid"] = False
            write_json(path, payload)
    phase = project_root / "output/data/autoresearch_phase_ledger.json"
    if phase.is_file():
        payload = json.loads(phase.read_text(encoding="utf-8"))
        payload["readiness_valid"] = False
        write_json(phase, payload)


def failed_settlement_report(plan: AutoResearchPlan, error: Exception) -> AutoResearchReport:
    """Keep unexpected final-writer/reader failures explicit, never earlier success."""
    return AutoResearchReport(
        project_name=plan.project_name,
        valid=False,
        plan=plan,
        issues=(
            AutoResearchIssue(
                severity="error",
                code="AUTORESEARCH.SETTLEMENT_FAILED",
                message=f"Final-byte settlement failed: {type(error).__name__}: {error}",
            ),
        ),
    )


def _frozen_upstream_evidence(project_root: Path) -> tuple[dict, dict | None]:
    """Hold prior scientific evidence, authenticated by its existing primary entries."""
    from infrastructure.core.files.secure_write import read_bytes_confined

    primary = artifact_manifest_from_payload(
        json.loads((project_root / "output/reports/artifact_manifest.json").read_text(encoding="utf-8"))
    )
    entries = {entry.path: entry for entry in primary.entries}
    names = ["output/data/research_object_manifest.json"]
    inventory_name = "output/data/autoresearch_supply_chain_inventory.json"
    if (project_root / inventory_name).is_file():
        names.append(inventory_name)
    held = {}
    for name in names:
        entry = entries.get(name)
        if entry is None:
            raise ValueError(f"Frozen upstream evidence lacks its primary binding: {name}")
        content = read_bytes_confined(project_root, project_root / name, max_bytes=max(1, entry.size_bytes))
        if len(content) != entry.size_bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise ValueError(f"Frozen upstream evidence changed: {name}")
        held[name] = json.loads(content)
    research = held[names[0]]
    if research.get("schema") != "template-autoresearch-research-object-manifest-v2":
        raise ValueError("Hydration requires the actual current loop's frozen upstream evidence")
    return research, held.get(inventory_name)


def _verify_frozen_upstream(project_root: Path, frozen: tuple[dict, dict | None], *, generated_at: str) -> None:
    """Verify original inputs/results afresh, never certify replacement science."""
    from infrastructure.core.files.secure_write import read_bytes_confined
    from ..security.payloads import integrity_attestation_payload
    from ..writers.integrity_boundary import UPSTREAM_OUTPUTS

    research, inventory = frozen
    rows = [row for row in research["artifacts"] if row.get("record_kind") == "upstream_checksum"]
    expected = {name for name in UPSTREAM_OUTPUTS if (project_root / name).is_file()}
    if len(rows) != len(expected) or {row["path"] for row in rows} != expected:
        raise ValueError("Frozen upstream result membership changed")
    ledger = research["source_ledger"]
    if ledger.get("record_kind") != "upstream_checksum" or ledger.get("path") != "manuscript/source_ledger.yaml":
        raise ValueError("Frozen source-ledger checksum binding is invalid")
    rows.append(ledger)
    for row in rows:
        content = read_bytes_confined(
            project_root,
            project_root / row["path"],
            max_bytes=max(1, row["size_bytes"]),
        )
        if (len(content), hashlib.sha256(content).hexdigest(), not content) != (
            row["size_bytes"],
            row["sha256"],
            row["empty"],
        ):
            raise ValueError(f"Frozen upstream result changed: {row['path']}")
    if inventory is not None:
        checked = integrity_attestation_payload(project_root, inventory, generated_at=generated_at)
        if checked["status"] != "passed":
            raise ValueError("Frozen upstream input/evidence integrity changed")


def settle_standalone_hydration(project_root: Path, repo_root: Path) -> list[Path]:
    """Strictly consume real loop outputs; settle catalogs, hydration, then validate."""
    from ..manuscript.artifact_loader import load_loop_artifacts
    from ..manuscript.manuscript_variables import compute_variables, write_manuscript_hydration_artifacts
    from ..writers.manifests import write_artifact_manifest, write_research_object_manifest, write_schema_manifest
    from infrastructure.rendering.manuscript_injection import (
        _hydration_member,
        _rebase_output_links_for_destination,
        hydrate_manuscript_tree,
        stale_hydration_paths,
        substitute_manuscript_text,
    )

    # Refuse invalid inputs before writing sidecars, resolved sources or a primary manifest.
    artifacts = load_loop_artifacts(project_root, require_valid=True)
    plan = build_autoresearch_plan(repo_root, project_root.name, projects_dir=str(project_root.parent))
    generated_at = str(artifacts.loop["generated_at"])
    mode = output_inventory_mode_for_project(repo_root, project_root)
    inventory = collect_stable_output_inventory(project_root / "output", inventory_mode=mode)
    paths = set(inventory.files).difference(stale_hydration_paths(project_root))
    paths.update(
        project_root / "output/manuscript" / path.name
        for path in (project_root / "manuscript").iterdir()
        if path.is_file() and _hydration_member(path.name)
    )
    paths.update(
        project_root / name
        for name in (
            "output/data/manuscript_variables.json",
            "output/data/manuscript_variable_provenance.json",
            "output/data/manuscript_figure_blocks.json",
            "output/data/research_object_manifest.json",
            "output/data/autoresearch_schema_manifest.json",
            "output/reports/artifact_manifest.json",
            "output/manuscript/hydration_manifest.json",
            "output/reports/evidence_registry.json",
        )
    )
    declared = sorted(paths)
    report = None
    try:
        from ..writers.io import write_json
        from .phase_ledger import _artifact_count_for_group

        frozen = _frozen_upstream_evidence(project_root)
        _verify_frozen_upstream(project_root, frozen, generated_at=generated_at)

        rel_paths = [path.relative_to(project_root).as_posix() for path in declared]
        for relative in (
            "output/data/autoresearch_loop.json",
            "output/reports/autoresearch_loop.json",
            "output/data/autoresearch_review_packet.json",
        ):
            path = project_root / relative
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["output_paths"] = rel_paths
            write_json(path, payload)
        ledger_path = project_root / "output/data/autoresearch_phase_ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger["declared_paths"] = rel_paths
        ledger["declared_artifact_count"] = len(rel_paths)
        ledger["standalone_hydration"] = True
        for row in ledger["phases"]:
            row.pop("observed_artifact_count", None)
            row["declared_artifact_count"] = _artifact_count_for_group(rel_paths, str(row["artifact_group"]))
        write_json(ledger_path, ledger)
        sanitize_machine_local_paths(project_root / "output")
        write_research_object_manifest(project_root, declared, generated_at=generated_at)
        write_schema_manifest(project_root, declared, generated_at=generated_at)
        # Structural table membership is needed before hydration, not this snapshot's hashes.
        write_artifact_manifest(project_root, repo_root=repo_root)
        sidecars = write_manuscript_hydration_artifacts(project_root, require_valid=True, validate_sources=True)
        variables = compute_variables(project_root)

        def render(_filename: str, text: str) -> str:
            resolved, unresolved = substitute_manuscript_text(text, variables)
            if unresolved:
                raise ValueError(f"Unresolved manuscript variables: {unresolved}")
            return _rebase_output_links_for_destination(resolved)

        # The platform's ownership-aware writer retains inherited publication outputs;
        # transmission bookends belong to rendering, not a hydration-side science run.
        hydrate_manuscript_tree(project_root, render)
        write_artifact_manifest(project_root, repo_root=repo_root)
        _verify_frozen_upstream(project_root, frozen, generated_at=generated_at)
        report = terminal_readiness(plan, project_root)
        if not report.valid:
            raise ValueError("Terminal AutoResearch settlement validation failed")
        return sidecars
    except Exception as error:  # noqa: BLE001 - final handler revokes readiness for every failure, then re-raises
        failure = report if report is not None and not report.valid else failed_settlement_report(plan, error)
        invalidate_settlement(project_root, plan, failure)
        write_artifact_manifest(project_root, repo_root=repo_root)
        raise
