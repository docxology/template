"""Reconstruct retained analysis boundaries under genuine native custody.

The complete Source controller inventory is authenticated by the externally
held original native artifact, then every retained body is independently read.
This is a boundary-byte bridge, not per-read causality, domain truth, or a new
per-leaf original-process capability. Those obligations remain explicit.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from infrastructure.core.analysis_data_custody import (
    DATA_FILES,
    DATA_ROOTS,
    MAX_FILES,
    MAX_FILE_BYTES,
    MAX_SNAPSHOT_BYTES,
)
from infrastructure.core.analysis_data_custody import SCHEMA as DATA_SCHEMA
from infrastructure.core.analysis_launch import analysis_receipt_path, analysis_stage_key
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.runtime.python_binding import admitted_runtime_report
from infrastructure.core.script_discovery import discover_analysis_scripts
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_analysis_read_replay import reconstruct_returned_reads
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_code_figure_registry import reconstruct_code_figure_registry
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation

SCHEMA = "template-native-analysis-boundary-graph-v3"
REMAINING = (
    "externally-held-per-leaf-original-process-capabilities-and-independent-actual-analysis-rerun",
    "complete-per-read-analysis-input-and-external-resource-lineage",
    "independent-project-domain-mapping-for-every-generated-value-unit-sign-and-figure",
    "source-owned-complete-registry-reconstruction-and-native-occurrence-consumption",
)
_BOUNDARY_FIELDS = {
    "schema",
    "run_id",
    "stage_key",
    "root_policy",
    "file_policy",
    "present_roots",
    "output_policy",
    "records",
    "total_bytes",
    "claim_boundary",
    "content_digest",
}


def _hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _binding(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256, "bytes": len(snapshot.content)}


def _boundary(
    raw: object,
    scope: str,
    run_id: str,
    stage: str,
    reader: SnapshotReader,
    deadline: float,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Read every authenticated inventory member; DATA cannot select a subset."""
    if (
        not isinstance(raw, dict)
        or set(raw) != _BOUNDARY_FIELDS
        or raw.get("schema") != DATA_SCHEMA
        or raw.get("run_id") != run_id
        or raw.get("stage_key") != stage
        or raw.get("root_policy") != list(DATA_ROOTS)
        or raw.get("file_policy") != list(DATA_FILES)
        or raw.get("output_policy") != "stable-shippable-output-v1"
        or raw.get("claim_boundary") != "boundary-inventory-only; not-per-read-lineage-or-scientific-truth"
        or raw.get("content_digest")
        != canonical_digest({key: value for key, value in raw.items() if key != "content_digest"})
    ):
        raise ValueError("analysis boundary differs from the complete authenticated Source protocol")
    roots, records = raw.get("present_roots"), raw.get("records")
    if (
        not isinstance(roots, list)
        or roots != [name for name in DATA_ROOTS if name in roots]
        or not isinstance(records, list)
        or len(records) > MAX_FILES
    ):
        raise ValueError("analysis boundary roots/records omit their Source order or exceed the ceiling")
    rows: dict[str, dict[str, Any]] = {}
    total = 0
    for row in records:
        remaining(deadline)
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "bytes", "retained_path", "native_identity"}
            or not isinstance(row.get("path"), str)
            or not _hash(row.get("sha256"))
            or type(row.get("bytes")) is not int
            or not 0 <= row["bytes"] <= MAX_FILE_BYTES
        ):
            raise ValueError("analysis boundary lost an exact regular original body binding")
        path = Path(row["path"])
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or path.as_posix() != row["path"]
            or not (
                row["path"] in DATA_FILES
                or any(path.is_relative_to(Path(root)) for root in roots)
                or path.is_relative_to(Path("output"))
            )
            or path.is_relative_to(Path("output/.pipeline"))
            or row["path"] in rows
        ):
            raise ValueError("analysis boundary omitted, repeated or escaped its complete Source policy")
        identity = row.get("native_identity")
        if (
            not isinstance(identity, list)
            or len(identity) != 5
            or any(type(value) is not int or value < 0 for value in identity)
            or identity[2] != row["bytes"]
        ):
            raise ValueError("analysis original body omitted its held OS identity")
        expected = (
            Path("output/.pipeline/analysis-data")
            / hashlib.sha256(run_id.encode()).hexdigest()
            / "blobs"
            / row["sha256"]
        ).as_posix()
        if row["retained_path"] != expected:
            raise ValueError("analysis original body moved outside its exact original run-owned hash slot")
        retained = reader.read(f"projects/{scope}/{expected}", max_bytes=MAX_FILE_BYTES)
        if retained.sha256 != row["sha256"] or len(retained.content) != row["bytes"]:
            raise ValueError("analysis original body differs from independently read retained bytes")
        rows[row["path"]] = {**row, "retained": _binding(retained)}
        total += row["bytes"]
    if list(rows) != sorted(rows) or total != raw.get("total_bytes") or total > MAX_SNAPSHOT_BYTES:
        raise ValueError("analysis boundary full ordered roster or total byte identity differs")
    return rows, {"content_digest": raw["content_digest"], "records": list(rows.values()), "total_bytes": total}


