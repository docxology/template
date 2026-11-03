"""A completed stage must not be relabelled by a deadline it outlived.

Fixture numbers are artifact run 41564487489, hydration child e4f931d56bb8:
began 3603.76, reaped 3821.12, its own deadline 3861.51 (40.39 s of slack),
exit 0 — while an enclosing deadline had already passed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from infrastructure.core.analysis_launch import deadline_relabels_outcome, launch_analysis_script
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus


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
