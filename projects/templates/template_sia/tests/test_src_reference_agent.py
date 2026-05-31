"""Tests for src.reference_agent."""

from __future__ import annotations

import csv
from pathlib import Path

from src.reference_agent import main, majority_label, run_agent, write_predictions

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET = PROJECT_ROOT / "tasks" / "mini_classify" / "data" / "public"


def test_majority_label():
    label = majority_label(DATASET / "train.csv")
    assert label in {"positive", "negative"}


def test_write_predictions(tmp_path: Path):
    path = write_predictions(dataset_dir=DATASET, working_dir=tmp_path, threshold=0.5)
    assert path.is_file()
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows


def test_run_agent(tmp_path: Path):
    path = run_agent(DATASET, tmp_path, threshold=0.25)
    assert path.name == "predictions.csv"


def test_main_cli(tmp_path: Path, capsys):
    code = main(
        [
            "--dataset_dir",
            str(DATASET),
            "--working_dir",
            str(tmp_path),
            "--threshold",
            "0.4",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "predictions.csv" in captured.out
