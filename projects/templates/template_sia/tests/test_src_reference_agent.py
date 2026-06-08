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


def _predictions(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["id"]: row["label"] for row in csv.DictReader(handle)}


def test_write_predictions(tmp_path: Path):
    # train.csv feature_0 by id: 0->0.10 1->0.90 2->0.20 3->0.85 4->0.15 5->0.95.
    # At threshold 0.5 the rule (feature_0 >= threshold -> positive) is exact.
    path = write_predictions(dataset_dir=DATASET, working_dir=tmp_path, threshold=0.5)
    assert path.is_file()
    assert _predictions(path) == {
        "0": "negative",
        "1": "positive",
        "2": "negative",
        "3": "positive",
        "4": "negative",
        "5": "positive",
    }


def test_run_agent(tmp_path: Path):
    # At threshold 0.25 every negative feature (0.10, 0.20, 0.15) still sits below
    # the cut, so the prediction set matches the 0.5-threshold case exactly.
    path = run_agent(DATASET, tmp_path, threshold=0.25)
    assert path.name == "predictions.csv"
    assert _predictions(path) == {
        "0": "negative",
        "1": "positive",
        "2": "negative",
        "3": "positive",
        "4": "negative",
        "5": "positive",
    }


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
