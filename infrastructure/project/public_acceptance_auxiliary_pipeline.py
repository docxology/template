"""Portable custody of a genuine complete core pipeline in disposable public source.

Hashes admit retained bytes and original observations; authenticated same-SHA
hosted handoff establishes origin. Per-key hashes do not reconstruct the original
aggregate environment digest. General pipeline/cache identities are unchanged.
"""

from __future__ import annotations

import hashlib
import argparse
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

from infrastructure.project.public_acceptance_auxiliary_pipeline_failure import (
    AuxiliaryPipelineFailure as AuxiliaryPipelineFailure,
    _retain_pipeline_child_facts as _retain_pipeline_child_facts,
    retain_pipeline_failure_logs,
)
from infrastructure.project.public_acceptance_auxiliary_pipeline_environment import (
    _LABELS as _LABELS,
    _clean_environment as _clean_environment,
    _components as _components,
    _read_logical_plan as _read_logical_plan,
    _source_records as _source_records,
    environment_observation as environment_observation,
    copy_public_pipeline_source,
)


SCHEMA = "template-auxiliary-pipeline-portable-v1"
_REQUIRED = frozenset({"setup", "project_tests", "analysis", "render_pdf", "validate", "copy"})


def child(spec_path: str) -> int:
    """Run the unmodified canonical executor from this copied implementation."""
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.execution_records import execution_record_payload
    from infrastructure.core.pipeline.fingerprints import tree_records
    from infrastructure.core.pipeline.types import PipelineConfig

    spec = json.loads(Path(spec_path).read_text())
    root, scope = Path(spec["root"]), spec["scope"]
    if root != Path.cwd() or Path(__file__).resolve().parents[1] != root / "infrastructure":
        raise ValueError("pipeline child did not import the admitted disposable source")
    before = _components(root, scope)
    records_before = _source_records(root, scope)
    env_before = environment_observation(root, scope)
    config = PipelineConfig(scope, root, mode="core", clean=False, skip_infra=True)
    config.run_timeout_seconds = spec["budget"]
    executor = PipelineExecutor(config)
    results = executor.execute_pipeline(deadline_monotonic=spec.get("operation_deadline"))
    execution = execution_record_payload(executor, results)
    after = _components(root, scope)
    env_after = environment_observation(root, scope)
    result = {
        "schema_version": SCHEMA,
        "producer_root": str(root),
        "scope": scope,
        "runtime": {
            "executable": sys.executable,
            "python_version": sys.version,
            "implementation": sys.implementation.name,
            "pycache_prefix": sys.pycache_prefix,
        },
        "host": {"system": platform.system(), "machine": platform.machine()},
        "source_before": before,
        "source_records_before": records_before,
        "source_records_after": _source_records(root, scope),
        "output_records": tree_records(config.project_dir / "output"),
        "source_after": after,
        "environment_before": env_before,
        "environment_after": env_after,
        "execution": execution,
        "original_exit_code": executor.run_result(results).exit_code,
    }
    Path(spec["result_path"]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return int(result["original_exit_code"])


def main() -> int:
    """Fixed audited module entrypoints for actual execution or logical DATA."""
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--child-spec")
    mode.add_argument("--logical-root", type=Path)
    parser.add_argument("--scope")
    parser.add_argument("--budget")
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    if args.child_spec is not None:
        return child(args.child_spec)
    from infrastructure.core.pipeline.plan import compile_execution_plan
    from infrastructure.core.pipeline.types import PipelineConfig
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    root = args.logical_root
    if (
        root != Path.cwd()
        or Path(__file__).resolve().parents[1] != root / "infrastructure"
        or args.scope not in PUBLIC_PROJECT_NAMES
        or args.result is None
        or args.budget is None
    ):
        raise ValueError("logical pipeline reader needs the exact Source root and declared scope")
    config = PipelineConfig(args.scope, root, mode="core", clean=False, skip_infra=True)
    config.run_timeout_seconds = json.loads(args.budget)
    plan = compile_execution_plan(config)
    args.result.write_text(
        json.dumps(
            {
                "plan": plan.to_dict(),
                "components": _components(root, args.scope),
                "source_records": _source_records(root, args.scope),
            }
        )
    )
    return 0


def run_pipeline(
    root: Path, scope: str, directory: Path, budget: int, *, operation_deadline: float | None = None
) -> dict[str, Any]:
    from infrastructure.core.execution_policy import apply_execution_policy
    from infrastructure.core.pipeline.fingerprints import tree_records
    from infrastructure.project.public_acceptance_auxiliary import supervise

    from infrastructure.core.pipeline.execution_session import compose_run_deadline

    deadline = compose_run_deadline(budget, operation_deadline)
    directory = evidence_directory(root, directory)
    reader = SnapshotReader(root, operation_deadline=deadline)
    with tempfile.TemporaryDirectory(prefix="pipeline-source-") as temporary:
        copied = Path(temporary).resolve() / "source"
        copied.mkdir()
        print(
            json.dumps(
                {
                    "role": "diagnostic-only-pipeline-progress",
                    "scope": scope,
                    "phase": "copy-public-source",
                    "original_deadline_monotonic": deadline,
                }
            ),
            flush=True,
        )
        files = copy_public_pipeline_source(root, copied, reader)
        print(
            json.dumps(
                {
                    "role": "diagnostic-only-pipeline-progress",
                    "scope": scope,
                    "phase": "prepare-original-child",
                    "public_source_files": len(files),
                }
            ),
            flush=True,
        )
        # File-only exports omit authored empty directories that enter the unchanged compiler's identity.
        for source_root, rows in _source_records(root, scope):
            for relative, kind, _ in rows:
                if kind == "directory":
                    (copied / source_root / relative).mkdir(parents=True, exist_ok=True)
        if not reader.unchanged():
            raise ValueError("public pipeline source changed during confined export")
        output = copied / "projects" / scope / "output"
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--", f"projects/{scope}/output"],
            cwd=root,
            capture_output=True,
            timeout=15,
            check=True,
        )
        baseline = []
        for relative in tracked.stdout.decode().split("\0"):
            if not relative:
                continue
            snapshot = reader.read(relative)
            destination = copied / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(snapshot.content)
            baseline.append(
                {
                    "relative": Path(relative).relative_to(Path("projects") / scope / "output").as_posix(),
                    "source_binding": {"path": relative, "sha256": snapshot.sha256},
                }
            )
        inner = copied / "output/readiness/pipeline-child"
        inner.mkdir(parents=True)
        spec = {
            "root": str(copied),
            "scope": scope,
            "budget": budget,
            "operation_deadline": deadline,
            "result_path": str(inner / "facts.json"),
        }
        spec_path = inner / "spec.json"
        spec_path.write_text(json.dumps(spec, sort_keys=True))
        # Read only source-owned public controls; protected values are never inspected.
        environment = _clean_environment()
        for key in (
            "PYTHONPATH",
            "PYTHONHOME",
            "VIRTUAL_ENV",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "COVERAGE_PROCESS_START",
            "COVERAGE_RCFILE",
            "UV_PROJECT_ENVIRONMENT",
        ):
            environment.pop(key, None)
        environment.update(
            UV_OFFLINE="1",
            UV_NO_SYNC="1",
            UV_NO_MANAGED_PYTHON="1",
            UV_PYTHON_DOWNLOADS="never",
            TEMPLATE_ROOT_PYTHON=sys.executable,
            UV_PYTHON=sys.executable,
            TEMPLATE_SKIP_LINK_SYNC="1",
            PYTHONUNBUFFERED="1",
            MPLBACKEND="Agg",
            MPLCONFIGDIR=str(inner / "font-cache"),
            COVERAGE_FILE=str(copied / "projects" / scope / ".coverage.project"),
            HYPOTHESIS_STORAGE_DIRECTORY=str(inner / "hypothesis"),
            OMP_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            PYTEST_ADDOPTS=f"--benchmark-storage=file://{copied / 'projects' / scope / 'output/.pipeline/benchmarks'}",
        )
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
        environment = apply_execution_policy(environment, root, mode="core")
        environment = apply_execution_policy(environment, copied, mode="core")
        from infrastructure.project.public_acceptance_auxiliary_bootstrap import (
            PIPELINE,
            PAYLOAD,
            prepare_audited_auxiliary_command,
        )

        command, payload = prepare_audited_auxiliary_command(
            Path(sys.executable), copied, PIPELINE, ("--child-spec", str(spec_path)), inner / "execution"
        )
        print(
            json.dumps(
                {
                    "role": "diagnostic-only-pipeline-progress",
                    "scope": scope,
                    "phase": "launch-original-child",
                    "original_deadline_monotonic": deadline,
                }
            ),
            flush=True,
        )
        process = supervise(
            command,
            copied,
            inner / "execution",
            deadline,
            environment=environment,
            bootstrap_payload=payload,
            stream_diagnostics=True,
        )
        retained_streams = {
            name: write_binary(
                root, directory / "pipeline-child" / f"{name}.txt", (copied / binding["path"]).read_bytes()
            )
            for name, binding in process["streams"].items()
        }
        process_binding = write_json(root, directory / "pipeline-child-process.json", process)
        spec_binding = write_binary(root, directory / "pipeline-child-spec.json", spec_path.read_bytes())
        bootstrap_binding = write_binary(
            root, directory / "pipeline-child-bootstrap.payload", (inner / "execution" / PAYLOAD).read_bytes()
        )
        try:
            facts, facts_binding = _retain_pipeline_child_facts(
                root,
                directory,
                inner,
                process,
                {
                    "process_artifact": process_binding,
                    "spec_artifact": spec_binding,
                    "streams": retained_streams,
                    "bootstrap_artifact": bootstrap_binding,
                },
            )
        except AuxiliaryPipelineFailure as error:
            error.observation["retained_failure_logs"] = retain_pipeline_failure_logs(root, directory, copied, output)
            raise
        artifacts: list[dict[str, Any]] = []
        size = 0
        for relative, kind, digest in tree_records(output):
            if kind != "file":
                continue
            content = (output / relative).read_bytes()
            size += len(content)
            if size > 256 * 1024 * 1024 or len(content) > 64 * 1024 * 1024 or len(artifacts) >= 4000:
                raise ValueError("actual pipeline output exceeds its confined retained-byte ceiling")
            artifacts.append(
                {
                    "relative": relative.removeprefix("./"),
                    "sha256": digest,
                    "binding": write_binary(root, directory / "pipeline-outputs" / relative, content),
                }
            )
        details = {
            "pipeline_schema": SCHEMA,
            "mode": "core",
            "run_id": facts["execution"]["run_id"],
            "selection": {"skip_clean": True, "skip_infra": True},
            "plan": facts["execution"]["plan"],
            "plan_digest": facts["execution"]["plan_digest"],
            "expected_stage_keys": facts["execution"]["expected_stage_keys"],
            "outcomes": facts["execution"]["outcomes"],
            "portable_pipeline_artifact": write_json(
                root,
                directory / "portable-pipeline.json",
                {
                    "schema_version": SCHEMA,
                    "scope": scope,
                    "source_files": files,
                    "process_artifact": process_binding,
                    "spec_artifact": spec_binding,
                    "facts_artifact": facts_binding,
                    "bootstrap_artifact": bootstrap_binding,
                    "retained_streams": retained_streams,
                    "output_before": baseline,
                    "output_after": artifacts,
                },
            ),
        }
        logical_observations: list[dict[str, Any]] = []
        try:
            validate_portable_pipeline(
                scope,
                details,
                SnapshotReader(root, operation_deadline=deadline),
                logical_observations=logical_observations,
            )
        except (OSError, ValueError, TypeError, KeyError, TimeoutError) as error:
            diagnostic_bindings: dict[str, Any] = {
                "process_artifact": process_binding,
                "facts_artifact": facts_binding,
                "portable_pipeline_artifact": details["portable_pipeline_artifact"],
            }
            if logical_observations:
                diagnostic_bindings["logical_plan_artifact"] = write_json(
                    root, directory / "pipeline-logical-plan.json", logical_observations[-1]
                )
            raise AuxiliaryPipelineFailure(process, facts, diagnostic_bindings, validation_error=str(error)) from error
        return details


