"""Deterministic majority-vote target agent for mini_classify."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def majority_label(train_csv: Path) -> str:
    """Return the most frequent label in train.csv."""
    counts: Counter[str] = Counter()
    with train_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            counts[row["label"]] += 1
    if not counts:
        raise ValueError(f"No labels found in {train_csv}")
    return counts.most_common(1)[0][0]


def write_predictions(
    *,
    dataset_dir: Path,
    working_dir: Path,
    threshold: float = 0.5,
) -> Path:
    """Predict labels from feature_0 threshold rule with majority fallback."""
    train_csv = dataset_dir / "train.csv"
    label = majority_label(train_csv)
    working_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = working_dir / "predictions.csv"
    rows: list[dict[str, str]] = []
    with train_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            feature = float(row["feature_0"])
            predicted = "positive" if feature >= threshold else "negative"
            if predicted not in {"positive", "negative"}:
                predicted = label
            rows.append({"id": str(index), "label": predicted})
    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "label"])
        writer.writeheader()
        writer.writerows(rows)
    return predictions_path


def run_agent(dataset_dir: Path, working_dir: Path, *, threshold: float = 0.5) -> Path:
    """Run the reference target agent."""
    return write_predictions(
        dataset_dir=dataset_dir,
        working_dir=working_dir,
        threshold=threshold,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset_dir", type=Path, required=True)
    parser.add_argument("--working_dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args(argv)
    path = run_agent(args.dataset_dir, args.working_dir, threshold=args.threshold)
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
