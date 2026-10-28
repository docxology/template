"""Portable native observer replay entry points; producer paths remain labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_pitch_source_admission import SourceCorrespondence

from infrastructure.reporting.native_office_mermaid_binding import OfficeMermaidReaderRuntime

from infrastructure.reporting.native_format_browser_replay import (
    replay_browser_observation as replay_browser_observation,
    replay_browser_controls as replay_browser_controls,
)
from infrastructure.reporting.native_format_observer_source_replay import (
    replay_office_conversion as replay_office_conversion,
)


def replay_native_observer(
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
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
    source_reference: PublicReference | None = None,
    verify_source_correspondence: SourceCorrespondence | None = None,
    office_mermaid_runtime: OfficeMermaidReaderRuntime | None = None,
    original_worker_pid: int | None = None,
    original_worker_platform: str | None = None,
) -> dict[str, Any]:
    """Independent current-source native observations for the actual artifact."""
    from infrastructure.reporting.native_oracle_dispatch import checked_native_observer_result
    from infrastructure.reporting.native_format_observer_dispatch import OBSERVER_SCHEMA
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _raster
    from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content

    if (
        raw.get("schema_version") != OBSERVER_SCHEMA
        or raw.get("id") != artifact.id
        or raw.get("format") != artifact.format
        or raw.get("input") != {"path": snapshot.relative, "sha256": snapshot.sha256}
    ):
        raise ValueError("native observer identity differs from source-owned obligation")
    from infrastructure.reporting.native_print_artifact_observer import selected_print_artifact

    scientific_witness: dict[str, Any] | None = None
    if selected_print_artifact(scope, artifact):
        from infrastructure.reporting.native_print_artifact_replay import replay_print_artifact

        if source_reference is None or verify_source_correspondence is None:
            raise ValueError("configured print replay requires genuine original/current Source admission")
        if original_worker_pid is None or original_worker_platform is None:
            raise ValueError("configured print replay requires the admitted original worker PID/platform")
        source_reference.verify_unchanged(deadline=deadline)
        verify_source_correspondence(source_reference, root, reader, deadline)
        result = replay_print_artifact(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            raw,
            reader,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            versions=versions,
            expected_pid=original_worker_pid,
            expected_platform=original_worker_platform,
            deadline=deadline,
        )
        verify_source_correspondence(source_reference, root, reader, deadline)
        source_reference.verify_unchanged(deadline=deadline)
        checked = checked_native_observer_result(scope, artifact, snapshot, run_id, reader, [result])
        checked["source_observer"] = raw
        return checked
    if artifact.format in {"pdf", "pptx"} and (artifact.id.endswith(":slides") or artifact.id.startswith("pitch:")):
        from infrastructure.reporting.native_format_observer_projection_replay import replay_projection_observer

        result = replay_projection_observer(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            raw,
            reader,
            run_id=run_id,
            custody=custody,
            versions=versions,
            deadline=deadline,
            env=env,
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
        )
        observations = [result["observation"]]
        if "companion" in result:
            observations.append(result["companion"])
    elif artifact.format == "pdf":
        from infrastructure.reporting.native_format_content_contracts import compile_pdf_content_contract

        _raster(raw, snapshot, 0, directory, reader, run_id, versions, custody)
        if artifact.id == "manuscript:pdf":
            from infrastructure.reporting.native_format_scientific_pdf_observer import replay_scientific_pdf_source

            if set(raw) != {
                "schema_version",
                "id",
                "format",
                "input",
                "scientific_pdf_source",
                "raster",
                "observation",
            }:
                raise ValueError("scientific PDF dispatch requires exact original source/native fields")
            source = raw["scientific_pdf_source"]
            if not isinstance(source, dict) or raw["observation"] != source.get("observation"):
                raise ValueError("scientific PDF aggregate differs from original source witness")
            result = replay_scientific_pdf_source(
                root,
                directory,
                scope,
                artifact,
                snapshot,
                raw["raster"],
                source,
                reader,
                run_id=run_id,
                custody=custody,
                env=env,
                deadline=deadline,
                source_reference=source_reference,
                verify_source_correspondence=verify_source_correspondence,
            )
            observations = [result["observation"]]
            scientific_witness = result["witness"]
        else:
            contract = compile_pdf_content_contract(root, scope, artifact, reader, deadline=deadline)
            if raw.get("content_contract") != contract.to_dict():
                raise ValueError("PDF source contracts changed")
            pixels = tuple(
                _file({"path": item["path"], "sha256": item["sha256"]}, reader).content
                for item in raw["raster"]["rasters"]
            )
            observed = inspect_pdf_content(snapshot.content, pixels, contract, deadline=deadline)
            if raw.get("observation") != observed:
                raise ValueError("PDF independent glyph/geometry/pixel replay differs")
            observations = [observed]
    elif artifact.format == "html":
        from infrastructure.reporting.native_format_html_admitted_source import replay_admitted_html_source

        contract, admitted = replay_admitted_html_source(
            root,
            directory,
            scope,
            artifact,
            raw["semantic_source"],
            reader,
            run_id=run_id,
            custody=custody,
            deadline=deadline,
            env=env,
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
        )
        if raw.get("content_contract") != contract.to_dict():
            raise ValueError("HTML source contract changed")
        result = replay_browser_observation(
            root,
            directory,
            snapshot,
            contract,
            raw["observation"],
            reader,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            metadata_source=admitted.metadata,
            admitted_source=admitted,
            deadline=deadline,
            env=env,
        )
        admitted.close(root, reader, deadline=deadline)
        observations = [result]
    elif artifact.format in {"docx", "epub"}:
        from infrastructure.reporting.native_office_full_replay import replay_office_full_source

        fields = {"schema_version", "id", "format", "input", "office_complete_source", "observation"}
        if artifact.format == "epub":
            fields.add("spine")
        if set(raw) != fields:
            raise ValueError("complete Office dispatch requires its exact original full-source fields")
        complete = raw["office_complete_source"]
        if not isinstance(complete, dict) or raw["observation"] != complete.get("observation"):
            raise ValueError("complete Office dispatch aggregate differs from the original full-source record")
        if artifact.format == "epub" and raw["spine"] != complete.get("spine"):
            raise ValueError("complete EPUB dispatch spine differs from its original source-reference record")
        if source_reference is None or verify_source_correspondence is None:
            raise ValueError("portable complete Office source requires original source and current-mirror admission")
        if reader.root != root.resolve():
            raise ValueError("portable complete Office reader differs from its admitted current mirror")
        source_reference.verify_unchanged(deadline=deadline)
        verify_source_correspondence(source_reference, root, reader, deadline)
        result = replay_office_full_source(
            root,
            directory,
            scope,
            artifact,
            snapshot,
            complete,
            reader,
            run_id=run_id,
            custody=custody,
            versions=versions,
            deadline=deadline,
            env=env,
            mermaid_runtime=office_mermaid_runtime,
        )
        verify_source_correspondence(source_reference, root, reader, deadline)
        source_reference.verify_unchanged(deadline=deadline)
        observations = (
            [result["spine"], result["observation"]] if artifact.format == "epub" else [result["observation"]]
        )
    else:
        raise ValueError("complete independent replay for this source projection is not implemented")
    checked = checked_native_observer_result(scope, artifact, snapshot, run_id, reader, observations)
    checked["source_observer"] = raw
    checked["scientific_source_witness"] = scientific_witness
    return checked
