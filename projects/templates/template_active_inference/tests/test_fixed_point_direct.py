"""Direct tests for ``roadmap_tracks.fixed_point``.

The semantic fixed point rewrites the full generated-artifact surface, so
every writing test runs against an isolated project-tree copy (see
``direct_recompute_support``). This keeps the module's coverage independent of
whether the tracked snapshot happens to read as stale on a given CI leg.
"""

from __future__ import annotations

import io
import json
import stat
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from roadmap_tracks.fixed_point import (
    FINGERPRINT_CACHE,
    _cached_fingerprint_matches,
    _confined_path_state,
    _existing_fixed_point_paths,
    _fingerprint,
    _observed_output_rels,
    _refresh_animation_outputs,
    _validate_fixed_point,
    _write_fingerprint_cache,
    run_semantic_fixed_point,
)
from roadmap_tracks.sheaf_track_validation import validate_sheaf_track_artifacts

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("fixed_point_tree"))


def _observed_output_snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        relative: (root / relative).read_bytes() if (root / relative).is_file() else None
        for relative in _observed_output_rels(root)
    }


@pytest.fixture(scope="module")
def settled_convergence_root(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, bytes | None]]:
    """Return one forced, byte-snapshotted fixed-point tree."""
    root = copy_project_tree(tmp_path_factory.mktemp("fixed_point_convergence") / "convergence-project")
    (root / FINGERPRINT_CACHE).unlink(missing_ok=True)
    run_semantic_fixed_point(root, require_analysis_outputs=False)
    return root, _observed_output_snapshot(root)


