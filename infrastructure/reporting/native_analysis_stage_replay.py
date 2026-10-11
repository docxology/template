"""Bind an analysis leaf to the one genuinely authenticated fixed stage chain."""

from __future__ import annotations

from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def authenticate_analysis_stage_child(
    source: NativeSourceContext,
    scope: str,
    worker: dict[str, Any],
    reader: SnapshotReader,
    owner: NativeStageChildReaderOperation | None,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Nomination DATA must resolve through actual Original/current parent custody.

    The role authenticates every enclosing parent ToolAPI, child Source/SDK
    execution closure, signed OS event and retained stage packet first. The
    leaf packet can only select an already closed real descendant. This proves
    this original execution edge; it does not perform a fresh analysis rerun or
    grant project scientific/native coverage from Source worker JSON.
    """
    remaining(deadline)
    if (
        type(owner) is not NativeStageChildReaderOperation
        or owner.source is not source
        or owner.scope != scope
        or owner.deadline < deadline
    ):
        raise ValueError("native analysis lacks its genuine fixed Original/current stage-chain reader")
    selected = worker.get("native_stage_child")
    if not isinstance(selected, dict) or set(selected) != {"path", "sha256"}:
        raise ValueError("native analysis lacks its actual fixed-stage child packet binding")
    authority = owner.descendant(selected, reader)
    packet = reader.read(selected["path"])
    if packet.sha256 != selected["sha256"]:
        raise ValueError("native analysis selected stage packet changed after genuine authentication")
    retained = packet.json_object()
    specification = authority["specification"]
    observation = authority["event"].json_object()
    request = reader.read(specification["request"]["path"])
    completion_binding = observation["result"]
    if not isinstance(completion_binding, dict) or set(completion_binding) != {"path", "sha256"}:
        raise ValueError("native analysis original child lacks its actual complete worker result")
    completion = reader.read(completion_binding["path"])
    tool_binding = retained["process_artifact"]
    tool = reader.read(tool_binding["path"])
    actual_tool = tool.json_object()
    process = worker.get("original_process")
    direct = worker.get("native_stage_process")
    request_data = request.json_object()
    if (
        request.sha256 != specification["request"]["sha256"]
        or request_data != worker.get("request")
        or canonical_digest(request_data) != specification["request_digest"]
        or completion.sha256 != completion_binding["sha256"]
        or completion.json_object() != worker.get("completion")
        or specification["protocol"] != "analysis"
        or specification["scope"] != scope
        or specification["pipeline_run_id"] != request_data.get("run_id")
        or specification["stage_key"] != request_data.get("stage_key")
        or specification["deadline_monotonic"] != request_data.get("original_deadline_monotonic")
        or observation["stage_return_code"] != 0
        or observation["stage_exception"] is not None
        or not isinstance(process, dict)
        or not isinstance(direct, dict)
        or set(direct) != {"artifact", "completion_authorized", "observation"}
        or direct["artifact"] != tool_binding
        or direct["completion_authorized"] is not True
        or direct["observation"] != actual_tool
        or tool.sha256 != tool_binding["sha256"]
        or actual_tool.get("pid") != authority["process"]["pid"]
        or actual_tool.get("original_exit_code") != 0
        or actual_tool.get("exit_code") != 0
        or actual_tool.get("timed_out") is not False
        or actual_tool.get("custody_refused") is not False
        or process.get("pid") != actual_tool["pid"]
        or process.get("command") != actual_tool["command"]
        or process.get("original_exit_code") != actual_tool["original_exit_code"]
        or process.get("observed_exit_code") != actual_tool["exit_code"]
        or process.get("timed_out") != actual_tool["timed_out"]
        or process.get("custody_refused") != actual_tool["custody_refused"]
        or process.get("original_deadline_monotonic") != specification["deadline_monotonic"]
    ):
        raise ValueError("native analysis request/result/process differs from the actual authenticated Source child")
    owner.verify(reader)
    remaining(deadline)
    return {
        "stage_child": selected,
        "tool_artifact": tool_binding,
        "source_closure": retained["closure_artifact"],
        "worker_pid": actual_tool["pid"],
        "parent_pid": actual_tool["owner_pid"],
        "actual_signed_os_exit": actual_tool["original_exit_code"],
        "script_completion_intent": completion.json_object()["original_exit_code"],
        "claim_boundary": (
            "authenticated-original-Source-child-edge; independent-analysis-rerun-and-domain-qualification-required"
        ),
    }
