"""Deterministic fixed-point settlement for semantic manuscript artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


FINGERPRINT_CACHE = "output/.fingerprint_cache.sha256"


def _write_fingerprint_cache(cache_path: Path, fingerprint: str) -> None:
    """Write the fingerprint cache, creating parent dirs as needed."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(fingerprint, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _refresh_animation_outputs(root: Path) -> dict[str, Path]:
    from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif

    paths: dict[str, Path] = {}
    try:
        paths["animation_gif"] = write_belief_trajectory_gif(root)
        paths["animation_deltas"] = write_animation_frame_deltas(root)
    except FileNotFoundError:
        return paths
    return paths


def _refresh_hydrated_manuscript(root: Path, *, require_analysis_outputs: bool) -> dict[str, Path]:
    from manuscript.refresh import settle_manuscript_artifacts

    result: dict[str, Path] = settle_manuscript_artifacts(root, require_analysis_outputs=require_analysis_outputs)
    return result


def _write_sheaf_owned_artifacts(root: Path) -> dict[str, Path]:
    from manuscript.sheaf.coverage import emit_coverage_artifacts

    result: dict[str, Path] = {"coverage_matrix": emit_coverage_artifacts(root)}
    return result


def _write_semantic_core(root: Path) -> dict[str, Path]:
    from manuscript.sheaf.semantic import write_semantic_gluing_outputs

    result: dict[str, Path] = write_semantic_gluing_outputs(root, settle=False)
    return result


def _write_contract_artifacts(root: Path) -> dict[str, Path]:
    from roadmap_tracks.formal_interop import write_formal_interop_artifacts

    result: dict[str, Path] = write_formal_interop_artifacts(root)
    from roadmap_tracks.integration_audit import write_integration_audit_artifacts

    result.update(write_integration_audit_artifacts(root))
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    result.update(write_supplemental_artifacts(root))
    return result


def _fingerprint(root: Path) -> str:
    from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS

    rels = [
        "output/data/manuscript_variables.json",
        "output/reports/manuscript_staleness_report.json",
        "output/data/sheaf_evidence_crosswalk.json",
        "output/data/sheaf_gluing_certificate.json",
        "output/data/validation_dependency_graph.json",
        "output/data/interop_roundtrip_report.json",
        "output/data/artifact_contract_index.json",
        "output/reports/replay_matrix.json",
        "output/reports/release_bundle_manifest.json",
        "output/data/sheaf_section_status_matrix.json",
        "output/reports/sheaf_render_log.json",
        "output/figures/si_belief_trajectory.gif",
        "output/data/animation_frame_deltas.json",
        *CANONICAL_ARTIFACTS.values(),
    ]
    hydrated = sorted(path.relative_to(root).as_posix() for path in (root / "output" / "manuscript").glob("*.md"))
    digest = hashlib.sha256()
    for rel in sorted(set([*rels, *hydrated])):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(root / rel).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_fixed_point(root: Path) -> list[str]:
    from manuscript.sheaf.semantic import validate_semantic_gluing
    from roadmap_tracks.formal_interop import validate_formal_interop_artifacts
    from roadmap_tracks.integration_audit import validate_integration_audit_artifacts
    from roadmap_tracks.sheaf_track_validation import validate_sheaf_track_artifacts

    issues: list[str] = []
    issues.extend(validate_formal_interop_artifacts(root))
    issues.extend(validate_integration_audit_artifacts(root))
    issues.extend(validate_semantic_gluing(root))
    issues.extend(validate_sheaf_track_artifacts(root))
    return issues


def _source_contract_issues(root: Path) -> list[str]:
    """Return source defects that generated-artifact settlement cannot repair.

    Fixed-point writers are deliberately allowed to replace generated outputs,
    but they must never launder an invalid authored model into a green artifact
    set.  The GNN lint builder is a pure parse of the live source files, so its
    findings are stable across settlement passes and can fail before any of the
    expensive writers run.
    """
    from roadmap_tracks.formal_interop import build_gnn_lint_report

    report = build_gnn_lint_report(root)
    return [str(issue) for issue in report.get("issues") or []]


def _existing_fixed_point_paths(root: Path) -> dict[str, Path]:
    from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS

    rels = {
        **CANONICAL_ARTIFACTS,
        "animation_gif": "output/figures/si_belief_trajectory.gif",
        "animation_deltas": "output/data/animation_frame_deltas.json",
        "variables": "output/data/manuscript_variables.json",
        "resolved_manuscript": "output/manuscript",
        "staleness": "output/reports/manuscript_staleness_report.json",
        "crosswalk": "output/data/sheaf_evidence_crosswalk.json",
        "certificate": "output/data/sheaf_gluing_certificate.json",
    }
    return {key: root / rel for key, rel in rels.items() if (root / rel).exists()}


