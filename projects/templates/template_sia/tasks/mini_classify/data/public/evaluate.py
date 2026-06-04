#!/usr/bin/env python3
"""Evaluate mini_classify predictions against private labels."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_labels(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            labels[row["id"]] = row["label"]
    return labels


def load_predictions(path: Path) -> dict[str, str]:
    predictions: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            predictions[row["id"]] = row["label"]
    return predictions


def accuracy(truth: dict[str, str], predicted: dict[str, str]) -> tuple[float, int]:
    common = sorted(set(truth) & set(predicted))
    if not common:
        return 0.0, 0
    correct = sum(1 for key in common if truth[key] == predicted[key])
    return correct / len(common), len(common)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gen-dir", type=Path, required=True)
    args = parser.parse_args()
    gen_dir = args.gen_dir.resolve()
    task_root = Path(__file__).resolve().parents[2]
    truth = load_labels(task_root / "data" / "private" / "labels.csv")
    predictions_path = gen_dir / "working" / "predictions.csv"
    if not predictions_path.is_file():
        raise SystemExit(f"Missing predictions: {predictions_path}")
    predicted = load_predictions(predictions_path)
    value, n_samples = accuracy(truth, predicted)
    payload = {
        "metric_name": "accuracy",
        "metric_value": value,
        "n_samples": n_samples,
    }
    out = gen_dir / "results.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
