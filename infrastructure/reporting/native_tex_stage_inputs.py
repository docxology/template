"""Reconstruct the Source-selected section compiler packet as DATA.

The enclosing genuine Stage owner authenticates the writer and actual ToolAPI.
This module grants no operation or tool authority and opens no Original paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.latex_utils import latex_compile_command
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact, native_artifact_contract
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.transmission.transmission_bookends import is_transmission_bookend
from infrastructure.validation.output.render_formats import render_config_manuscript_dir


def validate_tex_section_inputs(
    source: NativeSourceContext,
    value: dict[str, Any],
    reader: SnapshotReader,
    *,
    scope: str,
    original_root_label: Path,
) -> tuple[NativeArtifact, ArtifactSnapshot]:
    """Require the exact authored/consumed section, compiler command and cwd."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file

    if (
        value["writer"] != "latex"
        or value["crossref_filter"] is not None
        or value["loader_qualification"] is not None
        or len(value["source_inputs"]) != 1
        or len(value["render_inputs"]) != 1
        or len(value["tool_artifacts"]) != 1
    ):
        raise ValueError("section compiler packet differs from its fixed Source input/tool role")
    project = reader.root / "projects" / scope
    authored, consumed = resolve_source_manuscript_dir(project), render_config_manuscript_dir(project)
    selected = _file(value["render_inputs"][0], reader)
    path = reader.root / selected.relative
    sections = tuple(
        item
        for item in discover_manuscript_files(consumed)
        if item.suffix == ".tex" and not is_transmission_bookend(item)
    )
    if path not in sections:
        raise ValueError("section compiler input is absent from the complete Source-consumed TeX roster")
    relative = path.relative_to(consumed)
    original = _file(value["source_inputs"][0], reader)
    expected_authored = (authored / relative).relative_to(reader.root).as_posix()
    if original.relative != expected_authored or original.content != source.reference.read(expected_authored):
        raise ValueError("section compiler authored counterpart differs from independently held Source")
    artifact_id = "section:" + relative.as_posix() + ":pdf"
    expected_output = f"projects/{scope}/output/pdf/{path.stem}.pdf"
    artifacts = tuple(
        item for item in native_artifact_contract(reader.root, scope, ("pdf",), reader) if item.id == artifact_id
    )
    if len(artifacts) != 1 or artifacts[0].path != expected_output:
        raise ValueError("section compiler differs from its exact declared Source PDF artifact")
    config = reader.read((consumed / "config.yaml").relative_to(reader.root).as_posix())
    settings = yaml.safe_load(config.content)
    if not isinstance(settings, dict):
        raise ValueError("section consumed Source configuration is not a mapping")
    rendering = RenderingConfig.from_project_config(settings, env={})
    compiler = rendering.latex_compiler
    command = value["command"]
    tool = _file(value["tool_artifacts"][0], reader).json_object()
    process = _file(tool["native_process_artifact"], reader).json_object()
    nomination = process["nomination"]
    if (
        not rendering.enable_pdf
        or compiler not in {"xelatex", "lualatex", "pdflatex"}
        or not command
        or tool["tool"] != compiler
        or process["launcher_preserved"] is not True
        or nomination["tool"] != compiler
        or Path(nomination["path"]).name != compiler
        or command[0] != nomination["path"]
        or tool["command"] != command
    ):
        raise ValueError("section compiler is not the exact Source-selected direct PDF engine")
    tex_label = original_root_label / selected.relative
    expected = latex_compile_command(tex_label, original_root_label / Path(expected_output).parent, command[0])
    if command != expected or value["cwd"] != str(tex_label.parent):
        raise ValueError("section actual compiler argv or cwd differs from the shared Source command")
    return artifacts[0], selected
