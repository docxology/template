"""Admitted manuscript projection and complete Pitch source companions.

These adapters conjoin existing genuine producers. They do not admit a full
native release, replace the selected projection oracle, or erase controls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_pitch_source_admission import (
    SourceCorrespondence,
    compile_admitted_pitch_projection,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def selected_source_projection(artifact: NativeArtifact) -> bool:
    """Select only exact source-owned native manuscript and Pitch projections."""
    return (artifact.format == "pdf" and artifact.id.endswith(":slides")) or (
        artifact.format in {"pdf", "pptx"} and artifact.id.startswith("pitch:")
    )


def projection_control_formats(contract: tuple[NativeArtifact, ...], formats: tuple[str, ...]) -> tuple[str, ...]:
    """Configured native PPTX obligations select their existing genuine controls.

    Pitch deck formats are declared in project_config.deck separately from the
    manuscript render selection, so slides=false cannot hide those controls.
    """
    return (*formats, "pptx") if "pptx" not in formats and any(item.format == "pptx" for item in contract) else formats


def _admit(
    root: Path,
    reader: SnapshotReader,
    reference: PublicReference | None,
    correspondence: SourceCorrespondence | None,
    deadline: float,
) -> tuple[str, ...]:
    if reference is None or correspondence is None:
        raise ProjectionSourceUnsupported(
            "projection requires independent immutable source and current-mirror admission"
        )
    if reader.root != root.resolve():
        raise ValueError("projection reader differs from its admitted current mirror")
    reference.verify_unchanged(deadline=deadline)
    correspondence(reference, root, reader, deadline)
    return tuple(sorted(row.path for row in (*reference.git.files, *reference.git.gitlinks)))


def _close(
    root: Path,
    reader: SnapshotReader,
    reference: PublicReference | None,
    correspondence: SourceCorrespondence | None,
    deadline: float,
) -> None:
    if reference is None or correspondence is None:
        raise ValueError("projection lost its original source admission")
    correspondence(reference, root, reader, deadline)
    reference.verify_unchanged(deadline=deadline)
    if not reader.unchanged():
        raise ValueError("projection current DATA changed during native observation")


def observe_admitted_manuscript_projection(
    root: Path,
    leaf: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    """Reach the all-page source/marked Beamer adapter under current custody.

    Foreign whole-manuscript references have no supplied number authority here;
    the existing producer must continue to diagnose those unresolved inputs.
    Reveal HTML retains its separate browser path and unsupported obligations.
    """
    from infrastructure.reporting.native_slide_observer import observe_manuscript_projection

    if artifact.format != "pdf" or not artifact.id.endswith(":slides"):
        raise ValueError("source-aware manuscript adapter requires its exact native PDF identity")
    _admit(root, reader, source_reference, verify_source_correspondence, deadline)
    result = observe_manuscript_projection(
        root, leaf, scope, artifact, snapshot, reader, env=env, deadline=deadline, run_id=run_id
    )
    _close(root, reader, source_reference, verify_source_correspondence, deadline)
    return result


def observe_admitted_pitch_companion(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    candidate_rasters: tuple[bytes, ...],
    reader: SnapshotReader,
    *,
    projection_contract: dict[str, Any],
    env: dict[str, str],
    deadline: float,
    run_id: str,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    """Bind native PDF theme/layout or editable package/notes/QR to current DATA."""
    tracked = _admit(root, reader, source_reference, verify_source_correspondence, deadline)
    if artifact.format == "pptx":
        from infrastructure.reporting.native_pitch_source_layout import observe_pitch_package_source

        result = observe_pitch_package_source(
            root,
            directory,
            scope,
            artifact,
            snapshot.content,
            reader,
            tracked_paths=tracked,
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
        companion_contract = result["contract"]
    elif artifact.format == "pdf":
        from infrastructure.reporting.native_pitch_source_native import observe_pitch_pdf_source_reference

        result = observe_pitch_pdf_source_reference(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            candidate_rasters,
            reader,
            tracked_paths=tracked,
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
        companion_contract = result["projection_contract"]
    else:
        raise ValueError("Pitch source companion requires its declared PDF/PPTX format")
    if companion_contract != projection_contract:
        raise ValueError("Pitch current native companion differs from immutable source page obligations")
    _close(root, reader, source_reference, verify_source_correspondence, deadline)
    return result


def inspect_admitted_pitch_pairs(
    root: Path,
    scope: str,
    contract: tuple[NativeArtifact, ...],
    artifacts: list[dict[str, Any]],
    reader: SnapshotReader,
    *,
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
    deadline: float,
) -> dict[str, Any]:
    """Reconstruct every configured pair, never receipt-provided source pages."""
    from infrastructure.reporting.native_pitch_source_parity import inspect_pitch_native_pairs

    if scope != "templates/template_pitch_deck":
        raise ValueError("complete Pitch pair adapter requires its exact public scope")
    _admit(root, reader, source_reference, verify_source_correspondence, deadline)
    obligations = [item for item in contract if item.id.startswith("pitch:")]
    rows = [item for item in artifacts if str(item.get("id", "")).startswith("pitch:")]
    if len({item.id for item in obligations}) != len(obligations) or len({item.get("id") for item in rows}) != len(
        rows
    ):
        raise ValueError("Pitch pair obligations or original artifact rows are duplicated")
    pages = {
        item.id: compile_admitted_pitch_projection(
            root,
            scope,
            item,
            reader,
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
            deadline=deadline,
        )
        for item in obligations
    }
    observations = {}
    for item in rows:
        raw = item.get("native_observer")
        if (
            not isinstance(raw, dict)
            or raw.get("id") != item["id"]
            or raw.get("input") != {"path": item.get("path"), "sha256": item.get("sha256")}
        ):
            raise ValueError("Pitch pair row differs from its original observed native artifact")
        observations[item["id"]] = raw
    result = inspect_pitch_native_pairs(observations, pages)
    _close(root, reader, source_reference, verify_source_correspondence, deadline)
    return result
