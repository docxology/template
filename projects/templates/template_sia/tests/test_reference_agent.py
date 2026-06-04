"""Tests for reference agent."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_reference_agent_writes_predictions(tmp_path: Path):
    agent = PROJECT_ROOT / "tasks" / "mini_classify" / "reference" / "reference_target_agent.py"
    dataset = PROJECT_ROOT / "tasks" / "mini_classify" / "data" / "public"
    working = tmp_path / "working"
    proc = subprocess.run(
        [
            sys.executable,
            str(agent),
            "--dataset_dir",
            str(dataset),
            "--working_dir",
            str(working),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    predictions = working / "predictions.csv"
    assert predictions.is_file()
    with predictions.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 1
    assert {"id", "label"}.issubset(rows[0].keys())
