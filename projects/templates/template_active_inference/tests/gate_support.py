"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml

from analysis import run_analysis, write_analysis_statistics
from manuscript.variables import generate_variables
from manuscript.hydrate import write_resolved_manuscript
from manuscript.sheaf import compose_all_sections
from orchestration.coverage_pipeline import ensure_coverage_artifacts
from roadmap_tracks import (
    validate_integration_audit_artifacts,
    validate_sheaf_track_artifacts,
    write_formal_interop_artifacts,
    write_integration_audit_artifacts,
    write_manuscript_staleness_report,
    write_sheaf_track_artifacts,
    write_toy_sweep_artifacts,
)
from simulation.graph_world import write_graph_world_artifacts
from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid
from simulation.si_runner import pymdp_available, run_and_persist
from validation_spine import write_validation_spine_artifacts
from visualizations.animation import (
    validate_animation_frame_deltas,
    write_animation_frame_deltas,
    write_belief_trajectory_gif,
)
from visualizations.figures import generate_all_figures

_BOOTSTRAPPED_ROOTS: set[Path] = set()
_BOOTSTRAPPED_SIGNATURES: dict[Path, str] = {}
_ALLOW_GATE_REBUILD_ENV = "TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD"

from contracts.artifact_contract import REQUIRED_GATE_ARTIFACTS as _REQUIRED_GATE_ARTIFACTS
from json_io import write_json