def validate_portable_pipeline(
    scope: str,
    details: dict[str, Any],
    reader: SnapshotReader,
    *,
    logical_observations: list[dict[str, Any]] | None = None,
) -> None:
    from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
    from infrastructure.core.pipeline.plan import ExecutionPlan
    from infrastructure.reporting.readiness_receipts import public_source_paths

    def artifact(binding: dict[str, str]) -> Any:
        snapshot = reader.read(binding["path"])
        if snapshot.sha256 != binding["sha256"]:
            raise ValueError("portable pipeline artifact differs from original byte custody")
        return snapshot

    if details.get("pipeline_schema") != SCHEMA or not isinstance(details.get("portable_pipeline_artifact"), dict):
        raise ValueError("versioned portable pipeline requires its original artifact binding")
    custody = artifact(details["portable_pipeline_artifact"]).json_object()
    if (
        custody.get("schema_version") != SCHEMA
        or custody.get("scope") != scope
        or not isinstance(custody.get("output_before"), list)
    ):
        raise ValueError("portable pipeline scope/schema/fresh-output boundary differs")
    expected_files = {path.relative_to(reader.root).as_posix() for path in public_source_paths(reader.root)}
    bound_files = custody["source_files"]
    if len(bound_files) != len(expected_files) or {row["path"] for row in bound_files} != expected_files:
        raise ValueError("portable pipeline omitted or duplicated current public source")
    for binding in bound_files:
        snapshot = artifact(binding)
        if type(binding.get("executable")) is not bool or binding["executable"] != bool(
            snapshot.path.stat(follow_symlinks=False).st_mode & stat.S_IXUSR
        ):
            raise ValueError("portable pipeline changed a public source executable role")
    process = artifact(custody["process_artifact"]).json_object()
    spec = artifact(custody["spec_artifact"]).json_object()
    facts = artifact(custody["facts_artifact"]).json_object()
    producer = facts["producer_root"]
    executable_hash = process.get("executable_sha256")
    if (
        not complete_auxiliary_observation(process)
        or process.get("producer_root") != producer
        or process.get("cwd") != producer
        or process.get("exit_code") != 0
        or process.get("timed_out") is not False
        or process.get("output_limit_exceeded") is not False
        or not isinstance(executable_hash, str)
        or len(executable_hash) != 64
        or process.get("executable_sha256_before") != executable_hash
        or process.get("executable_sha256_after") != executable_hash
        or spec
        != {
            "root": producer,
            "scope": scope,
            "budget": details["plan"]["run_timeout_seconds"],
            "result_path": str(Path(producer) / "output/readiness/pipeline-child/facts.json"),
        }
        or facts.get("schema_version") != SCHEMA
        or facts.get("scope") != scope
        or facts.get("original_exit_code") != 0
        or facts.get("host") != process.get("host")
        or facts["runtime"]["executable"] != process["selected_interpreter"]
    ):
        raise ValueError("portable pipeline original child/process/spec/exit custody differs")
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import (
        PIPELINE,
        validate_audited_auxiliary_command,
    )

    validate_audited_auxiliary_command(
        reader,
        process,
        module=PIPELINE,
        arguments=("--child-spec", str(Path(producer) / "output/readiness/pipeline-child/spec.json")),
        execution_relative="output/readiness/pipeline-child/execution",
        retained_payload=custody["bootstrap_artifact"],
    )
    for name, binding in custody["retained_streams"].items():
        if artifact(binding).sha256 != process["streams"][name]["sha256"]:
            raise ValueError("portable pipeline original streams changed")
    before, after = facts["source_before"], facts["source_after"]
    env_before, env_after = facts["environment_before"], facts["environment_after"]
    if (
        before != after
        or env_before != env_after
        or facts["source_records_before"] != facts["source_records_after"]
        or canonical_digest(facts["source_records_before"]) != before["source"]
    ):
        raise ValueError("portable pipeline original source/tool/runtime/environment changed")
    if (
        set(before) != {"source", "python", "tools"}
        or before["python"]["version"] != facts["runtime"]["python_version"]
        or before["python"]["implementation"] != "cpython"
        or facts["runtime"]["implementation"] != "cpython"
        or env_before["key_hashes_digest"] != canonical_digest(env_before["key_hashes"])
    ):
        raise ValueError("portable pipeline original source/environment component custody differs")
    from infrastructure.core.secrets import is_secret_env_name

    if any(is_secret_env_name(key) for key in env_before["key_hashes"]):
        raise ValueError("portable pipeline observed protected credential names")
    if (
        env_before["labels"].get("TEMPLATE_ROOT_PYTHON") != process["selected_interpreter"]
        or env_before["labels"].get("UV_PYTHON") != process["selected_interpreter"]
        or env_before["labels"].get("UV_OFFLINE") != "1"
        or env_before["labels"].get("PYTEST_ADDOPTS")
        != f"--benchmark-storage=file://{Path(producer) / 'projects' / scope / 'output/.pipeline/benchmarks'}"
        or env_before["labels"].get("PYTHONPYCACHEPREFIX") != facts["runtime"]["pycache_prefix"]
        or before["tools"].get("python") != {"path": process["executable"], "content": [[".", "file", executable_hash]]}
    ):
        raise ValueError("portable pipeline original interpreter/tools/fresh-cache labels differ")
    for key, value in env_before["labels"].items():
        if key not in _LABELS or env_before["key_hashes"].get(key) != hashlib.sha256(value.encode()).hexdigest():
            raise ValueError("portable pipeline original controlled labels differ from hashed observations")
    execution = facts["execution"]
    original = ExecutionPlan.from_dict(details["plan"], expected_digest=details["plan_digest"])
    if (
        original.source_identity != canonical_digest(before)
        or original.environment_identity != env_before["aggregate_digest"]
        or execution["source_identity"] != original.source_identity
        or execution["environment_identity"] != original.environment_identity
        or execution["plan_digest"] != original.digest
        or execution["plan"] != details["plan"]
        or execution["outcomes"] != details["outcomes"]
        or execution["run_id"] != details["run_id"]
        or execution["complete"] is not True
        or execution["exit_code"] != 0
        or execution["selection"] != details["selection"]
        or details["selection"] != {"skip_clean": True, "skip_infra": True}
        or not _REQUIRED.issubset(original.expected_stage_keys)
    ):
        raise ValueError("portable pipeline original full plan/environment/selection/outcomes differ")
    for row in custody["output_before"]:
        binding = row["source_binding"]
        if binding["path"] != f"projects/{scope}/output/{row['relative']}":
            raise ValueError("portable pipeline baseline is outside current public output scope")
        artifact(binding)
    logical = _read_logical_plan(
        reader.root,
        scope,
        original.run_timeout_seconds,
        env_before["labels"]["SOURCE_DATE_EPOCH"],
        deadline=reader.operation_deadline,
    )
    if logical_observations is not None:
        # Diagnostic DATA only: preserve the actual independently compiled plan
        # before comparing identities. It can never authorize a failed gate.
        logical_observations.append(logical)
    current = ExecutionPlan.from_dict(logical["plan"])
    current_components = logical["components"]
    if current_components["source"] != before["source"] or logical["source_records"] != facts["source_records_before"]:
        raise ValueError("portable pipeline current logical source differs from original source component")
    reconstructed = replace(
        current, source_identity=canonical_digest(before), environment_identity=env_before["aggregate_digest"]
    )
    if reconstructed.digest != original.digest or details["expected_stage_keys"] != list(original.expected_stage_keys):
        raise ValueError("portable pipeline differs from independently compiled complete logical source plan")
    outcomes = []
    for row in details["outcomes"]:
        values = dict(row)
        values["status"] = StageStatus(values["status"])
        values["attempt_exit_codes"] = tuple(values["attempt_exit_codes"])
        outcome = StageOutcome(**values)
        if outcome.status is not StageStatus.SUCCEEDED:
            raise ValueError("portable pipeline requires every original stage freshly succeeded")
        outcomes.append(outcome)
    result = RunResult(original.expected_stage_keys, tuple(outcomes))
    if not result.complete or result.exit_code != 0:
        raise ValueError("portable pipeline omitted/reordered/duplicated fresh stage outcomes")
    files = custody["output_after"]
    original_files = {
        relative.removeprefix("./"): digest for relative, kind, digest in facts["output_records"] if kind == "file"
    }
    if {row["relative"]: row["sha256"] for row in files} != original_files:
        raise ValueError("portable pipeline omitted/added/rewrote original fresh output inventory")
    if not files or len({row["relative"] for row in files}) != len(files):
        raise ValueError("portable pipeline has no fresh complete output inventory")
    for row in files:
        relative = Path(row["relative"])
        if relative.is_absolute() or ".." in relative.parts or artifact(row["binding"]).sha256 != row["sha256"]:
            raise ValueError("portable pipeline fresh output byte binding is unsafe or changed")
    execution_file = next((row for row in files if row["relative"] == ".pipeline/execution.json"), None)
    if execution_file is None or artifact(execution_file["binding"]).json_object() != execution:
        raise ValueError("portable pipeline omitted its original complete execution record")


if __name__ == "__main__":
    raise SystemExit(main())
