"""Read-only compilation shares execution's source, controls, and plugins."""

from __future__ import annotations

from pathlib import Path
from dataclasses import replace
import time

import yaml
import pytest

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import PlannedStage, compile_execution_plan
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    StagePolicy,
    StageContract,
    StageHooks,
)

pytestmark = pytest.mark.timeout(60)


def _config(tmp_path: Path) -> PipelineConfig:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "child.py").write_text("pass\n")
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": [{"name": "Child", "key": "child", "script": "scripts/child.py"}],
                "control": {"stage_policies": {1: {"require_approval": True}}},
                "telemetry": {"enabled": False},
            }
        )
    )
    return PipelineConfig("demo", tmp_path, clean=False)


def test_compiler_creates_no_project_output_and_matches_executor(tmp_path: Path) -> None:
    config = _config(tmp_path)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    plan = compile_execution_plan(config)
    assert plan.expected_stage_keys == ("child",)
    assert plan.stages[0].policy.require_approval
    assert len(plan.environment_identity) == 64
    assert plan.schema_version == 3
    assert not (config.project_dir / "output").exists()
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
    executor = PipelineExecutor(config)
    executor.preview_stage_names()
    assert executor.execution_plan is not None
    assert executor.execution_plan.to_dict() == plan.to_dict()


def test_read_only_compiler_includes_plugins_and_preserves_target_policy(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (config.project_dir / "pipeline_plugins.yaml").write_text(
        yaml.safe_dump(
            {
                "plugins": [
                    {
                        "name": "Extra",
                        "key": "extra",
                        "script": "scripts/child.py",
                        "depends_on": ["Child"],
                        "contract": {
                            "output_artifacts": ["output/extra.txt"],
                            "definition_of_done": "Extra data is produced",
                            "failure_code": "extra_failed",
                        },
                    }
                ]
            }
        )
    )
    config.control = PipelineControlConfig(stage_policies={2: StagePolicy(require_approval=True)})
    full = compile_execution_plan(config)
    selected = compile_execution_plan(config, target_stage="extra")
    assert full.expected_stage_keys == ("child", "extra")
    assert selected.expected_stage_keys == ("extra",)
    assert selected.stages[0].policy.require_approval
    assert selected.stages[0].dependencies == ("child",)
    assert not (config.project_dir / "output").exists()


def test_explicit_execution_source_overrides_project_and_methods_sources(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (config.project_dir / "methods_pipeline.yaml").write_text("invalid methods input that execution must not read")
    explicit = tmp_path / "selected.yaml"
    explicit.write_text(
        yaml.safe_dump(
            {
                "stages": [{"name": "Selected", "key": "selected", "script": "scripts/child.py"}],
                "control": {"stage_policies": {1: {"pause_before": True}}},
            }
        )
    )
    config.pipeline_path = explicit
    plan = compile_execution_plan(config)
    assert plan.expected_stage_keys == ("selected",)
    assert plan.stages[0].policy.pause_before
    assert not plan.stages[0].policy.require_approval
    assert plan.provenance == "selected.yaml"
    assert not (config.project_dir / "output").exists()


def test_compiler_accepts_an_already_resolved_control_override(tmp_path: Path) -> None:
    config = _config(tmp_path)
    control = PipelineControlConfig(hitl_mode="checkpoint", stage_policies={1: StagePolicy(pause_after=True)})
    plan = compile_execution_plan(config, control)
    assert plan.hitl_mode == "checkpoint"
    assert plan.stages[0].policy.pause_after
    assert not plan.stages[0].policy.require_approval
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("selection", [None, "analysis", ("child", "analysis")])
@pytest.mark.parametrize("timeout", ["0", "none", "NaN", "inf", "-1", "bad"])
def test_analysis_selection_rejects_invalid_deadline_without_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selection: str | tuple[str, ...] | None, timeout: str
) -> None:
    config = _config(tmp_path)
    declaration = yaml.safe_load((config.project_dir / "pipeline.yaml").read_text())
    declaration["stages"].append(
        {"name": "Analysis", "key": "analysis", "script": "scripts/child.py", "depends_on": ["Child"]}
    )
    (config.project_dir / "pipeline.yaml").write_text(yaml.safe_dump(declaration))
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", timeout)
    with pytest.raises(ValueError, match="ANALYSIS_SCRIPT_TIMEOUT_SEC must be positive finite"):
        if selection is None:
            compile_execution_plan(config)
        elif isinstance(selection, str):
            compile_execution_plan(config, target_stage=selection)
        else:
            compile_execution_plan(config, target_stages=selection)
    assert not (config.project_dir / "output").exists()
    assert compile_execution_plan(config, target_stage="child").expected_stage_keys == ("child",)


def test_custom_analysis_key_cannot_bypass_canonical_target_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    script = tmp_path / "scripts/pipeline/stage_02_analysis.py"
    script.parent.mkdir()
    script.write_text("raise RuntimeError('must not execute')\n")
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {"stages": [{"name": "Domain Analysis", "key": "domain", "script": str(script.relative_to(tmp_path))}]}
        )
    )
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", "unlimited")
    with pytest.raises(ValueError, match="positive finite"):
        compile_execution_plan(config, target_stage="domain")
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("method", ["run_analysis", "run_render", "run_validation", "_run_script", "config"])
def test_retired_or_arbitrary_method_refuses_before_execution(tmp_path: Path, method: str) -> None:
    config = _config(tmp_path)
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump({"stages": [{"name": "Domain", "key": "domain", "method": method}]})
    )
    with pytest.raises(ValueError, match="Unsupported canonical method target"):
        compile_execution_plan(config, target_stage="domain")
    assert not (config.project_dir / "output").exists()


