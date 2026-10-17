"""Actual fresh worker launch rechecks the controller's original admission."""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifact_contracts import capture_inputs
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.outcomes import StageOutcome
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.stage_admission import original_stage_admission, validate_stage_admission
from infrastructure.core.pipeline._stage_execution import invoke_stage_function
from infrastructure.core.pipeline.stage_launch import launch_python_stage
from infrastructure.core.pipeline.stages import build_stage_subprocess_env
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    StageContract,
    StagePolicy,
    StageSpec,
)
from tests._support.projects import make_project

pytestmark = pytest.mark.timeout(120)


@pytest.mark.parametrize("mutation", ["unchanged", "input", "review", "authority", "reject-before-consume"])
def test_real_worker_refuses_substitution_after_original_admission(tmp_path: Path, mutation: str) -> None:
    project = make_project(tmp_path, with_output=True)
    reviewed = project / "output/data/reviewed.txt"
    reviewed.write_text("reviewed", encoding="utf-8")
    script = tmp_path / "scripts/consume.py"
    script.parent.mkdir()
    script.write_text(
        "from pathlib import Path\n"
        "source = Path('projects/template_test/output/data/reviewed.txt')\n"
        "source.with_name('stage-marker.txt').write_text(source.read_text())\n",
        encoding="utf-8",
    )
    config = PipelineConfig("template_test", tmp_path, clean=False)
    stage = StageSpec(
        "Actual consume",
        lambda: True,
        key="consume",
        contract=StageContract(
            input_artifacts=("output/data/reviewed.txt",), output_artifacts=("output/data/stage-marker.txt",)
        ),
        policy=StagePolicy(require_approval=True),
    )
    controller = HitlController(
        project_output_dir=project / "output",
        repo_root=tmp_path,
        run_id="actual-run",
        plan_digest="a" * 64,
        control=PipelineControlConfig(stage_policies={1: stage.policy}),
    )
    snapshot = capture_inputs(config, stage.contract)
    controller.pause(stage_num=1, stage_name=stage.name, reason="approval_required", stage_spec=stage)
    controller.approve("Review exactly admitted input and output bytes")
    assert controller.decision_for_stage(stage) == "approve"
    admission = original_stage_admission(snapshot, stage, controller)
    source = source_fingerprint(tmp_path, project)
    if mutation == "input":
        reviewed.write_text("unreviewed", encoding="utf-8")
    elif mutation == "review":
        (project / "output/data/unreviewed-extra.txt").write_text("unreviewed", encoding="utf-8")
    elif mutation == "authority":
        controller.decisions_path.write_text("", encoding="utf-8")
    elif mutation == "reject-before-consume":
        binding = controller.approved_binding(stage)
        assert binding is not None
        controller._append_decision(
            action="reject",
            stage_num=1,
            stage_name=stage.name,
            message="A later actual decision refuses execution",
            bindings=binding,
        )
        # The real writer supplies the complete row. A history substitution
        # must not conceal that newer authority immediately before consumption.
        rows = controller.decisions_path.read_text().splitlines()
        controller.decisions_path.write_text("\n".join(rows[:-2] + [rows[-1], rows[-2]]) + "\n", encoding="utf-8")
    env = build_stage_subprocess_env(tmp_path, project, mode="core")
    env.update(PIPELINE_RUN_ID="actual-run", PIPELINE_PLAN_DIGEST="a" * 64, PIPELINE_STAGE_KEY="consume")
    outcome = launch_python_stage(
        repo=tmp_path,
        project=project,
        argv=[sys.executable, str(script)],
        env=env,
        deadline=time.monotonic() + 60,
        stage_key="consume",
        run_id="actual-run",
        source_digest=source,
        definition=None,
        skip_path=project / "output/.pipeline/skip.json",
        allow_skip=False,
        stage_admission=admission,
    )
    marker = reviewed.with_name("stage-marker.txt")
    if mutation == "unchanged":
        assert outcome.status is StageStatus.SUCCEEDED and outcome.child_exit_code == 0
        assert marker.read_text() == "reviewed"
    else:
        assert outcome.status is StageStatus.BLOCKED and outcome.child_exit_code is None
        assert outcome.diagnostic
        if mutation == "input":
            assert "reviewed.txt" in outcome.diagnostic
        assert not marker.exists(), "changed inputs must be refused before the actual child body"


