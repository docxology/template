"""Real artifact custody controls without substituting any producer."""

from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifact_contracts import capture_inputs, declared_input_paths, require_outputs
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.types import PipelineConfig, StageContract, StageSpec


def test_repository_inputs_resolve_to_repository_and_mutation_is_detected(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    source = tmp_path / "infrastructure"
    source.mkdir()
    consumed = source / "algorithm.py"
    consumed.write_text("value = 1\n")
    contract = StageContract(input_artifacts=("infrastructure/",))
    assert declared_input_paths(tmp_path, project, contract) == (source,)
    snapshot = capture_inputs(PipelineConfig("demo", tmp_path), contract)
    consumed.write_text("value = 2\n")
    assert snapshot.current_digest() != snapshot.digest


def test_required_output_missing_is_not_completion(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    with pytest.raises(ValueError, match="Required output"):
        require_outputs(PipelineConfig("demo", tmp_path), StageContract(output_artifacts=("output/data/result.csv",)))


def test_mutable_declaration_is_explicit_and_does_not_hide_other_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    reports = project / "output" / "reports"
    data = project / "output" / "data"
    reports.mkdir(parents=True)
    data.mkdir()
    values = data / "observations.csv"
    values.write_text("value\n1\n")
    contract = StageContract(
        input_artifacts=("output/",), output_artifacts=("output/reports/",), mutable_artifacts=("output/reports/",)
    )
    snapshot = capture_inputs(PipelineConfig("demo", tmp_path), contract)
    (reports / "validation.json").write_text("{}")
    assert snapshot.current_digest() == snapshot.digest
    values.write_text("value\n2\n")
    assert snapshot.current_digest() != snapshot.digest


def test_cross_project_input_requires_explicit_custody(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    with pytest.raises(ValueError, match="Cross-project"):
        declared_input_paths(tmp_path, project, StageContract(input_artifacts=("projects/other/data.csv",)))


def test_approval_binds_external_repository_consumed_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    output = project / "output"
    output.mkdir(parents=True)
    consumed = tmp_path / "pyproject.toml"
    consumed.write_text("[project]\nname='first'\n")
    controller = HitlController(project_output_dir=output, repo_root=tmp_path, run_id="run", plan_digest="plan")
    spec = StageSpec("Child", lambda: True, StageContract(input_artifacts=("pyproject.toml",)), key="child")
    controller.pause(stage_num=1, stage_name="Child", reason="approval_required", stage_spec=spec)
    consumed.write_text("[project]\nname='second'\n")
    with pytest.raises(ValueError, match="contents changed"):
        HitlController(project_output_dir=output).approve()
    assert controller.waiting_path.exists()


def test_approval_binds_declared_delivery_outputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    output = project / "output"
    output.mkdir(parents=True)
    artifact = tmp_path / "output" / "demo" / "data" / "result.txt"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("reviewed")
    controller = HitlController(project_output_dir=output, run_id="run", plan_digest="plan")
    spec = StageSpec(
        "Copy", lambda: True, StageContract(output_artifacts=("output/{project}/data/result.txt",)), key="copy"
    )
    controller.pause(stage_num=1, stage_name="Copy", reason="approval_required", stage_spec=spec)
    artifact.write_text("unreviewed")
    with pytest.raises(ValueError, match="contents changed"):
        controller.approve()
    assert controller.waiting_path.exists()


@pytest.mark.parametrize("record", ['{"action":"consume"}', '{"action":"typo"}'])
def test_semantically_corrupt_consumption_refuses_replay(tmp_path: Path, record: str) -> None:
    output = tmp_path / "output"
    controller = HitlController(project_output_dir=output, run_id="run", plan_digest="plan")
    spec = StageSpec("Child", lambda: True, key="child")
    controller.pause(stage_num=1, stage_name="Child", reason="approval_required", stage_spec=spec)
    controller.approve()
    assert controller.decision_for_stage(spec) == "approve"
    rows = controller.decisions_path.read_text().splitlines()
    controller.decisions_path.write_text("\n".join((*rows[:-1], record)) + "\n")
    with pytest.raises(ValueError, match="authorization refused"):
        HitlController(project_output_dir=output, run_id="run", plan_digest="plan").decision_for_stage(spec)
