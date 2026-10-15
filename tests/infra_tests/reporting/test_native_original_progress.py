"""Real diagnostic I/O preserves the original clock and confines emitted data."""

from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import json
import os
import time

import pytest

from infrastructure.reporting.native_original_progress import original_cell_progress

SCOPE = "templates/template_code_project"


def test_original_progress_reports_expired_clock_without_granting_or_renewing_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    deadline = time.monotonic() - 1
    for phase in ("selection-start", "worker-start", "worker-completed", "terminal-observed"):
        original_cell_progress(phase, SCOPE, deadline)
    captured = capsys.readouterr()
    assert not captured.out
    rows = [json.loads(line) for line in captured.err.splitlines()]
    assert len(rows) == 4
    for row in rows:
        assert set(row) == {"schema_version", "phase", "scope", "pid", "observed_monotonic", "remaining_seconds"}
        assert row["schema_version"] == "template-native-original-progress-v1"
        assert row["scope"] == SCOPE and row["pid"] == os.getpid()
        assert row["remaining_seconds"] < 0
        assert row["observed_monotonic"] + row["remaining_seconds"] == deadline


@pytest.mark.parametrize(
    "phase,scope,deadline",
    [
        ("unknown", SCOPE, 1.0),
        ("worker-start", "working/private", 1.0),
        ("worker-start", SCOPE + "\nprivate", 1.0),
        ("worker-start", SCOPE, float("nan")),
        ("worker-start", SCOPE, True),
    ],
)
def test_original_progress_refuses_unbounded_labels_or_clock_before_output(
    capsys: pytest.CaptureFixture[str], phase: str, scope: str, deadline: float
) -> None:
    with pytest.raises(ValueError, match="fixed public phase/scope"):
        original_cell_progress(phase, scope, deadline)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_real_closed_diagnostic_stream_does_not_replace_original_failure() -> None:
    stream = StringIO()
    stream.close()
    with redirect_stderr(stream):
        original_cell_progress("terminal-observed", SCOPE, time.monotonic() - 1)
