"""Retain the actual combined PDF/HTML Pandoc command under the fixed stage owner.

This edge authenticates Source-selected command consumption. Scientific truth,
complete output semantics and loader qualification are separate obligations.
"""

from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.combined_native_commands import RENDERER_CROSSREF_SCHEMA, pre_crossref_json_command
from infrastructure.reporting.native_crossref_pandoc import source_crossref_pandoc
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_tool_process import _physical_identity
from infrastructure.reporting.native_stage_child import current_native_stage_directory, retain_native_stage_artifact
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.validation.output.render_formats import render_config_manuscript_dir

_SCHEMA = "template-source-native-renderer-command-v1"
_ORIGIN_KEYS = (
    "TEMPLATE_PUBLIC_REFERENCE_ROOT",
    "TEMPLATE_PUBLIC_REFERENCE_COMMIT",
    "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT",
)


def _binding(item: ArtifactSnapshot) -> dict[str, str]:
    return {"path": item.relative, "sha256": item.sha256}


def _selected_files(command: list[str], cwd: Path) -> tuple[Path, ...]:
    """Select only exact file operands from the actual Source-built argv."""
    selected: list[Path] = []
    file_options = {"--lua-filter", "--bibliography", "--metadata-file", "--template", "--reference-doc"}
    for index, operand in enumerate(command[1:], 1):
        for option in file_options:
            name = operand[len(option) + 1 :] if operand.startswith(option + "=") else None
            if operand == option:
                if index + 1 >= len(command):
                    raise ValueError("native renderer Source file option lacks its actual operand")
                name = command[index + 1]
            if name is not None:
                path = Path(name)
                selected.append((path if path.is_absolute() else cwd / path).absolute())
    return tuple(dict.fromkeys(selected))


