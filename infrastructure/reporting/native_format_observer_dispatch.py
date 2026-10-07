"""Actual native observer dispatch; unsupported source projections stay blocked."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any
from collections.abc import Callable

from infrastructure.project.public_acceptance_evidence import write_json
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

OBSERVER_SCHEMA = "template-native-observer-dispatch-v1"


def _manuscript_contracts(root: Path, scope: str, reader: SnapshotReader) -> tuple[NativeContentContract, ...]:
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.validation.output.render_formats import render_config_manuscript_dir
    from infrastructure.validation.publication.rendered_provenance import validate_rendered_provenance

    if not validate_rendered_provenance(root, scope).valid:
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
    if artifact.format in {"pdf", "pptx"} and (artifact.id.endswith(":slides") or artifact.id.startswith("pitch:")):
        from infrastructure.reporting.native_projection_contracts import (
            compile_scope_projection_contract,
            projection_contract_record,
            ProjectionSourceUnsupported,
        )

        try:
            pages = compile_scope_projection_contract(root, scope, artifact, reader)
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
        observed["projection_contract"] = projection_contract_record(pages)
        return observed
    if artifact.format == "pdf":
        content = compile_pdf_content_contract(root, scope, artifact, reader, deadline=deadline)
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
        result = inspect_pdf_content(
            snapshot.content,
            tuple(reader.read(item["path"]).content for item in raster["rasters"]),
            content,
            deadline=deadline,
        )
        observed.update({"content_contract": content.to_dict(), "raster": raster, "observation": result})
    elif artifact.format == "html":
        from infrastructure.reporting.native_format_semantic_source import observe_html_source
        from infrastructure.reporting.native_format_browser_oracles import audit_browser_html

        content, semantic = observe_html_source(
            root, leaf, scope, artifact, reader, env=env, deadline=deadline, run_id=run_id
        )
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
        )
        observed.update({"content_contract": content.to_dict(), "semantic_source": semantic, "observation": result})
    elif artifact.format == "docx":
        from infrastructure.reporting.native_office_observer import convert_office, observe_office_layout

        chapters = _manuscript_contracts(root, scope, reader)
        content = NativeContentContract(
            artifact.id,
            tuple(item for chapter in chapters for item in chapter.sources),
            tuple(item for chapter in chapters for item in chapter.blocks),
            tuple(item for chapter in chapters for item in chapter.blockers),
        )
        converted = convert_office(root, leaf, snapshot, "docx", env=env, deadline=deadline, run_id=run_id)
        result = observe_office_layout(
            root, leaf, converted, source_contract=content, env=env, deadline=deadline, run_id=run_id
        )
        observed.update({"content_contract": content.to_dict(), "observation": result})
    elif artifact.format == "epub":
        from infrastructure.reporting.native_epub_observer import (
            inspect_epub,
            inspect_epub_spine,
            inspect_epub_reader_layout,
        )

        chapters = _manuscript_contracts(root, scope, reader)
        converted = inspect_epub(
            root,
            leaf,
            snapshot,
            env=env,
            deadline=deadline,
            run_id=run_id,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            frozen_engine=frozen_epub_engine,
        )
        pdf = reader.read(converted["pdf"]["path"])
        raster = audit_pdf_raster(
            root,
            leaf,
            pdf,
            parse_native_bytes("pdf", pdf.content),
            env=env,
            deadline=deadline,
            run_id=run_id,
            ordinal=0,
        )
        result = inspect_epub_reader_layout(
            pdf.content,
            tuple(reader.read(item["path"]).content for item in raster["rasters"]),
            chapters,
            deadline=deadline,
        )
        observed.update(
            {
                "chapter_contracts": [chapter.to_dict() for chapter in chapters],
                "conversion": converted,
                "raster": raster,
                "spine": inspect_epub_spine(snapshot.content, chapters),
                "observation": result,
            }
        )
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
) -> list[dict[str, Any]]:
    """Supervise actual oracle exits after successful real native execution."""
    import time
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.project.public_acceptance_evidence import bootstrap_command, read_json
    from infrastructure.reporting.native_format_acceptance_contracts import PROCESS_SCHEMA
    from infrastructure.reporting.native_format_browser_oracles import (
        BROWSER_CONTROL_CODES,
        require_browser_control_result,
    )

    require_result: Callable[[str, dict[str, Any]], int]
    if semantic:
        from infrastructure.reporting.native_format_browser_semantic_controls import (
            SEMANTIC_CONTROL_CODES,
            require_semantic_control_result,
        )

        names = SEMANTIC_CONTROL_CODES
        require_result = require_semantic_control_result
        module = "infrastructure.reporting.native_format_browser_semantic_controls"
        prefix = "browser-semantic"
    else:
        names = BROWSER_CONTROL_CODES
        require_result = require_browser_control_result
        module = "infrastructure.reporting.native_format_browser_oracles"
        prefix = "browser-control"
    records = []
    for name in names:
        leaf = directory / f"{prefix}-{name}"
        create_private_native_directory(root, leaf)
        output = leaf / "control-observation.json"
        command = bootstrap_command(
            interpreter or Path(sys.executable),
            root,
            module,
            "--control",
            name,
            "--root",
            str(root),
            "--directory",
            str(leaf),
            "--deadline",
            str(deadline),
            "--run-id",
            run_id,
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("browser controls exhausted original deadline")
        process = run_bounded_subprocess(command, cwd=root, env=env, timeout=min(remaining, 120))
        if process.timed_out:
            raise TimeoutError("actual browser control timed out")
        raw = read_json(root, output)
        code = require_result(name, raw["observation"])
        if (
            process.returncode != code
            or process.original_returncode != code
            or raw["oracle_exit_code"] != code
            or process.custody_refused
        ):
            raise ValueError("actual browser control did not preserve its intended original process outcome")
        binding = write_json(
            root,
            leaf / "control-process.json",
            {
                "schema_version": PROCESS_SCHEMA,
                "run_id": run_id,
                "command": list(command),
                "exit_code": process.returncode,
                "original_exit_code": process.original_returncode,
                "timed_out": process.timed_out,
                "custody_refused": process.custody_refused,
            },
        )
        snapshot = SnapshotReader(root).read(output.relative_to(root).as_posix())
        records.append(
            {
                "name": name,
                "artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
                "process_artifact": binding,
                "original_exit_code": process.original_returncode,
            }
        )
    return records


def observe_format_controls(
    root: Path,
    directory: Path,
    formats: tuple[str, ...],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    interpreter: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> dict[str, Any]:
    """Source-owned complete format control selection; exceptions retain failure."""
    result: dict[str, Any] = {"schema_version": "template-native-observer-controls-v1"}
    if "html" in formats:
        result["html"] = observe_browser_controls(root, directory, env=env, deadline=deadline, run_id=run_id)
        result["html_semantic"] = observe_browser_controls(
            root, directory, env=env, deadline=deadline, run_id=run_id, interpreter=interpreter, semantic=True
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
    return result