def test_fingerprint_is_deterministic_and_content_sensitive(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    assert first == _fingerprint(copied_root)
    probe = copied_root / "output" / "data" / "manuscript_variables.json"
    original = probe.read_bytes()
    try:
        probe.write_bytes(original + b"\n")
        assert _fingerprint(copied_root) != first
    finally:
        probe.write_bytes(original)
    assert _fingerprint(copied_root) == first


def test_fingerprint_tracks_rendered_figure_paths_and_raw_bytes(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    png = copied_root / "output" / "figures" / "ising_mi_curve.png"
    original = png.read_bytes()
    added_gif = copied_root / "output" / "figures" / "fingerprint_probe.gif"
    try:
        with Image.open(io.BytesIO(original)) as image:
            image.load()
            original_mode = image.mode
            original_size = image.size
            original_pixels = image.tobytes()
            recompressed_buffer = io.BytesIO()
            image.save(recompressed_buffer, format="PNG", compress_level=1, optimize=False)
        recompressed = recompressed_buffer.getvalue()
        assert recompressed != original, "recompression fixture must change the deposited bytes"
        png.write_bytes(recompressed)
        with Image.open(png) as image:
            image.load()
            assert (image.mode, image.size, image.tobytes()) == (original_mode, original_size, original_pixels)
        assert _fingerprint(copied_root) != first

        png.write_bytes(original)
        assert _fingerprint(copied_root) == first

        with Image.open(io.BytesIO(original)) as image:
            edited = image.convert("RGBA")
        pixel = edited.getpixel((0, 0))
        edited.putpixel((0, 0), (255 - pixel[0], pixel[1], pixel[2], pixel[3]))
        pixel_buffer = io.BytesIO()
        edited.save(pixel_buffer, format="PNG")
        png.write_bytes(pixel_buffer.getvalue())
        assert _fingerprint(copied_root) != first

        png.write_bytes(original)
        png.unlink()
        assert _fingerprint(copied_root) != first
        png.write_bytes(original)
        assert _fingerprint(copied_root) == first

        Image.new("RGB", (2, 2), (10, 20, 30)).save(added_gif, format="GIF")
        with_gif = _fingerprint(copied_root)
        assert with_gif != first
        added_gif.unlink()
        assert _fingerprint(copied_root) == first
    finally:
        png.write_bytes(original)
        added_gif.unlink(missing_ok=True)
    assert _fingerprint(copied_root) == first


def test_fingerprint_tracks_generation_source_bytes(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    sources = (
        copied_root / "src" / "manuscript" / "sheaf" / "layers_report.py",
        copied_root / "tests" / "test_layers_report.py",
    )
    for source in sources:
        original = source.read_bytes()
        try:
            source.write_bytes(original + b"\n")
            assert _fingerprint(copied_root) != first, source
        finally:
            source.write_bytes(original)
    assert _fingerprint(copied_root) == first


def test_fingerprint_tracks_complete_registry_derived_output_inventory(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    state_only = {"output/pdf/template_active_inference_combined.pdf", "output/web/index.html"}
    for relative in _observed_output_rels(copied_root):
        report = copied_root / relative
        if report.is_file():
            original = report.read_bytes()
            try:
                report.unlink()
                assert _fingerprint(copied_root) != first, relative
                report.write_bytes(original + b"\n")
                if relative in state_only:
                    assert _fingerprint(copied_root) == first, relative
                else:
                    assert _fingerprint(copied_root) != first, relative
            finally:
                report.write_bytes(original)
        else:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("introduced negative-evidence sentinel\n", encoding="utf-8")
            try:
                assert _fingerprint(copied_root) != first, relative
            finally:
                report.unlink()
    assert _fingerprint(copied_root) == first


def test_fingerprint_tracks_hydrated_auxiliary_membership(copied_root: Path) -> None:
    first = _fingerprint(copied_root)
    for relative in ("output/manuscript/config.yaml", "output/manuscript/references.bib"):
        path = copied_root / relative
        original = path.read_bytes()
        try:
            path.unlink()
            assert _fingerprint(copied_root) != first
            path.write_bytes(original + b"\n")
            assert _fingerprint(copied_root) != first
        finally:
            path.write_bytes(original)
    extra = copied_root / "output" / "manuscript" / "stale-extra.bib"
    extra.write_text("@misc{stale}\n", encoding="utf-8")
    try:
        assert _fingerprint(copied_root) != first
    finally:
        extra.unlink()
    assert _fingerprint(copied_root) == first


def test_fingerprint_tracks_real_git_head_without_project_byte_change(tmp_path: Path) -> None:
    root = copy_project_tree(tmp_path / "git-project")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixed Point Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "fixed-point@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
    before = _fingerprint(root)
    subprocess.run(["git", "-C", str(root), "commit", "--allow-empty", "-qm", "identity-only"], check=True)
    assert _fingerprint(root) != before


@pytest.mark.parametrize(
    "relative",
    [
        "src/manuscript/sheaf/layers_report.py",
        "output/data/artifact_provenance.json",
        "output/manuscript/config.yaml",
        "output/manuscript/references.bib",
        "output/figures/ising_mi_curve.png",
    ],
)
def test_fingerprint_rejects_symlinked_observed_leaf(copied_root: Path, tmp_path: Path, relative: str) -> None:
    path = copied_root / relative
    original = path.read_bytes()
    outside = tmp_path / relative.replace("/", "-")
    outside.write_bytes(original)
    path.unlink()
    path.symlink_to(outside)
    try:
        with pytest.raises(RuntimeError, match="must not contain symlinks"):
            _fingerprint(copied_root)
        assert outside.read_bytes() == original
    finally:
        path.unlink()
        path.write_bytes(original)


def test_fingerprint_rejects_symlinked_parent_and_wrong_file_type(copied_root: Path, tmp_path: Path) -> None:
    parent = copied_root / "src" / "manuscript" / "sheaf"
    real_parent = copied_root / "src" / "manuscript" / "sheaf-real"
    parent.rename(real_parent)
    parent.symlink_to(real_parent, target_is_directory=True)
    try:
        with pytest.raises(RuntimeError, match="must not contain symlinks"):
            _fingerprint(copied_root)
    finally:
        parent.unlink()
        real_parent.rename(parent)

    report = copied_root / "output" / "data" / "artifact_provenance.json"
    original = report.read_bytes()
    report.unlink()
    report.mkdir()
    try:
        with pytest.raises(RuntimeError, match="observed file is a directory"):
            _fingerprint(copied_root)
    finally:
        report.rmdir()
        report.write_bytes(original)

    outside = tmp_path / "outside"
    outside.write_text("unchanged", encoding="utf-8")
    for relative in ("../outside", str(outside)):
        with pytest.raises(RuntimeError, match="normalized project-relative"):
            _confined_path_state(copied_root, relative)
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_only_exact_cache_match_allows_fast_path(copied_root: Path) -> None:
    cache_path = copied_root / FINGERPRINT_CACHE
    cache_path.unlink(missing_ok=True)
    current = _fingerprint(copied_root)
    assert not _cached_fingerprint_matches(copied_root, current)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    _write_fingerprint_cache(copied_root, "stale")
    assert not _cached_fingerprint_matches(copied_root, current)

    cache_path.write_bytes(b"\xff")
    assert not _cached_fingerprint_matches(copied_root, current)

    _write_fingerprint_cache(copied_root, current)
    assert _cached_fingerprint_matches(copied_root, current)


def test_fingerprint_cache_rejects_symlink(copied_root: Path, tmp_path: Path) -> None:
    cache_path = copied_root / FINGERPRINT_CACHE
    cache_path.unlink(missing_ok=True)
    outside = tmp_path / "outside-cache"
    outside.write_text("outside", encoding="utf-8")
    cache_path.symlink_to(outside)
    try:
        with pytest.raises(RuntimeError, match="cache path must not contain symlinks"):
            _cached_fingerprint_matches(copied_root, _fingerprint(copied_root))
        with pytest.raises(RuntimeError, match="cache path must not contain symlinks"):
            _write_fingerprint_cache(copied_root, "replacement")
        assert outside.read_text(encoding="utf-8") == "outside"
    finally:
        cache_path.unlink(missing_ok=True)


def test_refresh_animation_outputs_tolerates_missing_inputs(tmp_path: Path) -> None:
    paths = _refresh_animation_outputs(tmp_path)
    assert paths == {}


def test_fixed_point_rejects_nonpositive_pass_budget(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_passes must be at least 2"):
        run_semantic_fixed_point(tmp_path, max_passes=1)


@pytest.mark.slow
@pytest.mark.timeout(2400)
def test_forced_settlement_is_byte_idempotent(
    settled_convergence_root: tuple[Path, dict[str, bytes | None]],
    tmp_path: Path,
) -> None:
    root, first = settled_convergence_root
    (root / FINGERPRINT_CACHE).unlink(missing_ok=True)
    run_semantic_fixed_point(root, require_analysis_outputs=False)
    assert _observed_output_snapshot(root) == first
    assert _validate_fixed_point(root) == []

    def assert_forgery_rejected(relative: str, mutate, expected_issue: str) -> None:
        path = root / relative
        original = path.read_bytes()
        try:
            payload = json.loads(original)
            mutate(payload)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            assert any(expected_issue in issue for issue in _validate_fixed_point(root))
        finally:
            path.write_bytes(original)
        assert _validate_fixed_point(root) == []

    def assert_external_path_forgery_rejected(
        relative: str,
        mutate,
        expected_issue: str,
        external: Path,
    ) -> None:
        path = root / relative
        original = path.read_bytes()
        external_original = external.read_bytes()
        external_mode = stat.S_IMODE(external.stat().st_mode)
        try:
            payload = json.loads(original)
            mutate(payload)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            # A validator that follows the forged absolute/traversal/symlink path
            # raises here for an unreadable target. The safe validator rejects the
            # saved row from canonical live membership before any target access.
            external.chmod(0)
            issues = validate_sheaf_track_artifacts(root)
            assert any(expected_issue in issue for issue in issues)
        finally:
            external.chmod(external_mode)
            path.write_bytes(original)
        assert external.read_bytes() == external_original
        assert validate_sheaf_track_artifacts(root) == []

    def forge_provenance_exclusion(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["artifact"] == "output/data/parameter_sweep.csv")
        row.update(
            cycle_excluded=True,
            hash_checked=False,
            hash_authority="output/reports/artifact_manifest.json",
            sha256="",
            content_sha256="",
            size_bytes=0,
        )

    def forge_contract_exclusion(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["artifact"] == "output/data/parameter_sweep.csv")
        row.update(freshness_cycle_excluded=True, source_sha256="", copied_sha256="")

    def forge_provenance_membership(payload: dict) -> None:
        rel = "output/data/analysis_statistics.json"
        payload["rows"] = [row for row in payload["rows"] if row["artifact"] != rel]
        payload["artifacts"].pop(rel)
        payload["artifact_count"] = len(payload["rows"])

    def forge_replay_truncation(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["hash_checked_artifacts"])
        rel = row["hash_checked_artifacts"].pop()
        row["artifacts"].remove(rel)
        row["output_hashes"].pop(rel)
        row["artifact_count"] = len(row["artifacts"])

    def forge_contract_copy_binding(payload: dict) -> None:
        row = payload["rows"][0]
        row.update(copied_path="../../forged", copied_status="matched", copied_exists=True, copied_parity_ok=True)

    def forge_release_structure(payload: dict) -> None:
        payload["rows"][0]["required_deliverable"] = False
        payload["copied_output_parity"]["rows"][0]["copied_path"] = "../../forged"
        payload["bundle_hash"] = "0" * 64

    def forge_release_note(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["note_id"] == "validation_report_all_passed")
        row["claim"] = "forged"
        row["authority"] = "forged"

    def forge_semantic_json_type(payload: dict) -> None:
        assert payload["manuscript_variables"]["semantic_ok"] is True
        payload["manuscript_variables"]["semantic_ok"] = 1

    def forge_release_json_type(payload: dict) -> None:
        row = payload["rows"][0]
        assert row["required_deliverable"] is True
        row["required_deliverable"] = 1

    absolute_external = tmp_path / "absolute-validator-target.bin"
    traversal_external = tmp_path / "traversal-validator-target.bin"
    symlink_external = tmp_path / "symlink-validator-target.bin"
    absolute_external.write_bytes(b"absolute target must remain unread and unchanged\n")
    traversal_external.write_bytes(b"traversal target must remain unread and unchanged\n")
    symlink_external.write_bytes(b"symlink target must remain unread and unchanged\n")
    symlink_rel = "output/data/validator-external-link.bin"
    symlink_path = root / symlink_rel
    symlink_path.symlink_to(symlink_external)

    def forge_provenance_absolute_path(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["hash_checked"])
        row["artifact"] = absolute_external.as_posix()

    def forge_replay_traversal_path(payload: dict) -> None:
        row = next(row for row in payload["rows"] if row["hash_checked_artifacts"])
        old_rel = row["hash_checked_artifacts"][0]
        traversal_rel = "../traversal-validator-target.bin"
        artifact_index = row["artifacts"].index(old_rel)
        row["artifacts"][artifact_index] = traversal_rel
        row["hash_checked_artifacts"] = sorted(set(row["artifacts"]) - set(row["cycle_excluded_artifacts"]))
        old_hash = row["output_hashes"].pop(old_rel)
        row["output_hashes"][traversal_rel] = old_hash

    def forge_release_symlink_path(payload: dict) -> None:
        row = next(row for row in payload["rows"] if not row["hash_cycle_excluded"])
        row["artifact"] = symlink_rel

    assert_forgery_rejected(
        "output/data/artifact_provenance.json",
        forge_provenance_exclusion,
        "artifact_provenance.json has incomplete provenance rows or bundles",
    )
    assert_forgery_rejected(
        "output/data/artifact_contract_index.json",
        forge_contract_exclusion,
        "artifact_contract_index.json has incomplete or stale artifact contract rows",
    )
    assert_forgery_rejected(
        "output/data/artifact_provenance.json",
        forge_provenance_membership,
        "artifact_provenance.json has incomplete provenance rows or bundles",
    )
    assert_forgery_rejected(
        "output/reports/replay_matrix.json",
        forge_replay_truncation,
        "replay_matrix.json hash eligibility partition is stale or forged",
    )
    assert_forgery_rejected(
        "output/data/artifact_contract_index.json",
        forge_contract_copy_binding,
        "artifact_contract_index.json has incomplete or stale artifact contract rows",
    )
    assert_forgery_rejected(
        "output/reports/release_bundle_manifest.json",
        forge_release_structure,
        "release_bundle_manifest.json is missing required deliverables",
    )
    assert_forgery_rejected(
        "output/reports/release_notes_evidence.json",
        forge_release_note,
        "release_notes_evidence.json has unsupported notes",
    )
    assert_forgery_rejected(
        "output/data/sheaf_gluing_certificate.json",
        forge_semantic_json_type,
        "stale relative to live semantic fields",
    )
    assert_forgery_rejected(
        "output/reports/release_bundle_manifest.json",
        forge_release_json_type,
        "release_bundle_manifest.json is missing required deliverables",
    )
    assert_external_path_forgery_rejected(
        "output/data/artifact_provenance.json",
        forge_provenance_absolute_path,
        "artifact_provenance.json has incomplete provenance rows or bundles",
        absolute_external,
    )
    assert_external_path_forgery_rejected(
        "output/reports/replay_matrix.json",
        forge_replay_traversal_path,
        "replay_matrix.json hash eligibility partition is stale or forged",
        traversal_external,
    )
    try:
        assert_external_path_forgery_rejected(
            "output/reports/release_bundle_manifest.json",
            forge_release_symlink_path,
            "release_bundle_manifest.json is missing required deliverables",
            symlink_external,
        )
    finally:
        symlink_path.unlink(missing_ok=True)


@pytest.mark.slow
@pytest.mark.timeout(1200)
def test_fast_path_returns_existing_paths_when_valid(
    settled_convergence_root: tuple[Path, dict[str, bytes | None]],
) -> None:
    # The shared fixture is settled from this platform's live builders. This
    # call must therefore take the validated fast path without rewriting.
    root, _ = settled_convergence_root
    assert _validate_fixed_point(root) == []
    fingerprint_before = _fingerprint(root)
    paths = run_semantic_fixed_point(root, require_analysis_outputs=False)
    expected = {key: path.resolve() for key, path in _existing_fixed_point_paths(root).items()}
    assert {key: path.resolve() for key, path in paths.items()} == expected
    assert paths, "fast path must report the existing artifact paths"
    for key, path in paths.items():
        assert path.exists(), key
    assert _fingerprint(root) == fingerprint_before, "fast path must not rewrite artifacts"


@pytest.mark.slow
@pytest.mark.timeout(1200)
def test_missing_figure_registry_triggers_full_settlement(copied_root: Path) -> None:
    registry_path = copied_root / "output" / "figures" / "figure_registry.json"
    registry_path.unlink()
    assert "missing output/figures/figure_registry.json" in _validate_fixed_point(copied_root)

    paths = run_semantic_fixed_point(copied_root, require_analysis_outputs=False)

    assert paths["figure_registry"] == registry_path
    assert registry_path.is_file()
    assert "{{" not in registry_path.read_text(encoding="utf-8")
    assert _validate_fixed_point(copied_root) == []


@pytest.mark.slow
@pytest.mark.timeout(1200)
def test_stale_artifact_triggers_full_settlement(copied_root: Path) -> None:
    target = copied_root / "output" / "data" / "interop_roundtrip_report.json"
    target.unlink()
    assert _validate_fixed_point(copied_root) != []
    # Production default budget: a leg whose floats drift (py3.10) may need a
    # third settlement pass, and an exhausted budget raises instead of degrading.
    paths = run_semantic_fixed_point(copied_root, require_analysis_outputs=False, max_passes=4)
    assert paths, "settlement must report written artifact paths"
    assert target.is_file(), "the deleted artifact must be regenerated"
    assert _validate_fixed_point(copied_root) == []
    model_checking = copied_root / "output" / "reports" / "model_checking_witnesses.json"
    assert json.loads(model_checking.read_text(encoding="utf-8"))["witness_count"] == 12
    expected = {key: path.resolve() for key, path in _existing_fixed_point_paths(copied_root).items()}
    assert {key: path.resolve() for key, path in paths.items()} == expected


def test_sheaf_track_writer_writes_canonical_artifacts(copied_root: Path) -> None:
    """The non-finalize multi-phase writer must emit canonical sheaf artifacts.

    Exercises ``sheaf_tracks_write.write_sheaf_track_artifacts(finalize=False)``
    directly against an isolated copy so the tracked snapshot is never
    rewritten. This is the convergence-loop writer body; it previously ran
    only when a gate rebuilt state, which is why ``sheaf_tracks_write`` was
    nearly uncovered.
    """
    from roadmap_tracks.sheaf_tracks_write import write_sheaf_track_artifacts

    paths = write_sheaf_track_artifacts(copied_root, finalize=False)
    assert paths, "the writer must report emitted artifact paths"
    for key in ("sensitivity", "uncertainty", "counterexample", "release_bundle"):
        assert key in paths, f"expected canonical artifact '{key}' in writer output"
        assert paths[key].is_file(), f"{key} artifact must exist on disk"


def test_semantic_core_writer_returns_certificate_paths(copied_root: Path) -> None:
    """``_write_semantic_core`` must return certificate/crosswalk paths.

    Regression control for the latent ImportError: the module used to import
    a non-existent ``write_semantic_outputs`` name and could never have run.
    """
    from roadmap_tracks.fixed_point import _write_semantic_core

    paths = _write_semantic_core(copied_root)
    assert "certificate" in paths
    assert "crosswalk" in paths
    assert paths["certificate"].is_file()
    assert paths["crosswalk"].is_file()


def test_sheaf_owned_writer_returns_coverage_matrix(copied_root: Path) -> None:
    """``_write_sheaf_owned_artifacts`` must return a dict keyed by path.

    Regression control for the latent TypeError: the function used to return
    a bare ``Path`` where the caller expects ``dict[str, Path]`` (the full
    convergence loop crashed with ``'PosixPath' object is not iterable``).
    """
    from roadmap_tracks.fixed_point import _write_sheaf_owned_artifacts

    paths = _write_sheaf_owned_artifacts(copied_root)
    assert isinstance(paths, dict)
    assert "coverage_matrix" in paths
    assert paths["coverage_matrix"].is_file()


def test_unfixable_source_defect_raises_instead_of_converging(
    copied_root: Path,
) -> None:
    """Negative control: the fixed point must FAIL, not launder, an unfixable defect.

    Corrupting a SOURCE contract (an ontology annotation with no variable
    declaration in a tracked GNN model) means every settlement pass rebuilds
    artifacts that still fail validation — writers regenerate outputs from the
    corrupted source, so no number of passes can converge. A fixed point that
    returned successfully here would be green-by-construction. (First version
    of this control exposed exactly that: validation bound only to SAVED
    artifacts, so the corrupted source fast-pathed straight through — closed
    by the saved-vs-live gnn_lint staleness check in
    validate_formal_interop_artifacts.)
    """
    gnn_model = copied_root / "gnn" / "si_tmaze.gnn.md"
    original = gnn_model.read_bytes()
    try:
        gnn_model.write_bytes(original + b"\nghost_variable=FabricatedOntologyTerm\n")
        with pytest.raises(RuntimeError, match="semantic fixed point cannot repair source contract defects"):
            run_semantic_fixed_point(copied_root, require_analysis_outputs=False, max_passes=2)
    finally:
        gnn_model.write_bytes(original)
