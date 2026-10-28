"""Read complete Source-selected section rosters under actual paired Stage roles.

This helper executes no compiler and creates no Source/Stage authority. The
returned DATA retains semantic and consuming-use residuals; actual typed roles
stay in the caller's in-memory tuple from the existing renderer replay.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_format_acceptance_contracts import CITATION_TOOL_FIELDS, TOOL_SCHEMA
from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
from infrastructure.reporting.native_tex_section_reference import RESIDUALS
from infrastructure.reporting.native_tex_stage_inputs import validate_tex_section_inputs
from infrastructure.reporting.native_tool_replay import validate_original_native_tool
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.transmission.transmission_bookends import is_transmission_bookend
from infrastructure.validation.output.render_formats import render_config_manuscript_dir

type RendererScopeReplay = tuple[
    dict[str, Any],
    NativeStageChildReaderOperation,
    NativeStageChildReaderOperation,
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]

_MODULES = (
    "reporting/native_tex_section_render.py",
    "reporting/native_pdf_citation_runtime.py",
    "rendering/latex_utils.py",
)


def _sections(
    scope: str,
    bindings: tuple[dict[str, str], ...],
    stage: NativeStageChildReaderOperation,
    reader: SnapshotReader,
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    stage.verify(reader)
    if reader.native_control_operation is not stage or stage.scope != scope:
        raise ValueError("section roster requires this actual paired Source/Stage reader")
    consumed = render_config_manuscript_dir(reader.root / "projects" / scope)
    selected = tuple(
        path.relative_to(consumed).as_posix()
        for path in discover_manuscript_files(consumed)
        if path.suffix == ".tex" and not is_transmission_bookend(path)
    )
    expected = tuple("section:" + name + ":pdf" for name in selected)
    rows = []
    observed: list[str] = []
    seen_bindings = set()
    for binding in bindings:
        remaining(stage.deadline)
        if binding["path"] in seen_bindings:
            raise ValueError("section roster repeats an actual retained compiler packet")
        seen_bindings.add(binding["path"])
        authority = stage.authenticate_artifact(binding, reader, run_id=stage.run_id, required_sdk_modules=_MODULES)
        packet = authority["event"].json_object()
        for tool_binding in packet["tool_artifacts"]:
            tool = _file(tool_binding, reader).json_object()
            validate_original_native_tool(
                tool_binding,
                tool,
                reader,
                run_id=stage.run_id,
                required_sdk_modules=(*_MODULES, "reporting/native_tool_process.py"),
            )
            if (
                frozenset(tool) != CITATION_TOOL_FIELDS
                or tool["schema_version"] != TOOL_SCHEMA
                or tool["run_id"] != stage.run_id
                or tool["purpose"] != "source-section-compile"
                or tool["command"] != packet["command"]
                or tool["cwd"] != packet["cwd"]
                or type(tool["exit_code"]) is not int
                or tool["exit_code"] != 0
                or type(tool["original_exit_code"]) is not int
                or tool["original_exit_code"] != 0
                or tool["timed_out"] is not False
                or tool["custody_refused"] is not False
                or tool["diagnostic"] != ""
                or tool["caller_deadline_monotonic"] != stage.deadline
            ):
                raise ValueError("section compiler ToolAPI changed its exact actual Source/run/OS/command/clock")
        artifact, tex = validate_tex_section_inputs(
            stage.source,
            packet,
            reader,
            scope=scope,
            original_root_label=Path(authority["source"]["current_mirror"]["root"]),
        )
        tool = _file(packet["tool_artifacts"][0], reader).json_object()
        tex_label = Path(authority["source"]["current_mirror"]["root"]) / tex.relative
        observed_input = {
            "path": str(tex_label),
            "name": tex_label.name,
            "sha256": tex.sha256,
            "bytes": len(tex.content),
        }
        copies = tool["consumed_input_artifacts"]
        if (
            not isinstance(copies, list)
            or len(copies) != 1
            or set(copies[0]) != {"observation", "artifact"}
            or copies[0]["observation"] != observed_input
        ):
            raise ValueError("section actual compiler omitted its exact consumed TeX copy binding")
        copy = _file(copies[0]["artifact"], reader)
        copy_label = Path(authority["source"]["current_mirror"]["root"]) / copy.relative
        observed_copy = {
            "path": str(copy_label),
            "name": copy_label.name,
            "sha256": copy.sha256,
            "bytes": len(copy.content),
        }
        if (
            tool["input_observations_before"] != [observed_copy, observed_input]
            or tool["input_observations_after"] != [observed_copy, observed_input]
            or copy.content != tex.content
        ):
            raise ValueError("section actual compiler changed its complete ordered copy and Source TeX input census")
        if artifact.id not in expected:
            raise ValueError("section roster contains an undeclared Source compiler target")
        if not observed or observed[-1] != artifact.id:
            observed.append(artifact.id)
        rows.append(
            {
                "artifact_id": artifact.id,
                "renderer": binding,
                "tex_input": {"path": tex.relative, "sha256": tex.sha256},
                "authored_input": packet["source_inputs"][0],
                "output": packet["output"],
                "tool_artifacts": packet["tool_artifacts"],
            }
        )
        _file(packet["output"], reader)
    if tuple(observed) != expected:
        raise ValueError("actual section compiler roster omitted, reordered or repeated a declared Source section")
    stage.verify(reader)
    if not reader.unchanged():
        raise ValueError("complete section Source/retained compiler roster changed during readback")
    return rows, expected


def validate_renderer_section_rosters(
    scope: str,
    replay: RendererScopeReplay,
    original_reader: SnapshotReader,
    current_reader: SnapshotReader,
) -> dict[str, Any]:
    """Authenticate both complete existing Core rosters without another writer."""
    data, old_stage, new_stage, old_sections, new_sections = replay
    if data["scope"] != scope or old_stage.deadline != new_stage.deadline or old_stage.run_id == new_stage.run_id:
        raise ValueError("paired section roster changed its existing scope/run/original clock")
    old, old_expected = _sections(scope, old_sections, old_stage, original_reader)
    new, new_expected = _sections(scope, new_sections, new_stage, current_reader)
    if old_expected != new_expected or len(old) != len(new):
        raise ValueError("Original/Current changed their full Source-selected section/pass roster")
    for before, after in zip(old, new, strict=True):
        if before["artifact_id"] != after["artifact_id"] or before["authored_input"] != after["authored_input"]:
            raise ValueError("Original/Current changed the actual Source-selected section order/input")
        if _file(before["tex_input"], original_reader).content != _file(after["tex_input"], current_reader).content:
            raise ValueError("Original/Current changed the complete consumed section TeX bytes")
    remaining(old_stage.deadline)
    return {
        "schema_version": "template-native-renderer-section-roster-v1",
        "scope": scope,
        "original": old,
        "current": new,
        "remaining": list(RESIDUALS) if old_expected else [],
        "observation_status": "observed",
        "admission_status": "blocked" if old_expected else "not-applicable",
    }
