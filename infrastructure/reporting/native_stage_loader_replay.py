"""Loader readback through the actual fixed renderer/Stage role.

The Original API remains separately admitted. Current admission comes only from
the already-live independent Source producer and its causally closed children.
No retained host, clock, qualification or tool record creates either owner.
"""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
    from infrastructure.reporting.native_tool_producer import NativeProducerOperation


def renderer_crossref_data(renderer: dict[str, Any], reader: SnapshotReader) -> tuple[dict[str, Any], dict[str, str]]:
    """Read finite retained edges after the caller authenticates the renderer.

    These pointers grant no authority. The Stage reader must authenticate both
    real native pairs and every filter child before admitting their DATA.
    """
    from infrastructure.rendering.combined_native_commands import RENDERER_CROSSREF_SCHEMA
    from infrastructure.reporting.native_crossref_pair import PARENT_SCHEMA
    from infrastructure.reporting.native_loader_replay import _bound

    envelope = _bound(renderer["crossref_filter"], reader).json_object()
    if set(envelope) != {"schema_version", "parent", "pre_crossref_parser"} or (
        envelope["schema_version"] != RENDERER_CROSSREF_SCHEMA
    ):
        raise ValueError("renderer Crossref lacks its exact Source parser/parent edge")
    parent = _bound(envelope["parent"], reader).json_object()
    if (
        set(parent) != {"schema_version", "scope", "run_id", "filter", "parent_loader_qualification"}
        or parent["schema_version"] != PARENT_SCHEMA
        or parent["scope"] != renderer["scope"]
        or parent["run_id"] != renderer["run_id"]
        or parent["parent_loader_qualification"] != renderer["loader_qualification"]
    ):
        raise ValueError("renderer parser envelope changed its genuine Source parent pair")
    _bound(envelope["pre_crossref_parser"], reader)
    return parent, envelope["pre_crossref_parser"]


def require_current_stage_reader(
    reader: SnapshotReader, stage_owner: NativeStageChildReaderOperation
) -> NativeProducerOperation:
    """Require the same genuine live Current Source/clock and exact Stage role."""
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    control = reader.native_control_operation
    if (
        type(stage_owner) is not NativeStageChildReaderOperation
        or reader.native_operation is not None
        or owner is None
        or reader.native_producer_operation is not owner
        or stage_owner.source is not owner.source
        or stage_owner.run_id != owner.run_id
        or stage_owner.deadline != owner.deadline
        or reader.root != owner.source.bindings.current_root
        or control is not stage_owner
        and not (
            type(control) is CrossrefFilterReaderOperation
            and getattr(control, "_renderer_stage_owner", None) is stage_owner
            and control.parent_reader.native_control_operation is stage_owner
        )
    ):
        raise ValueError("Current loader needs its genuine live Source/clock and exact renderer Stage role")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    stage_owner.verify(reader)
    remaining(owner.deadline)
    return owner


def _current_loader(
    binding: dict[str, str], reader: SnapshotReader, stage_owner: NativeStageChildReaderOperation
) -> dict[str, Any]:
    from infrastructure.reporting.native_loader_build import SOURCE
    from infrastructure.reporting.native_loader_replay import MODULES, _bound, validate_native_loader_data
    from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact

    owner = require_current_stage_reader(reader, stage_owner)
    authority = authenticate_original_native_artifact(
        binding, reader, run_id=owner.run_id, required_sdk_modules=MODULES
    )
    tool = authority["event"].json_object()
    native = _bound(tool["native_process_artifact"], reader).json_object()
    raw = validate_native_loader_data(
        native,
        reader,
        original_deadline=authority["original"].original_deadline,
        original_completion=authority["original"].observed_completion,
    )
    compiler = _bound(raw["compiler"], reader).json_object()
    spec = authority.get("renderer_stage_specification", authority["specification"])
    # The Current owner is still live on this host. The fixed stage's actual
    # Source-closed parent platform must agree; no old host record nominates it.
    host = {"system": platform.system(), "machine": platform.machine()}
    source = owner.source.current_source_reader.read(SOURCE)
    if (
        host["system"] != "Linux"
        or spec["parent_platform"] != host["system"]
        or compiler["architecture"] != host["machine"]
        or owner.source.reference.read(SOURCE) != source.content
        or compiler["source"]["sha256"] != source.sha256
        or raw["source_binding"] != [owner.source.reference.commit, owner.source.reference.source_identity]
    ):
        raise ValueError("Current loader Source compiler/ABI differs from its actual live host/Stage custody")
    for key in ("compiler_header_selection", "compiler"):
        authenticate_original_native_artifact(compiler[key], reader, run_id=owner.run_id, required_sdk_modules=MODULES)
    if host != {"system": platform.system(), "machine": platform.machine()}:
        raise ValueError("Current loader actual host changed during complete readback")
    require_current_stage_reader(reader, stage_owner)
    return raw