def _leaf(
    scope: str,
    run_id: str,
    plan: str,
    stage: str,
    reader: SnapshotReader,
    source: NativeSourceContext,
    original_root: Path,
    deadline: float,
    stage_owner: NativeStageChildReaderOperation | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    project = reader.root / "projects" / scope
    path = analysis_receipt_path(project, run_id, stage).relative_to(reader.root).as_posix()
    item = reader.read(path, max_bytes=64 * 1024 * 1024)
    leaf = item.json_object()
    if (
        leaf.get("schema") != "template-analysis-leaf/3"
        or leaf.get("run_id") != run_id
        or leaf.get("stage_key") != stage
        or leaf.get("plan_digest") != plan
        or leaf.get("complete") is not True
        or leaf.get("cache_reuse_authorized") is not False
        or leaf.get("dependency_proof") != "metadata-record-declarations"
    ):
        raise ValueError("native analysis leaf is not the exact actual complete original selection")
    before, after, worker = leaf.get("controller_before"), leaf.get("controller_after"), leaf.get("worker")
    if not isinstance(before, dict) or before != after or not isinstance(worker, dict):
        raise ValueError("native analysis leaf lost unchanged controller Source/runtime custody")
    request, completion, process = worker.get("request"), worker.get("completion"), worker.get("original_process")
    if not isinstance(request, dict) or not isinstance(completion, dict) or not isinstance(process, dict):
        raise ValueError("native analysis leaf lacks actual controller request/completion/process observations")
    from infrastructure.reporting.native_analysis_stage_replay import authenticate_analysis_stage_child

    native_stage = authenticate_analysis_stage_child(source, scope, worker, reader, stage_owner, deadline=deadline)
    nonce = request.get("analysis_nonce")
    original_project = original_root / "projects" / scope
    script_relative = stage.partition(":")[2]
    if (
        request.get("schema") != "template-python-analysis/4"
        or completion.get("schema") != request["schema"]
        or any(
            request.get(key) != value or completion.get(key) != value
            for key, value in (("run_id", run_id), ("stage_key", stage), ("plan_digest", plan))
        )
        or request.get("repo_root") != str(original_root)
        or request.get("project_root") != str(original_project)
        or request.get("cwd") != str(original_project if stage.startswith("hydration:") else original_root)
        or request.get("definition") is not None
        or request.get("stage_admission") is not None
        or request.get("argv") != [str(original_project / script_relative)]
        or not isinstance(nonce, str)
        or len(nonce) != 32
        or any(char not in "0123456789abcdef" for char in nonce)
        or completion.get("analysis_nonce") != nonce
        or process.get("analysis_nonce") != nonce
        or completion.get("request_digest") != canonical_digest(request)
        or process.get("request_digest") != canonical_digest(request)
        or completion.get("custody") != "verified"
        or completion.get("supervisory_interrupted") is not False
        or completion.get("original_exit_code") != 0
        or request.get("source_digest") != before.get("source_digest")
        or any(
            request.get(key) != before.get(key) or completion.get(key) != before.get(key)
            for key in ("source_content_digest", "runtime_digest")
        )
        or request.get("runtime_binding") != before.get("runtime_binding")
        or not isinstance(request.get("runtime_binding"), dict)
        or request.get("runtime_digest") != canonical_digest(request["runtime_binding"])
        or not admitted_runtime_report(completion.get("actual_runtime"), request["runtime_binding"])
    ):
        raise ValueError("native analysis completion differs from its actual Source/runtime/request/nonce identity")
    observed_deadline = cast(int | float, process.get("original_deadline_monotonic"))
    completed = cast(int | float, process.get("observed_completion_monotonic"))
    if (
        type(process.get("pid")) is not int
        or process["pid"] <= 0
        or process.get("original_exit_code") != 0
        or process.get("observed_exit_code") != 0
        or process.get("timed_out") is not False
        or process.get("custody_refused") is not False
        or observed_deadline != request.get("original_deadline_monotonic")
        or any(type(value) not in (int, float) or not math.isfinite(value) for value in (observed_deadline, completed))
        or not completed < observed_deadline
    ):
        raise ValueError("native analysis controller did not observe an actual successful bounded original child")
    outcome = leaf.get("outcome")
    if (
        not isinstance(outcome, dict)
        or outcome.get("stage_key") != stage
        or outcome.get("status") != "succeeded"
        or outcome.get("child_exit_code") != 0
        or outcome.get("attempt_exit_codes") != [0]
        or outcome.get("attempt_count") != 1
    ):
        raise ValueError("native analysis outcome lost its original successful invocation")
    inputs, input_graph = _boundary(request.get("data_before"), scope, run_id, stage, reader, deadline)
    outputs, output_graph = _boundary(completion.get("data_after"), scope, run_id, stage, reader, deadline)
    if completion.get("data_before_digest") != input_graph["content_digest"]:
        raise ValueError("native analysis worker observed a different incoming boundary")
    reads = reconstruct_returned_reads(
        completion.get("analysis_reads"), scope, request, process, inputs, source, reader, deadline
    )
    last_writes = {row["path"]: row for row in reads["completed_writes"]["records"]}
    for name, written in last_writes.items():
        final = outputs.get(name)
        if final is None or (final["sha256"], final["native_identity"]) != (
            written["sha256"],
            written["native_identity"],
        ):
            raise ValueError("final analysis output differs from its last actual completed Source write")
    return (
        {
            "stage_key": stage,
            "leaf": _binding(item),
            "request_digest": canonical_digest(request),
            "analysis_nonce": nonce,
            "observed_process": process,
            "native_stage_original": native_stage,
            "incoming": input_graph,
            "outgoing": output_graph,
            "registered_returned_reads": reads,
        },
        inputs,
        outputs,
    )


def _reconstruct(
    source: NativeSourceContext,
    scope: str,
    run_id: str,
    plan: str,
    reader: SnapshotReader,
    original_root: Path,
    deadline: float,
    stage_owner: NativeStageChildReaderOperation,
) -> dict[str, Any]:
    if (
        not isinstance(source, NativeSourceContext)
        or scope not in PUBLIC_PROJECT_NAMES
        or not isinstance(run_id, str)
        or not run_id
        or not _hash(plan)
    ):
        raise ValueError("analysis graph needs genuine Source and the exact original core run/plan")
    remaining(deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    project = reader.root / "projects" / scope
    scripts = discover_analysis_scripts(reader.root, scope, project_dir=project)
    keys = tuple(analysis_stage_key(path, project) for path in scripts)
    aggregate = None
    run: dict[str, Any] = {}
    if keys:
        aggregate_path = analysis_receipt_path(project, run_id, "aggregate").with_name("run.json")
        aggregate = reader.read(aggregate_path.relative_to(reader.root).as_posix(), max_bytes=8 * 1024 * 1024)
        run = aggregate.json_object()
        if (
            run.get("schema") != "template-analysis-run/3"
            or run.get("run_id") != run_id
            or run.get("plan_digest") != plan
            or run.get("expected_stage_keys") != list(keys)
            or run.get("complete") is not True
            or run.get("exit_code") != 0
            or run.get("cache_reuse_authorized") is not False
            or run.get("source_before") != run.get("source_after")
            or not isinstance(run.get("leaf_sha256"), dict)
            or set(run["leaf_sha256"]) != set(keys)
        ):
            raise ValueError("native analysis aggregate omits/changes the complete Source-selected producer roster")
    hydration_script = project / "scripts/z_generate_manuscript_variables.py"
    hydration_key = "hydration:scripts/z_generate_manuscript_variables.py"
    selected = keys + ((hydration_key,) if hydration_script.is_file() else ())
    stages = []
    latest: dict[str, tuple[str, dict[str, Any]]] = {}
    last_outputs = None
    for stage in selected:
        relative = stage.partition(":")[2]
        script = reader.read(f"projects/{scope}/{relative}", max_bytes=8 * 1024 * 1024)
        if source.reference.read(script.relative) != script.content:
            raise ValueError("native analysis producer differs from independent held Source")
        graph, inputs, outputs = _leaf(scope, run_id, plan, stage, reader, source, original_root, deadline, stage_owner)
        graph["script"] = _binding(script)
        if stage in keys and run["leaf_sha256"][stage] != graph["leaf"]["sha256"]:
            raise ValueError("native aggregate points at a different original analysis leaf")
        # Rendering begins after the analysis aggregate; intervening Stage-03
        # metadata work is a separate unresolved edge, never silently equated.
        if last_outputs is not None and not stage.startswith("hydration:") and inputs != last_outputs:
            raise ValueError("successive original analysis boundaries lost their full byte/OS identity chain")
        for name, row in outputs.items():
            if name not in inputs or (row["sha256"], row["native_identity"]) != (
                inputs[name]["sha256"],
                inputs[name]["native_identity"],
            ):
                latest[name] = (stage, row)
        last_outputs = outputs
        stages.append(graph)
    consumed = []
    unresolved = list(REMAINING)
    # Native reconstruction selects every generated variable/figure body that
    # rendering can consume through its standard data/manuscript roots.
    for name, (stage, row) in sorted(latest.items()):
        if not (
            name == "output/data/manuscript_variables.json"
            or Path(name).is_relative_to(Path("output/figures"))
            or Path(name).is_relative_to(Path("output/manuscript"))
        ):
            continue
        actual = reader.read(f"projects/{scope}/{name}", max_bytes=MAX_FILE_BYTES)
        if actual.sha256 != row["sha256"] or len(actual.content) != row["bytes"]:
            raise ValueError("consumed generated body differs from its latest actual analysis/hydration output")
        consumed.append({"producer_stage": stage, "body": _binding(actual), "original_retained": row["retained"]})
    variables_path = project / "output/data/manuscript_variables.json"
    if variables_path.is_file() and "output/data/manuscript_variables.json" not in latest:
        unresolved.append("consumed-variable-body-was-not-created-or-written-by-an-observed-original-producer")
    if hydration_script.is_file():
        unresolved.append("analysis-to-render-hydration-boundary-intervening-metadata-and-resource-custody")
    registry = (
        reconstruct_code_figure_registry(source, reader, deadline=deadline)
        if scope == "templates/template_code_project"
        else None
    )
    body = {
        "schema_version": SCHEMA,
        "scope": scope,
        "pipeline_run_id": run_id,
        "plan_digest": plan,
        "source_binding": [source.reference.commit, source.reference.source_identity],
        "aggregate": None if aggregate is None else _binding(aggregate),
        "ordered_stages": stages,
        "produced_current_bodies": consumed,
        "source_registry_reconstruction": registry,
        "unresolved_edges": unresolved,
    }
    if not reader.unchanged():
        raise ValueError("native retained analysis bodies/receipts changed across complete graph reconstruction")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    remaining(deadline)
    return {**body, "content_digest": canonical_digest(body)}


def observe_native_analysis_boundary_graph(
    source: NativeSourceContext,
    scope: str,
    run_id: str,
    plan: str,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Observe inside the actual original Source worker; never create authority."""
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or owner.deadline != deadline:
        raise ValueError("native analysis graph requires its real Source owner and already-live original clock")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation

    stage_owner = NativeStageChildReaderOperation(
        source, reader, list(owner.stage_children), scope=scope, run_id=owner.run_id, deadline=deadline
    )
    graph = _reconstruct(source, scope, run_id, plan, reader, reader.root, deadline, stage_owner)
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    return graph


def replay_native_analysis_boundary_graph(
    scope: str,
    native_execution: ArtifactSnapshot,
    reader: SnapshotReader,
) -> dict[str, Any]:
    """Authenticate the whole original first, then independently rebuild bytes.

    The fixed typed stage chain authenticates each actual original leaf tool.
    Its JSON remains DATA; independent actual rerun/domain gates are separate.
    """
    operation = require_native_operation(reader)
    original = operation.originals.get(scope)
    if (
        original is None
        or native_execution.relative != original.native_execution_relative
        or native_execution.sha256 != original.native_execution_sha256
        or reader.read(native_execution.relative) != native_execution
    ):
        raise ValueError("native analysis is not the externally authenticated actual original native artifact")
    raw = native_execution.json_object()
    pipeline = raw.get("pipeline")
    if (
        raw.get("scope") != scope
        or raw.get("run_id") != original.run_id
        or not isinstance(pipeline, dict)
        or pipeline.get("mode") != "core"
    ):
        raise ValueError("native analysis omitted its exact actual full original core execution")
    command = original.command
    if command.count("--root") != 1 or command.index("--root") + 1 >= len(command):
        raise ValueError("held original native command omitted its genuine Source root selector")
    original_root = Path(command[command.index("--root") + 1])
    if not original_root.is_absolute() or ".." in original_root.parts:
        raise ValueError("held original native root is not its absolute supervised Source path")
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation

    stage_owner = NativeStageChildReaderOperation(
        operation.source,
        reader,
        cast(list[dict[str, str]], raw.get("stage_children")),
        scope=scope,
        run_id=original.run_id,
        deadline=operation.deadline,
    )
    expected = _reconstruct(
        operation.source,
        scope,
        pipeline.get("run_id", ""),
        pipeline.get("plan_digest", ""),
        reader,
        original_root,
        operation.deadline,
        stage_owner,
    )
    if raw.get("analysis_data_graph") != expected:
        raise ValueError("retained native analysis graph differs from complete independent body/Source reconstruction")
    operation.verify(reader)
    return expected
