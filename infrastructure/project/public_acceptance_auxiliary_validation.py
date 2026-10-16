"""Independent admission of raw auxiliary process and scientific evidence."""

from __future__ import annotations

import re
import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_supervision import (
    PROCESS_SCHEMA,
    _CENSUS_DIAGNOSTIC_ENUMS,
    _CENSUS_DIAGNOSTIC_INTS,
    complete_auxiliary_observation,
)

from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


from infrastructure.project.public_acceptance_auxiliary_transfer_validation import (
    validate_sandbox_transfer as validate_sandbox_transfer,
)


def _supervision_diagnostic(process: dict[str, Any]) -> str:
    """Bound refusal facts without rendering arbitrary retained process DATA."""
    observed: dict[str, Any] = {"schema_matches": process.get("schema_version") == PROCESS_SCHEMA}
    for key in ("accepted", "timed_out", "output_limit_exceeded"):
        value = process.get(key)
        observed[key] = value if type(value) is bool else "invalid"
    for key in ("pid", "exit_code"):
        value = process.get(key)
        observed[key] = value if value is None or type(value) is int and -(2**31) <= value < 2**31 else "invalid"
    cleanup = process.get("cleanup")
    if not isinstance(cleanup, dict):
        observed["cleanup"] = "invalid"
    else:
        facts: dict[str, Any] = {}
        for key in (
            "guardian_armed",
            "guardian_finished",
            "root_reaped",
            "final_census_succeeded",
            "deadline_exceeded",
            "verified",
        ):
            value = cleanup.get(key)
            facts[key] = value if type(value) is bool else "invalid"
        for key in ("final_token_sweep_matched_pids", "final_census_matched_pids", "diagnostics"):
            value = cleanup.get(key)
            facts[key + "_count"] = len(value) if type(value) is list else "invalid"
        for key in ("guardian_pid", "guardian_exit_code"):
            value = cleanup.get(key)
            facts[key] = value if value is None or type(value) is int and -(2**31) <= value < 2**31 else "invalid"
        for label in ("guardian_error", "final_census_error"):
            error = cleanup.get(label)
            if not isinstance(error, dict):
                continue
            allowed = {
                "OSError",
                "PermissionError",
                "FileNotFoundError",
                "ProcessLookupError",
                "RuntimeError",
                "ValueError",
                "TimeoutError",
                "TimeoutExpired",
                "SubprocessError",
                "CalledProcessError",
                "GuardianCustodyError",
            }
            for key in ("type", "cause"):
                value = error.get(key)
                facts[label + "_" + key] = value if type(value) is str and value in allowed else "unknown"
            value = error.get("errno")
            facts[label + "_errno"] = value if type(value) is int and 0 <= value <= 4095 else None
            procfs = error.get("procfs")
            if label == "final_census_error" and isinstance(procfs, dict):
                safe_procfs: dict[str, Any] = {
                    key: value
                    for key, lower, upper in _CENSUS_DIAGNOSTIC_INTS
                    if type(value := procfs.get(key)) is int and lower <= value <= upper
                }
                safe_procfs.update(
                    (key, value)
                    for key, allowed in _CENSUS_DIAGNOSTIC_ENUMS
                    if type(value := procfs.get(key)) is str and value in allowed
                )
                facts[label + "_procfs"] = safe_procfs
        observed["cleanup"] = facts
    return json.dumps(observed, sort_keys=True)[:2048]


