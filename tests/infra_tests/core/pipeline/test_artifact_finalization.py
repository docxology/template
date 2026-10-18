"""Regression tests for artifact-manifest finalization at validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.artifacts import (
    aggregate_artifact_manifests,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)
from infrastructure.core.pipeline.types import PipelineControlConfig, StageContract, StagePolicy


_PIPELINE_YAML = """\
stages:
  - name: Render Outputs
    key: render_pdf
    script: scripts/pipeline/stage_03_render.py
    tags: [core]
  - name: Provenance Commitment Gate
    key: validate
    script: scripts/pipeline/stage_04_validate.py
    depends_on: [Render Outputs]
    tags: [core]
  - name: Review Outputs
    key: llm_reviews
    script: scripts/pipeline/stage_06_llm_review.py
    depends_on: [Provenance Commitment Gate]
    tags: [llm]
  - name: Translate Outputs
    key: llm_translations
    script: scripts/pipeline/stage_06_llm_review.py
    depends_on: [Provenance Commitment Gate]
    tags: [llm]
  - name: Copy Outputs
    key: copy
    script: scripts/pipeline/stage_05_copy.py
    depends_on: [Provenance Commitment Gate]
    tags: [core]
telemetry:
  enabled: false
"""

_RENDER_SCRIPT = """\
from pathlib import Path
import sys

project = sys.argv[sys.argv.index("--project") + 1]
artifact = Path.cwd() / "projects" / project / "output" / "data" / "result.txt"
artifact.parent.mkdir(parents=True, exist_ok=True)
artifact.with_name("retired.txt").unlink(missing_ok=True)
artifact.write_text("rendered\\n", encoding="utf-8")
"""

_VALIDATE_SCRIPT = """\
from pathlib import Path
import hashlib
import json
import sys

project = sys.argv[sys.argv.index("--project") + 1]
root = Path.cwd()
manifest = root / "projects" / project / "output" / "reports" / "artifact_manifest.json"
for entry in json.loads(manifest.read_bytes())["entries"]:
    artifact = root / "projects" / project / entry["path"]
    assert artifact.is_file(), f"stale removed artifact: {entry['path']}"
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == entry["sha256"], f"stale digest: {entry['path']}"
digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
(root / "validation-manifest.sha256").write_text(digest + "\\n", encoding="utf-8")
"""

_ASSERT_COMMITMENT_SCRIPT = """\
from pathlib import Path
import hashlib
import sys

project = sys.argv[sys.argv.index("--project") + 1]
root = Path.cwd()
manifest = root / "projects" / project / "output" / "reports" / "artifact_manifest.json"
expected = (root / "validation-manifest.sha256").read_text(encoding="utf-8").strip()
actual = hashlib.sha256(manifest.read_bytes()).hexdigest()
raise SystemExit(0 if actual == expected else 9)
"""


def _make_pipeline_repo(root: Path, *, validation_key: str = "validate") -> tuple[Path, Path]:
    project = root / "projects" / "template_test"
    (project / "output").mkdir(parents=True)
    for name in ("src", "tests", "manuscript"):
        (project / name).mkdir()
    scripts = root / "scripts" / "pipeline"
    scripts.mkdir(parents=True)
    (scripts / "stage_03_render.py").write_text(_RENDER_SCRIPT, encoding="utf-8")
    (scripts / "stage_04_validate.py").write_text(_VALIDATE_SCRIPT, encoding="utf-8")
    (scripts / "stage_05_copy.py").write_text(_ASSERT_COMMITMENT_SCRIPT, encoding="utf-8")
    (scripts / "stage_06_llm_review.py").write_text(_ASSERT_COMMITMENT_SCRIPT, encoding="utf-8")
    pipeline_path = root / "pipeline.yaml"
    pipeline_path.write_text(_PIPELINE_YAML.replace("key: validate", f"key: {validation_key}"), encoding="utf-8")
    return project, pipeline_path


def _manifest_digest(project: Path) -> str:
    manifest = project / "output" / "reports" / "artifact_manifest.json"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_duplicate_validation_display_name_is_rejected_before_child_execution(tmp_path: Path) -> None:
    """Declarations cannot disguise two different keys with one validation name."""
    project, pipeline_path = _make_pipeline_repo(tmp_path)
    pipeline_path.write_text(
        pipeline_path.read_text().replace("name: Render Outputs", "name: Provenance Commitment Gate")
    )
    executor = PipelineExecutor(PipelineConfig("template_test", tmp_path, pipeline_path=pipeline_path, clean=False))
    with pytest.raises(ValueError, match="Duplicate stage names"):
        executor.execute_pipeline()
    assert not (project / "output/data/result.txt").exists()
    assert not (tmp_path / "validation-manifest.sha256").exists()


def test_direct_boundary_requires_the_planned_key_or_keyless_display_fallback(tmp_path: Path) -> None:
    """An explicit nonboundary key cannot borrow a canonical validator's name."""
    project, pipeline_path = _make_pipeline_repo(tmp_path, validation_key="commitment_check")
    executor = PipelineExecutor(PipelineConfig("template_test", tmp_path, pipeline_path=pipeline_path, clean=False))
    executor.preview_stage_names()
    assert executor.execution_plan is not None
    stages = executor.execution_plan.bind(executor)
    render, validation = stages[:2]

    executor._prepare_artifact_manifest_for_stage(render._replace(name=validation.name), [])

    assert not executor._artifact_manifest_sealed
    assert not (project / "output/reports/artifact_manifest.json").exists()
    executor._prepare_artifact_manifest_for_stage(validation._replace(key=""), [])
    assert executor._artifact_manifest_sealed


