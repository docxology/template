"""Actual paired native execution and separately authenticated current replay.

The fixed Source route compares unchanged and instrumented executions of the
same real binary and input cohort. This is subordinate to complete Source and
scientific acceptance; retained DATA never creates either live capability.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_loader_build import CompiledNativeLoader, compile_native_loader
from infrastructure.reporting.native_loader_observation import NativeLoaderObservation
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_crossref_pair import SourceCrossrefPair

SCHEMA = "template-native-tool-loader-qualification-v3"
_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "source_binding",
        "tool",
        "purpose",
        "baseline_tool",
        "observed_tool",
        "compiler",
        "loader_lifecycle",
        "selected_inputs",
        "stdin",
        "baseline_outputs",
        "observed_outputs",
        "noninterference",
        "scope_limit",
        "environment_scope",
        "crossref_filters",
    }
)
# environment_digest commits the exact Source-selected map before independent
# guardian and loader injections. Actual injected maps must each validate below.
_PARITY = ("command", "cwd", "environment_digest", "executable", "executable_sha256", "original_exit_code", "exit_code")


def _file(path: Path, reader: SnapshotReader) -> dict[str, str]:
    observed = reader.read(path.absolute().relative_to(reader.root).as_posix())
    return {"path": observed.relative, "sha256": observed.sha256}


def _outputs(runtime: CitationRuntime, paths: tuple[Path, ...], label: str) -> list[dict[str, Any]]:
    reader = SnapshotReader(runtime.root)
    result = []
    for index, path in enumerate(paths):
        remaining(runtime.deadline)
        observed = reader.read(path.absolute().relative_to(runtime.root).as_posix())
        frozen = runtime.freeze(f"{label}-output-{index:03d}.input", observed.content)
        result.append({"original_label": str(path.absolute()), "artifact": _file(frozen, reader)})
    return result


def _compare(left: dict[str, Any], right: dict[str, Any], reader: SnapshotReader) -> None:
    from infrastructure.reporting.native_environment_custody import validate_native_environment
    from infrastructure.reporting.native_loader_replay import _bound

    if any(left[key] != right[key] for key in _PARITY) or left["original_exit_code"] != 0:
        raise ValueError(
            "auditor changed the actual command/body/CWD, Source-selected environment, or signed OS result"
        )
    environments = []
    for tool in (left, right):
        native = _bound(tool["native_process_artifact"], reader).json_object()
        validate_native_environment(native, tool, reader)
        environments.append(native["environment_custody"])
    if any(
        environments[0][key] != environments[1][key] for key in ("source_allowed_commitments", "source_allowed_digest")
    ):
        raise ValueError("native pair changed its exact credential-stripped Source-selected environment")
    if environments[0]["guardian_run_token"] == environments[1]["guardian_run_token"]:
        raise ValueError("native pair reused an independently owned guardian identity")
    for channel in ("stdout", "stderr"):
        a, b = left["raw_" + channel], right["raw_" + channel]
        if (
            a["bytes"] != b["bytes"]
            or _bound({key: a[key] for key in ("path", "sha256")}, reader).content
            != _bound({key: b[key] for key in ("path", "sha256")}, reader).content
        ):
            raise ValueError("auditor changed a complete actual native raw output stream")


def qualify_native_loader_tool(
    runtime: CitationRuntime,
    name: str,
    arguments: list[str],
    purpose: str,
    *,
    input_paths: tuple[Path, ...] = (),
    stdin_path: Path | None = None,
    output_paths: tuple[Path, ...] = (),
    cwd: Path | None = None,
    compiled: CompiledNativeLoader | None = None,
    crossref_pair: SourceCrossrefPair | None = None,
) -> tuple[dict[str, Any], dict[str, str], CompiledNativeLoader]:
    """Execute two real children, retaining every original selected output."""
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != runtime.run_id or owner.deadline != runtime.deadline:
        raise ValueError("loader pair requires the genuine Source owner and same existing original clock")
    reader = SnapshotReader(runtime.root, native_producer_operation=owner)
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    from infrastructure.reporting.native_loader_observation import ENV_KEYS

    if ENV_KEYS & set(runtime.env) or any(key.startswith("DYLD_") for key in runtime.env):
        raise ValueError("native pair refuses ambient loader instrumentation before either actual child")
    if crossref_pair is not None:
        from infrastructure.reporting.native_crossref_pair import SourceCrossrefPair

        if type(crossref_pair) is not SourceCrossrefPair or crossref_pair.owner is not owner or name != "pandoc":
            raise ValueError("filtered loader pair requires its concrete genuine Source two-child preparation")
        crossref_pair.verify()
        if (
            runtime.env != crossref_pair.environment
            or arguments.count(str(runtime.root / crossref_pair.launcher["path"])) != 1
        ):
            raise ValueError("filtered parent pair changed its identical selected environment/launcher argv")
    inputs = tuple(dict.fromkeys((*input_paths, *((stdin_path,) if stdin_path is not None else ()))))
    held_inputs = [_file(path, reader) for path in inputs]
    if len(set(path.absolute() for path in output_paths)) != len(output_paths):
        raise ValueError("loader pair cannot repeat a selected actual output")
    if any(path.absolute() in {item.absolute() for item in inputs} for path in output_paths):
        raise ValueError("loader pair cannot overwrite its own admitted actual inputs")
    if compiled is None:
        compiler = CitationRuntime(
            runtime.root,
            runtime.directory / "source-loader-build",
            env=runtime.env,
            deadline=runtime.deadline,
            run_id=runtime.run_id,
        )
        compiled = compile_native_loader(compiler)
    compiled.verify(deadline=runtime.deadline)
    baseline = runtime.tool(
        name,
        list(arguments),
        "baseline-" + purpose,
        input_paths=inputs,
        stdin_path=stdin_path,
        cwd=cwd,
        while_live=None if crossref_pair is None else lambda live: crossref_pair.observe(0, live),
        phase_deadline=None if crossref_pair is None else crossref_pair.deadline,
    )
    baseline_binding = runtime.tools[-1]
    if crossref_pair is not None:
        crossref_pair.finish(0, baseline_binding)
    left_outputs = _outputs(runtime, output_paths, "baseline-" + purpose)
    if held_inputs != [_file(path, reader) for path in inputs]:
        raise ValueError("baseline native execution changed the original selected input cohort")
    if crossref_pair is None:
        leaf = compiled.directory / ("callbacks-" + purpose)
        create_private_native_directory(runtime.root, leaf)
        deadline = min(runtime.deadline, time.monotonic() + 120.0)
        observer = NativeLoaderObservation(compiled, leaf, purpose=purpose, deadline=deadline)
    else:
        observer = crossref_pair.parent_loader
        deadline = crossref_pair.deadline
        if observer.compiled is not compiled or observer.purpose != purpose or observer.deadline != deadline:
            raise ValueError("filtered native qualification substituted its concrete predeclared parent observer")
    observed = runtime.tool(
        name,
        list(arguments),
        purpose,
        input_paths=inputs,
        stdin_path=stdin_path,
        cwd=cwd,
        loader=observer,
        phase_deadline=deadline,
        while_live=None if crossref_pair is None else lambda live: crossref_pair.observe(1, live),
    )
    observed_binding = runtime.tools[-1]
    if crossref_pair is not None:
        crossref_pair.finish(1, observed_binding)
    right_outputs = _outputs(runtime, output_paths, "observed-" + purpose)
    _compare(baseline, observed, reader)
    for left, right in zip(left_outputs, right_outputs, strict=True):
        if reader.read(left["artifact"]["path"]).content != reader.read(right["artifact"]["path"]).content:
            raise ValueError("auditor changed an actual Source-selected native output file")
    for selected in (baseline_binding, observed_binding):
        owner.validate_tool(selected, reader.read(selected["path"]).json_object(), reader, run_id=runtime.run_id)
    if observer.binding is None or held_inputs != [_file(path, reader) for path in inputs] or not reader.unchanged():
        raise ValueError("actual loader lifecycle/unchanged selected input/output custody is absent")
    value = {
        "schema_version": SCHEMA,
        "run_id": runtime.run_id,
        "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
        "tool": name,
        "purpose": purpose,
        "baseline_tool": baseline_binding,
        "observed_tool": observed_binding,
        "compiler": compiled.binding,
        "loader_lifecycle": observer.binding,
        "selected_inputs": held_inputs,
        "stdin": None if stdin_path is None else _file(stdin_path, reader),
        "baseline_outputs": left_outputs,
        "observed_outputs": right_outputs,
        "noninterference": "exact-actual-command-input-output-and-signed-os-result",
        "scope_limit": "this-original-argument-input-output-and-host-cohort",
        "environment_scope": "exact-source-selected-before-independent-guardian-and-loader-injections",
        "crossref_filters": None if crossref_pair is None else list(crossref_pair.completed),
    }
    selected = write_json(runtime.root, runtime.directory / (purpose + ".loader-qualification.json"), value)
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    return observed, selected, compiled


def replay_native_loader_qualification(
    binding: dict[str, str], reader: SnapshotReader, *, run_id: str
) -> dict[str, Any]:
    """Authenticate originals before reconstructing bodies, maps and parity."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_loader_replay import MODULES, _bound, replay_native_loader_original
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool

    operation = require_native_operation(reader)
    raw = _bound(binding, reader).json_object()
    if not isinstance(raw, dict):
        raise ValueError("loader qualification must be a retained JSON object")
    if (
        set(raw) != _FIELDS
        or raw["schema_version"] != SCHEMA
        or raw["run_id"] != run_id
        or raw["source_binding"] != [operation.source.reference.commit, operation.source.reference.source_identity]
        or raw["noninterference"] != "exact-actual-command-input-output-and-signed-os-result"
        or raw["scope_limit"] != "this-original-argument-input-output-and-host-cohort"
        or raw["environment_scope"] != "exact-source-selected-before-independent-guardian-and-loader-injections"
    ):
        raise ValueError("loader pair differs from its exact Source/original run/schema/cohort")
    baseline, observed = (_bound(raw[key], reader).json_object() for key in ("baseline_tool", "observed_tool"))
    for key, tool in (("baseline_tool", baseline), ("observed_tool", observed)):
        validate_original_native_tool(raw[key], tool, reader, run_id=run_id, required_sdk_modules=MODULES)
        if (
            tool["tool"] != raw["tool"]
            or tool["purpose"] != ("baseline-" if key == "baseline_tool" else "") + raw["purpose"]
        ):
            raise ValueError("loader pair substituted an actual original Source-selected tool role")
    lifecycle = replay_native_loader_original(raw["observed_tool"], reader, run_id=run_id)
    if (
        lifecycle["compiler"] != raw["compiler"]
        or raw["loader_lifecycle"]
        != _bound(observed["native_process_artifact"], reader).json_object()["loader_lifecycle"]
    ):
        raise ValueError("loader pair substituted its actual compiler/callback cohort")
    _compare(baseline, observed, reader)
    if raw["crossref_filters"] is not None:
        from infrastructure.reporting.native_crossref_replay import CrossrefFilterReaderOperation
        from infrastructure.reporting.native_crossref_pair import LEG_SCHEMA

        filters = raw["crossref_filters"]
        if raw["tool"] != "pandoc" or not isinstance(filters, list) or len(filters) != 2:
            raise ValueError("filtered parent qualification lacks exactly two actual original filter children")
        declarations = []
        for slot, (binding, parent_binding) in enumerate(
            zip(filters, (raw["baseline_tool"], raw["observed_tool"]), strict=True)
        ):
            leg = _bound(binding, reader).json_object()
            if (
                leg.get("schema_version") != LEG_SCHEMA
                or leg.get("parent_tool") != parent_binding
                or leg.get("pair_invocation", {}).get("slot") != slot
            ):
                raise ValueError("filtered qualification substituted its original baseline/observed child ordinal")
            spec = _bound(leg["specification"], reader).json_object()
            CrossrefFilterReaderOperation(
                operation.source, binding, reader, scope=spec["scope"], run_id=run_id, deadline=operation.deadline
            ).replay()
            declarations.append(leg["pair_invocation"]["declaration"])
        if declarations[0] != declarations[1]:
            raise ValueError("filtered parent qualification changed its single immutable two-invocation declaration")
    for item in raw["selected_inputs"]:
        body = _bound(item, reader)
        for tool in (baseline, observed):
            consumed = [
                entry for entry in tool["consumed_input_artifacts"] if entry["observation"]["sha256"] == body.sha256
            ]
            if not consumed or not any(_bound(entry["artifact"], reader).content == body.content for entry in consumed):
                raise ValueError("loader pair selected input is absent from actual consumed-byte custody")
    if raw["stdin"] is not None and raw["stdin"] not in raw["selected_inputs"]:
        raise ValueError("loader pair stdin differs from the exact admitted selected input cohort")
    if len(raw["baseline_outputs"]) != len(raw["observed_outputs"]):
        raise ValueError("loader pair omitted an actual selected output")
    labels = set()
    for left, right in zip(raw["baseline_outputs"], raw["observed_outputs"], strict=True):
        if (
            set(left) != {"original_label", "artifact"}
            or set(right) != set(left)
            or left["original_label"] != right["original_label"]
            or left["original_label"] in labels
            or _bound(left["artifact"], reader).content != _bound(right["artifact"], reader).content
        ):
            raise ValueError("loader pair actual selected output labels/complete bytes differ")
        labels.add(left["original_label"])
    operation.verify(reader)
    return raw


