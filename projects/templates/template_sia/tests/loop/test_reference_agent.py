"""Tests for reference agent."""

from __future__ import annotations

import csv
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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


@pytest.mark.parametrize(
    ("generation", "expected"),
    [
        (1, ["negative", "negative", "negative", "negative", "negative", "positive"]),
        (2, ["negative", "negative", "negative", "positive", "positive", "positive"]),
        (3, ["negative", "positive", "positive", "positive", "positive", "positive"]),
    ],
)
def test_recorded_agent_cli_preserves_each_generation_threshold(
    tmp_path: Path, generation: int, expected: list[str]
) -> None:
    """Execute each unchanged archived CLI against threshold boundary inputs.

    This exercises the archived implementation separately from fixture replay;
    replay still reads recorded artifacts without executing generated agents.
    """
    agent = PROJECT_ROOT / "src/template_sia/fixtures/recorded_generations" / f"gen_{generation}" / "target_agent.py"
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "train.csv").write_text(
        "id,feature_0,label\n"
        "0,0.249,negative\n1,0.250,negative\n2,0.299,negative\n"
        "3,0.300,positive\n4,0.499,positive\n5,0.500,positive\n",
        encoding="utf-8",
    )
    working = tmp_path / "working"
    original = sys.argv
    try:
        sys.argv = [str(agent), "--dataset_dir", str(dataset), "--working_dir", str(working)]
        with pytest.raises(SystemExit) as completed:
            runpy.run_path(str(agent), run_name="__main__")
        assert completed.value.code == 0
    finally:
        sys.argv = original
    with (working / "predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["id"] for row in rows] == [str(index) for index in range(6)]
    assert [row["label"] for row in rows] == expected
