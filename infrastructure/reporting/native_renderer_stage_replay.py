"""Read actual Original/Current combined renderers from one Core run each.

The caller supplies already-admitted Original and the already-live independent
Current producer. This module reconstructs inputs and shared Source commands;
it never executes Core, Common, a parser, a compiler or a renderer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from infrastructure.project.public_reference_git import remaining
from infrastructure.rendering._bibliography import (
    pandoc_bibliography_args,
    resolve_bibliography,
)
from infrastructure.rendering._web_markdown_preprocess import html_safe_markdown
from infrastructure.rendering._web_postprocess import MATHJAX_URL
from infrastructure.rendering.combined_native_commands import (
    html_combined_command,
    html_metadata_arguments,
    pdf_combined_command,
    pre_crossref_json_command,
)
from infrastructure.rendering.manuscript_hydration_replay import (
    combine_held_manuscripts,
)
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_hydration_reconstruction import (
    observe_native_pdf_recomposition,
    replay_native_pdf_recomposition,
)
from infrastructure.reporting.native_stage_child_custody import (
    NativeStageChildReaderOperation,
)
from infrastructure.reporting.native_stage_loader_replay import (
    replay_stage_loader_qualification,
    renderer_crossref_data,
    require_current_stage_reader,
)
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
)
from infrastructure.reporting.native_tool_replay import validate_original_native_tool
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)

_SCHEMA = "template-source-native-renderer-command-v1"
_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "scope",
        "writer",
        "source_binding",
        "owner_pid",
        "command",
        "cwd",
        "source_inputs",
        "render_inputs",
        "output",
        "tool_artifacts",
        "crossref_filter",
        "loader_qualification",
    }
)
_MODULES = (
    "reporting/native_renderer_source_call.py",
    "rendering/combined_native_commands.py",
)


def _binding(item: ArtifactSnapshot) -> dict[str, str]:
    return {"path": item.relative, "sha256": item.sha256}


def _one_renderer(
    binding: dict[str, str],
    reader: SnapshotReader,
    stage: NativeStageChildReaderOperation,
    hydration: dict[str, Any],
    pdf_body: bytes | None,
) -> dict[str, Any]:
    from infrastructure.core.project_paths import resolve_source_manuscript_dir
    from infrastructure.reporting.native_crossref_replay import (
        CrossrefFilterReaderOperation,
    )
    from infrastructure.reporting.native_crossref_pair import parent_launcher_binding
    from infrastructure.validation.output.render_formats import (
        render_config_manuscript_dir,
    )

    authority = stage.authenticate_artifact(binding, reader, run_id=stage.run_id, required_sdk_modules=_MODULES)
    raw = authority["event"].json_object()
    spec, source = authority["specification"], stage.source
    if (
        set(raw) != _FIELDS
        or raw["schema_version"] != _SCHEMA
        or raw["writer"] not in {"latex", "html"}
        or raw["run_id"] != stage.run_id
        or raw["scope"] != stage.scope
        or raw["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or raw["owner_pid"] != authority["process"]["pid"]
        or spec["pipeline_run_id"] != hydration["pipeline_run_id"]
        or not raw["tool_artifacts"]
    ):
        raise ValueError("renderer differs from its genuine Stage/Source/Core/writer role")
    project = reader.root / "projects" / stage.scope
    consumed = render_config_manuscript_dir(project)
    authored = resolve_source_manuscript_dir(project)
    original_root = Path(authority["source"]["current_mirror"]["root"])
    original_project = original_root / "projects" / stage.scope
    original_consumed = original_root / consumed.relative_to(reader.root)
    original_figures = original_project / "output/figures"
    sdk = Path(authority["source"]["selected_sdk"]["package_root"])
    writer = raw["writer"]
    combined_relative = f"projects/{stage.scope}/output/{'pdf' if writer == 'latex' else 'web'}/_combined_manuscript.md"
    combined = reader.read(combined_relative)
    rows = hydration["ordered_inputs"]
    bodies = tuple(_file({key: row["consumed"][key] for key in ("path", "sha256")}, reader).content for row in rows)
    expected_body = (
        pdf_body
        if writer == "latex"
        else html_safe_markdown(
            combine_held_manuscripts(bodies, separator="\n---\n\n").decode(),
            render_citations=False,
        ).encode()
    )
    if expected_body is None or combined.content != expected_body:
        raise ValueError("renderer combined input differs from genuine complete Source recomposition")
    configuration = _file({key: hydration["config"][key] for key in ("path", "sha256")}, reader)
    if configuration.relative != (consumed / "config.yaml").relative_to(reader.root).as_posix():
        raise ValueError("renderer config differs from its independently reconstructed consumed role")
    settings = yaml.safe_load(configuration.content)
    if settings is not None and not isinstance(settings, dict):
        raise ValueError("renderer Source config is not an admitted mapping")
    command = raw["command"]
    if not isinstance(command, list) or not command or command.count("-o") != 1:
        raise ValueError("renderer lacks one exact native output operand")
    if command.index("-o") + 1 >= len(command):
        raise ValueError("renderer native output operand is absent")
    output_label = Path(command[command.index("-o") + 1])
    if writer == "latex":
        if output_label != original_project / "output/pdf/_combined_manuscript.tex":
            raise ValueError("PDF renderer output is not its fixed Source-selected LaTeX role")
    elif (
        output_label.parent != original_project / "output/web"
        or re.fullmatch(r"\.index\.[0-9a-f]{24}\.html\.tmp", output_label.name) is None
    ):
        raise ValueError("HTML renderer output is not its genuine Source-exclusive temporary role")
    tools = []
    for tool_binding in raw["tool_artifacts"]:
        tool = _file(tool_binding, reader).json_object()
        validate_original_native_tool(
            tool_binding,
            tool,
            reader,
            run_id=stage.run_id,
            required_sdk_modules=_MODULES,
        )
        tools.append(tool)
    final_tool = tools[-1]
    if (
        final_tool["tool"] != "pandoc"
        or final_tool["purpose"] != "source-renderer"
        or final_tool["command"] != command
        or final_tool["cwd"] != raw["cwd"]
    ):
        raise ValueError("renderer command/CWD differs from the actual final retained Pandoc ToolAPI")
    if raw["cwd"] not in {str(original_root), str(original_project)}:
        raise ValueError("renderer CWD differs from its actual fixed Source stage role")
    crossref = None
    crossref_data = None
    qualification_binding = raw["loader_qualification"]
    parser_binding = None
    parser_ast = None
    residuals: list[str] = []
    if raw["crossref_filter"] is not None:
        _, parser_binding = renderer_crossref_data(raw, reader)
        role = CrossrefFilterReaderOperation.from_renderer_stage(binding, reader, stage)
        child_authority = role._child()
        leg = child_authority["renderer_parent_observation"]
        launcher = parent_launcher_binding(leg)
        crossref = str(original_root / launcher["path"])
        crossref_data = role.replay()
    formalism = sdk / "rendering/formalism.lua"
    lua_paths = [formalism]
    if writer == "latex":
        expected_command = pdf_combined_command(
            final_tool["executable"],
            original_root / combined.relative,
            output_label,
            original_consumed,
            original_figures,
            settings,
            ["--lua-filter", str(formalism)],
            crossref,
        )
        bibliographies: list[Path] = []
    else:
        lua_paths = [sdk / "rendering/convert_latex_images.lua", formalism]
        resources = [original_consumed]
        if (project / "output/figures").exists():
            resources.append(original_figures)
        bibliography_args = pandoc_bibliography_args(resolve_bibliography(consumed))
        bibliographies = [Path(value.removeprefix("--bibliography=")) for value in bibliography_args]
        expected_command = html_combined_command(
            final_tool["executable"],
            original_root / combined.relative,
            output_label,
            MATHJAX_URL,
            html_metadata_arguments(settings),
            resources,
            lua_paths,
            crossref,
            [original_root / path.relative_to(reader.root) for path in bibliographies],
        )
    if command != expected_command:
        raise ValueError("renderer native command differs from the independently reconstructed Source command")
    # Reconstruct insertion order used by the Source call: combined, complete
    # consumed roster, config, selected Lua operands and bibliography operands.
    render_inputs = [combined]
    source_inputs = []
    for row in rows:
        consumed_item = _file({key: row["consumed"][key] for key in ("path", "sha256")}, reader)
        render_inputs.append(consumed_item)
        authored_path = authored / (reader.root / consumed_item.relative).relative_to(consumed)
        source_item = reader.read(authored_path.relative_to(reader.root).as_posix())
        if source.reference.read(source_item.relative) != source_item.content:
            raise ValueError("renderer authored input differs from independently admitted Source")
        source_inputs.append(source_item)
    render_inputs.append(configuration)
    authored_config = reader.read((authored / "config.yaml").relative_to(reader.root).as_posix())
    if source.reference.read(authored_config.relative) != authored_config.content:
        raise ValueError("renderer authored config differs from independently admitted Source")
    source_inputs.append(authored_config)
    external = 0
    renderer_leaf = Path(binding["path"]).parent
    for path in lua_paths:
        member = path.relative_to(sdk).as_posix()
        selected_source = reader.read("infrastructure/" + member)
        if source.reference.read(selected_source.relative) != selected_source.content:
            raise ValueError("renderer selected Lua Source bytes differ from independently held Source")
        if path.is_relative_to(original_root):
            selected = reader.read(path.relative_to(original_root).as_posix())
        else:
            selected = reader.read((renderer_leaf / f"selected-sdk-asset-{external:02d}.lua").as_posix())
            external += 1
        if selected.content != selected_source.content:
            raise ValueError("renderer frozen actual installed Lua differs from the exact selected Source asset")
        render_inputs.append(selected)
        source_inputs.append(selected_source)
    for path in bibliographies:
        item = reader.read(path.relative_to(reader.root).as_posix())
        render_inputs.append(item)
        try:
            original = source.reference.read(item.relative)
        except ValueError:
            continue
        if original != item.content:
            raise ValueError("renderer selected Source bibliography differs from held Source")
        source_inputs.append(item)
    expected_inputs = list(dict.fromkeys(_binding(item)["path"] for item in render_inputs))
    expected_source = list(dict.fromkeys(_binding(item)["path"] for item in source_inputs))
    if raw["render_inputs"] != [_binding(reader.read(path)) for path in expected_inputs] or raw["source_inputs"] != [
        _binding(reader.read(path)) for path in expected_source
    ]:
        raise ValueError("renderer omitted/reordered/substituted the complete reconstructed Source/input cohort")
    if parser_binding is not None:
        parser = _file(parser_binding, reader).json_object()
        if (
            parser["purpose"] != "source-renderer-pre-crossref-parser"
            or parser["selected_inputs"] != raw["render_inputs"]
            or parser["stdin"] is not None
            or parser["crossref_filters"] is not None
            or parser["baseline_outputs"]
            or parser["observed_outputs"]
        ):
            raise ValueError("renderer parser replaced its complete selected input/output role")
        for key in ("baseline_tool", "observed_tool"):
            if parser[key] not in raw["tool_artifacts"]:
                raise ValueError("renderer parser tool is absent from the genuine Stage tool cohort")
            tool = _file(parser[key], reader).json_object()
            if (
                tool["command"] != pre_crossref_json_command(expected_command, writer)
                or tool["cwd"] != raw["cwd"]
                or tool["executable"] != final_tool["executable"]
                or tool["executable_sha256"] != final_tool["executable_sha256"]
            ):
                raise ValueError("renderer parser differs from the independently reconstructed Source/native command")
        observed_parser = _file(parser["observed_tool"], reader).json_object()
        parser_ast = {key: observed_parser["raw_stdout"][key] for key in ("path", "sha256")}
    output = _file(raw["output"], reader)
    qualifier = None
    if qualification_binding is not None:
        if crossref_data is not None:
            qualifier = crossref_data["parent_loader_qualification"]
            if qualifier != _file(qualification_binding, reader).json_object():
                raise ValueError("renderer parent pair readback differs from its exact retained binding")
        else:
            qualifier = replay_stage_loader_qualification(
                qualification_binding,
                reader,
                stage_owner=stage,
                renderer_binding=binding,
            )
        if (
            qualifier["observed_tool"] != raw["tool_artifacts"][-1]
            or qualifier["selected_inputs"] != raw["render_inputs"]
            or len(qualifier["observed_outputs"]) != 1
        ):
            raise ValueError("renderer qualifier changed its final actual tool/input/output cohort")
        selected_output = qualifier["observed_outputs"][0]
        if (
            selected_output["original_label"] != str(output_label)
            or _file(selected_output["artifact"], reader).content != output.content
        ):
            raise ValueError("renderer held output differs from the sole genuine qualified observed output")
    stage.verify(reader)
    if not reader.unchanged():
        raise ValueError("renderer complete retained input/output/command custody changed during readback")
    return {
        "stage_key": spec["stage_key"],
        "writer": writer,
        "renderer": binding,
        "combined": _binding(combined),
        "output": _binding(output),
        "source_inputs": raw["source_inputs"],
        "render_inputs": raw["render_inputs"],
        "loader_qualification": qualification_binding,
        "crossref": crossref_data,
        "pre_crossref_parser": parser_binding,
        "parser_ast": parser_ast,
        "unresolved_edges": residuals,
    }


def _scope_renderers(
    reader: SnapshotReader,
    stage: NativeStageChildReaderOperation,
    hydration: dict[str, Any],
    pdf_body: bytes | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    results = []
    sections = []
    mermaid_commands = []
    keys = set()
    for _, authority in stage._authenticated_descendants(reader):
        if authority["specification"]["pipeline_run_id"] != hydration["pipeline_run_id"]:
            raise ValueError("renderer stage belongs to a different actual complete Core execution")
        for binding in authority["event"].json_object()["stage_artifacts"]:
            packet = _file(binding, reader).json_object()
            if packet.get("schema_version") == "template-source-native-mermaid-production-command-v1":
                from infrastructure.reporting.native_mermaid_production_tool import (
                    replay_source_native_mermaid_command,
                )

                checked_mermaid = replay_source_native_mermaid_command(binding, reader, stage)
                mermaid_commands.append(
                    {
                        **checked_mermaid,
                        "unresolved_edges": list(checked_mermaid["remaining_admission"]),
                    }
                )
                continue
            if (
                packet["writer"] == "latex"
                and packet["crossref_filter"] is None
                and packet["loader_qualification"] is None
                and len(packet["source_inputs"]) == 1
                and len(packet["render_inputs"]) == 1
                and Path(packet["source_inputs"][0]["path"]).suffix == ".tex"
                and Path(packet["source_inputs"][0]["path"]).name == Path(packet["render_inputs"][0]["path"]).name
            ):
                # This is the exact Source collector's distinct section role.
                # Its complete TeX semantics remain the Root section reader's
                # obligation; combined-Pandoc replay cannot approve that role.
                stage.authenticate_artifact(
                    binding,
                    reader,
                    run_id=stage.run_id,
                    required_sdk_modules=(
                        "reporting/native_tex_section_render.py",
                        "reporting/native_pdf_citation_runtime.py",
                        "rendering/latex_utils.py",
                    ),
                )
                sections.append(binding)
                continue
            result = _one_renderer(binding, reader, stage, hydration, pdf_body)
            key = (result["stage_key"], result["writer"])
            if key in keys:
                raise ValueError("renderer graph repeats a fixed Source stage/writer role")
            keys.add(key)
            results.append(result)
    if {item["writer"] for item in results} != {"latex", "html"}:
        raise ValueError("complete Core lacks its actual Source combined PDF/HTML renderer stages")
    return results, sections, mermaid_commands


def replay_native_renderer_stages(
    scope: str,
    native_execution: ArtifactSnapshot,
    original_reader: SnapshotReader,
    current_pipeline: ArtifactSnapshot,
    current_reader: SnapshotReader,
) -> tuple[
    dict[str, Any],
    NativeStageChildReaderOperation,
    NativeStageChildReaderOperation,
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    """Read both existing Core runs while Current custody is still live."""
    operation = require_native_operation(original_reader)
    original = operation.originals.get(scope)
    owner = current_native_producer_operation()
    if (
        original is None
        or owner is None
        or current_reader.native_producer_operation is not owner
        or owner.run_id == original.run_id
        or owner.deadline != operation.deadline
        or owner.source.reference.commit != operation.source.reference.commit
        or owner.source.reference.source_identity != operation.source.reference.source_identity
        or current_reader.root == original_reader.root
        or current_reader.root.is_relative_to(original_reader.root)
        or original_reader.root.is_relative_to(current_reader.root)
        or owner.source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or owner.source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or native_execution.relative != original.native_execution_relative
        or native_execution.sha256 != original.native_execution_sha256
        or original_reader.read(native_execution.relative) != native_execution
        or current_reader.read(current_pipeline.relative) != current_pipeline
        or current_pipeline.path != owner.stage_scope_directory(scope) / "current-analysis/pipeline.json"
    ):
        raise ValueError("renderer readback needs actual external Original and the same existing live Current Core")
    owner.verify(current_reader, run_id=owner.run_id, deadline=operation.deadline)
    current = current_pipeline.json_object()
    if (
        set(current)
        != {
            "mode",
            "run_id",
            "plan",
            "plan_digest",
            "expected_stage_keys",
            "outcomes",
            "execution_exit_code",
            "deadline_monotonic",
            "stage_children",
            "tool_artifacts",
            "published_source_audit_artifact",
        }
        or current["mode"] != "core"
        or current["execution_exit_code"] != 0
        or current["deadline_monotonic"] != operation.deadline
        or current["plan"]["project"] != scope
        or current["stage_children"] != list(owner.stage_children)
        or current["tool_artifacts"] != list(owner.retained_tool_bindings)[: len(current["tool_artifacts"])]
        or [item["stage_key"] for item in current["outcomes"]] != current["expected_stage_keys"]
        or any(item["status"] != "succeeded" or item["child_exit_code"] != 0 for item in current["outcomes"])
    ):
        raise ValueError("renderer Current pipeline differs from the actual completed Core/closed stage roster")
    from infrastructure.validation.publication.audit import build_native_published_audit

    published = build_native_published_audit(owner.source, scope, current_reader, deadline=operation.deadline)
    if _file(current["published_source_audit_artifact"], current_reader).json_object() != published.to_dict():
        raise ValueError("Current pre-Core published audit differs from independent pristine Source evidence")
    old_raw = native_execution.json_object()
    old_hydration, old_pdf = replay_native_pdf_recomposition(scope, native_execution, original_reader)
    new_hydration, new_pdf = observe_native_pdf_recomposition(
        owner.source,
        scope,
        current["run_id"],
        current["plan_digest"],
        current_reader,
        deadline=operation.deadline,
    )
    old_stage = NativeStageChildReaderOperation(
        operation.source,
        original_reader,
        old_raw["stage_children"],
        scope=scope,
        run_id=original.run_id,
        deadline=operation.deadline,
    )
    new_stage = NativeStageChildReaderOperation(
        owner.source,
        current_reader,
        list(owner.stage_children),
        scope=scope,
        run_id=owner.run_id,
        deadline=operation.deadline,
    )
    old_stage_reader = SnapshotReader(
        original_reader.root,
        native_operation=operation,
        native_control_operation=old_stage,
    )
    new_stage_reader = SnapshotReader(
        current_reader.root,
        native_producer_operation=owner,
        native_control_operation=new_stage,
    )
    require_current_stage_reader(new_stage_reader, new_stage)
    old, old_sections, old_mermaid = _scope_renderers(old_stage_reader, old_stage, old_hydration, old_pdf)
    new, new_sections, new_mermaid = _scope_renderers(new_stage_reader, new_stage, new_hydration, new_pdf)
    if len(old_sections) != len(new_sections):
        raise ValueError("Original/Current changed their distinct actual Source TeX section roster")
    if [(item["stage_key"], item["writer"]) for item in old] != [(item["stage_key"], item["writer"]) for item in new]:
        raise ValueError("Original/Current omitted/reordered actual Source renderer roles")
    for left, right in zip(old, new, strict=True):
        if left["source_inputs"] != right["source_inputs"]:
            raise ValueError("Original/Current changed their complete independently held Source input cohort")
        if (
            _file(left["combined"], old_stage_reader).content != _file(right["combined"], new_stage_reader).content
            or _file(left["output"], old_stage_reader).content != _file(right["output"], new_stage_reader).content
        ):
            raise ValueError("independent Current renderer changed complete Source composition/native output bytes")
        old_inputs = [_file(value, old_stage_reader).content for value in left["render_inputs"]]
        new_inputs = [_file(value, new_stage_reader).content for value in right["render_inputs"]]
        if old_inputs != new_inputs:
            raise ValueError("independent Current renderer changed its complete reconstructed consumed input bytes")
        if (left["parser_ast"] is None) != (right["parser_ast"] is None):
            raise ValueError("Original/Current changed their Source-selected parser/filter role")
        if left["parser_ast"] is not None:
            from infrastructure.reporting.native_crossref_worker import filter_json

            if filter_json(_file(left["parser_ast"], old_stage_reader).content) != filter_json(
                _file(right["parser_ast"], new_stage_reader).content
            ):
                raise ValueError("independent Current parser changed the complete Source-selected AST")
    operation.verify(original_reader)
    owner.verify(current_reader, run_id=owner.run_id, deadline=operation.deadline)
    remaining(operation.deadline)
    data = {
        "schema_version": "template-native-renderer-stage-replay-v2",
        "scope": scope,
        "original": old,
        "current": new,
        "section_packets": {"original": old_sections, "current": new_sections},
        "mermaid_commands": {"original": old_mermaid, "current": new_mermaid},
        "unresolved_edges": list(
            dict.fromkeys(edge for row in (*old, *new, *old_mermaid, *new_mermaid) for edge in row["unresolved_edges"])
        ),
    }
    return data, old_stage, new_stage, tuple(old_sections), tuple(new_sections)
