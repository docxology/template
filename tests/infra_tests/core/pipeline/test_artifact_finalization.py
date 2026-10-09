"""Regression tests for artifact-manifest finalization at validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.types import PipelineControlConfig, StagePolicy


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
artifact.write_text("rendered\\n", encoding="utf-8")
"""

_VALIDATE_SCRIPT = """\
from pathlib import Path
import hashlib
import sys

project = sys.argv[sys.argv.index("--project") + 1]
root = Path.cwd()
manifest = root / "projects" / project / "output" / "reports" / "artifact_manifest.json"
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
    assert len(stage_manifests) == 1
    assert "render-outputs" in stage_manifests[0].name


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