def _write_fixed_point_pass(root: Path, *, require_analysis_outputs: bool) -> dict[str, Path]:
    from roadmap_tracks.formal_interop import write_formal_interop_artifacts
    from roadmap_tracks.sheaf_tracks import write_sheaf_track_artifacts
    from roadmap_tracks.toy_sweep import write_toy_sweep_artifacts

    paths: dict[str, Path] = {}
    paths.update(_refresh_animation_outputs(root))
    paths.update(write_toy_sweep_artifacts(root))
    paths.update(write_formal_interop_artifacts(root))
    paths.update(write_sheaf_track_artifacts(root, finalize=False))
    paths.update(_write_sheaf_owned_artifacts(root))
    paths.update(_refresh_hydrated_manuscript(root, require_analysis_outputs=require_analysis_outputs))
    paths.update(_write_semantic_core(root))
    paths.update(_write_contract_artifacts(root))
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    paths.update(write_supplemental_artifacts(root))
    return paths


def _write_final_validation_pass(root: Path, *, require_analysis_outputs: bool) -> dict[str, Path]:
    """Refresh self-referential reports and write the certificate from the final live state."""
    from roadmap_tracks.formal_interop import write_formal_interop_artifacts
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    paths: dict[str, Path] = {}
    paths.update(write_formal_interop_artifacts(root))
    paths.update(_write_sheaf_owned_artifacts(root))
    paths.update(_refresh_animation_outputs(root))
    paths.update(_refresh_hydrated_manuscript(root, require_analysis_outputs=require_analysis_outputs))
    paths.update(_write_contract_artifacts(root))
    paths.update(_write_semantic_core(root))
    paths.update(write_supplemental_artifacts(root))
    paths.update(_write_contract_artifacts(root))
    paths.update(_write_semantic_core(root))
    return paths


def run_semantic_fixed_point(
    project_root: Path,
    *,
    require_analysis_outputs: bool = True,
    max_passes: int = 4,
) -> dict[str, Path]:
    """Settle manuscript, semantic, and contract artifacts to a validated fixed point.

    When the fingerprint cache matches the current artifact hashes, the expensive
    multi-pass rebuild is skipped entirely — returning in < 0.1 s instead of 600+ s.
    """
    root = project_root.resolve()
    source_issues = _source_contract_issues(root)
    if source_issues:
        joined = "; ".join(dict.fromkeys(source_issues))
        raise RuntimeError(f"semantic fixed point cannot repair source contract defects: {joined}")

    # Fast path: if cached fingerprint matches, skip the expensive rebuild entirely.
    cache_path = root / FINGERPRINT_CACHE
    current = _fingerprint(root)
    if cache_path.is_file():
        cached = cache_path.read_text(encoding="utf-8").strip()
        if cached == current:
            return _existing_fixed_point_paths(root)
        # Fingerprint changed — fall through to rebuild.

    initial_issues = _validate_fixed_point(root)
    if not initial_issues:
        _write_fingerprint_cache(cache_path, current)
        return _existing_fixed_point_paths(root)

    paths: dict[str, Path] = {}
    from roadmap_tracks.formal_interop import write_formal_interop_artifacts

    paths.update(write_formal_interop_artifacts(root, missing_only=True))
    if paths:
        final_issues = _validate_fixed_point(root)
        if not final_issues:
            _write_fingerprint_cache(cache_path, _fingerprint(root))
            return _existing_fixed_point_paths(root)

    previous = ""
    for _ in range(max_passes):
        paths.update(_write_fixed_point_pass(root, require_analysis_outputs=require_analysis_outputs))
        paths.update(_write_final_validation_pass(root, require_analysis_outputs=require_analysis_outputs))
        current = _fingerprint(root)
        final_issues = _validate_fixed_point(root)
        if not final_issues:
            _write_fingerprint_cache(cache_path, current)
            return paths
        if current == previous:
            break
        previous = current
    if final_issues:
        joined = "; ".join(dict.fromkeys(final_issues))
        raise RuntimeError(f"semantic fixed point did not validate: {joined}")
    raise RuntimeError("semantic fixed point did not converge")
