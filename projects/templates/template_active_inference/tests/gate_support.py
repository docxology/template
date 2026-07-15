"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
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


def _validate_semantic_gluing(project_root: Path) -> list[str]:
    from manuscript.sheaf.semantic import validate_semantic_gluing

    return validate_semantic_gluing(project_root)


def _validate_claim_ledger(project_root: Path) -> bool:
    from gates.claim_ledger import validate_claim_ledger

    return validate_claim_ledger(project_root)


@dataclass
class GateArtifactRuntime:
    """Explicit cache, validators, and writers used by gate orchestration."""

    required_artifacts: tuple[str, ...] = _REQUIRED_GATE_ARTIFACTS
    bootstrapped_roots: set[Path] = field(default_factory=lambda: _BOOTSTRAPPED_ROOTS)
    bootstrapped_signatures: dict[Path, str] = field(default_factory=lambda: _BOOTSTRAPPED_SIGNATURES)
    signature_override: Callable[[Path], str | None] | None = None
    readiness_override: Callable[[Path], tuple[str, ...]] | None = None
    artifacts_present_override: Callable[[Path], bool] | None = None
    required_exist_override: Callable[[Path], bool] | None = None
    settle_override: Callable[..., None] | None = None
    semantic_fixed_point_runner: Callable[..., dict] | None = None
    validate_semantic: Callable[[Path], list[str]] = _validate_semantic_gluing
    validate_animation: Callable[[Path], list[str]] = validate_animation_frame_deltas
    validate_integration: Callable[[Path], list[str]] = validate_integration_audit_artifacts
    validate_sheaf: Callable[[Path], list[str]] = validate_sheaf_track_artifacts
    validate_claims: Callable[[Path], bool] = _validate_claim_ledger
    analysis_runner: Callable[[Path], object] = run_analysis
    pymdp_probe: Callable[[], bool] = pymdp_available
    simulation_runner: Callable[[Path], object] = run_and_persist
    policy_comparison_writer: Callable[[Path], object] = write_policy_comparison
    policy_grid_writer: Callable[[Path], object] = write_policy_posterior_grid
    graph_writer: Callable[[Path], object] = write_graph_world_artifacts
    statistics_writer: Callable[[Path], object] = write_analysis_statistics
    section_composer: Callable[[Path], object] = compose_all_sections
    coverage_writer: Callable[..., object] = ensure_coverage_artifacts
    validation_spine_writer: Callable[[Path], object] = write_validation_spine_artifacts
    toy_sweep_writer: Callable[[Path], object] = write_toy_sweep_artifacts
    formal_interop_writer: Callable[[Path], object] = write_formal_interop_artifacts
    sheaf_writer: Callable[..., object] = write_sheaf_track_artifacts
    figure_writer: Callable[[Path], object] = generate_all_figures
    gif_writer: Callable[[Path], object] = write_belief_trajectory_gif
    animation_writer: Callable[[Path], object] = write_animation_frame_deltas
    integration_writer: Callable[[Path], object] = write_integration_audit_artifacts


_DEFAULT_RUNTIME = GateArtifactRuntime()


def _runtime(runtime: GateArtifactRuntime | None) -> GateArtifactRuntime:
    return runtime or _DEFAULT_RUNTIME


