#!/usr/bin/env python3
"""Reference target agent — feature_0 threshold rule."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

THRESHOLD = 0.5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset_dir", type=Path, required=True)
    parser.add_argument("--working_dir", type=Path, required=True)
    args = parser.parse_args()
    train_csv = args.dataset_dir / "train.csv"
    args.working_dir.mkdir(parents=True, exist_ok=True)
    out = args.working_dir / "predictions.csv"
    rows: list[dict[str, str]] = []
    with train_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            feature = float(row["feature_0"])
            label = "positive" if feature >= THRESHOLD else "negative"
            rows.append({"id": row["id"], "label": label})
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
