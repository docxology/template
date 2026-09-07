"""Regression tests for source-backed SIA claim-ledger rows."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_public_train_claim_matches_committed_csv() -> None:
    """The ledger's public-train row count must remain bound to real input data."""
    ledger = yaml.safe_load((PROJECT_ROOT / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    claim = next(row for row in ledger["claims"] if row["claim_id"] == "public-train-rows")
    csv_path = PROJECT_ROOT / claim["artifact_path"]

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert claim["value"] == len(rows) == 6
    assert claim["source"].startswith("tasks/mini_classify/data/public/train.csv")