@pytest.mark.parametrize(
    "full_pipeline",
    [pytest.param(False, marks=pytest.mark.timeout(120)), pytest.param(True, marks=pytest.mark.timeout(240))],
)
@pytest.mark.parametrize("validation_key", ["validate", "commitment_check"])
def test_validation_seals_aggregate_before_core_and_full_downstream_stages(
    tmp_path: Path,
    full_pipeline: bool,
    validation_key: str,
) -> None:
    """Validation observes the final aggregate, which downstream stages preserve."""
    root = tmp_path / "repo"
    project, pipeline_path = _make_pipeline_repo(root, validation_key=validation_key)
    data = project / "output/data"
    data.mkdir()
    (data / "result.txt").write_text("old rendering\n")
    (data / "retired.txt").write_text("retired output\n")
    for number, name in ((2, "Render Outputs"), (99, "Retired Output Stage")):
        write_stage_artifact_manifest(
            repo_root=root,
            project_dir=project,
            stage_num=number,
            stage_name=name,
            contract=StageContract(output_artifacts=("projects/{project}/output/",)),
        )
    stage_directory = project / "output/.pipeline/artifacts"
    historical = {path: path.read_bytes() for path in stage_directory.glob("stage-*.json")}
    executor = PipelineExecutor(
        PipelineConfig(
            project_name="template_test",
            repo_root=root,
            pipeline_path=pipeline_path,
            clean=False,
            mode="live" if full_pipeline else "core",
        )
    )

    results = executor.execute_pipeline()

    assert all(result.success for result in results)
    assert executor.run_result(results).complete
    committed_digest = (root / "validation-manifest.sha256").read_text(encoding="utf-8").strip()
    assert _manifest_digest(project) == committed_digest
    stage_manifests = sorted((project / "output" / ".pipeline" / "artifacts").glob("stage-*.json"))
    assert len(stage_manifests) == 3
    assert all(path.read_bytes() == body for path, body in historical.items())
    payload = json.loads((project / "output/reports/artifact_manifest.json").read_bytes())
    assert {entry["path"] for entry in payload["entries"]} == {"output/data/result.txt"}
    assert payload["entries"][0]["stage_num"] == 1
    assert payload["entries"][0]["stage_name"] == "Render Outputs"
    assert payload["entries"][0]["sha256"] == hashlib.sha256((data / "result.txt").read_bytes()).hexdigest()