def test_composed_analysis_overflow_refuses_before_any_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    (config.project_dir / "scripts").mkdir()
    for name in ("first.py", "second.py"):
        (config.project_dir / "scripts" / name).write_text("raise RuntimeError('must not execute')\n")
    script = tmp_path / "scripts/pipeline/stage_02_analysis.py"
    script.parent.mkdir()
    script.write_text("raise RuntimeError('must not execute')\n")
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump({"stages": [{"name": "Domain", "key": "domain", "script": str(script.relative_to(tmp_path))}]})
    )
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", "1e308")
    with pytest.raises(ValueError, match="Composed analysis run timeout must be finite"):
        compile_execution_plan(config, target_stage="domain")
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("method", ["_run_clean_outputs", "run_project_tests", "run_infrastructure_tests"])
@pytest.mark.parametrize("arguments", [[], ["ignored-before-4"]])
def test_canonical_methods_admit_only_their_actual_argument_contract(
    tmp_path: Path, method: str, arguments: list[str]
) -> None:
    config = _config(tmp_path)
    script = tmp_path / "scripts/pipeline/stage_01_test.py"
    script.parent.mkdir()
    script.write_text("raise RuntimeError('must not execute')\n")
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump({"stages": [{"name": "Direct", "key": "direct", "method": method, "args": arguments}]})
    )
    if arguments:
        with pytest.raises(ValueError, match="does not accept arguments"):
            compile_execution_plan(config, target_stage="direct")
    else:
        assert compile_execution_plan(config, target_stage="direct").stages[0].method == method
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("kind", ["missing", "directory", "link", "fifo", "oversized", "unsupported"])
def test_script_target_requires_bounded_real_repository_python_file(tmp_path: Path, kind: str) -> None:
    config = _config(tmp_path)
    target = tmp_path / "scripts/target.py"
    if kind == "directory":
        target.mkdir()
    elif kind == "link":
        target.symlink_to(tmp_path / "scripts/child.py")
    elif kind == "fifo":
        import os

        os.mkfifo(target)
    elif kind == "oversized":
        with target.open("wb") as stream:
            stream.truncate(8 * 1024 * 1024 + 1)
    elif kind == "unsupported":
        target = tmp_path / "scripts/target.sh"
        target.write_text("exit 0\n")
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump({"stages": [{"name": "Target", "key": "target", "script": str(target.relative_to(tmp_path))}]})
    )
    with pytest.raises((ValueError, OSError)):
        compile_execution_plan(config)
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("kind", ["method", "arguments", "missing_script"])
def test_direct_frozen_plan_cannot_bypass_canonical_admission(tmp_path: Path, kind: str) -> None:
    config = _config(tmp_path)
    plan = compile_execution_plan(config)
    executor = PipelineExecutor(config)
    stage = plan.stages[0]
    if kind == "method":
        stage = replace(stage, script=None, method="run_analysis", arguments=())
    elif kind == "arguments":
        stage = replace(stage, script=None, method="_run_clean_outputs", arguments=("ignored",))
    else:
        stage = replace(stage, script="scripts/missing.py")
    with pytest.raises((ValueError, OSError)):
        executor.execute_plan(replace(plan, stages=(stage,)))
    assert not (config.project_dir / "output/.pipeline/execution.json").exists()


def test_public_execution_canonicalizes_mutable_transport_aliases_before_use(tmp_path: Path) -> None:
    config = _config(tmp_path)
    plan = compile_execution_plan(config)
    arguments = list(plan.stages[0].arguments)
    stages = [replace(plan.stages[0], arguments=arguments)]  # type: ignore[arg-type]
    supplied = replace(plan, stages=stages)  # type: ignore[arg-type]
    executor = PipelineExecutor(config)
    result = executor.execute_plan(supplied, deadline_monotonic=time.monotonic() - 1)
    assert result[0].exit_code == 124
    assert executor.execution_plan is not None
    assert executor.execution_plan.digest == plan.digest
    assert isinstance(executor.execution_plan.stages, tuple)
    assert isinstance(executor.execution_plan.stages[0].arguments, tuple)
    arguments.append("unreviewed")
    stages.clear()
    assert executor.execution_plan.digest == plan.digest
    assert not (config.project_dir / "output/.pipeline/execution.json").exists()


