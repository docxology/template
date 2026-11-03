"""A completed stage must not be relabelled by a deadline it outlived.

Fixture numbers are artifact run 41564487489, hydration child e4f931d56bb8:
began 3603.76, reaped 3821.12, its own deadline 3861.51 (40.39 s of slack),
exit 0 — while an enclosing deadline had already passed.

The same rule holds where the enclosing stage result carries the 124: a
completed child keeps its own verdict, and only a child that itself recorded a
timeout earns the TIMED_OUT label.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from infrastructure.core.analysis_launch import deadline_relabels_outcome, launch_analysis_script
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus, attach_stage_outcome
from infrastructure.core.pipeline.types import PipelineStageResult


def _completed() -> StageOutcome:
    return StageOutcome(
        "hydration:scripts/z_generate_manuscript_variables.py",
        StageStatus.SUCCEEDED,
        child_exit_code=0,
    )


def test_completed_stage_is_never_relabelled_by_a_passed_deadline() -> None:
    outcome = _completed()
    assert outcome.complete
    assert deadline_relabels_outcome(outcome, time.monotonic() - 1.0) is False


def test_incomplete_stage_is_still_refused_by_a_passed_deadline() -> None:
    outcome = StageOutcome("render_pdf", StageStatus.FAILED, child_exit_code=1)
    assert deadline_relabels_outcome(outcome, time.monotonic() - 1.0) is True


def test_child_handed_an_expired_deadline_is_still_refused(tmp_path: Path) -> None:
    """Negative control: the guard must not make a genuinely late launch succeed."""
    script = tmp_path / "z_generate_manuscript_variables.py"
    script.write_text("print('Generated 46 manuscript variables')\n")
    outcome = launch_analysis_script(
        script,
        tmp_path,
        tmp_path,
        [sys.executable, str(script)],
        {"PATH": "/usr/bin:/bin"},
        time.monotonic() - 1.0,
        stage_key="hydration:scripts/z_generate_manuscript_variables.py",
        cwd=tmp_path,
    )
    assert outcome.complete is False
    assert outcome.status is not StageStatus.SUCCEEDED


def _stage_result(exit_code: int) -> PipelineStageResult:
    """Build the stage result the executor hands to ``attach_stage_outcome``."""
    return PipelineStageResult(7, "render_pdf", False, 0.0, exit_code, "Python stage timeout", stage_completed=False)


def test_a_timed_out_child_keeps_its_own_timeout_label() -> None:
    """A child whose own verdict is TIMED_OUT is not re-derived from the exit code."""
    child = StageOutcome("render_pdf", StageStatus.TIMED_OUT, 124, "Python stage timeout")
    result = attach_stage_outcome(_stage_result(124), child, "render_pdf")
    assert result.outcome is not None
    assert result.outcome.status is StageStatus.TIMED_OUT
    assert result.outcome.diagnostic == "Python stage timeout"


def test_a_completed_child_is_not_relabelled_by_an_enclosing_124() -> None:
    """The 124 belongs to the enclosing wrapper; the completed child keeps its verdict."""
    result = attach_stage_outcome(_stage_result(124), _completed(), "hydration")
    assert result.outcome is not None
    assert result.outcome.status is StageStatus.SUCCEEDED
    assert result.outcome.complete is True
    assert result.outcome.stage_key == "hydration"


def test_a_bare_124_without_a_consumed_clock_is_not_a_timeout() -> None:
    """A non-completed child that recorded no expiry is not relabelled TIMED_OUT."""
    child = StageOutcome("render_pdf", StageStatus.FAILED, 1, "Stage script exited 1")
    result = attach_stage_outcome(_stage_result(124), child, "render_pdf")
    assert result.outcome is not None
    assert result.outcome.status is StageStatus.FAILED