@pytest.mark.timeout(120)
@pytest.mark.parametrize("validation_key", ["validate", "commitment_check"])
def test_resume_after_validation_preserves_committed_aggregate(tmp_path: Path, validation_key: str) -> None:
    """A resumed post-validation stage must not re-aggregate committed evidence."""
    root = tmp_path / "repo"
    project, pipeline_path = _make_pipeline_repo(root, validation_key=validation_key)
    executor = PipelineExecutor(
        PipelineConfig(
            project_name="template_test",
            repo_root=root,
            pipeline_path=pipeline_path,
            clean=False,
            total_stages=3,
            control=PipelineControlConfig(stage_policies={2: StagePolicy(pause_after=True)}),
        )
    )
    paused = executor.execute_pipeline()
    assert executor.run_result(paused).exit_code == 75
    committed_digest = _manifest_digest(project)
    assert (root / "validation-manifest.sha256").read_text().strip() == committed_digest
    HitlController(project_output_dir=project / "output").approve("Reviewed exact validation commitment")
    executor.config.resume = True

    results = executor.execute_pipeline()

    assert [result.stage_name for result in results] == [
        "Render Outputs",
        "Provenance Commitment Gate",
        "Copy Outputs",
    ]
    assert all(result.success for result in results)
    assert executor.run_result(results).complete
    assert _manifest_digest(project) == committed_digest
    stage_manifests = sorted((project / "output" / ".pipeline" / "artifacts").glob("stage-*.json"))
    assert len(stage_manifests) == 1 and "render-outputs" in stage_manifests[0].name


@pytest.mark.parametrize("fault", ["missing", "metadata", "symlink"])
def test_latest_stage_manifest_refuses_unowned_nomination(tmp_path: Path, fault: str) -> None:
    """A nominated completed record cannot fall back to a fresh output scan."""
    project = tmp_path / "projects/template_test"
    output = project / "output"
    (output / "data").mkdir(parents=True)
    (output / "data/result.txt").write_text("actual\n")
    stage = write_stage_artifact_manifest(
        repo_root=tmp_path,
        project_dir=project,
        stage_num=1,
        stage_name="Render Outputs",
        contract=StageContract(output_artifacts=("projects/{project}/output/",)),
    )
    aggregate_artifact_manifests(output, inventory_mode=stage.inventory_mode)
    assert validate_artifact_manifest(
        aggregate_artifact_manifests(output, inventory_mode=stage.inventory_mode),
        project_dir=project,
        expected_inventory_mode=stage.inventory_mode,
    ).valid
    aggregate = output / "reports/artifact_manifest.json"
    original = aggregate.read_bytes()
    record = output / ".pipeline/artifacts/stage-01-render-outputs.json"
    if fault == "missing":
        record.unlink()
    elif fault == "metadata":
        payload = json.loads(record.read_bytes())
        payload["entries"][0]["stage_num"] = 2
        record.write_text(json.dumps(payload))
    else:
        outside = tmp_path / "outside.json"
        outside.write_bytes(record.read_bytes())
        record.unlink()
        record.symlink_to(outside)
    with pytest.raises(ValueError, match="latest stage"):
        aggregate_artifact_manifests(output, inventory_mode=stage.inventory_mode, latest_stage=(1, "Render Outputs"))
    assert aggregate.read_bytes() == original


def test_latest_stage_manifest_never_rehashes_subsequent_output_mutation(tmp_path: Path) -> None:
    """Priority changes record ordering, never the bytes the producer attested."""
    project = tmp_path / "projects/template_test"
    output = project / "output"
    (output / "data").mkdir(parents=True)
    artifact = output / "data/result.txt"
    artifact.write_text("attested\n")
    stage = write_stage_artifact_manifest(
        repo_root=tmp_path,
        project_dir=project,
        stage_num=1,
        stage_name="Render Outputs",
        contract=StageContract(output_artifacts=("projects/{project}/output/",)),
    )
    artifact.write_text("changed after producer\n")
    (output / "data/unattested.txt").write_text("added after producer\n")
    aggregate = aggregate_artifact_manifests(
        output, inventory_mode=stage.inventory_mode, latest_stage=(1, "Render Outputs")
    )
    assert aggregate.entries == stage.entries
    report = validate_artifact_manifest(aggregate, project_dir=project, expected_inventory_mode=stage.inventory_mode)
    assert "changed artifact: output/data/result.txt" in report.issues
    assert "unattested stable artifact: output/data/unattested.txt" in report.issues

    artifact.unlink()
    (output / "data/unattested.txt").unlink()
    empty = write_stage_artifact_manifest(
        repo_root=tmp_path,
        project_dir=project,
        stage_num=2,
        stage_name="Empty Outputs",
        contract=StageContract(output_artifacts=("projects/{project}/output/",)),
    )
    assert not empty.entries
    artifact.write_text("added after empty producer\n")
    aggregate = aggregate_artifact_manifests(
        output, inventory_mode=stage.inventory_mode, latest_stage=(2, "Empty Outputs")
    )
    assert not aggregate.entries
    assert (
        "unattested stable artifact: output/data/result.txt"
        in validate_artifact_manifest(
            aggregate, project_dir=project, expected_inventory_mode=stage.inventory_mode
        ).issues
    )


