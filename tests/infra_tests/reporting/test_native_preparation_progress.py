"""Actual export diagnostic I/O grants no Source or runtime acceptance."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_preparation_progress import export_timing_progress

SCOPE = "templates/template_code_project"


def _actual_child(tmp_path: Path, body: str) -> tuple[int, int, str, str]:
    root = Path(__file__).resolve().parents[3]
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1", PYTHONOPTIMIZE="0")
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", body],
        cwd=tmp_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = child.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()
        raise
    return child.pid, child.returncode, stdout, stderr


def test_export_timing_actual_child_reports_full_roster_expired_clock_and_byte_bound(tmp_path: Path) -> None:
    body = """
import json, time
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_preparation_progress import export_timing_progress
clock = time.monotonic() - 1
for ordinal, scope in enumerate(("root", *PUBLIC_PROJECT_NAMES)):
    export_timing_progress("begin", ordinal, scope, clock)
    export_timing_progress("end", ordinal, scope, clock)
print(json.dumps({"deadline": clock}))
"""
    pid, code, stdout, stderr = _actual_child(tmp_path, body)
    assert code == 0
    deadline = json.loads(stdout)["deadline"]
    rows = [json.loads(line) for line in stderr.splitlines()]
    scopes = ("root", *PUBLIC_PROJECT_NAMES)
    assert len(scopes) == 26 and len(rows) == 52
    assert len(stderr.encode("utf-8")) <= 16 * 1024
    assert [(row["ordinal"], row["scope"], row["phase"]) for row in rows] == [
        (ordinal, scope, phase) for ordinal, scope in enumerate(scopes) for phase in ("begin", "end")
    ]
    assert [row["observed_monotonic"] for row in rows] == sorted(row["observed_monotonic"] for row in rows)
    for row in rows:
        assert set(row) == {
            "schema_version",
            "phase",
            "ordinal",
            "scope",
            "pid",
            "observed_monotonic",
            "remaining_seconds",
        }
        assert row["schema_version"] == "template-native-export-timing-v1"
        assert row["pid"] == pid and row["remaining_seconds"] < 0
        assert row["observed_monotonic"] + row["remaining_seconds"] == deadline


@pytest.mark.parametrize(
    "phase,ordinal,scope,deadline",
    [
        ("unknown", 0, "root", 1.0),
        ("begin", True, "root", 1.0),
        ("begin", len(PUBLIC_PROJECT_NAMES) + 1, SCOPE, 1.0),
        ("begin", 1, "working/private", 1.0),
        ("begin", 1, "root", 1.0),
        ("begin", 1, SCOPE, float("nan")),
    ],
    ids=["phase", "ordinal-type", "ordinal-bound", "private-scope", "root-ordinal", "nonfinite-clock"],
)
def test_export_timing_refuses_unbounded_diagnostic_data_without_output_or_authority(
    capsys: pytest.CaptureFixture[str], phase: str, ordinal: int, scope: str, deadline: float
) -> None:
    assert export_timing_progress(phase, ordinal, scope, deadline) is None
    observed = capsys.readouterr()
    assert observed.out == observed.err == ""


def test_export_timing_actual_closed_stream_preserves_child_exit(tmp_path: Path) -> None:
    body = """
import sys
from infrastructure.reporting.native_preparation_progress import export_timing_progress
export_timing_progress("begin", 0, "root", 1.0)
sys.stderr.close()
export_timing_progress("end", 0, "root", 1.0)
raise SystemExit(23)
"""
    pid, code, stdout, stderr = _actual_child(tmp_path, body)
    assert code == 23 and stdout == ""
    rows = [json.loads(line) for line in stderr.splitlines()]
    assert len(rows) == 1 and rows[0]["phase"] == "begin" and rows[0]["pid"] == pid