def _required_gate_artifacts_signature(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> str | None:
    active = _runtime(runtime)
    if active.signature_override is not None:
        return active.signature_override(project_root)
    if not active.required_artifacts:
        return None
    digest = hashlib.sha256()
    for rel in active.required_artifacts:
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


def gate_artifact_readiness_issues(
    project_root: Path, *, runtime: GateArtifactRuntime | None = None
) -> tuple[str, ...]:
    active = _runtime(runtime)
    if active.readiness_override is not None:
        return active.readiness_override(project_root)
    issues: list[str] = []
    missing = [rel for rel in active.required_artifacts if not (project_root / rel).is_file()]
    if missing:
        shown = ", ".join(missing[:10])
        suffix = "" if len(missing) <= 10 else f", ... ({len(missing)} total)"
        issues.append(f"missing required gate artifacts: {shown}{suffix}")
        return tuple(issues)
    try:
        semantic_issues = active.validate_semantic(project_root)
        animation_issues = active.validate_animation(project_root)
        integration_issues = active.validate_integration(project_root)
        sheaf_issues = active.validate_sheaf(project_root)
        if semantic_issues:
            issues.append(f"semantic gluing issues: {len(semantic_issues)}")
        if animation_issues:
            issues.append(f"animation frame-delta issues: {len(animation_issues)}")
        if integration_issues:
            issues.append(f"integration audit issues: {len(integration_issues)}")
        if sheaf_issues:
            issues.append(f"sheaf track issues: {len(sheaf_issues)}")
        if not active.validate_claims(project_root):
            issues.append("claim ledger validation failed")
    except Exception as exc:
        issues.append(f"readiness check raised {type(exc).__name__}: {exc}")
    return tuple(issues)


def _stale_gate_artifact_message(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> str:
    issues = gate_artifact_readiness_issues(project_root, runtime=runtime)
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


def _settle_generated_contracts(
    project_root: Path,
    out: Path,
    *,
    passes: int | None = None,
    runtime: GateArtifactRuntime | None = None,
) -> None:
    """Converge visual, integration, sheaf, and hydrated-manuscript artifacts."""
    active = _runtime(runtime)
    if active.semantic_fixed_point_runner is None:
        from roadmap_tracks.fixed_point import run_semantic_fixed_point
    else:
        run_semantic_fixed_point = active.semantic_fixed_point_runner

    requested_passes = _fixed_point_passes() if passes is None else passes
    semantic_max_passes = max(4, requested_passes * 4)
    for _ in range(max(1, requested_passes)):
        active.sheaf_writer(project_root, finalize=False)
        active.figure_writer(project_root)
        active.gif_writer(project_root)
        active.animation_writer(project_root)
        run_semantic_fixed_point(
            project_root,
            require_analysis_outputs=False,
            max_passes=semantic_max_passes,
        )
    if not out.is_file():
        _hydrate_fixed_point(project_root, out)


def refresh_generated_gate_artifacts(
    project_root: Path,
    *,
    force: bool = True,
    runtime: GateArtifactRuntime | None = None,
) -> None:
    """Refresh generated manuscript/semantic artifacts after mutation tests.

    Post-mutation cleanup forces regeneration by default because source and
    generated-output negative controls can leave derived artifacts stale even
    after the edited file is restored byte-for-byte. Callers that know no source
    or generated artifact changed may pass ``force=False`` to reuse the cache.
    """
    active = _runtime(runtime)
    root = project_root.resolve()
    existing_signature = _required_gate_artifacts_signature(root, runtime=active)
    if not force and existing_signature and active.bootstrapped_signatures.get(root) == existing_signature:
        return
    if not force and existing_signature and _gate_artifacts_present(root, runtime=active):
        active.bootstrapped_signatures[root] = existing_signature
        active.bootstrapped_roots.add(root)
        return
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if active.settle_override is not None:
        active.settle_override(root, out)
    else:
        _settle_generated_contracts(root, out, runtime=active)
    refresh_gate_artifact_session_signature(root, runtime=active)


def refresh_gate_artifact_session_signature(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> None:
    active = _runtime(runtime)
    root = project_root.resolve()
    signature = _required_gate_artifacts_signature(root, runtime=active)
    if not signature:
        raise AssertionError("required gate artifacts are incomplete; cannot refresh session signature")
    if not _gate_artifacts_present(root, runtime=active):
        raise AssertionError("gate artifacts are invalid; cannot refresh session signature")
    active.bootstrapped_signatures[root] = signature
    active.bootstrapped_roots.add(root)


def refresh_output_gate_contracts(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> None:
    active = _runtime(runtime)
    root = project_root.resolve()
    animation_issues = active.validate_animation(root)
    integration_issues = active.validate_integration(root)
    sheaf_issues = active.validate_sheaf(root)
    if not animation_issues and not integration_issues and not sheaf_issues:
        refresh_gate_artifact_session_signature(root, runtime=active)
        return
    if animation_issues:
        active.animation_writer(root)
    if integration_issues or sheaf_issues:
        active.integration_writer(root)
        active.sheaf_writer(root)
    animation_issues = active.validate_animation(root)
    if animation_issues:
        active.animation_writer(root)
        animation_issues = active.validate_animation(root)
    integration_issues = active.validate_integration(root)
    sheaf_issues = active.validate_sheaf(root)
    remaining = {
        "animation": animation_issues,
        "integration": integration_issues,
        "sheaf": sheaf_issues,
    }
    remaining = {name: issues for name, issues in remaining.items() if issues}
    if remaining:
        raise AssertionError(f"output gate contracts remain invalid after refresh: {remaining}")
    refresh_gate_artifact_session_signature(root, runtime=active)


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


def _gate_artifacts_present(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> bool:
    active = _runtime(runtime)
    if active.artifacts_present_override is not None:
        return active.artifacts_present_override(project_root)
    return not gate_artifact_readiness_issues(project_root, runtime=active)


def _required_gate_artifacts_exist(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> bool:
    active = _runtime(runtime)
    if active.required_exist_override is not None:
        return active.required_exist_override(project_root)
    for rel in active.required_artifacts:
        path = project_root / rel
        if not path.is_file():
            return False
        if rel.startswith("output/figures/") and path.suffix.lower() in {".png", ".gif"}:
            from visualizations.figure_io import image_render_metrics

            metrics = image_render_metrics(path)
            if not metrics["width_px"] or not metrics["height_px"] or not metrics["nonblank"]:
                return False
    return True


def ensure_gate_artifacts(project_root: Path, *, runtime: GateArtifactRuntime | None = None) -> None:
    """Rebuild analysis, simulation, sheaf, and figure outputs for gate checks."""
    active = _runtime(runtime)
    root = project_root.resolve()
    signature = _required_gate_artifacts_signature(root, runtime=active)
    if signature and active.bootstrapped_signatures.get(root) == signature:
        active.bootstrapped_roots.add(root)
        return
    if _gate_artifacts_present(root, runtime=active):
        active.bootstrapped_roots.add(root)
        if signature:
            active.bootstrapped_signatures[root] = signature
        return

    if not _gate_rebuild_allowed():
        raise AssertionError(_stale_gate_artifact_message(root, runtime=active))

    active.analysis_runner(project_root)
    if active.pymdp_probe():
        active.simulation_runner(project_root)
        active.policy_comparison_writer(project_root)
        active.policy_grid_writer(project_root)
    else:
        pytest.skip("pymdp not installed")
    active.graph_writer(project_root)
    active.statistics_writer(project_root)
    active.section_composer(project_root)
    active.coverage_writer(project_root, write_page=True, render_heatmap=True, force=True)
    active.validation_spine_writer(project_root)
    active.toy_sweep_writer(project_root)
    active.formal_interop_writer(project_root)
    active.validation_spine_writer(project_root)
    active.sheaf_writer(project_root, finalize=False)
    active.figure_writer(project_root)
    active.gif_writer(project_root)
    active.animation_writer(project_root)
    out = project_root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if active.settle_override is not None:
        active.settle_override(project_root, out)
    else:
        _settle_generated_contracts(project_root, out, runtime=active)
    # NOTE: the final convergence pass is intentionally narrower than the full
    # bootstrap. It settles cross-artifact contract rows after figures, integration
    # reports, sheaf consolidation, and hydrated manuscript variables have all moved.
    refresh_gate_artifact_session_signature(root, runtime=active)