@pytest.mark.timeout(120)
def test_manifest_commit_failure_preserves_original_producer_exit(tmp_path: Path) -> None:
    """A real producer0 cannot hide an actual manifest persistence failure."""
    project, pipeline_path = _make_pipeline_repo(tmp_path)
    artifact = project / "output/data/result.txt"
    artifact.parent.mkdir()
    artifact.write_text("rendered\n")
    stage = write_stage_artifact_manifest(
        repo_root=tmp_path,
        project_dir=project,
        stage_num=2,
        stage_name="Render Outputs",
        contract=StageContract(output_artifacts=("projects/{project}/output/",)),
    )
    aggregate_artifact_manifests(project / "output", inventory_mode=stage.inventory_mode)
    assert validate_artifact_manifest(
        aggregate_artifact_manifests(project / "output", inventory_mode=stage.inventory_mode),
        project_dir=project,
        expected_inventory_mode=stage.inventory_mode,
    ).valid
    original = _manifest_digest(project)
    render = tmp_path / "scripts/pipeline/stage_03_render.py"
    render.write_text(
        render.read_text()
        + """
control = artifact.parents[1] / ".pipeline/artifacts"
control.rename(Path.cwd() / "preserved-original-controls")
control.write_text("actual persistence obstruction\\n")
"""
    )
    executor = PipelineExecutor(PipelineConfig("template_test", tmp_path, pipeline_path=pipeline_path, clean=False))
    results = executor.execute_pipeline()
    assert len(results) == 1
    assert not results[0].success and not results[0].stage_completed
    assert results[0].exit_code == 1
    assert results[0].outcome is not None
    assert results[0].outcome.child_exit_code == 0
    assert results[0].outcome.status.value == "failed"
    assert "Artifact manifest commit failed" in results[0].error_message
    assert executor.run_result(results).exit_code == 1
    assert not (tmp_path / "validation-manifest.sha256").exists()
    assert _manifest_digest(project) == original
    assert (tmp_path / "preserved-original-controls/stage-02-render-outputs.json").is_file()


@pytest.mark.timeout(120)
def test_missing_latest_stage_blocks_validation_after_real_render_pause(tmp_path: Path) -> None:
    """A valid old aggregate cannot replace its missing completed-stage record."""
    project, pipeline_path = _make_pipeline_repo(tmp_path)
    executor = PipelineExecutor(
        PipelineConfig(
            "template_test",
            tmp_path,
            pipeline_path=pipeline_path,
            clean=False,
            control=PipelineControlConfig(stage_policies={1: StagePolicy(pause_after=True)}),
        )
    )
    paused = executor.execute_pipeline()
    assert executor.run_result(paused).exit_code == 75
    assert len(paused) == 1 and paused[0].stage_completed
    assert paused[0].outcome is not None and paused[0].outcome.child_exit_code == 0
    original = _manifest_digest(project)
    HitlController(project_output_dir=project / "output").approve("Review exact completed render")
    (project / "output/.pipeline/artifacts/stage-01-render-outputs.json").unlink()
    executor.config.resume = True
    results = executor.execute_pipeline()
    assert len(results) == 2, [result.error_message for result in results]
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
    assert results[-1].stage_key == "validate"
    assert not results[-1].success and not results[-1].stage_completed
    assert results[-1].outcome is not None
    assert results[-1].outcome.child_exit_code is None
    assert results[-1].outcome.status.value == "blocked"
    assert "latest stage" in results[-1].error_message
    assert executor.run_result(results).exit_code == 75
    assert not executor._artifact_manifest_sealed
    assert not (tmp_path / "validation-manifest.sha256").exists()
    assert _manifest_digest(project) == original
