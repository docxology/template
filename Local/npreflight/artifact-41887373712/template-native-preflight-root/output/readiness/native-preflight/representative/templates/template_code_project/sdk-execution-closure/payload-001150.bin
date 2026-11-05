"""Actual native observer dispatch; unsupported source projections stay blocked."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference import PublicReference
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
    audit_pdf_raster,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, create_private_native_directory
from infrastructure.reporting.native_format_content_contracts import (
    NativeContentContract,
    compile_pdf_content_contract,
    content_contract_from_bytes,
)
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_pitch_source_admission import (
    SourceCorrespondence,
    compile_admitted_pitch_projection,
)

from infrastructure.reporting.native_office_mermaid_binding import OfficeMermaidAdmission

from infrastructure.reporting.native_print_artifact_observer import selected_print_artifact

OBSERVER_SCHEMA = "template-native-observer-dispatch-v2"


def _manuscript_contracts(root: Path, scope: str, reader: SnapshotReader) -> tuple[NativeContentContract, ...]:
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.validation.output.render_formats import render_config_manuscript_dir
    from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance

    if not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("native text obligations require current consumed hydration")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    snapshots = [reader.read(path.relative_to(root).as_posix()) for path in discover_manuscript_files(manuscript)]
    return tuple(
        content_contract_from_bytes(f"chapter:{ordinal}", ((snapshot.relative, snapshot.content),))
        for ordinal, snapshot in enumerate(snapshots)
    )


def _chrome(env: dict[str, str]) -> str:
    configured = env.get("CHROME_EXECUTABLE_PATH")
    if configured:
        path = Path(configured)
        if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
            raise NativeToolUnavailable("configured native Chromium browser is not an actual executable file")
        return str(path)
    selected = shutil.which("chromium", path=env.get("PATH")) or shutil.which("google-chrome", path=env.get("PATH"))
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if selected:
        return selected
    if mac.is_file():
        return str(mac)
    raise NativeToolUnavailable("actual native Chromium browser is unavailable")


def observe_native_artifact(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    ordinal: int,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
    source_reference: PublicReference | None = None,
    verify_source_correspondence: SourceCorrespondence | None = None,
    office_mermaid_admission: OfficeMermaidAdmission | None = None,
) -> dict[str, Any]:
    """Observe exact current artifacts with native tools and source contracts.

    Each observer gets a fresh confined directory. Return values describe real
    conformance; full acceptance still requires corresponding complete controls.
    """
    from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content

    leaf = directory / f"observer-{ordinal:04d}"
    create_private_native_directory(root, leaf)
    observed: dict[str, Any] = {
        "schema_version": OBSERVER_SCHEMA,
        "id": artifact.id,
        "format": artifact.format,
        "input": {"path": snapshot.relative, "sha256": snapshot.sha256},
    }
    if selected_print_artifact(scope, artifact):
        from infrastructure.reporting.native_print_artifact_observer import observe_print_artifact

        if source_reference is None or verify_source_correspondence is None:
            raise NativeToolUnavailable("configured print requires original source and current-mirror admission")
        if reader.root != root.resolve():
            raise ValueError("configured print reader differs from its admitted current mirror")
        source_reference.verify_unchanged(deadline=deadline)
        verify_source_correspondence(source_reference, root, reader, deadline)
        observed.update(
            observe_print_artifact(
                root, leaf, scope, artifact, snapshot, reader, env=env, deadline=deadline, run_id=run_id
            )
        )
        verify_source_correspondence(source_reference, root, reader, deadline)
        source_reference.verify_unchanged(deadline=deadline)
        return observed
    if artifact.format == "pdf" and artifact.id.endswith(":slides"):
        from infrastructure.reporting.native_projection_source_dispatch import observe_admitted_manuscript_projection
        from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported

        try:
            complete = observe_admitted_manuscript_projection(
                root,
                leaf,
                scope,
                artifact,
                snapshot,
                reader,
                env=env,
                deadline=deadline,
                run_id=run_id,
                source_reference=source_reference,
                verify_source_correspondence=verify_source_correspondence,
            )
        except ProjectionSourceUnsupported as error:
            observed["observation"] = {"status": "blocked", "findings": [], "blockers": [str(error)]}
            return observed
        observed.update({"manuscript_projection": complete, "observation": complete["observation"]})
        return observed
    if artifact.format in {"pdf", "pptx"} and artifact.id.startswith("pitch:"):
        from infrastructure.reporting.native_projection_contracts import (
            projection_contract_record,
            ProjectionSourceUnsupported,
        )

        try:
            pages = compile_admitted_pitch_projection(
                root,
                scope,
                artifact,
                reader,
                source_reference=source_reference,
                verify_source_correspondence=verify_source_correspondence,
                deadline=deadline,
            )
        except ProjectionSourceUnsupported as error:
            observed["observation"] = {"status": "blocked", "findings": [], "blockers": [str(error)]}
            return observed
        if artifact.format == "pptx":
            from infrastructure.reporting.native_office_observer import convert_office, observe_office_layout

            converted = convert_office(root, leaf, snapshot, "pptx", env=env, deadline=deadline, run_id=run_id)
            result = observe_office_layout(
                root, leaf, converted, projection_pages=pages, env=env, deadline=deadline, run_id=run_id
            )
            observed["observation"] = result
        else:
            from infrastructure.reporting.native_projection_checks import inspect_projection

            raster = audit_pdf_raster(
                root,
                leaf,
                snapshot,
                parse_native_bytes("pdf", snapshot.content),
                env=env,
                deadline=deadline,
                run_id=run_id,
                ordinal=0,
            )
            result = inspect_projection(
                snapshot.content,
                tuple(reader.read(item["path"]).content for item in raster["rasters"]),
                pages,
                deadline=deadline,
                native_context=(root, leaf, env, run_id),
            )
            observed.update({"raster": raster, "observation": result})
        from infrastructure.reporting.native_projection_source_dispatch import observe_admitted_pitch_companion

        observed["projection_contract"] = projection_contract_record(pages)
        layout = observed["observation"] if artifact.format == "pptx" else observed
        pixels = tuple(reader.read(item["path"]).content for item in layout["raster"]["rasters"])
        companion = observe_admitted_pitch_companion(
            root,
            leaf / "source-companion",
            scope,
            artifact,
            snapshot,
            pixels,
            reader,
            projection_contract=observed["projection_contract"],
            env=env,
            deadline=deadline,
            run_id=run_id,
            source_reference=source_reference,
            verify_source_correspondence=verify_source_correspondence,
        )
        observed["source_package" if artifact.format == "pptx" else "source_native_reference"] = companion
        return observed
    if artifact.format == "pdf":
        raster = audit_pdf_raster(
            root,
            leaf,
            snapshot,
            parse_native_bytes("pdf", snapshot.content),
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
        if artifact.id == "manuscript:pdf":
            from infrastructure.reporting.native_format_scientific_pdf_observer import observe_scientific_pdf_source

            source = observe_scientific_pdf_source(
                root,
                leaf,
                scope,
                artifact,
                snapshot,
                raster,
                reader,
                env=env,
                deadline=deadline,
                run_id=run_id,
                source_reference=source_reference,
                verify_source_correspondence=verify_source_correspondence,
            )
            observed.update({"scientific_pdf_source": source, "raster": raster, "observation": source["observation"]})
        else:
            content = compile_pdf_content_contract(root, scope, artifact, reader, deadline=deadline)
            result = inspect_pdf_content(
                snapshot.content,
                tuple(reader.read(item["path"]).content for item in raster["rasters"]),
                content,
                deadline=deadline,
            )
            observed.update({"content_contract": content.to_dict(), "raster": raster, "observation": result})
    elif artifact.format == "html":
        from infrastructure.reporting.native_format_html_admitted_source import observe_admitted_html_source
        from infrastructure.reporting.native_format_browser_oracles import audit_browser_html
        from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported

        try:
            content, semantic, admitted = observe_admitted_html_source(
                root,
                leaf,
                scope,
                artifact,
                reader,
                env=env,
                deadline=deadline,
                run_id=run_id,
                source_reference=source_reference,
                verify_source_correspondence=verify_source_correspondence,
            )
        except ProjectionSourceUnsupported as error:
            observed["observation"] = {"status": "blocked", "findings": [], "blockers": [str(error)]}
            return observed
        result = audit_browser_html(
            root,
            leaf,
            snapshot.content,
            content,
            chrome=_chrome(env),
            env=env,
            deadline=deadline,
            run_id=run_id,
            artifact=snapshot,
            metadata_source=admitted.metadata,
            admitted_source=admitted,
        )
        admitted.close(root, reader, deadline=deadline)
        observed.update({"content_contract": content.to_dict(), "semantic_source": semantic, "observation": result})
    elif artifact.format in {"docx", "epub"}:
        from infrastructure.reporting.native_office_full_observer import observe_office_full_source

        if source_reference is None or verify_source_correspondence is None:
            raise NativeToolUnavailable(
                "complete Office source observation requires original source and current-mirror admission"
            )
        if reader.root != root.resolve():
            raise ValueError("complete Office source reader differs from its admitted current mirror")
        source_reference.verify_unchanged(deadline=deadline)
        verify_source_correspondence(source_reference, root, reader, deadline)
        complete = observe_office_full_source(
            root,
            leaf,
            scope,
            artifact,
            snapshot,
            reader,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_epub_engine=frozen_epub_engine,
            mermaid_admission=office_mermaid_admission,
        )
        verify_source_correspondence(source_reference, root, reader, deadline)
        source_reference.verify_unchanged(deadline=deadline)
        observed.update({"office_complete_source": complete, "observation": complete["observation"]})
        if artifact.format == "epub":
            observed["spine"] = complete["spine"]
    else:
        observed["observation"] = {
            "status": "blocked",
            "findings": [],
            "blockers": [f"{artifact.id}: independently reconstructed source projection dispatch unavailable"],
        }
    return observed


def observe_browser_controls(
    root: Path,
    directory: Path,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    interpreter: Path | None = None,
    semantic: bool = False,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    """Select only genuine Source-owned basic/semantic original child roles."""
    from infrastructure.reporting.native_format_browser_child import supervise_browser_source_controls

    if scope is None:
        raise ValueError("browser controls require their original explicit admitted public scope")
    return supervise_browser_source_controls(
        root,
        directory,
        scope,
        env=env,
        deadline=deadline,
        run_id=run_id,
        interpreter=interpreter or Path(sys.executable),
        semantic=semantic,
    )


def observe_format_controls(
    root: Path,
    directory: Path,
    formats: tuple[str, ...],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    scope: str | None = None,
    interpreter: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> dict[str, Any]:
    """Source-owned complete format control selection; exceptions retain failure."""
    result: dict[str, Any] = {"schema_version": "template-native-observer-controls-v2"}
    if "html" in formats:
        result["html"] = observe_browser_controls(
            root, directory, env=env, deadline=deadline, run_id=run_id, scope=scope
        )
        result["html_semantic"] = observe_browser_controls(
            root,
            directory,
            env=env,
            deadline=deadline,
            run_id=run_id,
            interpreter=interpreter,
            semantic=True,
            scope=scope,
        )
    if "docx" in formats:
        from infrastructure.reporting.native_office_observer import supervise_office_controls

        result["docx"] = supervise_office_controls(
            root,
            directory,
            "docx",
            interpreter=interpreter or Path(sys.executable),
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
    if "epub" in formats:
        if epubcheck_jar is None or java_executable is None:
            raise NativeToolUnavailable("actual EPUBCheck JAR and Java runtime are required")
        from infrastructure.reporting.native_epub_observer import supervise_epub_controls

        result["epub"] = supervise_epub_controls(
            root,
            directory,
            interpreter=interpreter or Path(sys.executable),
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_engine=frozen_epub_engine,
        )
    if "slides" in formats or "pptx" in formats:
        from infrastructure.reporting.native_projection_checks import supervise_projection_controls

        result["projection"] = supervise_projection_controls(
            root, directory, interpreter=interpreter or Path(sys.executable), env=env, deadline=deadline, run_id=run_id
        )
        from infrastructure.reporting.native_office_observer import supervise_office_controls

        result["pptx"] = supervise_office_controls(
            root,
            directory,
            "pptx",
            interpreter=interpreter or Path(sys.executable),
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
    if "slides" in formats:
        if scope is None:
            raise ValueError("slide controls require the exact enclosing public Source scope")
        from infrastructure.reporting.native_slide_control_adapter import supervise_slide_source_controls

        result["slide_source"] = supervise_slide_source_controls(
            root,
            directory,
            scope=scope,
            interpreter=interpreter or Path(sys.executable),
            env=env,
            deadline=deadline,
            run_id=run_id,
        )
    return result
