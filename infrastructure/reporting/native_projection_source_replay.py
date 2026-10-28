"""Independent admitted manuscript and complete Pitch companion readback."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.native_pitch_source_admission import SourceCorrespondence
from infrastructure.reporting.native_projection_source_dispatch import _admit, _close
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _original_tools(
    bindings: list[dict[str, str]], reader: SnapshotReader, run_id: str
) -> Callable[[dict[str, Any]], None]:
    """Bind supplied callbacks to exact retained original native process custody."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool

    held = []
    for binding in bindings:
        raw = _file(binding, reader).json_object()
        _tool(binding, reader, run_id, raw["tool"], raw["purpose"], raw["command"][1:])
        held.append(raw)

    def validate(raw: dict[str, Any]) -> None:
        if raw not in held:
            raise ValueError("source companion referenced an unadmitted original native tool")

    return validate


@contextmanager
def _current_source_tools(reader: SnapshotReader, deadline: float) -> Iterator[str]:
    """Fresh tools use independently admitted current Source and its current run."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
        native_producer_operation,
    )

    operation = require_native_operation(reader)
    if deadline != operation.deadline:
        raise ValueError("projection current native tools require the unchanged admitted reader deadline")
    source = operation.source
    current_run_id = source.bindings.run_id
    operation.verify(reader)
    owner = current_native_producer_operation()
    if owner is None:
        with native_producer_operation(source, run_id=current_run_id, deadline=deadline):
            yield current_run_id
    else:
        if owner.source is not source or owner.run_id != current_run_id or owner.deadline != deadline:
            raise ValueError("projection current native tools differ from their genuine Source/clock/run")
        yield current_run_id
    operation.verify(reader)


def replay_admitted_manuscript_projection(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _raster
    from infrastructure.reporting.native_slide_replay import replay_manuscript_slide_reference

    _admit(root, reader, source_reference, verify_source_correspondence, deadline)
    if set(raw) != {"schema_version", "id", "format", "input", "manuscript_projection", "observation"}:
        raise ValueError("manuscript native dispatch omitted its complete source reference")
    complete = raw["manuscript_projection"]
    if not isinstance(complete, dict) or set(complete) != {"source", "reference", "raster", "observation"}:
        raise ValueError("manuscript complete native source fields differ")
    if raw["observation"] != complete["observation"]:
        raise ValueError("manuscript native dispatch conceals its full source observation")
    _raster(complete, snapshot, 0, directory, reader, run_id, versions, custody)
    bindings = list(complete["source"]["tool_artifacts"])
    references = complete["reference"]["references"]
    if set(references) != {"source", "marked"}:
        raise ValueError("manuscript source/marked native references are incomplete")
    for label in ("source", "marked"):
        reference = references[label]
        reference_pdf = _file(reference["pdf"], reader)
        reference_directory = directory / "reference" / label
        if reference_pdf.path != reference_directory / "oracle.pdf":
            raise ValueError("manuscript native reference belongs to another original attempt")
        _raster(reference, reference_pdf, 0, reference_directory, reader, run_id, versions, custody)
        bindings.extend(reference["tool_artifacts"])
        bindings.extend(item["artifact"] for item in reference["raster"]["tool_artifacts"])
    with _current_source_tools(reader, deadline) as current_run_id:
        observed = replay_manuscript_slide_reference(
            root,
            scope,
            artifact,
            snapshot.content,
            tuple(
                _file({"path": row["path"], "sha256": row["sha256"]}, reader).content
                for row in complete["raster"]["rasters"]
            ),
            complete,
            reader,
            read_artifact=lambda binding: _file(binding, reader).content,
            validate_original_tool=_original_tools(bindings, reader, run_id),
            env=env,
            deadline=deadline,
            run_id=current_run_id,
        )
    _close(root, reader, source_reference, verify_source_correspondence, deadline)
    return observed


def _package_qr(
    root: Path,
    directory: Path,
    original: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
) -> None:
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
    from infrastructure.reporting.native_qr_runtime import replay_projection_qr_runtime

    for ordinal, page in enumerate(original["pages"], 1):
        qr = page["qr"]
        if qr is None:
            continue
        leaf = directory / f"package-qr-{ordinal}"
        runtime = _file(qr["runtime_artifact"], reader)
        decoded = _file(qr["tool_artifact"], reader)
        if runtime.path != leaf / f"qr-runtime-{ordinal}.json" or decoded.path != leaf / f"qr-decode-{ordinal}.json":
            raise ValueError("Pitch package QR belongs to another original page/attempt")
        native_input = reader.read((leaf / f"qr-page-{ordinal}.png").relative_to(root).as_posix())
        if native_input.sha256 != qr["raster_sha256"]:
            raise ValueError("Pitch package original QR pixel input changed")
        data = runtime.json_object()
        for binding in (data["version_artifact"], data["loader_artifact"], qr["tool_artifact"]):
            tool = _file(binding, reader).json_object()
            code = qr["original_exit_code"] if binding == qr["tool_artifact"] else 0
            _tool(binding, reader, run_id, tool["tool"], tool["purpose"], tool["command"][1:], code)
        replay_projection_qr_runtime(
            qr,
            read_artifact=lambda binding: _file(binding, reader).content,
            producer_path=lambda relative: str(producer_path(custody, root, root / relative)),
            run_id=run_id,
        )


def replay_admitted_pitch_companion(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    candidate_rasters: tuple[bytes, ...],
    original: dict[str, Any],
    reader: SnapshotReader,
    *,
    projection_contract: dict[str, Any],
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
    source_reference: PublicReference | None,
    verify_source_correspondence: SourceCorrespondence | None,
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _raster

    tracked = _admit(root, reader, source_reference, verify_source_correspondence, deadline)
    if artifact.format == "pdf":
        from infrastructure.reporting.native_pitch_source_native import replay_pitch_pdf_source_reference

        if (
            set(original)
            != {
                "schema_version",
                "input_sha256",
                "projection_contract",
                "source_pdf",
                "raster",
                "native_projection",
                "status",
                "findings",
                "blockers",
            }
            or original["schema_version"] != "template-native-pitch-source-pdf-reference-v1"
        ):
            raise ValueError("Pitch original native PDF source fields differ")
        source_pdf = _file(original["source_pdf"], reader)
        if source_pdf.path != directory / "source-model.pdf":
            raise ValueError("Pitch source PDF belongs to another original attempt")
        _raster(original, source_pdf, 0, directory, reader, run_id, versions, custody)
        bindings = [item["artifact"] for item in original["raster"]["tool_artifacts"]]
        independent = replay_pitch_pdf_source_reference(
            root,
            scope,
            artifact,
            snapshot.content,
            candidate_rasters,
            original,
            reader,
            tracked_paths=tracked,
            read_artifact=lambda binding: _file(binding, reader).content,
            validate_original_tool=_original_tools(bindings, reader, run_id),
            deadline=deadline,
        )
        expected = {key: original[key] for key in ("native_projection", "status", "findings", "blockers")}
        if independent != expected or original["projection_contract"] != projection_contract:
            raise ValueError("Pitch current complete PDF source outcome differs")
    elif artifact.format == "pptx":
        from infrastructure.reporting.native_pitch_source import compile_pitch_source_model
        from infrastructure.reporting.native_pitch_source_layout import (
            LAYOUT_CANONICALIZATION,
            LAYOUT_SCHEMA,
            pitch_package_layout,
            replay_pitch_source_layout,
        )
        from infrastructure.reporting.native_pitch_source_parity import inspect_pitch_package
        from infrastructure.reporting.native_projection_contracts import compile_projection_contract
        from infrastructure.core.pipeline.fingerprints import canonical_digest

        if (
            set(original)
            != {
                "schema_version",
                "input_sha256",
                "parser",
                "contract",
                "source_notes_checked",
                "pages",
                "findings",
                "blockers",
                "status",
                "source_layout",
            }
            or original["schema_version"] != "template-native-pitch-package-source-v1"
        ):
            raise ValueError("Pitch original complete source package fields differ")
        if (
            not isinstance(original["source_layout"], dict)
            or original["source_layout"].get("schema_version") != LAYOUT_SCHEMA
            or original["source_layout"].get("canonicalization") != LAYOUT_CANONICALIZATION
        ):
            raise ValueError("Pitch original package layout canonicalization requires fresh versioned evidence")
        source = _file(original["source_layout"]["source_artifact"], reader)
        if (
            source.path != directory / "source-model.pptx"
            or canonical_digest(pitch_package_layout(source.content))
            != original["source_layout"]["source_layout_digest"]
        ):
            raise ValueError("Pitch original full source package layout custody differs")
        _package_qr(root, directory, original, reader, run_id=run_id, custody=custody)
        model, source_base = compile_pitch_source_model(
            root, scope, artifact, reader, tracked_paths=tracked, deadline=deadline
        )
        pages = compile_projection_contract(model, source_base_url=source_base, reader=reader)
        with (
            _current_source_tools(reader, deadline) as current_run_id,
            tempfile.TemporaryDirectory(prefix="pitch-package-replay-", dir=root / "output/readiness") as private,
        ):
            leaf = Path(private)
            independent = inspect_pitch_package(
                snapshot.content,
                pages,
                deadline=deadline,
                native_context=(root, leaf, env, current_run_id),
                source_model=model,
            )
        independent = json.loads(json.dumps(independent))
        layout = replay_pitch_source_layout(
            root, scope, artifact, snapshot.content, reader, tracked_paths=tracked, deadline=deadline
        )
        independent["findings"].extend(layout["findings"])
        independent["status"] = "fail" if independent["findings"] else "blocked" if independent["blockers"] else "pass"
        left = copy.deepcopy(original)
        expected_layout = {key: value for key, value in left.pop("source_layout").items() if key != "source_artifact"}
        if layout != expected_layout or left["contract"] != projection_contract:
            raise ValueError("Pitch current complete source package theme/layout differs")
        for value in (left, independent):
            for page in value["pages"]:
                if page["qr"] is not None:
                    page["qr"].pop("tool_artifact", None)
                    page["qr"].pop("runtime_artifact", None)
        if left != independent:
            raise ValueError("Pitch independent source text/fonts/notes/images/QR/package observations differ")
    else:
        raise ValueError("Pitch portable source companion has an undeclared native format")
    if (
        original.get("input_sha256") != snapshot.sha256
        or hashlib.sha256(snapshot.content).hexdigest() != snapshot.sha256
    ):
        raise ValueError("Pitch original companion consumed different native artifact bytes")
    _close(root, reader, source_reference, verify_source_correspondence, deadline)
    return independent