def test_retry_readmits_original_inputs_after_a_real_failed_child(tmp_path: Path) -> None:
    project = make_project(tmp_path, with_output=True)
    reviewed = project / "output/data/reviewed.txt"
    reviewed.write_text("reviewed", encoding="utf-8")
    script = tmp_path / "scripts/retry.py"
    script.parent.mkdir()
    script.write_text(
        "from pathlib import Path\n"
        "source = Path('projects/template_test/output/data/reviewed.txt')\n"
        "with source.with_name('stage-marker.txt').open('a') as marker:\n"
        "    marker.write('actual attempt\\n')\n"
        "source.write_text('changed by first actual attempt')\n"
        "raise SystemExit(7)\n",
        encoding="utf-8",
    )
    config = PipelineConfig("template_test", tmp_path, clean=False)
    stage = StageSpec(
        "Actual retry",
        lambda: True,
        key="retry",
        contract=StageContract(
            input_artifacts=("output/data/reviewed.txt",),
            output_artifacts=("output/data/stage-marker.txt",),
            retry_policy=1,
        ),
    )
    controller = HitlController(
        project_output_dir=project / "output", repo_root=tmp_path, run_id="actual-run", plan_digest="a" * 64
    )
    admission = original_stage_admission(capture_inputs(config, stage.contract), stage, controller)
    source = source_fingerprint(tmp_path, project)
    env = build_stage_subprocess_env(tmp_path, project, mode="core")
    env.update(PIPELINE_RUN_ID="actual-run", PIPELINE_PLAN_DIGEST="a" * 64, PIPELINE_STAGE_KEY="retry")

    def actual_attempt() -> StageOutcome:
        outcome = launch_python_stage(
            repo=tmp_path,
            project=project,
            argv=[sys.executable, str(script)],
            env=env,
            deadline=time.monotonic() + 60,
            stage_key="retry",
            run_id="actual-run",
            source_digest=source,
            definition=None,
            skip_path=project / "output/.pipeline/skip.json",
            allow_skip=False,
            stage_admission=admission,
        )
        assert outcome.status is StageStatus.FAILED and outcome.child_exit_code == 7
        # This explicit executable classifies the genuine exit 7 as retryable;
        # the original child evidence remains unchanged.
        return replace(outcome, retryable=outcome.child_exit_code == 7)

    def readmit() -> StageOutcome | None:
        try:
            validate_stage_admission(
                admission, repo=tmp_path, project=project, run_id="actual-run", plan_digest="a" * 64, stage_key="retry"
            )
        except ValueError as exc:
            return StageOutcome("retry", StageStatus.BLOCKED, None, str(exc))
        return None

    outcome = invoke_stage_function(actual_attempt, retry_policy=1, before_attempt=readmit)

    assert isinstance(outcome, StageOutcome) and outcome.status is StageStatus.FAILED
    assert outcome.child_exit_code == 7 and outcome.attempt_exit_codes == (7,) and outcome.attempt_count == 1
    assert "changed before the actual attempt" in outcome.diagnostic
    assert RunResult(("retry",), (outcome,)).exit_code == 1
    assert reviewed.read_text() == "changed by first actual attempt"
    assert reviewed.with_name("stage-marker.txt").read_text() == "actual attempt\n"


@pytest.mark.parametrize("mutation", ["input", "source"])
@pytest.mark.parametrize("code", [0, 7, 130, 124])
def test_actual_child_exit_dominates_later_input_or_source_refusal(
    tmp_path: Path,
    mutation: str,
    code: int,
) -> None:
    project = make_project(tmp_path, with_output=True)
    reviewed = project / "output/data/reviewed.txt"
    reviewed.write_text("reviewed", encoding="utf-8")
    script = tmp_path / "scripts/exit_after_mutation.py"
    script.parent.mkdir()
    change = (
        "source.write_text('changed by actual child')\n"
        if mutation == "input"
        else "Path(__file__).write_text(Path(__file__).read_text() + '\\n# actual source mutation\\n')\n"
    )
    script.write_text(
        "from pathlib import Path\n"
        "source = Path('projects/template_test/output/data/reviewed.txt')\n"
        "source.with_name('stage-marker.txt').write_text('actual child ran')\n"
        + change
        + f"raise SystemExit({code})\n",
        encoding="utf-8",
    )
    config = PipelineConfig("template_test", tmp_path, clean=False)
    stage = StageSpec(
        "Actual mutation",
        lambda: True,
        key="mutate",
        contract=StageContract(
            input_artifacts=("output/data/reviewed.txt",), output_artifacts=("output/data/stage-marker.txt",)
        ),
    )
    controller = HitlController(
        project_output_dir=project / "output", repo_root=tmp_path, run_id="actual-run", plan_digest="a" * 64
    )
    admission = original_stage_admission(capture_inputs(config, stage.contract), stage, controller)
    source = source_fingerprint(tmp_path, project)
    env = build_stage_subprocess_env(tmp_path, project, mode="core")
    env.update(PIPELINE_RUN_ID="actual-run", PIPELINE_PLAN_DIGEST="a" * 64, PIPELINE_STAGE_KEY="mutate")

    outcome = launch_python_stage(
        repo=tmp_path,
        project=project,
        argv=[sys.executable, str(script)],
        env=env,
        deadline=time.monotonic() + 60,
        stage_key="mutate",
        run_id="actual-run",
        source_digest=source,
        definition=None,
        skip_path=project / "output/.pipeline/skip.json",
        allow_skip=False,
        stage_admission=admission,
    )

    expected = {0: StageStatus.BLOCKED, 7: StageStatus.FAILED, 130: StageStatus.INTERRUPTED, 124: StageStatus.TIMED_OUT}
    assert outcome.status is expected[code] and outcome.child_exit_code == code
    assert outcome.diagnostic
    assert RunResult(("mutate",), (outcome,)).exit_code == {0: 75, 7: 1, 130: 130, 124: 124}[code]
    assert reviewed.with_name("stage-marker.txt").read_text() == "actual child ran"
    if mutation == "input":
        assert reviewed.read_text() == "changed by actual child"
    else:
        assert "# actual source mutation" in script.read_text()