def reproduce_native_loader_qualification(
    original: dict[str, str],
    reader: SnapshotReader,
    current: CitationRuntime,
    name: str,
    arguments: list[str],
    purpose: str,
    *,
    original_run_id: str,
    input_paths: tuple[Path, ...] = (),
    stdin_path: Path | None = None,
    output_paths: tuple[Path, ...] = (),
    cwd: Path | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Execute the enclosing reader's independently reconstructed Source inputs."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_loader_replay import _bound

    operation = require_native_operation(reader)
    raw = replay_native_loader_qualification(original, reader, run_id=original_run_id)
    owner = current_native_producer_operation()
    if (
        owner is None
        or owner.source is not operation.source
        or owner.deadline != operation.deadline
        or current.deadline != operation.deadline
        or raw["tool"] != name
    ):
        raise ValueError("current loader pair requires actual independent Source/reader/live-tool custody")
    result, binding, _ = qualify_native_loader_tool(
        current,
        name,
        arguments,
        purpose,
        input_paths=input_paths,
        stdin_path=stdin_path,
        output_paths=output_paths,
        cwd=cwd,
    )
    fresh_reader = SnapshotReader(current.root, native_producer_operation=owner)
    original_tool = _bound(raw["observed_tool"], reader).json_object()
    for channel in ("stdout", "stderr"):
        old, new = original_tool["raw_" + channel], result["raw_" + channel]
        if reader.read(old["path"]).content != fresh_reader.read(new["path"]).content:
            raise ValueError("fresh independent Source native tool changed the complete original raw output")
    fresh = fresh_reader.read(binding["path"]).json_object()
    if len(fresh["observed_outputs"]) != len(raw["observed_outputs"]):
        raise ValueError("fresh independent native tool changed the complete selected output cohort")
    for old, new in zip(raw["observed_outputs"], fresh["observed_outputs"], strict=True):
        if _bound(old["artifact"], reader).content != _bound(new["artifact"], fresh_reader).content:
            raise ValueError("fresh independent native tool changed an original complete selected output")
    operation.verify(reader)
    return result, binding
