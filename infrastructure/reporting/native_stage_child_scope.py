"""Actual fixed child scope for Source renderer records; no directory authority."""

from __future__ import annotations

import inspect
import json
import os
import sys
import types
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.native_stage_child_contracts import (
    binding,
    validate_specification,
)
from infrastructure.reporting.native_tool_producer import (
    NativeProducerOperation,
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)

RENDERER_SCHEMA = "template-source-native-renderer-command-v1"
RENDERER_FIELDS = frozenset(
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


@dataclass
class _StageScope:
    owner: NativeProducerOperation
    source: NativeSourceContext
    specification: ArtifactSnapshot
    directory: Path
    artifacts: dict[str, str] = field(default_factory=dict)

    def verify(self) -> SnapshotReader:
        owner, source, specification, directory = self.owner, self.source, self.specification, self.directory
        artifacts, current_scope = self.artifacts, _CURRENT.get()
        held_artifacts = dict(artifacts)

        def check_scope() -> None:
            if (
                self.owner is not owner
                or self.source is not source
                or self.specification is not specification
                or self.directory is not directory
                or self.artifacts is not artifacts
                or artifacts != held_artifacts
                or _CURRENT.get() is not current_scope
                or current_native_producer_operation() is not owner
                or owner.source is not source
                or owner.owner_pid != os.getpid()
            ):
                raise ValueError(
                    "native stage DATA scope differs from its actual live independently admitted child owner"
                )

        check_scope()
        reader = SnapshotReader(source.bindings.current_root, native_producer_operation=owner)
        with owner._verification_guard(reader, run_id=owner.run_id, deadline=owner.deadline):
            check_scope()
            try:
                self._verify_data(reader, owner, source, specification, directory)
            finally:
                check_scope()
        check_scope()
        self._verify_data(reader, owner, source, specification, directory)
        if not reader.unchanged():
            raise ValueError("native stage DATA scope changed during complete Source closure")
        return reader

    def _verify_data(
        self,
        reader: SnapshotReader,
        owner: NativeProducerOperation,
        source: NativeSourceContext,
        specification: ArtifactSnapshot,
        directory: Path,
    ) -> None:
        """Fixed scope comparisons; no Source admission or returned authority."""
        from infrastructure.reporting.native_stage_child import directory_identity

        held = reader.read(specification.relative)
        spec = held.json_object()
        validate_specification(spec)
        if (
            held.sha256 != specification.sha256
            or held.content != specification.content
            or spec["run_id"] != owner.run_id
            or spec["source"] != json.loads(source._descriptor_data(spec["scope"], deadline=owner.deadline))
            or spec["parent_pid"] != os.getppid()
            or spec["deadline_monotonic"] != owner.deadline
            or directory != reader.root / spec["directory"]
            or directory != owner._stage_scope_directory_data(spec["scope"])
            or directory_identity(directory) != tuple(spec["directory_identity"])
        ):
            raise ValueError("native stage DATA scope lost its actual parent specification or physical directory")


_CURRENT: ContextVar[_StageScope | None] = ContextVar("template_actual_native_stage_scope", default=None)


@contextmanager
def _actual_native_stage_scope(owner: NativeProducerOperation, specification: ArtifactSnapshot) -> Iterator[None]:
    """Only the actual fixed Source worker opens its independently admitted scope."""
    from infrastructure.core.bytecode_audit import canonical_code

    frame = inspect.currentframe()
    caller = frame.f_back if frame is not None else None
    # contextmanager invokes the generator from contextlib; its caller is the
    # real fixed worker entering this context. No serialized field selects it.
    actual = caller.f_back if caller is not None else None
    worker = owner.source.bindings.selected_sdk_package_root / "reporting/native_stage_child_worker.py"
    authored = owner.source.current_source_reader.read("infrastructure/reporting/native_stage_child_worker.py")
    compiled = compile(
        authored.content,
        str(worker),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    declared = [item for item in compiled.co_consts if isinstance(item, types.CodeType) and item.co_name == "main"]
    if (
        actual is None
        or len(declared) != 1
        or actual.f_code.co_filename != str(worker)
        or canonical_code(actual.f_code) != canonical_code(declared[0])
        or _CURRENT.get() is not None
    ):
        raise ValueError("native stage scope requires the actual selected Source stage-worker entrypoint")
    spec = specification.json_object()
    context = _StageScope(
        owner,
        owner.source,
        specification,
        owner.source.bindings.current_root / spec["directory"],
    )
    context.verify()
    token = _CURRENT.set(context)
    try:
        yield
        context.verify()
    finally:
        _CURRENT.reset(token)


def current_native_stage_directory(*, require_render: bool = False) -> Path | None:
    """Return verified child DATA location; a path never admits Source or tools."""
    context = _CURRENT.get()
    if context is None:
        return None
    context.verify()
    if require_render:
        spec = context.specification.json_object()
        if (
            spec["protocol"] != "stage"
            or spec["stage_key"] != "render_pdf"
            or spec["script"]["path"] != "scripts/pipeline/stage_03_render.py"
        ):
            raise ValueError("native renderer launch requires the exact actual Source render stage")
    return context.directory


def validate_renderer_stage_artifact(
    source: NativeSourceContext,
    value: dict[str, Any],
    reader: SnapshotReader,
    *,
    scope: str,
    run_id: str,
    owner_pid: int,
    original_root_label: Path | None = None,
) -> None:
    """Fixed record DATA checks; actual ToolAPI authority is checked separately."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    if value.get("schema_version") == "template-source-native-mermaid-production-command-v1":
        from infrastructure.reporting.native_mermaid_production_tool import (
            validate_source_native_mermaid_stage_artifact,
        )

        validate_source_native_mermaid_stage_artifact(
            source,
            value,
            reader,
            scope=scope,
            run_id=run_id,
            owner_pid=owner_pid,
            original_root_label=original_root_label,
        )
        return
    root_label = reader.root if original_root_label is None else original_root_label
    if (
        set(value) != RENDERER_FIELDS
        or value["schema_version"] != RENDERER_SCHEMA
        or value["run_id"] != run_id
        or value["scope"] != scope
        or value["owner_pid"] != owner_pid
        or value["writer"] not in {"latex", "html"}
        or value["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or not isinstance(value["command"], list)
        or not value["command"]
        or any(not isinstance(item, str) or "\0" in item for item in value["command"])
        or not Path(value["command"][0]).is_absolute()
        or not isinstance(value["source_inputs"], list)
        or not value["source_inputs"]
        or not isinstance(value["render_inputs"], list)
        or not value["render_inputs"]
        or not isinstance(value["tool_artifacts"], list)
        or not value["tool_artifacts"]
    ):
        raise ValueError("native stage renderer packet differs from the fixed actual Source writer/owner/input role")
    seen: set[str] = set()
    for selected in value["source_inputs"]:
        snapshot = _file(selected, reader)
        if snapshot.relative in seen or snapshot.content != source.reference.read(snapshot.relative):
            raise ValueError("native stage renderer Source input repeats or differs from independently held original")
        seen.add(snapshot.relative)
    section = (
        value["writer"] == "latex"
        and len(value["source_inputs"]) == 1
        and Path(_file(value["source_inputs"][0], reader).relative).suffix == ".tex"
    )
    if section:
        from infrastructure.reporting.native_tex_stage_inputs import (
            validate_tex_section_inputs,
        )

        validate_tex_section_inputs(source, value, reader, scope=scope, original_root_label=root_label)
    elif value["cwd"] not in {str(root_label), str(root_label / "projects" / scope)}:
        raise ValueError("native stage renderer cwd differs from its fixed Source writer role")
    for selected in (*value["render_inputs"], value["output"]):
        _file(selected, reader)
    for name in ("crossref_filter", "loader_qualification"):
        if value[name] is not None:
            _file(value[name], reader)


def retain_native_stage_artifact(
    snapshot: ArtifactSnapshot,
    *,
    tool_artifacts: Sequence[dict[str, str]],
) -> dict[str, str]:
    """Retain this Source renderer packet only after actual live ToolAPI checks."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    context = _CURRENT.get()
    if context is None:
        raise ValueError("native stage renderer retention requires the actual admitted fixed child scope")
    reader = context.verify()
    actual = reader.read(snapshot.relative)
    if (
        actual.sha256 != snapshot.sha256
        or actual.content != snapshot.content
        or not actual.path.is_relative_to(context.directory)
    ):
        raise ValueError("native stage renderer packet is not the actual child-owned Source-written snapshot")
    spec, value = context.specification.json_object(), actual.json_object()
    if (
        spec["protocol"] != "stage"
        or spec["stage_key"] != "render_pdf"
        or spec["script"]["path"] != "scripts/pipeline/stage_03_render.py"
    ):
        raise ValueError("renderer retention requires the exact actual Source render stage")
    validate_renderer_stage_artifact(
        context.source,
        value,
        reader,
        scope=spec["scope"],
        run_id=context.owner.run_id,
        owner_pid=context.owner.owner_pid,
    )
    if value["tool_artifacts"] != list(tool_artifacts):
        raise ValueError("native stage renderer packet replaced its actual ToolAPI bindings")
    seen: set[str] = set()
    for selected in tool_artifacts:
        tool = _file(selected, reader)
        if tool.relative in seen:
            raise ValueError("native stage renderer packet repeats a ToolAPI event")
        seen.add(tool.relative)
        context.owner.validate_tool(selected, tool.json_object(), reader, run_id=context.owner.run_id)
    final_tool = _file(tool_artifacts[-1], reader).json_object()
    if final_tool["command"] != value["command"] or final_tool["cwd"] != value["cwd"]:
        raise ValueError("renderer packet command/cwd differs from its actual retained final ToolAPI")
    if actual.relative in context.artifacts or not reader.unchanged():
        raise ValueError("native stage renderer packet repeats or changed during genuine ToolAPI retention")
    context.artifacts[actual.relative] = actual.sha256
    context.verify()
    return binding(actual)


def _retained_native_stage_artifacts() -> list[dict[str, str]]:
    context = _CURRENT.get()
    if context is None:
        raise ValueError("native stage artifact accessor requires the actual child scope")
    reader = context.verify()
    retained = []
    for relative, digest in context.artifacts.items():
        snapshot = reader.read(relative)
        if snapshot.sha256 != digest:
            raise ValueError("native stage retained Source renderer packet changed")
        retained.append(binding(snapshot))
    if not reader.unchanged():
        raise ValueError("native stage retained Source packets changed during accessor readback")
    return retained
