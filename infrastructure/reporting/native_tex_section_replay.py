"""Authenticate an Original TeX section and independently repeat its full writer.

Current Source nomination is supplied by the controller, never decoded from the
reference. Retained Original paths are labels; no departed producer is reopened.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering.latex_utils import latex_compile_command
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_pdf_citation_runtime import dependency_identity
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tex_section_reference import RESIDUALS, SCHEMA, observe_tex_section_reference
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

FIELDS = frozenset(
    {
        "schema_version",
        "scope",
        "artifact_id",
        "artifact_path",
        "run_id",
        "sdk_context",
        "compiler",
        "tex_input",
        "inputs",
        "tool_artifacts",
        "dependency_custody",
        "references",
        "recorder_noninterference",
        "blockers",
        "component_status",
        "admission_status",
    }
)


def _manifest(raw: dict[str, Any], reader: SnapshotReader, input_directory: Path) -> list[dict[str, Any]]:
    operation = require_native_operation(reader)
    rows = raw["inputs"]
    if (
        not isinstance(rows, list)
        or not rows
        or len(rows) > 10000
        or [row["path"] for row in rows] != sorted({row["path"] for row in rows})
    ):
        raise ValueError("section reference input closure is empty, duplicated or unordered")
    result = []
    total = 0
    for row in rows:
        if set(row) != {"path", "role", "sha256", "bytes", "frozen"} or row["role"] not in {
            "authored",
            "consumed",
            "authored-consumed",
            "generated-figure",
            "generated-audit-figure",
        }:
            raise ValueError("section reference changes the Source input role/fieldset")
        reader.public_path(row["path"])
        if not Path(row["path"]).is_relative_to(Path("projects") / raw["scope"]):
            raise ValueError("section reference input belongs to another Source project")
        held = _file(row["frozen"], reader)
        total += len(held.content)
        if (
            held.sha256 != row["sha256"]
            or len(held.content) != row["bytes"]
            or total > 128 * 1024 * 1024
            or Path(held.relative) != input_directory / row["path"]
        ):
            raise ValueError("section retained Source input changed or exceeds native byte bounds")
        if row["role"] in {"authored", "authored-consumed"}:
            if held.content != operation.source.reference.read(row["path"]):
                raise ValueError("section authored bytes differ from independently held immutable Source")
        result.append({key: row[key] for key in ("path", "role", "sha256", "bytes")})
    tex = _file(raw["tex_input"], reader)
    if sum(row["frozen"] == raw["tex_input"] and "consumed" in row["role"] for row in rows) != 1:
        raise ValueError("section selected TeX lacks one exact Source-consumed frozen binding")
    if tex.path.suffix != ".tex":
        raise ValueError("section original reference is not its selected TeX writer input")
    return result


def _consumed_tex(tool: dict[str, Any], tex_binding: dict[str, str], tex_label: Path, reader: SnapshotReader) -> None:
    process = _file(tool["native_process_artifact"], reader).json_object()
    nomination = process["nomination"]
    if (
        tool["tool"] not in {"xelatex", "lualatex", "pdflatex"}
        or process["launcher_preserved"] is not True
        or nomination["tool"] != tool["tool"]
        or Path(nomination["path"]).name != tool["tool"]
        or tool["command"] != [nomination["path"], *tool["command"][1:]]
    ):
        raise ValueError("section actual compiler did not preserve its fixed Source-selected engine launcher")
    before = tool["input_observations_before"]
    selected = [row for row in before if row["path"] == str(tex_label)]
    if (
        len(selected) != 1
        or tool["input_observations_after"] != before
        or selected[0]["sha256"] != tex_binding["sha256"]
    ):
        raise ValueError("section actual compiler changed or omitted its exact selected TeX input")
    copies = [row for row in tool["consumed_input_artifacts"] if row["observation"] == selected[0]]
    if len(copies) != 1 or _file(copies[0]["artifact"], reader).content != _file(tex_binding, reader).content:
        raise ValueError("section compiler actual consumed copy differs from independently held Source TeX")


def _dependencies(raw: dict[str, Any], reader: SnapshotReader) -> list[list[Any]]:
    custody = raw["dependency_custody"]
    if (
        set(custody) != {"before", "after", "dependency_identity", "retained", "discovery_fls", "reference_fls"}
        or not custody["before"]
        or custody["before"] != custody["after"]
        or custody["dependency_identity"] != dependency_identity(custody["before"])
        or len(custody["retained"]) != len(custody["before"])
    ):
        raise ValueError("section reference lacks complete before/after original dependency custody")
    for retained, observed in zip(custody["retained"], custody["before"], strict=True):
        if (
            set(observed) != {"path", "name", "sha256", "bytes"}
            or {key: retained[key] for key in observed} != observed
            or set(retained) != {*observed, "artifact"}
        ):
            raise ValueError("section retained dependency differs from actual consuming recorder census")
        held = _file(retained["artifact"], reader)
        if held.sha256 != observed["sha256"] or len(held.content) != observed["bytes"]:
            raise ValueError("section original retained package/font body changed")
    for label in ("discovery_fls", "reference_fls"):
        if not _file(custody[label], reader).content.startswith(b"PWD "):
            raise ValueError("section reference omitted its actual recorder working directory")
    return dependency_identity(custody["before"])


def _parity(raw: dict[str, Any], reader: SnapshotReader, *, deadline: float) -> dict[str, Any]:
    writer, reference = raw["references"]["writer"], raw["references"]["reference"]
    value = inspect_pdf_reference_parity(
        _file(writer["pdf"], reader).content,
        _file(reference["pdf"], reader).content,
        tuple(_file(row, reader).content for row in writer["rasters"]),
        tuple(_file(row, reader).content for row in reference["rasters"]),
        deadline=deadline,
    )
    if value != raw["recorder_noninterference"] or raw["component_status"] != (
        "fail" if value["findings"] else "passed"
    ):
        raise ValueError("section reference conceals its complete native recorder noninterference result")
    return value


def _rasters(
    original: dict[str, Any],
    current: dict[str, Any],
    reader: SnapshotReader,
    current_reader: SnapshotReader,
    *,
    original_directory: Path,
    current_directory: Path,
    run_id: str,
    current_run_id: str,
) -> None:
    for reference, selected, directory, nonce in (
        (original, reader, original_directory, run_id),
        (current, current_reader, current_directory, current_run_id),
    ):
        raster = reference["raster"]
        if (
            set(raster) != {"dpi", "input_artifact", "rasters", "tool_artifacts"}
            or raster["dpi"] != 150
            or _file(raster["input_artifact"], selected).content != _file(reference["pdf"], selected).content
            or [{"path": row["path"], "sha256": row["sha256"]} for row in raster["rasters"]] != reference["rasters"]
            or len(raster["tool_artifacts"]) != 2
        ):
            raise ValueError("section raster omits complete actual PDF/page/input/tool bindings")
        for binding, (tool, purpose, arguments) in zip(
            raster["tool_artifacts"],
            (
                (
                    "pdftoppm",
                    "raster-0000",
                    ["-r", "150", "-png", str(directory / "input-0000.pdf"), str(directory / "raster-0000")],
                ),
                ("pdffonts", "fonts-0000", [str(directory / "input-0000.pdf")]),
            ),
            strict=True,
        ):
            _tool(binding, selected, nonce, tool, purpose, arguments)
    for held, fresh in zip(original["raster"]["tool_artifacts"], current["raster"]["tool_artifacts"], strict=True):
        before, after = _file(held, reader).json_object(), _file(fresh, current_reader).json_object()
        if any(before[key] != after[key] for key in ("executable", "executable_sha256")):
            raise ValueError("section actual Original/current raster tool body differs")


def replay_tex_section_reference(
    scope: str,
    artifact: NativeArtifact,
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    current_source: NativeSourceContext,
    directory: Path,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Authenticate Original first, then use a genuine separate Current Source owner."""
    operation = require_native_operation(reader)
    original_launch = operation.originals.get(scope)
    if original_launch is None or deadline != operation.deadline or reader.native_producer_operation is not None:
        raise ValueError("section replay requires externally held Original launch and its existing clock")
    authority = authenticate_original_native_artifact(
        binding,
        reader,
        run_id=original_launch.run_id,
        required_sdk_modules=(
            "reporting/native_tex_section_source.py",
            "reporting/native_tex_section_reference.py",
            "rendering/latex_utils.py",
            "reporting/native_pdf_citation_runtime.py",
        ),
    )
    original = authority["event"].json_object()
    if (
        set(original) != FIELDS
        or original["schema_version"] != SCHEMA
        or original["scope"] != scope
        or original["artifact_id"] != artifact.id
        or original["artifact_path"] != artifact.path
        or original["run_id"] != original_launch.run_id
        or original["sdk_context"] != authority["source"]
        or original["blockers"] != list(RESIDUALS)
        or original["admission_status"] != "blocked"
    ):
        raise ValueError("section Original source/run/role or retained semantic residuals differ")
    original_manifest = _manifest(original, reader, Path(binding["path"]).parent / "compile/source")
    original_dependencies = _dependencies(original, reader)
    original_parity = _parity(original, reader, deadline=deadline)
    owner = current_native_producer_operation()
    if (
        not isinstance(current_source, NativeSourceContext)
        or owner is None
        or owner.source is not current_source
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_commit != operation.source.bindings.expected_commit
        or current_source.bindings.expected_source_identity != operation.source.bindings.expected_source_identity
        or current_source.bindings.selected_sdk_package_root != operation.source.bindings.selected_sdk_package_root
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or current_source.bindings.run_id in {operation.source.bindings.run_id, original_launch.run_id}
        or owner.run_id != current_source.bindings.run_id
        or owner.deadline != deadline
        or not directory.is_relative_to(owner.stage_scope_directory(scope))
    ):
        raise ValueError("section current reproduction lacks exact independent Source/SDK/root/owner nomination")
    root = current_source.bindings.current_root
    for protected in (
        operation.source.bindings.current_root,
        operation.source.reference.root,
        operation.source.bindings.selected_sdk_package_root,
    ):
        if root.is_relative_to(protected) or protected.is_relative_to(root):
            raise ValueError("section Current root overlaps held Original, Source or installed SDK")
    current_reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
    fresh_binding = observe_tex_section_reference(
        root, directory, scope, artifact, current_reader, env=env, deadline=deadline
    )
    fresh = _file(fresh_binding, current_reader).json_object()
    fresh_manifest = [{key: row[key] for key in ("path", "role", "sha256", "bytes")} for row in fresh["inputs"]]
    if (
        fresh_manifest != original_manifest
        or fresh["compiler"] != original["compiler"]
        or _dependencies(fresh, current_reader) != original_dependencies
        or _file(fresh["tex_input"], current_reader).content != _file(original["tex_input"], reader).content
    ):
        raise ValueError("fresh Current section writer uses another complete Source input/dependency body")
    fresh_parity = _parity(fresh, current_reader, deadline=deadline)
    original_root = Path(authority["source"]["current_mirror"]["root"])
    original_tex = original_root / original["tex_input"]["path"]
    current_tex = root / fresh["tex_input"]["path"]
    # Runtime is selected from the authenticated aggregate's fixed owned layout.
    compile_directory = original_root / Path(binding["path"]).parent / "compile"
    if len(original["tool_artifacts"]) != 6 or len(fresh["tool_artifacts"]) != 6:
        raise ValueError("section reference lacks its exact actual two-pass discovery/writer/reference cohort")
    for ordinal, (held, new) in enumerate(zip(original["tool_artifacts"], fresh["tool_artifacts"], strict=True)):
        label = ("discovery", "writer", "reference")[ordinal // 2]
        arguments = latex_compile_command(
            original_tex, compile_directory / label, original["compiler"], recorder=label != "writer"
        )[1:]
        original_tool = _tool(
            held,
            reader,
            original_launch.run_id,
            original["compiler"],
            f"section-{label}-{ordinal % 2 + 1:02d}",
            arguments,
        )
        _consumed_tex(original_tool, original["tex_input"], original_tex, reader)
        current_tool = _file(new, current_reader).json_object()
        current_arguments = latex_compile_command(
            current_tex, directory / "compile" / label, fresh["compiler"], recorder=label != "writer"
        )[1:]
        _tool(
            new,
            current_reader,
            owner.run_id,
            fresh["compiler"],
            f"section-{label}-{ordinal % 2 + 1:02d}",
            current_arguments,
        )
        _consumed_tex(current_tool, fresh["tex_input"], current_tex, current_reader)
        if (
            original_tool["cwd"] != str(original_tex.parent)
            or any(original_tool[key] != current_tool[key] for key in ("executable", "executable_sha256"))
            or current_tool["cwd"] != str(current_tex.parent)
        ):
            raise ValueError("section actual Original/current compiler body or original Source cwd differs")
    comparisons = {}
    for label in ("writer", "reference"):
        held, new = original["references"][label], fresh["references"][label]
        _rasters(
            held,
            new,
            reader,
            current_reader,
            run_id=original_launch.run_id,
            current_run_id=owner.run_id,
            original_directory=compile_directory / label,
            current_directory=directory / "compile" / label,
        )
        comparisons[label] = inspect_pdf_reference_parity(
            _file(held["pdf"], reader).content,
            _file(new["pdf"], current_reader).content,
            tuple(_file(row, reader).content for row in held["rasters"]),
            tuple(_file(row, current_reader).content for row in new["rasters"]),
            deadline=deadline,
        )
    owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
    operation.verify(reader)
    remaining(deadline)
    return {
        "schema_version": "template-native-tex-section-current-reference-v1",
        "scope": scope,
        "artifact_id": artifact.id,
        "original_run_id": original_launch.run_id,
        "current_run_id": owner.run_id,
        "current_reference": fresh_binding,
        "original_recorder_noninterference": original_parity,
        "current_recorder_noninterference": fresh_parity,
        "every_page_comparisons": comparisons,
        "blockers": list(RESIDUALS),
        "component_status": "fail"
        if any(item["findings"] for item in (original_parity, fresh_parity, *comparisons.values()))
        else "passed",
        "admission_status": "blocked",
    }
