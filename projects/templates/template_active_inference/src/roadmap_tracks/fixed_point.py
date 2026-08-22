"""Deterministic fixed-point settlement for semantic manuscript artifacts."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path


FINGERPRINT_CACHE = "output/.fingerprint_cache.sha256"
_FINGERPRINT_INPUT_DIRS = ("data", "gnn", "lean", "manuscript", "scripts", "src", "tests")
_FINGERPRINT_INPUT_SUFFIXES = frozenset(
    {".bib", ".csv", ".json", ".lean", ".md", ".py", ".sh", ".tex", ".toml", ".txt", ".yaml", ".yml"}
)
_FINGERPRINT_INPUT_NAMES = frozenset({"lean-toolchain"})
_FINGERPRINT_IGNORED_NAMES = frozenset({"AGENTS.md", "README.md", "SKILL.md"})
_FINGERPRINT_ROOT_INPUTS = frozenset(
    {
        "domain_profile.yaml",
        "experiment_plan.yaml",
        "figures.yaml",
        "pymdp.yaml",
        "pyproject.toml",
        "tracks.yaml",
        "uv.lock",
    }
)
_DOWNSTREAM_STATE_ONLY_OUTPUTS = frozenset(
    {"output/pdf/template_active_inference_combined.pdf", "output/web/index.html"}
)


def _fingerprint_cache_path(root: Path) -> Path:
    """Return the confined cache path, rejecting symlinked path components."""
    project_root = root.resolve()
    cache_path = project_root / FINGERPRINT_CACHE
    cursor = project_root
    parts = Path(FINGERPRINT_CACHE).parts
    for index, part in enumerate(parts):
        cursor /= part
        if cursor.is_symlink():
            raise RuntimeError(f"semantic fixed-point cache path must not contain symlinks: {cursor}")
        if index < len(parts) - 1 and cursor.exists() and not cursor.is_dir():
            raise RuntimeError(f"semantic fixed-point cache parent is not a directory: {cursor}")
    return cache_path


def _write_fingerprint_cache(root: Path, fingerprint: str) -> None:
    """Atomically write the confined cache without following a cache symlink."""
    cache_path = _fingerprint_cache_path(root)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=cache_path.parent,
            prefix=f".{cache_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(fingerprint)
            stream.flush()
            os.fsync(stream.fileno())
        temp_path.replace(cache_path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _normalized_rel(rel: str) -> Path:
    relative = Path(rel)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"semantic fixed-point path must be a normalized project-relative path: {rel}")
    return relative


def _confined_path_state(
    root: Path,
    rel: str,
    *,
    allow_directory: bool = False,
    content_sensitive: bool = True,
) -> str:
    """Return a race-checked state token without following any symlink."""
    relative = _normalized_rel(rel)
    cursor = root.resolve()
    leaf_stat: os.stat_result | None = None
    for index, part in enumerate(relative.parts):
        cursor /= part
        try:
            current_stat = cursor.lstat()
        except FileNotFoundError:
            return "missing"
        if stat.S_ISLNK(current_stat.st_mode):
            raise RuntimeError(f"semantic fixed-point observed path must not contain symlinks: {cursor}")
        if index < len(relative.parts) - 1:
            if not stat.S_ISDIR(current_stat.st_mode):
                raise RuntimeError(f"semantic fixed-point observed parent is not a directory: {cursor}")
            continue
        leaf_stat = current_stat

    if leaf_stat is None:
        raise RuntimeError(f"semantic fixed-point observed path has no leaf: {rel}")
    if stat.S_ISDIR(leaf_stat.st_mode):
        if allow_directory:
            return "directory"
        raise RuntimeError(f"semantic fixed-point observed file is a directory: {cursor}")
    if not stat.S_ISREG(leaf_stat.st_mode):
        raise RuntimeError(f"semantic fixed-point observed path is not a regular file: {cursor}")
    if not content_sensitive:
        return "file"

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(cursor, flags)
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode) or (
            opened_stat.st_dev,
            opened_stat.st_ino,
        ) != (leaf_stat.st_dev, leaf_stat.st_ino):
            raise RuntimeError(f"semantic fixed-point observed file changed during read: {cursor}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return f"file:{digest.hexdigest()}"


def _walk_generation_inputs(root: Path, dirname: str) -> set[str]:
    """Walk one declared input tree without following directory symlinks."""
    rels: set[str] = {dirname}
    base = root / dirname
    state = _confined_path_state(root, dirname, allow_directory=True)
    if state == "missing":
        return rels
    if state != "directory":
        raise RuntimeError(f"semantic fixed-point input root is not a directory: {base}")
    pending = [base]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                rel = path.relative_to(root).as_posix()
                if entry.is_symlink():
                    raise RuntimeError(f"semantic fixed-point input tree must not contain symlinks: {path}")
                if entry.is_dir(follow_symlinks=False):
                    rels.add(rel)
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    if entry.name in _FINGERPRINT_IGNORED_NAMES:
                        continue
                    if path.suffix.lower() in _FINGERPRINT_INPUT_SUFFIXES or entry.name in _FINGERPRINT_INPUT_NAMES:
                        rels.add(rel)
                else:
                    raise RuntimeError(f"semantic fixed-point input tree contains a special file: {path}")
    return rels


def _generation_input_rels(root: Path) -> list[str]:
    """Return deterministic source/config inputs that can change generated evidence."""
    rels = set(_FINGERPRINT_ROOT_INPUTS)
    for dirname in _FINGERPRINT_INPUT_DIRS:
        rels.update(_walk_generation_inputs(root, dirname))
    return sorted(rels)


def _observed_output_rels(root: Path) -> list[str]:
    """Derive the complete positive, negative, and hydrated output inventory from SSOTs."""
    from contracts.artifact_contract import VARIABLE_ARTIFACTS
    from gates.artifact_manifest import REQUIRED_OUTPUTS
    from manuscript.sheaf.semantic_maps import ARTIFACT_PRODUCERS
    from roadmap_tracks.sheaf_tracks_builders_formal import BLOCKED_SCOPE_SENTINELS
    from roadmap_tracks.sheaf_tracks_builders_release import RELEASE_BUNDLE_REQUIRED_ARTIFACTS
    from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, LEGACY_ARTIFACTS

    rels = set(REQUIRED_OUTPUTS)
    rels.update(ARTIFACT_PRODUCERS)
    rels.update(VARIABLE_ARTIFACTS.values())
    rels.update(CANONICAL_ARTIFACTS.values())
    rels.update(LEGACY_ARTIFACTS)
    rels.update(BLOCKED_SCOPE_SENTINELS)
    rels.update(RELEASE_BUNDLE_REQUIRED_ARTIFACTS)

    manuscript_dir = root / "output" / "manuscript"
    state = _confined_path_state(root, "output/manuscript", allow_directory=True)
    if state == "directory":
        with os.scandir(manuscript_dir) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink():
                    raise RuntimeError(f"hydrated manuscript must not contain symlinks: {path}")
                if entry.is_dir(follow_symlinks=False):
                    raise RuntimeError(f"hydrated manuscript contains an unexpected directory: {path}")
                if not entry.is_file(follow_symlinks=False):
                    raise RuntimeError(f"hydrated manuscript contains a special file: {path}")
                if path.suffix.lower() in {".bib", ".md"} or path.name == "config.yaml":
                    rels.add(path.relative_to(root).as_posix())
    figures_dir = root / "output" / "figures"
    figures_state = _confined_path_state(root, "output/figures", allow_directory=True)
    if figures_state == "directory":
        with os.scandir(figures_dir) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink():
                    raise RuntimeError(f"rendered figure inventory must not contain symlinks: {path}")
                if entry.is_file(follow_symlinks=False) and path.suffix.lower() in {".gif", ".png"}:
                    rels.add(path.relative_to(root).as_posix())
    return sorted(rels)


def _cached_fingerprint_matches(root: Path, current: str) -> bool:
    """Return whether the disposable cache exactly binds the current state."""
    cache_path = _fingerprint_cache_path(root)
    try:
        return cache_path.is_file() and cache_path.read_text(encoding="utf-8").strip() == current
    except (OSError, UnicodeError):
        return False


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
    # Formal artifacts are written immediately before the canonical sheaf
    # writer in each fixed-point pass.  Re-running the base formal writer here
    # would overwrite the enriched 12-row model-checking artifact emitted by
    # ``write_sheaf_track_artifacts(finalize=False)`` and leave its saved hash
    # stale.  Keep this helper limited to the integration/supplemental writers
    # that do not compete for the formal artifact paths.
    result: dict[str, Path] = {}
    from roadmap_tracks.integration_audit import write_integration_audit_artifacts

    result.update(write_integration_audit_artifacts(root))
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    result.update(write_supplemental_artifacts(root))
    return result


def _fingerprint(root: Path) -> str:
    from roadmap_tracks.sheaf_tracks_io import _source_commit

    digest = hashlib.sha256()
    for rel in _generation_input_rels(root):
        state = _confined_path_state(root, rel, allow_directory=True)
        digest.update(b"input\0")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(state.encode("ascii"))
        digest.update(b"\0")
    for rel in _observed_output_rels(root):
        state = _confined_path_state(
            root,
            rel,
            content_sensitive=rel not in _DOWNSTREAM_STATE_ONLY_OUTPUTS,
        )
        digest.update(b"output\0")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(state.encode("ascii"))
        digest.update(b"\0")
    digest.update(b"source-commit\0")
    digest.update(_source_commit(root).encode("utf-8"))
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
    variables_path = root / "output" / "data" / "manuscript_variables.json"
    try:
        from json_io import load_json_strict

        variables = load_json_strict(variables_path)
    except ValueError as exc:
        issues.append(str(exc))
    else:
        if not variables:
            issues.append("missing canonical manuscript variables for figure registry hydration")
        else:
            from visualizations.figure_registry import validate_figure_registry_json

            issues.extend(validate_figure_registry_json(root, variables))
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
        "figure_registry": "output/figures/figure_registry.json",
        "staleness": "output/reports/manuscript_staleness_report.json",
        "crosswalk": "output/data/sheaf_evidence_crosswalk.json",
        "certificate": "output/data/sheaf_gluing_certificate.json",
    }
    paths: dict[str, Path] = {}
    for key, rel in rels.items():
        state = _confined_path_state(root, rel, allow_directory=rel == "output/manuscript")
        if state != "missing":
            paths[key] = root / rel
    return paths


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
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    paths: dict[str, Path] = {}
    paths.update(_write_sheaf_owned_artifacts(root))
    paths.update(_refresh_animation_outputs(root))
    paths.update(_refresh_hydrated_manuscript(root, require_analysis_outputs=require_analysis_outputs))
    # Hydration rewrites figure_registry.json (and variables), so the canonical
    # sheaf-track writers must run after them: they alone own artifact_provenance,
    # replay_matrix, release_bundle, and contract-index records bound to those
    # final bytes.
    from roadmap_tracks.sheaf_tracks import write_sheaf_track_artifacts

    paths.update(write_sheaf_track_artifacts(root, finalize=False))
    paths.update(_write_contract_artifacts(root))
    paths.update(_write_semantic_core(root))
    paths.update(write_supplemental_artifacts(root))
    # Terminal order matters: the certificate embeds live release predicates and
    # the provenance/contract artifacts hash the certificate bytes. Ending on a
    # contract refresh (then one final certificate rewrite, which only changes
    # hash-cycle-excluded surfaces) leaves every saved-vs-live comparison green
    # instead of oscillating between passes.
    paths.update(_write_contract_artifacts(root))
    paths.update(_write_semantic_core(root))
    paths.update(_write_contract_artifacts(root))
    return paths


def run_semantic_fixed_point(
    project_root: Path,
    *,
    require_analysis_outputs: bool = True,
    max_passes: int = 4,
) -> dict[str, Path]:
    """Settle manuscript, semantic, and contract artifacts to a validated fixed point.

    When the fingerprint cache exactly matches the current generation inputs and
    artifact hashes, the expensive multi-pass rebuild is skipped entirely. The
    disposable cache is never evidence authority: a missing or stale cache forces
    regeneration instead of blessing outputs produced by unknown source bytes.
    """
    if max_passes < 2:
        raise ValueError("semantic fixed-point max_passes must be at least 2")
    root = project_root.resolve()
    current = _fingerprint(root)
    source_issues = _source_contract_issues(root)
    if source_issues:
        joined = "; ".join(dict.fromkeys(source_issues))
        raise RuntimeError(f"semantic fixed point cannot repair source contract defects: {joined}")

    # A cache match is only a performance hint. Re-run the live validators so a
    # forged/disposable cache file can never bless an invalid artifact set.
    if _cached_fingerprint_matches(root, current) and not _validate_fixed_point(root):
        return _existing_fixed_point_paths(root)

    paths: dict[str, Path] = {}
    previous: str | None = None
    final_issues: list[str] = []
    for _ in range(max_passes):
        paths.update(_write_fixed_point_pass(root, require_analysis_outputs=require_analysis_outputs))
        paths.update(_write_final_validation_pass(root, require_analysis_outputs=require_analysis_outputs))
        current = _fingerprint(root)
        final_issues = _validate_fixed_point(root)
        if not final_issues and previous == current:
            _write_fingerprint_cache(root, current)
            return _existing_fixed_point_paths(root)
        if final_issues and previous == current:
            break
        previous = current
    if final_issues:
        joined = "; ".join(dict.fromkeys(final_issues))
        raise RuntimeError(f"semantic fixed point did not validate: {joined}")
    raise RuntimeError("semantic fixed point did not converge")