@pytest.mark.parametrize(
    "script,method",
    [
        (None, "_run_clean_outputs"),
        ("scripts/pipeline/stage_00_setup.py", None),
        ("scripts/pipeline/stage_01_test.py", None),
        ("scripts/pipeline/stage_05_copy.py", None),
        ("./scripts/pipeline/stage_05_copy.py", None),
        ("scripts//pipeline/./stage_05_copy.py", None),
        ("scripts/pipeline/stage_06_llm_review.py", None),
        ("scripts/pipeline/stage_08_connector_search.py", None),
        ("scripts/pipeline/stage_09_provenance_record.py", None),
        ("scripts/pipeline/stage_12_metadata.py", None),
        ("scripts/runner/archive_publication.py", None),
        ("scripts/runner/bundle_executable.py", None),
    ],
)
def test_effectful_canonical_target_cannot_reuse_under_a_custom_stage_key(
    script: str | None, method: str | None
) -> None:
    stage = PlannedStage(
        "custom", "Custom", script, method, (), (), (), StageContract(), StageHooks(), StagePolicy(), False
    )
    assert not stage.cacheable


def test_pure_target_remains_eligible_for_source_bound_reuse() -> None:
    stage = PlannedStage(
        "custom",
        "Custom",
        "scripts/pipeline/stage_04_validate.py",
        None,
        (),
        (),
        (),
        StageContract(),
        StageHooks(),
        StagePolicy(),
        False,
    )
    assert stage.cacheable


@pytest.mark.parametrize(
    "script",
    [
        "scripts/pipeline/stage_06_llm_review.py",
        "scripts/pipeline/stage_08_connector_search.py",
        "scripts/runner/archive_publication.py",
    ],
)
def test_canonical_live_target_requires_live_mode_even_under_custom_key(tmp_path: Path, script: str) -> None:
    config = _config(tmp_path)
    target = tmp_path / script
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("raise RuntimeError('preview must not execute')\n")
    declaration = config.project_dir / "pipeline.yaml"
    declaration.write_text(
        yaml.safe_dump({"stages": [{"name": "Aliased", "key": "alias", "script": script, "tags": []}]})
    )
    with pytest.raises(ValueError, match="explicit --mode live"):
        compile_execution_plan(config, target_stage="alias")
    config.mode = "live"
    plan = compile_execution_plan(config, target_stage="alias")
    assert "live" in plan.stages[0].tags and not plan.stages[0].cacheable
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize(
    "script",
    [
        "scripts/pipeline/stage_08_connector_search.py",
        "scripts/pipeline/stage_09_provenance_record.py",
        "scripts/pipeline/stage_11_ebook.py",
        "scripts/pipeline/stage_12_metadata.py",
        "scripts/pipeline/stage_13_docxplus.py",
        "scripts/runner/archive_publication.py",
        "scripts/runner/bundle_executable.py",
    ],
)
def test_canonical_opt_in_targets_remain_explicit_with_empty_declared_opt_in_tags(tmp_path: Path, script: str) -> None:
    config = _config(tmp_path)
    config.mode = "live"
    target = tmp_path / script
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("raise RuntimeError('preview must not execute')\n")
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "opt_in_tags": [],
                "stages": [
                    {"name": "Child", "key": "child", "script": "scripts/child.py"},
                    {"name": "Aliased", "key": "alias", "script": script, "tags": []},
                ],
            }
        )
    )
    assert compile_execution_plan(config).expected_stage_keys == ("child",)
    assert compile_execution_plan(config, target_stage="alias").expected_stage_keys == ("alias",)
    assert not (config.project_dir / "output").exists()


@pytest.mark.parametrize("method", [False, True])
def test_actual_infrastructure_target_honors_skip_infra_with_custom_key(tmp_path: Path, method: bool) -> None:
    config = _config(tmp_path)
    config.skip_infra = True
    target = tmp_path / "scripts/pipeline/stage_01_test.py"
    target.parent.mkdir()
    target.write_text("raise RuntimeError('preview must not execute')\n")
    selected = (
        {"method": "run_infrastructure_tests"}
        if method
        else {"script": "scripts/pipeline/stage_01_test.py", "args": ["--infra-only"]}
    )
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": [
                    {"name": "Child", "key": "child", "script": "scripts/child.py"},
                    {"name": "Shared", "key": "shared", **selected},
                ]
            }
        )
    )
    assert compile_execution_plan(config).expected_stage_keys == ("child",)
    assert compile_execution_plan(config, target_stage="shared").expected_stage_keys == ("shared",)


def test_cleanup_selection_uses_actual_method_and_requires_nonempty_result(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (config.project_dir / "pipeline.yaml").write_text(
        yaml.safe_dump({"stages": [{"name": "Cleanup", "key": "custom", "method": "_run_clean_outputs"}]})
    )
    with pytest.raises(ValueError, match="nonempty selected"):
        compile_execution_plan(config)
    config.clean = True
    assert compile_execution_plan(config).expected_stage_keys == ("custom",)
