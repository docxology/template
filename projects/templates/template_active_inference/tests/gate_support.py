"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

import json
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
from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif
from visualizations.figures import generate_all_figures

_BOOTSTRAPPED_ROOTS: set[Path] = set()

_REQUIRED_GATE_ARTIFACTS: tuple[str, ...] = (
    "output/data/parameter_sweep.csv",
    "output/data/si_tmaze_summary.json",
    "output/data/si_tmaze_trace.json",
    "output/data/si_policy_comparison.json",
    "output/data/pymdp_policy_posterior_grid.json",
    "output/reports/pymdp_runtime_diagnostics.json",
    "output/data/si_graph_world_summary.json",
    "output/data/si_graph_world_trace.json",
    "output/data/analysis_statistics.json",
    "output/data/sheaf_coverage_matrix.json",
    "output/data/artifact_provenance.json",
    "output/data/manuscript_variables.json",
    "output/data/sheaf_gluing_certificate.json",
    "output/data/sensitivity_sweep.json",
    "output/data/analytical_assumption_index.json",
    "output/data/si_graph_world_topology_traces.json",
    "output/data/uncertainty_summary.json",
    "output/data/toy_benchmark_matrix.json",
    "output/data/interop_roundtrip_report.json",
    "output/reports/model_checking_witnesses.json",
    "output/reports/adversarial_audit.json",
    "output/reports/replay_matrix.json",
    "output/data/track_lane_matrix.json",
    "output/data/artifact_contract_index.json",
    "output/data/track_improvement_scope.json",
    "output/reports/blocked_scope_manifest.json",
    "output/data/evidence_field_index.json",
    "output/reports/release_bundle_manifest.json",
    "output/data/theorem_traceability_matrix.json",
    "output/reports/artifact_diffoscope.json",
    "output/data/proof_extraction_index.json",
    "output/data/state_space_catalog.json",
    "output/data/causal_ablation_matrix.json",
    "output/reports/artifact_license_audit.json",
    "output/reports/release_notes_evidence.json",
    "output/reports/security_posture_audit.json",
    "output/data/proof_dependency_graph.json",
    "output/data/state_transition_table.json",
    "output/reports/ablation_sensitivity_report.json",
    "output/reports/release_attestation.json",
    "output/data/validation_gate_index.json",
    "output/data/validation_dependency_graph.json",
    "output/data/sheaf_section_status_matrix.json",
    "output/reports/sheaf_render_log.json",
    "output/reports/visualization_quality_audit.json",
    "output/data/statistical_visualization_bridge.json",
    "output/figures/semantic_gluing_graph.png",
    "output/figures/track_lane_promotion_map.png",
    "output/figures/artifact_contract_map.png",
    "output/figures/si_belief_trajectory.gif",
    "output/data/animation_frame_deltas.json",
    "output/reports/manuscript_staleness_report.json",
    "output/reports/reproducibility_replay.json",
    "output/reports/counterexample_matrix.json",
    "output/figures/theorem_traceability_graph.png",
    "output/figures/causal_ablation_heatmap.png",
    "output/figures/security_posture_map.png",
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextmanager
def temporary_json_mutation(path: Path, mutate: Callable[[dict], None]) -> Iterator[dict]:
    """Temporarily mutate a JSON artifact and restore it byte-for-byte."""
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    mutate(payload)
    _write_json(path, payload)
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


def _settle_generated_contracts(project_root: Path, out: Path, *, passes: int = 1) -> None:
    """Converge visual, integration, sheaf, and hydrated-manuscript artifacts."""
    from roadmap_tracks.fixed_point import run_semantic_fixed_point

    for _ in range(passes):
        generate_all_figures(project_root)
        write_belief_trajectory_gif(project_root)
        write_animation_frame_deltas(project_root)
        compose_all_sections(project_root)
        _hydrate_fixed_point(project_root, out)
        write_integration_audit_artifacts(project_root)
        write_sheaf_track_artifacts(project_root, finalize=False)
        run_semantic_fixed_point(project_root, require_analysis_outputs=False)


def refresh_generated_gate_artifacts(project_root: Path, *, force: bool = True) -> None:
    """Refresh generated manuscript/semantic artifacts after mutation tests.

    Post-mutation cleanup forces regeneration by default because source and
    generated-output negative controls can leave derived artifacts stale even
    after the edited file is restored byte-for-byte. Callers that know no source
    or generated artifact changed may pass ``force=False`` to reuse the cache.
    """
    root = project_root.resolve()
    if not force and root in _BOOTSTRAPPED_ROOTS and _required_gate_artifacts_exist(root):
        return
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _settle_generated_contracts(root, out)
    _BOOTSTRAPPED_ROOTS.add(root)


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
    if not _required_gate_artifacts_exist(project_root):
        return False
    try:
        from manuscript.sheaf.semantic import validate_semantic_gluing
        from roadmap_tracks import validate_integration_audit_artifacts, validate_sheaf_track_artifacts

        return (
            not validate_semantic_gluing(project_root)
            and not validate_integration_audit_artifacts(project_root)
            and not validate_sheaf_track_artifacts(project_root)
        )
    except Exception:
        return False


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
    if _gate_artifacts_present(root):
        _BOOTSTRAPPED_ROOTS.add(root)
        return
    if root in _BOOTSTRAPPED_ROOTS and _gate_artifacts_present(root):
        return
    if root in _BOOTSTRAPPED_ROOTS and _required_gate_artifacts_exist(root):
        refresh_generated_gate_artifacts(root)
        return

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
    generate_all_figures(project_root)
    write_belief_trajectory_gif(project_root)
    write_animation_frame_deltas(project_root)
    write_validation_spine_artifacts(project_root)
    write_toy_sweep_artifacts(project_root)
    write_formal_interop_artifacts(project_root)
    write_validation_spine_artifacts(project_root)
    write_sheaf_track_artifacts(project_root, finalize=False)
    out = project_root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _settle_generated_contracts(project_root, out)
    # NOTE: the final convergence pass is intentionally narrower than the full
    # bootstrap. It settles cross-artifact contract rows after figures, integration
    # reports, sheaf consolidation, and hydrated manuscript variables have all moved.
    _BOOTSTRAPPED_ROOTS.add(root)