def validate_auxiliary_process(gate: str, fingerprint: str, details: dict[str, Any], reader: SnapshotReader) -> None:
    """Read exact process/fact bytes; summary assertions cannot replace execution."""

    def artifact(binding: Any) -> Any:
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("auxiliary evidence needs an exact artifact binding")
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("auxiliary evidence artifact changed")
        return snapshot

    process = artifact(details.get("process_artifact")).json_object()
    raw = artifact(details.get("raw_artifact")).json_object()
    command = process.get("command")
    producer_root = process.get("producer_root")
    if not isinstance(producer_root, str) or not Path(producer_root).is_absolute() or ".." in Path(producer_root).parts:
        raise ValueError("auxiliary process omitted its original canonical producer root")
    spec_binding = process.get("spec_artifact")
    spec = artifact(spec_binding).json_object()
    original_spec = str(Path(producer_root) / spec_binding["path"])
    if not complete_auxiliary_observation(process):
        # Keep the original refusal actionable after its producer was deleted.
        # Commands, environment values and process streams stay in bound DATA.
        raise ValueError(
            "auxiliary process does not establish actual complete source-bound execution: supervision "
            + _supervision_diagnostic(process)
        )
    if (
        process.get("gate") != gate
        or any(process.get(key) != fingerprint for key in ("source_fingerprint", "source_before", "source_after"))
        or process.get("cwd") != producer_root
        or type(process.get("exit_code")) is not int
        or process["exit_code"] != 0
        or process.get("timed_out") is not False
        or process.get("output_limit_exceeded") is not False
        or not isinstance(command, list)
        or not command
        or command[0] != process.get("selected_interpreter")
        or spec.get("gate") != gate
        or spec.get("raw_path") != details.get("raw_artifact", {}).get("path")
        or command != details.get("command")
        or details.get("execution_exit_code") != process.get("exit_code")
        or process.get("raw_artifact") != details.get("raw_artifact")
        or raw.get("gate") != gate
        or raw.get("status") != "pass"
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != 0
    ):
        raise ValueError("auxiliary process does not establish actual complete source-bound execution")
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, validate_audited_auxiliary_command

    validate_audited_auxiliary_command(
        reader,
        process,
        module=WORKER,
        arguments=("--spec", original_spec),
        execution_relative=str(Path(spec_binding["path"]).parent / "execution"),
    )
    digest = process.get("executable_sha256")
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or process.get("executable_sha256_before") != digest
        or process.get("executable_sha256_after") != digest
        or raw.get("runtime", {}).get("executable") != command[0]
        or raw.get("runtime", {}).get("implementation") != "CPython"
        or not str(raw.get("runtime", {}).get("python_version", "")).startswith(("3.12.", "3.13.", "3.14."))
    ):
        raise ValueError("auxiliary original runtime/executable observations are incomplete or changed")
    extra = {"command", "process_artifact", "raw_artifact", "negative_controls", "execution_exit_code"}
    expected = {key: value for key, value in details.items() if key not in extra}
    observed = {key: value for key, value in raw.get("details", {}).items() if key != "negative_controls"}
    if expected != observed:
        raise ValueError("auxiliary summary differs from independently read actual child facts")
    streams = process.get("streams")
    if not isinstance(streams, dict) or set(streams) != {"stdout", "stderr"}:
        raise ValueError("auxiliary execution omitted raw process streams")
    for stream in streams.values():
        artifact(stream)
    if gate == "root:roster":
        import tomllib
        from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

        observations = observed.get("source_roster_observations", [])
        if observed.get("projects") != list(PUBLIC_PROJECT_NAMES) or [
            item.get("scope") for item in observations
        ] != list(PUBLIC_PROJECT_NAMES):
            raise ValueError("actual source roster is incomplete or duplicated")
        for item in observations:
            binding = item.get("metadata_artifact", {})
            if binding.get("path") != f"projects/{item['scope']}/pyproject.toml":
                raise ValueError("actual roster metadata is outside its declared source root")
            metadata = tomllib.loads(artifact(binding).content.decode())["project"]
            if item.get("package") != metadata["name"] or item.get("version") != metadata["version"]:
                raise ValueError("actual roster package observations differ from source metadata bytes")
    if gate.startswith("root:macos:") and process.get("host", {}).get("system") != "Darwin":
        raise ValueError("macOS auxiliary checks did not execute on Darwin")
    if gate == "root:macos:rendering":
        from infrastructure.reporting.native_print_witness_validation import validate_print_witness

        validate_print_witness(
            observed.get("print_witness_artifact"), reader, expected_pid=raw["pid"], expected_runtime=raw["runtime"]
        )
    if gate == "root:macos:process":
        descendant = observed.get("descendant_process", {})
        if (
            observed.get("assertions", {}).get("descendant_cleanup") is not True
            or descendant.get("timed_out") is not True
            or type(descendant.get("exit_code")) is not int
            or descendant["exit_code"] >= 0
        ):
            raise ValueError("macOS process acceptance omitted real descendant timeout/cleanup")
    for control in details.get("negative_controls", []):
        negative = artifact(control.get("artifact")).json_object()
        if negative.get("schema_version") != PROCESS_SCHEMA:
            # Native formal controls are exact records inside the already-bound native execution.
            native_controls = artifact(details.get("native_artifact")).json_object().get("checks", [])
            if not any(
                {key: value for key, value in negative.items() if key != "native_schema"} == check
                for check in native_controls
            ) or not str(negative.get("name", "")).endswith("NegControl"):
                raise ValueError("auxiliary negative control lacks actual supervised/native execution")
            continue
        specification = artifact(negative.get("spec_artifact")).json_object()
        facts = artifact(negative.get("raw_artifact")).json_object()
        if (
            negative.get("gate") != gate
            or negative.get("source_fingerprint") != fingerprint
            or negative.get("cwd") != producer_root
            or negative.get("producer_root") != producer_root
            or negative.get("selected_interpreter") != command[0]
            or specification.get("gate") != gate
            or specification.get("negative") is not True
            or specification.get("raw_path") != negative["raw_artifact"]["path"]
            or facts != negative.get("raw_facts")
            or facts.get("gate") != gate
            or facts.get("status") != "negative-control"
            or facts.get("exit_code") != 23
            or not complete_auxiliary_observation(negative)
            or negative.get("exit_code") != 23
            or negative.get("timed_out") is not False
            or negative.get("output_limit_exceeded") is not False
            or negative.get("executable_sha256_before") != digest
            or negative.get("executable_sha256_after") != digest
        ):
            raise ValueError("auxiliary negative control differs from actual same-worker failing checker")
        validate_audited_auxiliary_command(
            reader,
            negative,
            module=WORKER,
            arguments=("--spec", str(Path(producer_root) / negative["spec_artifact"]["path"])),
            execution_relative=str(Path(negative["spec_artifact"]["path"]).parent / "negative-execution"),
        )
        for stream in negative.get("streams", {}).values():
            artifact(stream)
    if gate.endswith(":pipeline") and details.get("pipeline_schema"):
        from infrastructure.project.public_acceptance_auxiliary_pipeline import validate_portable_pipeline

        validate_portable_pipeline(gate.removesuffix(":pipeline"), details, reader)
    if details.get("native_artifact"):
        native = artifact(details["native_artifact"]).json_object()
        if native.get("status") != "passed":
            raise ValueError("actual native producer failed")
        schema = native.get("schema_version")
        if schema == "template-auxiliary-source-domain-v1":
            from infrastructure.project.public_acceptance_auxiliary_domains import validate_domain

            validate_domain(native, reader)
        elif schema == "template-formal/tool-acceptance/1":
            if (
                native.get("schema_version") != "template-formal/tool-acceptance/1"
                or native.get("source_unchanged") is not True
                or native.get("execution_kind") != "actual"
                or native.get("paid") is not False
            ):
                raise ValueError("formal native producer omitted actual pinned-source custody")
            checks = native.get("checks", [])
            if not checks or any(check.get("status") != "passed" for check in checks):
                raise ValueError("native formal producer omitted successful actual checks")
        elif gate.startswith("templates/template_eda_notebook:"):
            if native.get("source_execution_audit") != "passed" or not native.get("observations"):
                raise ValueError("native notebook omitted its fresh scientific/kernel observations")
        elif schema == "template/literature-unpaid-acceptance/1":
            capability = gate.split(":live:", 1)[-1]
            if (
                native.get("schema_version") != "template/literature-unpaid-acceptance/1"
                or native.get("execution_mode") != "live-unpaid"
                or native.get("paid_integrations") is not False
                or native.get("source_unchanged") is not True
                or native.get("consumed_unchanged") is not True
                or native.get("producer_results", {}).get(capability, {}).get("status") != "passed"
            ):
                raise ValueError("native literature omitted actual complete capability/input custody")
        elif schema == "template-sia/numeric-proposal-receipt/1":
            if (
                native.get("execution_mode") != "ollama_docker_numeric_proposals"
                or native.get("frozen_inputs_verified") is not True
                or native.get("rollback_verified") is not True
                or native.get("production_source_applied") is not False
                or native.get("holdout_used_for_selection") is not False
                or type(native.get("mutation_count")) is not int
                or native["mutation_count"] < 1
                or type(native.get("heldout_cases")) is not int
                or native["heldout_cases"] < 1
            ):
                raise ValueError("native SIA omitted actual mutation/holdout/rollback custody")
        elif native.get("runner") == "docker":
            if (
                native.get("cleanup_verified") is not True
                or native.get("network") != "none"
                or native.get("read_only_root") is not True
                or native.get("host_credentials_forwarded") is not False
                or native.get("returncode") != 0
                or "independent_accuracy" not in native
            ):
                raise ValueError("native Docker omitted isolation/cleanup/independent scoring")
            import csv
            import io

            dataset = list(csv.DictReader(io.StringIO(artifact(native.get("dataset_artifact")).content.decode())))
            predictions = list(
                csv.DictReader(io.StringIO(artifact(native.get("prediction_artifact")).content.decode()))
            )
            predicted = {row["id"]: row["label"] for row in predictions}
            if (
                not dataset
                or len(predicted) != len(dataset)
                or len(predictions) != len(dataset)
                or any(predicted.get(row["id"]) != row["label"] for row in dataset)
                or native.get("independent_accuracy") != 1.0
            ):
                raise ValueError("actual Docker numerical predictions differ from retained public dataset labels")
        elif schema == "template-autoscientists/local-coordination/1":
            count = native.get("settings", {}).get("experiments_per_arm")
            arms = native.get("arms", {})
            if (
                native.get("mode") != "live"
                or native.get("execution_mode") != "local_ollama_multistep_coordination"
                or native.get("paid_integrations_used") is not False
                or native.get("source_applied") is not False
                or native.get("source_unchanged") is not True
                or type(count) is not int
                or not 3 <= count <= 6
                or set(arms) != {"coordinated", "baseline"}
                or any(
                    arm.get("generation_calls_used") != count
                    or len(arm.get("calls", [])) != count
                    or arm.get("objective_evaluations_used") != 3 + 3 * count
                    for arm in arms.values()
                )
            ):
                raise ValueError("native coordination omitted actual matched multi-step arm observations")
        elif schema == "autopoiesis/selected-child-execution/2":
            domains = ["optimization", "dynamics", "statistics", "signal", "graph"]
            records = native.get("executed_children", [])
            if (
                native.get("selection_scope") != "one-per-selected-domain"
                or [record.get("domain") for record in records] != domains
                or any(
                    record.get("status") != "passed"
                    or record.get("source_sha256") != record.get("export_source_sha256")
                    or record.get("independent_analysis", {}).get("status") != "passed"
                    or any(
                        record.get(stage, {}).get("returncode") != 0
                        or record.get(stage, {}).get("timed_out") is not False
                        for stage in ("tests", "analysis")
                    )
                    for record in records
                )
            ):
                raise ValueError("native child execution omitted scientific/export/process observations")
            for record in records:
                analysis = artifact(record.get("retained_analysis_artifact"))
                if analysis.sha256 != record.get("analysis_artifact_sha256"):
                    raise ValueError("actual child numerical artifact differs from independently verified export")
                coverage = artifact(record.get("retained_coverage_artifact")).json_object()
                totals = coverage.get("totals", {})
                if (
                    type(totals.get("percent_covered")) not in {int, float}
                    or not 90 <= totals["percent_covered"] <= 100
                    or not totals.get("num_statements")
                    or not coverage.get("files")
                ):
                    raise ValueError("actual selected child coverage is incomplete")
                import tempfile
                from infrastructure.project.public_acceptance_auxiliary_native import project_module

                checker = project_module(
                    reader.root, "templates/template_autopoiesis", "template_autopoiesis.gates.child_results"
                )
                with tempfile.TemporaryDirectory(prefix="template-child-readback-") as temporary:
                    child_root = Path(temporary)
                    path = child_root / "output/data/analysis_results.json"
                    path.parent.mkdir(parents=True)
                    path.write_bytes(analysis.content)
                    if checker.verify_analysis_results(child_root, record["domain"]) != record["independent_analysis"]:
                        raise ValueError(
                            "retained child scientific values differ from current independent numerical kernels"
                        )
        elif schema == "template-auxiliary-descriptor-v1":
            import csv
            import io

            observations, datasets = native.get("observations", []), native.get("datasets", [])
            if not observations or len(observations) != len(datasets):
                raise ValueError("actual descriptor omitted file byte/row observations")
            for observed, binding in zip(observations, datasets, strict=True):
                data = artifact(binding)
                rows = len(list(csv.reader(io.StringIO(data.content.decode())))) - 1
                if (
                    observed.get("status") != "verified"
                    or observed.get("declared_checksum") != "sha256:" + data.sha256
                    or observed.get("actual_checksum") != "sha256:" + data.sha256
                    or observed.get("actual_rows") != rows
                    or observed.get("declared_rows") != rows
                ):
                    raise ValueError("actual descriptor numerical/checksum observations differ from retained datasets")
        elif schema == "template-auxiliary-methods-dsl-v1":
            methods = native.get("methods", [])
            if (
                not methods
                or native.get("volume_conversion_litres") != 1
                or any(
                    not item.get("plan", {}).get("steps")
                    or not item.get("gates")
                    or any(gate.get("passed") is not True for gate in item["gates"])
                    for item in methods
                )
            ):
                raise ValueError("actual methods compilation omitted dimensional/plan gate observations")
        elif schema == "template-auxiliary-network-faults-v1":
            observations = native.get("observations", {})
            if (
                len(observations.get("clean", [])) != 8
                or observations.get("drop") != []
                or len(observations.get("duplicate", [])) != 16
                or any(item.get("valid") is not False for item in observations.get("corrupt", []))
                or observations.get("reorder") == observations.get("clean")
            ):
                raise ValueError("native network faults did not execute complete proof-of-detection")
        elif schema == "template-auxiliary-pymdp-v1":
            observations = native.get("observations", {})
            steps = observations.get("steps")
            if (
                type(steps) is not int
                or steps <= 0
                or len(observations.get("actions", [])) != steps
                or len(observations.get("trace_steps", [])) != steps
                or not observations.get("runtime_diagnostics")
            ):
                raise ValueError("native pymdp omitted actual inference trace/runtime observations")
        elif schema == "template-auxiliary-active-lean-v1":
            if native.get("build_exit_code") != 0 or not native.get("axiom_audit"):
                raise ValueError("actual Active Inference Lean proof/audit is incomplete")
        elif schema == "template-auxiliary-local-generation-v1":
            request, response = json.loads(native.get("request_json", "")), json.loads(native.get("response_json", ""))
            if (
                request.get("model") != response.get("model")
                or response.get("done") is not True
                or not response.get("response")
                or not native.get("reviewed_sources")
                or native.get("source_unchanged") is not True
                or hashlib.sha256(request.get("prompt", "").encode()).hexdigest() != native.get("prompt_sha256")
                or re.fullmatch(r"[0-9a-f]{64}", str(native.get("model_sha256"))) is None
            ):
                raise ValueError("actual local generation omitted selected model/input/request/response custody")
        elif schema == "template-auxiliary-resource-execution-v1":
            if native.get("executor", {}).get("stdout") != "4\n" or native.get("executor", {}).get("exit_code") != 0:
                raise ValueError("native public resource execution omitted actual computation")
        elif schema == "template-auxiliary-publication-native-v1":
            from pypdf import PdfReader
            import io

            artifacts = native.get("artifacts", [])
            if not artifacts:
                raise ValueError("native publication omitted actual artifacts")
            for record in artifacts:
                pdf = artifact(record.get("pdf"))
                if len(PdfReader(io.BytesIO(pdf.content)).pages) != record.get("pages") or len(
                    record.get("rasters", [])
                ) != record.get("pages"):
                    raise ValueError("native publication page/raster inventory differs from actual PDF bytes")
                from PIL import Image, ImageStat

                for raster in record["rasters"]:
                    with Image.open(io.BytesIO(artifact(raster).content)) as image:
                        if (
                            image.width * image.height > 20_000_000
                            or max(ImageStat.Stat(image.convert("L")).stddev) <= 0
                        ):
                            raise ValueError("actual retained publication raster is blank or oversized")
                if record.get("pptx"):
                    from pptx import Presentation

                    if len(Presentation(io.BytesIO(artifact(record["pptx"]).content)).slides) != record["pages"]:
                        raise ValueError("actual retained PDF/PPTX slide inventories differ")
        else:
            raise ValueError("unrecognized scientific native producer schema")
