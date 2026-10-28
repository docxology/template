"""Actual original/current Pandoc adapters for a Source-selected crossref child."""

from __future__ import annotations

import os
import platform
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_filter import (
    prepare_source_crossref_filter,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_loader_build import CompiledNativeLoader


def source_crossref_pandoc(
    runtime: CitationRuntime,
    scope: str,
    arguments: list[str],
    purpose: str,
    *,
    output_format: str,
    input_paths: tuple[Path, ...] = (),
    cwd: Path | None = None,
    output_paths: tuple[Path, ...] = (),
    compiled: CompiledNativeLoader | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Replace the one Source-selected --filter operand before actual Popen."""
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != runtime.run_id or owner.deadline != runtime.deadline:
        raise ValueError(
            "crossref Pandoc adapter requires its genuine current Source/SDK producer and same original clock"
        )
    reader = SnapshotReader(runtime.root, native_producer_operation=owner)
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    indices = [index for index, value in enumerate(arguments) if value == "--filter"]
    if len(indices) != 1 or indices[0] + 1 >= len(arguments):
        raise ValueError("crossref Pandoc adapter requires one exact Source-owned filter argv operand")
    index = indices[0] + 1
    if Path(arguments[index]).name != "pandoc-crossref":
        raise ValueError("crossref Pandoc adapter cannot replace another selected filter")
    nominated = shutil.which(arguments[index], path=runtime.env.get("PATH"))
    if nominated is None:
        raise ValueError("crossref Source argv lacks its independently selected physical executable")
    crossref_body = file_observation(Path(nominated).resolve(strict=True))
    if platform.system() == "Linux":
        from infrastructure.project.public_acceptance_evidence import write_json
        from infrastructure.reporting.native_crossref_pair import PARENT_SCHEMA, prepare_source_crossref_pair
        from infrastructure.reporting.native_loader_build import CompiledNativeLoader, SOURCE, compile_native_loader
        from infrastructure.reporting.native_loader_qualification import qualify_native_loader_tool

        if compiled is None:
            compiler = CitationRuntime(
                runtime.root,
                runtime.directory / ("source-loader-build-" + purpose),
                env=runtime.env,
                deadline=runtime.deadline,
                run_id=runtime.run_id,
            )
            compiled = compile_native_loader(compiler)
            runtime.tools.extend(compiler.tools)
        else:
            if type(compiled) is not CompiledNativeLoader or compiled.owner is not owner:
                raise ValueError("Crossref parser/parent reuse needs the same genuine Source compiler owner")
            compiled.verify(deadline=runtime.deadline)
            held = reader.read(compiled.binding["path"])
            payload = held.json_object()
            source = owner.source.current_source_reader.read(SOURCE)
            if (
                held.sha256 != compiled.binding["sha256"]
                or payload["schema_version"] != "template-source-native-loader-compilation-v1"
                or payload["run_id"] != runtime.run_id
                or payload["source_binding"] != [owner.source.reference.commit, owner.source.reference.source_identity]
                or payload["source"] != {"path": SOURCE, "sha256": source.sha256}
                or source.content != owner.source.reference.read(SOURCE)
                or payload["library"]
                != {
                    "path": compiled.library.relative_to(runtime.root).as_posix(),
                    "sha256": compiled.observation["sha256"],
                }
                or payload["library_identity"] != compiled.identity
                or payload["platform"] != platform.system()
                or payload["architecture"] != platform.machine()
            ):
                raise ValueError("Crossref parser/parent compiler reuse changed actual Source/run/body/host custody")
            for key, role in (
                ("compiler_header_selection", "loader-header-selection"),
                ("compiler", "loader-source-compilation"),
            ):
                tool = reader.read(payload[key]["path"]).json_object()
                owner.validate_tool(payload[key], tool, reader, run_id=runtime.run_id)
                if tool["tool"] != "cc" or tool["purpose"] != role or tool["original_exit_code"] != 0:
                    raise ValueError("Crossref parser/parent reuse omitted the genuine successful compiler ToolAPI")
        pair_deadline = min(runtime.deadline, time.monotonic() + 120.0)
        with prepare_source_crossref_pair(
            runtime.root,
            runtime.directory / ("source-filter-pair-" + purpose),
            scope,
            reader,
            env=runtime.env,
            deadline=pair_deadline,
            output_format=output_format,
            compiled=compiled,
            purpose=purpose,
        ) as pair:
            for item in pair.filters:
                specification = reader.read(item.declaration["path"]).json_object()
                if specification["crossref"] != crossref_body:
                    raise ValueError("paired crossref nomination differs from its Source-selected argv body")
            argv = list(arguments)
            argv[index] = str(runtime.root / pair.launcher["path"])
            before_env = runtime.env
            try:
                runtime.env = pair.environment
                result, qualification, _ = qualify_native_loader_tool(
                    runtime,
                    "pandoc",
                    argv,
                    purpose,
                    input_paths=tuple(dict.fromkeys((*input_paths, *runtime.inputs))),
                    output_paths=output_paths,
                    cwd=cwd,
                    compiled=compiled,
                    crossref_pair=pair,
                )
            finally:
                runtime.env = before_env
            binding = write_json(
                runtime.root,
                runtime.directory / (purpose + ".crossref-pair.json"),
                {
                    "schema_version": PARENT_SCHEMA,
                    "scope": scope,
                    "run_id": runtime.run_id,
                    "filter": pair.completed[1],
                    "parent_loader_qualification": qualification,
                },
            )
            if not reader.unchanged():
                raise ValueError("paired crossref original Source/filter/input evidence changed")
            remaining(runtime.deadline)
            return result, binding
    if compiled is not None:
        raise ValueError("Source compiler reuse requires the actual supported Linux parent path")
    deadline = min(runtime.deadline, time.monotonic() + 120.0)
    leaf = runtime.directory / ("source-filter-" + purpose)
    with prepare_source_crossref_filter(
        runtime.root,
        leaf,
        scope,
        reader,
        env=runtime.env,
        deadline=deadline,
        output_format=output_format,
    ) as original:
        specification = reader.read(original.declaration["path"]).json_object()
        if specification["crossref"] != crossref_body:
            raise ValueError("crossref wrapper nomination differs from its original Source-selected argv body")
        argv = list(arguments)
        argv[index] = str(runtime.root / original.launcher["path"])
        before_env = runtime.env
        try:
            runtime.env = original.environment
            result = runtime.tool(
                "pandoc",
                argv,
                purpose,
                input_paths=tuple(dict.fromkeys((*input_paths, *runtime.inputs))),
                while_live=original.observe,
                cwd=cwd,
                phase_deadline=deadline,
            )
        finally:
            runtime.env = before_env
        binding = original.finish(runtime.tools[-1])
        if not reader.unchanged():
            raise ValueError("actual crossref Pandoc original input/filter/Source evidence changed")
        remaining(runtime.deadline)
        return result, binding


def reproduce_crossref_filter(
    root: Path,
    scope: str,
    original_binding: dict[str, str],
    reader: SnapshotReader,
    current_ast: bytes,
    *,
    original_run_id: str,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Authenticate original child, then execute an independently nominated one.

    current_ast must come from the enclosing independently reparsed complete
    Source occurrence adapter. This component neither approves generated values
    nor authenticates loaded Crossref native libraries.
    """
    from uuid import uuid4
    from infrastructure.reporting.native_crossref_replay import (
        CrossrefFilterReaderOperation,
    )
    from infrastructure.reporting.native_crossref_worker import filter_json
    from infrastructure.reporting.native_format_joint_source import (
        require_native_operation,
    )
    from infrastructure.reporting.native_format_acceptance_evidence import _file

    operation = require_native_operation(reader)
    if deadline != operation.deadline:
        raise ValueError("crossref current replay cannot replace its genuine original operation clock")
    admitted = CrossrefFilterReaderOperation(
        operation.source,
        original_binding,
        reader,
        scope=scope,
        run_id=original_run_id,
        deadline=deadline,
    ).replay()
    original_input = _file(admitted["input"], reader)
    original_output = _file(admitted["output"], reader)
    if filter_json(current_ast) != filter_json(original_input.content):
        raise ValueError(
            "crossref original filter input differs from independently reparsed complete current Source AST"
        )
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source is not operation.source
        or owner.owner_pid != os.getpid()
        or owner.deadline != deadline
    ):
        raise ValueError("crossref current parser requires the actual independently admitted current Source owner")
    leaf = root / "output/readiness/current-native-readers" / owner.run_id / ("crossref-" + uuid4().hex)
    runtime = CitationRuntime(root, leaf, env=env, deadline=deadline, run_id=owner.run_id)
    source = runtime.freeze("independent-source.json", current_ast)
    _, binding = source_crossref_pandoc(
        runtime,
        scope,
        [
            str(source),
            "--from=json",
            "--to=" + admitted["output_format"],
            "--filter",
            "pandoc-crossref",
        ],
        "current-crossref-json",
        output_format=admitted["output_format"],
    )
    from infrastructure.reporting.native_crossref_pair import parent_observation

    current_parent = parent_observation(binding, reader)
    current_child = _file(current_parent["observation"], reader).json_object()
    current_output = _file(current_child["output"], reader)
    if filter_json(current_output.content) != filter_json(original_output.content):
        raise ValueError("current independently executed crossref output differs from original admitted JSON")
    operation.verify(reader)
    remaining(deadline)
    blockers = list(dict.fromkeys((*admitted["blockers"], *current_child["blockers"])))
    return {
        "schema_version": "template-source-crossref-reproduction-v1",
        "original_run_id": original_run_id,
        "current_run_id": owner.run_id,
        "reader_filter": binding,
        "blockers": blockers,
        "status": "blocked" if blockers else "passed",
    }
