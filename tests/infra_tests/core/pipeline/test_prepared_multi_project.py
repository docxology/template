"""Prepared multi-project plans remain bound across validation and real workers."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.core.pipeline.multi_project_runtime import (
    ProjectExecutionSpec,
    freeze_project_plans,
    freeze_shared_plan,
    selected_project_config,
)
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.project.discovery import discover_projects
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


def _prepare(
    root: Path, *, shared: bool = True
) -> tuple[MultiProjectOrchestrator, tuple[ProjectExecutionSpec, ...], ProjectExecutionSpec | None]:
    scaffold_pipeline(root, ("templates/alpha", "templates/beta"), canonical_gate=False)
    # Exercise the actual shared-gate role rather than merely borrowing its key.
    gate = root / "scripts/pipeline/stage_01_test.py"
    gate.parent.mkdir(parents=True, exist_ok=True)
    gate.write_bytes((root / "scripts/stage.py").read_bytes())
    definition = root / "infrastructure/core/pipeline/pipeline.yaml"
    declaration = yaml.safe_load(definition.read_text())
    declaration["stages"][0]["script"] = "scripts/pipeline/stage_01_test.py"
    declaration["stages"][0]["args"].append("--infra-only")
    definition.write_text(yaml.safe_dump(declaration))
    config = MultiProjectConfig(
        root,
        discover_projects(root),
        run_infra_tests=shared,
        run_timeout_seconds=180,
        deadline_monotonic=time.monotonic() + 180,
    )
    specs = freeze_project_plans(config.projects, root, mode=config.mode, resume=config.resume, timeout=180)
    return MultiProjectOrchestrator(config), specs, freeze_shared_plan(specs) if shared else None


def _outputs(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for output in (*root.glob("projects/templates/*/output"), root / "output")
        if output.exists()
        for path in (output, *output.rglob("*"))
    }


@pytest.mark.parametrize(
    "fault",
    [
        "selection",
        "order",
        "repo",
        "projects_dir",
        "mode",
        "resume",
        "timeout",
        "boolean",
        "boolean_mutated",
        "plan_project",
        "plan_mode",
        "plan_timeout",
        "shared_missing",
        "shared_extra",
        "shared_selection",
        "shared_provenance",
        "shared_target",
        "shared_config",
    ],
)
def test_prepared_identity_refusal_precedes_all_runtime_writes(tmp_path: Path, fault: str) -> None:
    orchestrator, specs, shared = _prepare(tmp_path)
    assert shared is not None
    before = _outputs(tmp_path)
    if fault == "boolean":
        # Typed configuration refuses a non-boolean flag at construction, so the
        # forged spec can never reach admission or a worker.
        with pytest.raises(ValueError, match="exact boolean"):
            replace(specs[0].config, skip_infra=1)
        assert _outputs(tmp_path) == before
        assert not (tmp_path / "process_order.log").exists()
        return
    if fault == "boolean_mutated":
        # A caller can still mutate an admitted-looking config after construction;
        # prepared admission must refuse the non-boolean flag itself.
        specs[0].config.skip_infra = 1  # type: ignore[assignment]
    elif fault == "selection":
        specs = specs[:1]
    elif fault == "order":
        specs = tuple(reversed(specs))
    elif fault in {"repo", "projects_dir", "mode", "resume", "timeout"}:
        changes = {
            "repo": {"repo_root": tmp_path / "other"},
            "projects_dir": {"projects_dir": "other"},
            "mode": {"mode": "live"},
            "resume": {"resume": True},
            "timeout": {"run_timeout_seconds": 181},
        }[fault]
        specs = (replace(specs[0], config=replace(specs[0].config, **changes)), specs[1])
    elif fault.startswith("plan_"):
        changes = {
            "plan_project": {"project": "templates/other"},
            "plan_mode": {"mode": "live"},
            "plan_timeout": {"run_timeout_seconds": 181},
        }[fault]
        specs = (replace(specs[0], plan=replace(specs[0].plan, **changes)), specs[1])
    elif fault == "shared_missing":
        shared = None
    elif fault == "shared_extra":
        orchestrator.config.run_infra_tests = False
    elif fault == "shared_selection":
        shared = replace(shared, plan=replace(shared.plan, stages=specs[0].plan.stages))
    elif fault == "shared_provenance":
        shared = replace(shared, plan=replace(shared.plan, provenance="projects/templates/alpha/pipeline.yaml"))
    elif fault == "shared_target":
        wrong = replace(shared.plan.stages[0], method=None, script="scripts/stage.py", arguments=())
        shared = replace(shared, plan=replace(shared.plan, stages=(wrong,)))
    else:
        shared = replace(shared, config=replace(shared.config, resume=True))
    with pytest.raises(ValueError):
        orchestrator.execute_prepared_projects(specs, shared)
    assert _outputs(tmp_path) == before
    assert not (tmp_path / "process_order.log").exists()


def test_prepared_admission_does_not_retain_caller_mutable_configuration(tmp_path: Path) -> None:
    orchestrator, specs, _ = _prepare(tmp_path)
    expected = selected_project_config(
        orchestrator.config.projects[0], tmp_path, mode="core", resume=False, timeout=180
    )
    admitted = orchestrator._admit_prepared_spec(specs[0], expected)
    before = admitted.to_dict()
    specs[0].config.resume = True
    specs[0].config.projects_dir = "other"
    assert admitted.config is not specs[0].config
    assert admitted.to_dict() == before
    assert admitted.plan.digest == specs[0].plan.digest


@pytest.mark.parametrize("target", ["method", "script"])
def test_prepared_custom_key_cannot_repeat_the_shared_infrastructure_role(tmp_path: Path, target: str) -> None:
    """Direct typed plans retain the once-only gate even under renamed stage keys."""
    from infrastructure.core.pipeline.target_contracts import effective_target_tags

    orchestrator, specs, shared = _prepare(tmp_path)
    assert shared is not None
    stage = replace(
        shared.plan.stages[0],
        key="renamed_shared_gate",
        name="Renamed Shared Gate",
        method="run_infrastructure_tests" if target == "method" else None,
        script="scripts/pipeline/stage_01_test.py" if target == "script" else None,
        arguments=() if target == "method" else ("--infra-only", "--project", specs[0].plan.project),
    )
    stage = replace(stage, tags=effective_target_tags(stage.tags, stage.script, stage.method))
    direct = replace(specs[0], plan=replace(specs[0].plan, stages=(stage,)))
    before = _outputs(tmp_path)
    with pytest.raises(ValueError, match="once-only gate"):
        orchestrator.execute_prepared_projects((direct, specs[1]), shared)
    assert _outputs(tmp_path) == before
    assert not (tmp_path / "process_order.log").exists()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("with_shared", [False, True])
def test_actual_prepared_workers_refuse_changed_definition_without_recompiling(
    tmp_path: Path, with_shared: bool
) -> None:
    orchestrator, specs, shared = _prepare(tmp_path, shared=with_shared)
    frozen_digests = tuple(spec.plan.digest for spec in specs)
    definition = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    definition.write_text(definition.read_text() + "\n# Definition changed after pure preflight.\n")
    if with_shared:
        # The parent re-admits the shared plan against held declarations before
        # its once-only gate starts, so drift refuses before any worker exists.
        with pytest.raises(ValueError, match="differs from its admitted declaration"):
            orchestrator.execute_prepared_projects(specs, shared)
        assert tuple(spec.plan.digest for spec in specs) == frozen_digests
        assert not (tmp_path / "process_order.log").exists()
        return
    result = orchestrator.execute_prepared_projects(specs, shared)
    assert result.exit_code == 75
    assert tuple(spec.plan.digest for spec in specs) == frozen_digests
    assert not (tmp_path / "process_order.log").exists()
    runs = (
        (result.shared_infrastructure_result.run_result,)
        if result.shared_infrastructure_result is not None
        else tuple(result.run_results.values())
    )
    assert runs and all(not run.complete for run in runs)
    assert all(run.outcomes[0].status is StageStatus.BLOCKED for run in runs)
    assert all(run.outcomes[0].child_exit_code is None for run in runs)
    assert all("source changed" in run.outcomes[0].diagnostic.lower() for run in runs)


@pytest.mark.timeout(240)
def test_actual_prepared_transport_preserves_exact_plans_and_once_only_shared_gate(tmp_path: Path) -> None:
    orchestrator, specs, shared = _prepare(tmp_path)
    assert shared is not None
    expected = {spec.plan.project: spec.plan.digest for spec in specs}
    result = orchestrator.execute_prepared_projects(specs, shared)
    assert result.exit_code == 0 and result.expected_projects == tuple(expected)
    assert result.shared_infrastructure_result is not None
    assert result.shared_infrastructure_result.run_result.expected_stage_keys == ("infra_tests",)
    assert result.shared_infrastructure_result.run_result.outcomes[0].child_exit_code == 0
    order = (tmp_path / "process_order.log").read_text().splitlines()
    assert order == ["templates/alpha:infra", "templates/alpha:analysis", "templates/beta:analysis"]
    for spec in specs:
        record = json.loads((spec.config.project_dir / "output/.pipeline/execution.json").read_text())
        assert record["plan_digest"] == expected[spec.plan.project]
        assert record["plan"] == json.loads(json.dumps(spec.plan.to_dict()))
        assert record["expected_stage_keys"] == ["analysis"]
        assert record["complete"] is True and record["exit_code"] == 0
