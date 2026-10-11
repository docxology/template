"""Complete Source-selected Pitch pair/page control targets, without admission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, native_artifact_contract
from infrastructure.reporting.native_pitch_source import compile_pitch_source_model
from infrastructure.reporting.native_projection_contracts import compile_projection_contract, projection_contract_record
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCOPE = "templates/template_pitch_deck"
CONTROL_NAMES = ("baseline", "layout", "theme", "notes", "citation", "qr-link", "qr-pixels")
IDS = tuple(f"pitch:{length}:{kind}" for length in ("short", "medium", "long") for kind in ("pdf", "pptx"))


@dataclass(frozen=True)
class PitchTarget:
    """One actual configured artifact and precisely one applicable native page."""

    artifact_id: str
    name: str
    page: int | None
    intended_diagnostic: str | None
    source_target: str = ""


def compile_pitch_control_plan(
    root: Path, reader: SnapshotReader, *, formats: tuple[str, ...], deadline: float
) -> tuple[dict[str, Any], dict[str, tuple[NativeArtifact, Any, tuple[Any, ...]]]]:
    """Derive every pair and applicability from the genuine owner-held Source.

    Neither a transported plan nor a caller-selected set of pages is authority.
    Empty citation/QR selections retain the complete Source page roster proving
    their absence. Notes are editable PPTX obligations; PDFs have no notes pane.
    """
    owner = current_native_producer_operation()
    if owner is None or reader.native_producer_operation is not owner or reader.root != root:
        raise ValueError("Pitch selectors require the actual live paired Source/SDK owner")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    owner.stage_scope_directory(SCOPE)
    result = compile_pitch_source_control_plan(root, reader, source=owner.source, formats=formats, deadline=deadline)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    return result


def compile_pitch_source_control_plan(
    root: Path,
    reader: SnapshotReader,
    *,
    source: NativeSourceContext,
    formats: tuple[str, ...],
    deadline: float,
) -> tuple[dict[str, Any], dict[str, tuple[NativeArtifact, Any, tuple[Any, ...]]]]:
    """Share exact held-Source target selection without creating a native owner.

    Original and reader requirements use this same selector. Actual execution
    continues through compile_pitch_control_plan and its live producer guards.
    Source/config/model/page/notes/applicability and finite-clock predicates are
    unchanged; no transported plan can select these targets.
    """
    if not isinstance(source, NativeSourceContext) or root != reader.root or root != source.bindings.current_root:
        raise ValueError("Pitch Source target compilation requires the genuine exact held Source root")
    remaining(deadline)
    source.verify_correspondence(source.reference, root, reader, deadline)
    held = source.current_source_reader
    config = reader.read(f"projects/{SCOPE}/manuscript/config.yaml")
    if config.content != held.read(config.relative).content:
        raise ValueError("Pitch current configuration differs from exact authored Source")
    artifacts = tuple(a for a in native_artifact_contract(root, SCOPE, formats, reader) if a.id.startswith("pitch:"))
    if tuple(a.id for a in artifacts) != IDS:
        raise ValueError("Pitch controls require all short/medium/long PDF/PPTX artifacts in Source order")
    tracked = tuple(sorted(row.path for row in (*source.reference.git.files, *source.reference.git.gitlinks)))
    models: dict[str, tuple[NativeArtifact, Any, tuple[Any, ...]]] = {}
    declarations: list[dict[str, Any]] = []
    targets: dict[str, list[dict[str, Any]]] = {name: [] for name in CONTROL_NAMES}
    for artifact in artifacts:
        remaining(deadline)
        model, base = compile_pitch_source_model(root, SCOPE, artifact, held, tracked_paths=tracked, deadline=deadline)
        pages = compile_projection_contract(model, source_base_url=base, reader=held)
        models[artifact.id] = artifact, model, pages
        notes = [slide.notes for slide in model.slides]
        if model.slides[0].kind != "title":
            notes.insert(0, "")
        if not pages or len(pages) != len(notes) or len(pages) > 500:
            raise ValueError("Pitch selectors differ from the complete bounded Source slide/notes plan")
        declarations.append(
            {"artifact": asdict(artifact), "projection": projection_contract_record(pages), "notes": notes}
        )
        targets["baseline"].append(asdict(PitchTarget(artifact.id, "baseline", None, None)))
        for page, expected in enumerate(pages, 1):
            remaining(deadline)
            package = artifact.format == "pptx"
            for name, code, target in (
                ("layout", "pitch.package.source.layout" if package else "projection.page.geometry", ""),
                ("theme", "pitch.package.source.layout" if package else "office.reference.pixels", ""),
                ("notes", "pitch.package.source.notes", notes[page - 1]),
                (
                    "citation",
                    "pitch.package.source.targets" if package else "projection.citation.target",
                    expected.citation,
                ),
                ("qr-link", "pitch.package.source.targets" if package else "projection.qr.link", expected.qr_target),
                ("qr-pixels", "projection.qr.pixels", expected.qr_target),
            ):
                if name == "notes" and not package:
                    continue
                if name in {"citation", "qr-link", "qr-pixels"} and not target:
                    continue
                targets[name].append(asdict(PitchTarget(artifact.id, name, page, code, target)))
    for length in ("short", "medium", "long"):
        pair = [row for row in declarations if row["artifact"]["id"].startswith(f"pitch:{length}:")]
        if pair[0]["projection"] != pair[1]["projection"] or pair[0]["notes"] != pair[1]["notes"]:
            raise ValueError("Pitch configured PDF/PPTX pair has different complete Source models")
    payload = {
        "schema_version": "template-native-pitch-control-plan-v1",
        "scope": SCOPE,
        "formats": list(formats),
        "config": {"path": config.relative, "sha256": config.sha256},
        "artifacts": declarations,
        "targets": targets,
        "active_controls": [name for name in CONTROL_NAMES if targets[name]],
    }
    source.verify_correspondence(source.reference, root, reader, deadline)
    remaining(deadline)
    return {**payload, "digest": canonical_digest(payload)}, models
