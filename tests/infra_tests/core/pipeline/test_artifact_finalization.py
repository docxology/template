"""Regression tests for artifact-manifest finalization at validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor
from infrastructure.core.pipeline.artifacts import aggregate_artifact_manifests
from infrastructure.core.runtime.checkpoint import StageResult


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


def _make_pipeline_repo(root: Path) -> tuple[Path, Path]:
    project = root / "projects" / "template_test"
    (project / "output").mkdir(parents=True)
    scripts = root / "scripts" / "pipeline"
    scripts.mkdir(parents=True)
    (scripts / "stage_03_render.py").write_text(_RENDER_SCRIPT, encoding="utf-8")
    (scripts / "stage_04_validate.py").write_text(_VALIDATE_SCRIPT, encoding="utf-8")
    (scripts / "stage_05_copy.py").write_text(_ASSERT_COMMITMENT_SCRIPT, encoding="utf-8")
    (scripts / "stage_06_llm_review.py").write_text(_ASSERT_COMMITMENT_SCRIPT, encoding="utf-8")
    pipeline_path = root / "pipeline.yaml"
    pipeline_path.write_text(_PIPELINE_YAML, encoding="utf-8")
    return project, pipeline_path


def _manifest_digest(project: Path) -> str:
    manifest = project / "output" / "reports" / "artifact_manifest.json"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.mark.timeout(120)
@pytest.mark.parametrize("full_pipeline", [False, True])
def test_validation_seals_aggregate_before_core_and_full_downstream_stages(
    tmp_path: Path,
    full_pipeline: bool,
) -> None:
    """Validation observes the final aggregate, which downstream stages preserve."""
    root = tmp_path / "repo"
    project, pipeline_path = _make_pipeline_repo(root)
    executor = PipelineExecutor(
        PipelineConfig(
            project_name="template_test",
            repo_root=root,
            pipeline_path=pipeline_path,
            clean=False,
            skip_llm=not full_pipeline,
        )
    )

    results = executor.execute_full_pipeline() if full_pipeline else executor.execute_core_pipeline()

    assert all(result.success for result in results)
    committed_digest = (root / "validation-manifest.sha256").read_text(encoding="utf-8").strip()
    assert _manifest_digest(project) == committed_digest
    stage_manifests = sorted((project / "output" / ".pipeline" / "artifacts").glob("stage-*.json"))
    assert len(stage_manifests) == 1
    assert "render-outputs" in stage_manifests[0].name


def test_resume_after_validation_preserves_committed_aggregate(tmp_path: Path) -> None:
    """A resumed post-validation stage must not re-aggregate committed evidence."""
    root = tmp_path / "repo"
    project, pipeline_path = _make_pipeline_repo(root)
    artifact = project / "output" / "data" / "result.txt"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("rendered\n", encoding="utf-8")
    aggregate_artifact_manifests(project / "output")
    committed_digest = _manifest_digest(project)
    (root / "validation-manifest.sha256").write_text(committed_digest + "\n", encoding="utf-8")

    executor = PipelineExecutor(
        PipelineConfig(
            project_name="template_test",
            repo_root=root,
            pipeline_path=pipeline_path,
            clean=False,
            skip_llm=True,
            resume=True,
            total_stages=3,
        )
    )
    executor.checkpoint_manager.save_checkpoint(
        pipeline_start_time=0.0,
        last_stage_completed=2,
        stage_results=[
            StageResult(name="Render Outputs", exit_code=0, duration=0.1),
            StageResult(name="Provenance Commitment Gate", exit_code=0, duration=0.1),
        ],
        total_stages=3,
    )

    results = executor.execute_core_pipeline()

    assert [result.stage_name for result in results] == [
        "Render Outputs",
        "Provenance Commitment Gate",
        "Copy Outputs",
    ]
    assert all(result.success for result in results)
    assert _manifest_digest(project) == committed_digest
    assert not (project / "output" / ".pipeline" / "artifacts").exists()