def run_source_native_pandoc(
    command: list[str],
    combined: Path,
    source_files: list[Path],
    *,
    writer: str,
    environment: dict[str, str] | None = None,
) -> bool:
    """Use actual child custody when present; ordinary calls retain their path.

    The origin environment is only a refusal guard. Neither it nor the child
    directory creates an owner, admits Source, or approves retained artifacts.
    """
    owner = current_native_producer_operation()
    if owner is None:
        if any(os.environ.get(key) for key in _ORIGIN_KEYS):
            raise ValueError("native-origin rendering lacks its actual independently admitted Source owner")
        return False
    directory = current_native_stage_directory()
    if directory is None:
        raise ValueError("native core rendering requires the actual fixed Source-admitted stage child")
    root = owner.source.bindings.current_root
    reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    combined = combined.absolute()
    parts = combined.relative_to(root).parts
    if len(parts) < 5 or parts[0] != "projects":
        raise ValueError("native renderer input lacks an actual public project location")
    scope = "/".join(parts[1:3])
    if scope not in PUBLIC_PROJECT_NAMES or writer not in {"latex", "html"} or not source_files:
        raise ValueError("native renderer requires the complete Source-selected public writer roster")
    cwd = Path.cwd().absolute()
    if cwd not in {root, root / "projects" / scope} or cwd != cwd.resolve(strict=True):
        raise ValueError("native renderer current cwd differs from its actual Source stage directory")
    if command.count("-o") != 1 or command.index("-o") + 1 >= len(command):
        raise ValueError("native renderer requires one exact actual output operand")
    output = Path(command[command.index("-o") + 1]).absolute()
    if not output.is_relative_to(root / "projects" / scope / "output"):
        raise ValueError("native renderer output escapes its actual project output tree")
    if len(command) < 2 or Path(command[1]).absolute() != combined:
        raise ValueError("native renderer command differs from its actual combined input")
    env = dict(os.environ) if environment is None else dict(environment)
    nominated = shutil.which(command[0], path=env.get("PATH"))
    if nominated is None:
        raise ValueError("native renderer lacks its Source-selected physical Pandoc executable")
    selected_command = [str(Path(nominated).resolve(strict=True)), *command[1:]]
    tool_nomination = shutil.which("pandoc", path=env.get("PATH"))
    if tool_nomination is None or Path(tool_nomination).resolve(strict=True) != Path(selected_command[0]):
        raise ValueError("native renderer Pandoc role differs from its exact actual Source-selected executable")
    project = root / "projects" / scope
    authored_root = resolve_source_manuscript_dir(project)
    consumed_root = render_config_manuscript_dir(project)
    source_inputs: dict[str, ArtifactSnapshot] = {}
    render_inputs: dict[str, ArtifactSnapshot] = {}

    def hold(path: Path) -> ArtifactSnapshot:
        remaining(owner.deadline)
        return reader.read(path.absolute().relative_to(root).as_posix())

    render_inputs[combined.as_posix()] = hold(combined)
    for path in source_files:
        item = hold(path)
        render_inputs[item.relative] = item
        authored = authored_root / path.absolute().relative_to(consumed_root)
        original = hold(authored)
        if original.content != owner.source.reference.read(original.relative):
            raise ValueError("native renderer authored input differs from independently held Source")
        source_inputs[original.relative] = original
    consumed_config = consumed_root / "config.yaml"
    if consumed_config.is_file():
        item = hold(consumed_config)
        render_inputs[item.relative] = item
    config = authored_root / "config.yaml"
    if config.is_file():
        original = hold(config)
        if original.content != owner.source.reference.read(original.relative):
            raise ValueError("native renderer original config differs from independently held Source")
        source_inputs[original.relative] = original
    leaf = directory / ("renderer-" + writer + "-" + secrets.token_hex(12))
    runtime = CitationRuntime(root, leaf, env=env, deadline=owner.deadline, run_id=owner.run_id)
    sdk_inputs: list[tuple[Path, dict[str, Any], dict[str, int]]] = []
    for path in _selected_files(command, cwd):
        if not path.is_relative_to(root):
            sdk_root = owner.source.bindings.selected_sdk_package_root
            if path != path.resolve(strict=True) or not path.is_relative_to(sdk_root):
                raise ValueError("native renderer external operand is outside its actual selected SDK")
            sdk_member = path.relative_to(sdk_root).as_posix()
            if sdk_member not in {"rendering/formalism.lua", "rendering/convert_latex_images.lua"}:
                raise ValueError("native renderer external operand is not a fixed Source Lua asset")
            original = hold(root / "infrastructure" / sdk_member)
            if original.content != owner.source.reference.read(original.relative):
                raise ValueError("native renderer SDK Lua Source member differs from independently held original")
            observed, identity = file_observation(path), _physical_identity(path)
            content = read_bytes_confined(sdk_root, path, max_bytes=8 * 1024 * 1024)
            if (
                content != original.content
                or observed != file_observation(path)
                or identity != _physical_identity(path)
            ):
                raise ValueError("native renderer actual installed Lua bytes/identity differ from exact Source")
            owned = runtime.freeze(f"selected-sdk-asset-{len(sdk_inputs):02d}.lua", content)
            item = hold(owned)
            sdk_inputs.append((path, observed, identity))
            render_inputs[item.relative] = item
            source_inputs[original.relative] = original
            continue
        item = hold(path)
        render_inputs[item.relative] = item
        try:
            authored_content = owner.source.reference.read(item.relative)
        except ValueError:
            continue  # Generated bibliography/config remains an explicit render input.
        if item.content != authored_content:
            raise ValueError("native renderer selected Source filter/config/bibliography changed")
        source_inputs[item.relative] = item
    filters = [index for index, value in enumerate(command) if value == "--filter"]
    filter_binding: dict[str, str] | None = None
    loader_qualification: dict[str, str] | None = None
    input_paths = tuple(item.path for item in render_inputs.values())
    if filters:
        from infrastructure.reporting.native_crossref_worker import filter_json
        from infrastructure.reporting.native_loader_build import compile_native_loader
        from infrastructure.reporting.native_loader_qualification import qualify_native_loader_tool

        compiler = CitationRuntime(
            root,
            leaf / "source-renderer-loader-build",
            env=env,
            deadline=owner.deadline,
            run_id=owner.run_id,
        )
        compiled = compile_native_loader(compiler)
        runtime.tools.extend(compiler.tools)
        parser_runtime = CitationRuntime(
            root,
            leaf / "pre-crossref-parser",
            env=env,
            deadline=owner.deadline,
            run_id=owner.run_id,
        )
        parser_result, parser_qualification, _ = qualify_native_loader_tool(
            parser_runtime,
            "pandoc",
            pre_crossref_json_command(selected_command, writer)[1:],
            "source-renderer-pre-crossref-parser",
            input_paths=input_paths,
            cwd=cwd,
            compiled=compiled,
        )
        runtime.tools.extend(parser_runtime.tools)
        parser_output = reader.read(parser_result["raw_stdout"]["path"])
        if parser_output.sha256 != parser_result["raw_stdout"]["sha256"]:
            raise ValueError("Source renderer parser changed its complete actual stdout")
        parser_ast = filter_json(parser_output.content)
        tool_result, filter_binding = source_crossref_pandoc(
            runtime,
            scope,
            command[1:],
            "source-renderer",
            output_format=writer,
            input_paths=input_paths,
            cwd=cwd,
            output_paths=(output,),
            compiled=compiled,
        )
        from infrastructure.reporting.native_crossref_pair import PARENT_SCHEMA

        parent = reader.read(filter_binding["path"]).json_object()
        if parent.get("schema_version") != PARENT_SCHEMA:
            raise ValueError("Source renderer parser requires its genuine two-leg filtered parent")
        loader_qualification = parent["parent_loader_qualification"]
        pair = reader.read(loader_qualification["path"]).json_object()
        for leg_binding in pair["crossref_filters"]:
            leg = reader.read(leg_binding["path"]).json_object()
            child = reader.read(leg["observation"]["path"]).json_object()
            if filter_json(reader.read(child["input"]["path"]).content) != parser_ast:
                raise ValueError(
                    "Source renderer parser differs from an actual complete selected-writer Crossref input"
                )
        filter_binding = write_json(
            root,
            leaf / "renderer-crossref-parser.json",
            {
                "schema_version": RENDERER_CROSSREF_SCHEMA,
                "parent": filter_binding,
                "pre_crossref_parser": parser_qualification,
            },
        )
    else:
        from infrastructure.reporting.native_loader_qualification import qualify_native_loader_tool

        tool_result, loader_qualification, _ = qualify_native_loader_tool(
            runtime,
            "pandoc",
            selected_command[1:],
            "source-renderer",
            input_paths=input_paths,
            output_paths=(output,),
            cwd=cwd,
        )
    for path, observed, identity in sdk_inputs:
        remaining(owner.deadline)
        if observed != file_observation(path) or identity != _physical_identity(path):
            raise ValueError("native renderer actually consumed installed Lua changed during Pandoc execution")
    held_output = hold(output)
    frozen_output = runtime.freeze("rendered-output.input", held_output.content)
    output_snapshot = hold(frozen_output)
    if held_output.sha256 != output_snapshot.sha256 or not reader.unchanged():
        raise ValueError("native renderer output/input changed before actual stage retention")
    tools = list(runtime.tools)
    value: dict[str, Any] = {
        "schema_version": _SCHEMA,
        "run_id": owner.run_id,
        "scope": scope,
        "writer": writer,
        "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
        "owner_pid": owner.owner_pid,
        "command": tool_result["command"],
        "cwd": str(cwd),
        "source_inputs": [_binding(item) for item in source_inputs.values()],
        "render_inputs": [_binding(item) for item in render_inputs.values()],
        "output": _binding(output_snapshot),
        "tool_artifacts": tools,
        "crossref_filter": filter_binding,
        "loader_qualification": loader_qualification,
    }
    packet = write_json(root, leaf / "renderer.json", value)
    retain_native_stage_artifact(reader.read(packet["path"]), tool_artifacts=tools)
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    remaining(owner.deadline)
    return True
