"""Real shared workers preserve project evidence and admit only their storage role."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from dataclasses import replace

import pytest
import yaml

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.pipeline.multi_project_parallel import run_projects_in_parallel
from infrastructure.core.pipeline.multi_project_runtime import (
    WORKER_SCHEMA,
    _worker_bootstrap,
    execute_frozen_specs,
    freeze_project_plans,
    freeze_shared_plan,
)
from infrastructure.core.pipeline.multi_project_support import run_shared_infrastructure
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.types import PipelineConfig
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


@pytest.mark.parametrize("field", ["clean", "skip_infra", "resume", "shared_infrastructure"])
@pytest.mark.parametrize("value", ["false", 0, None])
def test_pipeline_configuration_refuses_untyped_execution_policy(tmp_path: Path, field: str, value: object) -> None:
    with pytest.raises(ValueError, match="must be an exact boolean"):
        PipelineConfig("templates/alpha", tmp_path, **{field: value})
    assert not list(tmp_path.iterdir())


def _fixture(root: Path, *, paused: bool = False) -> tuple[str, ...]:
    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(root, names)
    declaration = root / "infrastructure/core/pipeline/pipeline.yaml"
    document = yaml.safe_load(declaration.read_text())
    child = document["stages"][1]
    child.update(name="Project child", key="child", args=["child"])
    child["contract"]["output_artifacts"] = ["projects/{project}/output/data/child.json"]
    if paused:
        document["control"] = {"stage_policies": {2: {"pause_before": True, "require_approval": True}}}
    document["telemetry"] = {"enabled": True, "track_resources": False, "track_diagnostics": False}
    document["stages"] = document["stages"][:2]
    declaration.write_text(yaml.safe_dump(document))
    return names


@pytest.mark.timeout(240)
@pytest.mark.parametrize("paused", [False, True])
def test_actual_shared_gate_preserves_all_ordinary_project_run_files(tmp_path: Path, paused: bool) -> None:
    names = _fixture(tmp_path, paused=paused)
    specs = freeze_project_plans(names[:1], tmp_path, mode="core", resume=False, timeout=90)
    _, runs = execute_frozen_specs(specs, workers=1, deadline=time.monotonic() + 90)
    assert runs[names[0]].exit_code == (75 if paused else 0)
    output = tmp_path / "projects" / names[0] / "output"
    before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    for required in (
        ".checkpoints/pipeline_checkpoint.json",
        ".pipeline/execution.json",
        "reports/pipeline_report.json",
        "logs/pipeline.log",
        "reports/telemetry.json",
    ):
        assert Path(required) in before
    if paused:
        assert Path("hitl/waiting.json") in before
    else:
        assert Path("reports/artifact_manifest.json") in before
        assert any(path.parts[:2] == ("reports", "snapshots") for path in before)
    shared = freeze_shared_plan(specs)
    actual = run_shared_infrastructure(shared, deadline=time.monotonic() + 90)
    assert actual.exit_code == 0 and actual.run_result.outcomes[0].child_exit_code == 0
    after = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    assert after == before
    isolated = shared.config.runtime_output_dir
    assert isolated.is_relative_to(tmp_path / "output/.pipeline/shared_infrastructure")
    for required in (
        ".checkpoints/pipeline_checkpoint.json",
        ".pipeline/execution.json",
        "reports/artifact_manifest.json",
        "reports/pipeline_report.json",
        "logs/pipeline.log",
        "logs/multi_project_worker.log",
        "reports/telemetry.json",
    ):
        assert (isolated / required).is_file()
    record = json.loads((isolated / ".pipeline/execution.json").read_text())
    assert record["shared_infrastructure"] is True and record["expected_stage_keys"] == ["infra_tests"]
    if not paused:
        manifest = json.loads((isolated / "reports/artifact_manifest.json").read_text())
        assert any(row["path"] == "output/data/child.json" for row in manifest["entries"])


@pytest.mark.timeout(420)
@pytest.mark.parametrize("workers", [1, 2])
def test_actual_serial_and_parallel_resume_keep_fresh_shared_gate_and_project_cache(
    tmp_path: Path, workers: int
) -> None:
    names = _fixture(tmp_path)
    fresh = run_projects_in_parallel(names, repo_root=tmp_path, max_workers=workers, run_timeout_seconds=180)
    assert fresh.exit_code == 0
    assert fresh.elapsed_seconds <= 195
    resumed = run_projects_in_parallel(
        names, repo_root=tmp_path, max_workers=workers, resume=True, run_timeout_seconds=180
    )
    assert resumed.exit_code == 0 and resumed.shared_infrastructure_result is not None
    assert resumed.elapsed_seconds <= 195
    assert resumed.shared_infrastructure_result.run_result.outcomes[0].status is StageStatus.SUCCEEDED
    assert all(run.outcomes[0].status is StageStatus.CACHED for run in resumed.run_results.values())
    order = (tmp_path / "process_order.log").read_text().splitlines()
    assert order.count("templates/alpha:infra") == 2
    assert order.count("templates/alpha:child") == order.count("templates/beta:child") == 1


@pytest.mark.timeout(45)
@pytest.mark.parametrize(
    "mutation",
    [
        "project_selection",
        "resume",
        "missing_role",
        "untyped_role",
        "forged_target",
        "forged_policy",
        "untyped_clean",
        "untyped_skip_infra",
        "untyped_resume",
    ],
)
def test_actual_worker_refuses_storage_role_before_any_executor_or_child(tmp_path: Path, mutation: str) -> None:
    names = _fixture(tmp_path)
    if mutation == "forged_target":
        (tmp_path / "scripts/unselected.py").write_text(
            "from pathlib import Path\nPath('unselected-marker').write_text('executed')\n"
        )
    specs = freeze_project_plans(names[:1], tmp_path, mode="core", resume=False, timeout=30)
    spec = specs[0] if mutation == "project_selection" else freeze_shared_plan(specs)
    if mutation in {"forged_target", "forged_policy"}:
        stage = spec.plan.stages[0]
        forged = (
            replace(stage, script="scripts/unselected.py")
            if mutation == "forged_target"
            else replace(stage, policy=replace(stage.policy, require_approval=True))
        )
        spec = replace(spec, plan=replace(spec.plan, stages=(forged,)))
    payload = {
        "schema_version": WORKER_SCHEMA,
        "nonce": "actual-role-control",
        "deadline_monotonic": time.monotonic() + 30,
        **spec.to_dict(),
    }
    if mutation == "missing_role":
        del payload["config"]["shared_infrastructure"]
    elif mutation == "untyped_role":
        payload["config"]["shared_infrastructure"] = "true"
    elif mutation.startswith("untyped_"):
        payload["config"][mutation.removeprefix("untyped_")] = "false"
    else:
        payload["config"]["shared_infrastructure"] = True
        if mutation == "resume":
            payload["config"]["resume"] = True
    request = tmp_path / "request.json"
    content = json.dumps(payload, sort_keys=True).encode()
    request.write_bytes(content)
    implementation = Path(__file__).resolve().parents[5]
    child = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _worker_bootstrap(implementation, spec.config.project_dir),
            str(tmp_path / "bytecode"),
            str(implementation),
            "--request",
            str(request),
            "--request-sha256",
            hashlib.sha256(content).hexdigest(),
            "--receipt",
            str(tmp_path / "result.json"),
        ],
        cwd=tmp_path,
        env=build_bounded_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 1, child.stderr
    assert not (tmp_path / "process_order.log").exists()
    assert not (tmp_path / "unselected-marker").exists()
    assert not (tmp_path / "result.json").exists()
    assert not (tmp_path / "output").exists()
    assert not any((tmp_path / "projects" / name / "output/logs").exists() for name in names)