def replay_stage_loader_qualification(
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    stage_owner: NativeStageChildReaderOperation,
    renderer_binding: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Read one Source-selected pair through a genuine renderer or filter role.

    This shares Source's full tool/compiler/callback and parity validators. Its
    finite binding admission follows the renderer's actual retained pointers;
    arbitrary qualification JSON cannot become an authenticated Stage member.
    """
    from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_loader_qualification import SCHEMA, _FIELDS, _compare
    from infrastructure.reporting.native_loader_replay import MODULES, _bound, replay_native_loader_original
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
    from infrastructure.reporting.native_tool_replay import (
        authenticate_original_native_artifact,
        validate_original_native_tool,
    )

    if type(stage_owner) is not NativeStageChildReaderOperation:
        raise ValueError("renderer loader replay requires the exact fixed Stage reader")
    stage_owner.verify(reader)
    operation = None
    owner = None
    if reader.native_operation is None:
        owner = require_current_stage_reader(reader, stage_owner)
        source = owner.source
    else:
        operation = require_native_operation(reader)
        source = operation.source
        if source is not stage_owner.source or operation.deadline != stage_owner.deadline:
            raise ValueError("Original renderer loader changed its actual Source/clock")
    run_id = stage_owner.run_id
    control = reader.native_control_operation
    renderer_role = None
    parser_binding = None
    parser_pair = False
    if control is stage_owner and renderer_binding is not None:
        authority = stage_owner.authenticate_artifact(
            renderer_binding,
            reader,
            run_id=run_id,
            required_sdk_modules=("reporting/native_renderer_source_call.py", *MODULES),
        )
        renderer = authority["event"].json_object()
        if renderer["crossref_filter"] is not None:
            parent, parser_binding = renderer_crossref_data(renderer, reader)
            parser_pair = binding == parser_binding
            if not parser_pair and parent["parent_loader_qualification"] != binding:
                raise ValueError("loader qualification is not the genuine renderer's exact parent pair")
            if not parser_pair:
                renderer_role = CrossrefFilterReaderOperation.from_renderer_stage(renderer_binding, reader, stage_owner)
        elif renderer["loader_qualification"] != binding:
            raise ValueError("loader qualification is not the genuine renderer's exact retained pair")
    elif (
        type(control) is CrossrefFilterReaderOperation
        and getattr(control, "_renderer_stage_owner", None) is stage_owner
    ):
        authority = control._child()
        payload = authority["child_observation"]
        if binding not in (payload.get("loader_qualifications") or []):
            raise ValueError("loader qualification is not the genuine renderer's actual nested filter pair")
    else:
        raise ValueError("loader qualification lacks its genuine renderer-to-filter retained pointer")
    raw: dict[str, Any] = _bound(binding, reader).json_object()
    if (
        set(raw) != _FIELDS
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
        or raw["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or raw["noninterference"] != "exact-actual-command-input-output-and-signed-os-result"
        or raw["scope_limit"] != "this-original-argument-input-output-and-host-cohort"
        or raw["environment_scope"] != "exact-source-selected-before-independent-guardian-and-loader-injections"
        or parser_pair
        and (
            raw["tool"] != "pandoc"
            or raw["purpose"] != "source-renderer-pre-crossref-parser"
            or raw["crossref_filters"] is not None
        )
    ):
        raise ValueError("renderer loader pair differs from the exact Source/run/schema/cohort")
    baseline, observed = (_bound(raw[key], reader).json_object() for key in ("baseline_tool", "observed_tool"))
    for key, tool in (("baseline_tool", baseline), ("observed_tool", observed)):
        validate_original_native_tool(raw[key], tool, reader, run_id=run_id, required_sdk_modules=MODULES)
        if (
            tool["tool"] != raw["tool"]
            or tool["purpose"] != ("baseline-" if key == "baseline_tool" else "") + raw["purpose"]
        ):
            raise ValueError("renderer loader pair changed an actual selected native tool role")
    lifecycle = (
        replay_native_loader_original(raw["observed_tool"], reader, run_id=run_id)
        if operation is not None
        else _current_loader(raw["observed_tool"], reader, stage_owner)
    )
    compiler = _bound(lifecycle["compiler"], reader).json_object()
    for key in ("compiler_header_selection", "compiler"):
        authenticate_original_native_artifact(compiler[key], reader, run_id=run_id, required_sdk_modules=MODULES)
    if (
        lifecycle["compiler"] != raw["compiler"]
        or raw["loader_lifecycle"]
        != _bound(observed["native_process_artifact"], reader).json_object()["loader_lifecycle"]
    ):
        raise ValueError("renderer loader pair replaced its genuine compiler/callback cohort")
    _compare(baseline, observed, reader)
    if raw["crossref_filters"] is not None:
        from infrastructure.reporting.native_crossref_pair import LEG_SCHEMA
        from infrastructure.reporting.native_crossref_worker import filter_json

        filters = raw["crossref_filters"]
        if raw["tool"] != "pandoc" or not isinstance(filters, list) or len(filters) != 2 or renderer_role is None:
            raise ValueError("filtered renderer needs exactly two genuine retained parent-pair children")
        if parser_binding is None:
            raise ValueError("filtered renderer lacks its genuine Source-selected parser pair")
        parser = replay_stage_loader_qualification(
            parser_binding, reader, stage_owner=stage_owner, renderer_binding=renderer_binding
        )
        parser_tool = _bound(parser["observed_tool"], reader).json_object()
        parsed = filter_json(
            _bound({key: parser_tool["raw_stdout"][key] for key in ("path", "sha256")}, reader).content
        )
        declarations = []
        for slot, (leg_binding, parent_binding) in enumerate(
            zip(filters, (raw["baseline_tool"], raw["observed_tool"]), strict=True)
        ):
            leg = _bound(leg_binding, reader).json_object()
            if (
                leg.get("schema_version") != LEG_SCHEMA
                or leg.get("parent_tool") != parent_binding
                or leg.get("pair_invocation", {}).get("slot") != slot
            ):
                raise ValueError("renderer qualification changed its real baseline/observed child ordinal")
            child = CrossrefFilterReaderOperation.from_renderer_pair_leg(renderer_role, leg_binding).replay()
            if filter_json(_bound(child["input"], reader).content) != parsed:
                raise ValueError("Source-selected qualified parser differs from an actual complete Crossref leg stdin")
            declarations.append(leg["pair_invocation"]["declaration"])
        if declarations[0] != declarations[1]:
            raise ValueError("renderer pair changed its single Source-selected two-invocation declaration")
    for item in raw["selected_inputs"]:
        body = _bound(item, reader)
        for tool in (baseline, observed):
            consumed = [
                entry for entry in tool["consumed_input_artifacts"] if entry["observation"]["sha256"] == body.sha256
            ]
            if not consumed or not any(_bound(entry["artifact"], reader).content == body.content for entry in consumed):
                raise ValueError("renderer pair input lacks actual complete consumed-byte custody")
    if raw["stdin"] is not None and raw["stdin"] not in raw["selected_inputs"]:
        raise ValueError("renderer pair stdin differs from its admitted complete input cohort")
    if len(raw["baseline_outputs"]) != len(raw["observed_outputs"]):
        raise ValueError("renderer pair omitted a real selected output")
    labels = set()
    for left, right in zip(raw["baseline_outputs"], raw["observed_outputs"], strict=True):
        if (
            set(left) != {"original_label", "artifact"}
            or set(right) != set(left)
            or left["original_label"] != right["original_label"]
            or left["original_label"] in labels
            or _bound(left["artifact"], reader).content != _bound(right["artifact"], reader).content
        ):
            raise ValueError("renderer pair selected output labels/complete bytes differ")
        labels.add(left["original_label"])
    if operation is not None:
        operation.verify(reader)
    else:
        require_current_stage_reader(reader, stage_owner)
    return raw