def _required_gate_artifacts_signature(project_root: Path) -> str | None:
    if not _REQUIRED_GATE_ARTIFACTS:
        return None
    digest = hashlib.sha256()
    for rel in _REQUIRED_GATE_ARTIFACTS:
        path = project_root / rel
        if not path.is_file():
            return None
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _fixed_point_passes() -> int:
    raw = os.environ.get("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "1")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 1
    return max(1, value)


def _gate_rebuild_allowed() -> bool:
    raw = os.environ.get(_ALLOW_GATE_REBUILD_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def gate_artifact_readiness_issues(project_root: Path) -> tuple[str, ...]:
    issues: list[str] = []
    missing = [rel for rel in _REQUIRED_GATE_ARTIFACTS if not (project_root / rel).is_file()]
    if missing:
        shown = ", ".join(missing[:10])
        suffix = "" if len(missing) <= 10 else f", ... ({len(missing)} total)"
        issues.append(f"missing required gate artifacts: {shown}{suffix}")
        return tuple(issues)
    try:
        from gates.claim_ledger import validate_claim_ledger
        from manuscript.sheaf.semantic import validate_semantic_gluing
        from roadmap_tracks import validate_integration_audit_artifacts, validate_sheaf_track_artifacts

        semantic_issues = validate_semantic_gluing(project_root)
        animation_issues = validate_animation_frame_deltas(project_root)
        integration_issues = validate_integration_audit_artifacts(project_root)
        sheaf_issues = validate_sheaf_track_artifacts(project_root)
        if semantic_issues:
            issues.append(f"semantic gluing issues: {len(semantic_issues)}")
        if animation_issues:
            issues.append(f"animation frame-delta issues: {len(animation_issues)}")
        if integration_issues:
            issues.append(f"integration audit issues: {len(integration_issues)}")
        if sheaf_issues:
            issues.append(f"sheaf track issues: {len(sheaf_issues)}")
        if not validate_claim_ledger(project_root):
            issues.append("claim ledger validation failed")
    except Exception as exc:
        issues.append(f"readiness check raised {type(exc).__name__}: {exc}")
    return tuple(issues)


def _stale_gate_artifact_message(project_root: Path) -> str:
    issues = gate_artifact_readiness_issues(project_root)
    detail = "\n".join(f"- {issue}" for issue in issues) or "- readiness status unknown"
    return (
        "template_active_inference gate artifacts are not ready. Standard pytest "
        "runs do not rebuild them because the cold rebuild is a long research "
        "pipeline step, not a template-unit-test step. Refresh the tracked output "
        f"snapshot explicitly with `{_ALLOW_GATE_REBUILD_ENV}=1` and the project "
        "verification/generation commands, then rerun tests.\n"
        f"{detail}"
    )


@contextmanager
def temporary_json_mutation(path: Path, mutate: Callable[[dict], None]) -> Iterator[dict]:
    """Temporarily mutate a JSON artifact and restore it byte-for-byte."""
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    mutate(payload)
    write_json(path, payload)
    try:
        yield payload
    finally:
        path.write_text(original, encoding="utf-8")


@contextmanager
def temporary_text_mutation(path: Path, mutate: Callable[[str], str]) -> Iterator[str]:
    """Temporarily mutate a text file and restore it byte-for-byte."""
    original = path.read_text(encoding="utf-8")
    mutated = mutate(original)
    path.write_text(mutated, encoding="utf-8")
    try:
        yield mutated
    finally:
        path.write_text(original, encoding="utf-8")


@contextmanager
def temporary_yaml_mutation(path: Path, mutate: Callable[[dict], None]) -> Iterator[dict]:
    """Temporarily mutate a YAML mapping and restore the source byte-for-byte."""
    original = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(original) or {}
    mutate(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    try:
        yield payload
    finally:
        path.write_text(original, encoding="utf-8")


def _hydrate_fixed_point(project_root: Path, out: Path) -> None:
    import json

    for _ in range(2):
        variables = generate_variables(project_root, require_analysis_outputs=False)
        out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
        write_resolved_manuscript(project_root, variables)
        write_manuscript_staleness_report(project_root)


def _settle_generated_contracts(project_root: Path, out: Path, *, passes: int | None = None) -> None:
    """Converge visual, integration, sheaf, and hydrated-manuscript artifacts."""
    from roadmap_tracks.fixed_point import run_semantic_fixed_point

    requested_passes = _fixed_point_passes() if passes is None else passes
    semantic_max_passes = max(4, requested_passes * 4)
    for _ in range(max(1, requested_passes)):
        write_sheaf_track_artifacts(project_root, finalize=False)
        generate_all_figures(project_root)
        write_belief_trajectory_gif(project_root)
        write_animation_frame_deltas(project_root)
        run_semantic_fixed_point(
            project_root,
            require_analysis_outputs=False,
            max_passes=semantic_max_passes,
        )
    if not out.is_file():
        _hydrate_fixed_point(project_root, out)


def refresh_generated_gate_artifacts(project_root: Path, *, force: bool = True) -> None:
    """Refresh generated manuscript/semantic artifacts after mutation tests.

    Post-mutation cleanup forces regeneration by default because source and
    generated-output negative controls can leave derived artifacts stale even
    after the edited file is restored byte-for-byte. Callers that know no source
    or generated artifact changed may pass ``force=False`` to reuse the cache.
    """
    root = project_root.resolve()
    existing_signature = _required_gate_artifacts_signature(root)
    if not force and existing_signature and _BOOTSTRAPPED_SIGNATURES.get(root) == existing_signature:
        return
    if not force and existing_signature and _gate_artifacts_present(root):
        _BOOTSTRAPPED_SIGNATURES[root] = existing_signature
        _BOOTSTRAPPED_ROOTS.add(root)
        return
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _settle_generated_contracts(root, out)
    refresh_gate_artifact_session_signature(root)


def refresh_gate_artifact_session_signature(project_root: Path) -> None:
    root = project_root.resolve()
    signature = _required_gate_artifacts_signature(root)
    if not signature:
        raise AssertionError("required gate artifacts are incomplete; cannot refresh session signature")
    if not _gate_artifacts_present(root):
        raise AssertionError("gate artifacts are invalid; cannot refresh session signature")
    _BOOTSTRAPPED_SIGNATURES[root] = signature
    _BOOTSTRAPPED_ROOTS.add(root)


def refresh_output_gate_contracts(project_root: Path) -> None:
    root = project_root.resolve()
    animation_issues = validate_animation_frame_deltas(root)
    integration_issues = validate_integration_audit_artifacts(root)
    sheaf_issues = validate_sheaf_track_artifacts(root)
    if not animation_issues and not integration_issues and not sheaf_issues:
        refresh_gate_artifact_session_signature(root)
        return
    if animation_issues:
        write_animation_frame_deltas(root)
    if integration_issues or sheaf_issues:
        write_integration_audit_artifacts(root)
        write_sheaf_track_artifacts(root)
    animation_issues = validate_animation_frame_deltas(root)
    if animation_issues:
        write_animation_frame_deltas(root)
        animation_issues = validate_animation_frame_deltas(root)
    integration_issues = validate_integration_audit_artifacts(root)
    sheaf_issues = validate_sheaf_track_artifacts(root)
    remaining = {
        "animation": animation_issues,
        "integration": integration_issues,
        "sheaf": sheaf_issues,
    }
    remaining = {name: issues for name, issues in remaining.items() if issues}
    if remaining:
        raise AssertionError(f"output gate contracts remain invalid after refresh: {remaining}")
    refresh_gate_artifact_session_signature(root)


def refresh_composed_gate_artifacts(project_root: Path) -> None:
    """Refresh derived manuscript files after byte-for-byte output mutations.

    Negative tests that edit composed manuscript pages or hydrated output files do
    not need to rebuild the full semantic fixed point. Re-compose the manuscript,
    refresh the coverage page/heatmap, and rehydrate variables so subsequent
    gates do not see stale derived Markdown from the mutation.
    """

    root = project_root.resolve()
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    compose_all_sections(root)
    ensure_coverage_artifacts(root, write_page=True, render_heatmap=True, force=True)
    _hydrate_fixed_point(root, out)


def _gate_artifacts_present(project_root: Path) -> bool:
    return not gate_artifact_readiness_issues(project_root)


def _required_gate_artifacts_exist(project_root: Path) -> bool:
    for rel in _REQUIRED_GATE_ARTIFACTS:
        path = project_root / rel
        if not path.is_file():
            return False
        if rel.startswith("output/figures/") and path.suffix.lower() in {".png", ".gif"}:
            from visualizations.figure_io import image_render_metrics

            metrics = image_render_metrics(path)
            if not metrics["width_px"] or not metrics["height_px"] or not metrics["nonblank"]:
                return False
    return True


def ensure_gate_artifacts(project_root: Path) -> None:
    """Rebuild analysis, simulation, sheaf, and figure outputs for gate checks."""
    root = project_root.resolve()
    signature = _required_gate_artifacts_signature(root)
    if signature and _BOOTSTRAPPED_SIGNATURES.get(root) == signature:
        _BOOTSTRAPPED_ROOTS.add(root)
        return
    if _gate_artifacts_present(root):
        _BOOTSTRAPPED_ROOTS.add(root)
        if signature:
            _BOOTSTRAPPED_SIGNATURES[root] = signature
        return

    if not _gate_rebuild_allowed():
        raise AssertionError(_stale_gate_artifact_message(root))

    run_analysis(project_root)
    if pymdp_available():
        run_and_persist(project_root)
        write_policy_comparison(project_root)
        write_policy_posterior_grid(project_root)
    else:
        pytest.skip("pymdp not installed")
    write_graph_world_artifacts(project_root)
    write_analysis_statistics(project_root)
    compose_all_sections(project_root)
    ensure_coverage_artifacts(project_root, write_page=True, render_heatmap=True, force=True)
    write_validation_spine_artifacts(project_root)
    write_toy_sweep_artifacts(project_root)
    write_formal_interop_artifacts(project_root)
    write_validation_spine_artifacts(project_root)
    write_sheaf_track_artifacts(project_root, finalize=False)
    generate_all_figures(project_root)
    write_belief_trajectory_gif(project_root)
    write_animation_frame_deltas(project_root)
    out = project_root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _settle_generated_contracts(project_root, out)
    # NOTE: the final convergence pass is intentionally narrower than the full
    # bootstrap. It settles cross-artifact contract rows after figures, integration
    # reports, sheaf consolidation, and hydrated manuscript variables have all moved.
    refresh_gate_artifact_session_signature(root)
