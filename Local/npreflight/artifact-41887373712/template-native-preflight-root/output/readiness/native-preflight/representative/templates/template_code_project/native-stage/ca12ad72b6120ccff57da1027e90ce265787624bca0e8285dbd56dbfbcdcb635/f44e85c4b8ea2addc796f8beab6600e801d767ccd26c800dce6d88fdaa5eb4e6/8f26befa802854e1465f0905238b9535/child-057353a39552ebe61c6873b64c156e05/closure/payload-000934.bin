"""One fresh synchronous post-return boundary for a genuine fixed stage child.

The ToolAPI has already retained its actual OS event. This operation closes
Source, Code, request and packet DATA before publishing any child capability.
It never encloses a running child or exports a verified token.
"""

from __future__ import annotations

import copy
import sys
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_stage_child_contracts import PACKET_SCHEMA, binding
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def observe_native_stage_child(preparation: Any, result: dict[str, Any]) -> dict[str, str]:
    """Called only by the fixed preparation after its actual ToolAPI returned."""
    from infrastructure.reporting import native_stage_child as factory
    from infrastructure.reporting.native_stage_child import NativeStageChildPreparation

    if (
        type(preparation) is not NativeStageChildPreparation
        or sys._getframe(1).f_code is not NativeStageChildPreparation.observe.__code__
    ):
        raise ValueError("native child completion requires the actual fixed parent preparation call")
    owner, source, scope, deadline = preparation.owner, preparation.source, preparation.scope, preparation.deadline
    reader = SnapshotReader(source.bindings.current_root, native_producer_operation=owner)
    preparation._verify_factory_data(reader, owner, source, scope, deadline)
    tools, children = owner._tools, owner._stage_children
    prepared_registry = factory._PREPARED
    original_tools = dict(tools)
    original_tool_data = {name: tuple(vars(event).items()) for name, event in original_tools.items()}
    original_children = dict(children)
    original_child_data = copy.deepcopy(children)
    if type(result) is not dict:
        raise ValueError("native stage observation needs the actual ToolAPI result DATA")
    selected_binding = result.get("artifact", result)
    if (
        type(selected_binding) is not dict
        or set(selected_binding) != {"path", "sha256"}
        or any(type(selected_binding[key]) is not str for key in ("path", "sha256"))
    ):
        raise ValueError("native stage observation needs its actual ToolAPI artifact binding")
    process_binding = dict(selected_binding)
    event = original_tools.get(process_binding["path"])
    if event is None:
        raise ValueError("native child completion has no actual retained ToolAPI event")
    with owner._verification_guard(reader, run_id=owner.run_id, deadline=deadline):
        preparation._verify_factory_data(reader, owner, source, scope, deadline)
        try:
            preparation._verify_owner_data(reader)
            process = reader.read(process_binding["path"])
            packet = {
                "schema_version": PACKET_SCHEMA,
                "process_artifact": process_binding,
                "specification_artifact": binding(preparation.specification),
                "artifact": binding(
                    reader.read((preparation.directory / "observation.json").relative_to(reader.root).as_posix())
                ),
                "closure_artifact": binding(
                    reader.read((preparation.closure / "receipt.json").relative_to(reader.root).as_posix())
                ),
                "original_exit_code": process.json_object()["original_exit_code"],
            }
            preparation._verify_closed_packet_data(packet, process_binding, reader)
            if (
                tools.get(process.relative) is not event
                or owner._tools is not tools
                or owner._stage_children is not children
            ):
                raise ValueError("native child completion lost its actual ToolAPI registry")
            retained = write_json(reader.root, preparation.directory / "stage-child.json", packet)
            held = reader.read(retained["path"])
            if held.sha256 != retained["sha256"] or held.json_object() != packet or held.relative in children:
                raise ValueError("native stage packet is replaced, duplicated or belongs to another actual attempt")
            record = {"sha256": held.sha256, "value": copy.deepcopy(packet), "process_binding": dict(process_binding)}
            if not reader.unchanged():
                raise ValueError("native stage child bytes changed before closing actual parent observation")
        finally:
            preparation._verify_factory_data(reader, owner, source, scope, deadline)
    # Closing Git/SDK checks may themselves expose late mutations in ignored
    # packet directories. Recheck held factory DATA and physical names now.
    preparation._verify_factory_data(reader, owner, source, scope, deadline)
    preparation._verify_owner_data(reader)
    if (
        owner._tools is not tools
        or owner._stage_children is not children
        or tools.get(process.relative) is not event
        or factory._PREPARED is not prepared_registry
        or len(tools) != len(original_tools)
        or any(tuple(vars(original).items()) != original_tool_data[name] for name, original in original_tools.items())
        or len(children) != len(original_children)
        or any(children.get(name) is not original for name, original in original_children.items())
        or children != original_child_data
        or any(tools.get(name) is not original for name, original in original_tools.items())
        or held.relative in children
        or not reader.unchanged()
    ):
        raise ValueError("native child completion changed during final Source closure")
    remaining(deadline)
    # Fixed publication only: no filesystem reads, callback, child or await
    # between this successful closure and adoption of the actual observation.
    children[held.relative] = record
    prepared_registry.pop(id(preparation))
    return retained
