"""Tests for summary statistics and group means (no mocks; real frames)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.eda.cleaning import clean_dataset
from src.eda.dataset import DatasetSchema, load_dataset
from src.eda.statistics import ColumnSummary, group_means, summary_statistics


def _toy_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subject_id": ["A", "B", "C", "D"],
            "group": ["alpha", "alpha", "beta", "beta"],
            "height_cm": [10.0, 20.0, 30.0, 40.0],
            "weight_kg": [1.0, 2.0, 3.0, 4.0],
            "resting_hr_bpm": [100.0, 90.0, 80.0, 70.0],
        }
    )


class TestSummaryStatistics:
    """Descriptive statistics match hand-computed values exactly."""

    def test_returns_one_summary_per_numeric_column(self):
        summaries = summary_statistics(_toy_frame())
        assert [s.column for s in summaries] == [
            "height_cm",
            "weight_kg",
            "resting_hr_bpm",
        ]
        assert all(isinstance(s, ColumnSummary) for s in summaries)

    def test_exact_values_for_height(self):
        summaries = summary_statistics(_toy_frame())
        height = next(s for s in summaries if s.column == "height_cm")
        assert height.count == 4
        assert height.mean == 25.0
        assert height.minimum == 10.0
        assert height.maximum == 40.0
        assert height.median == 25.0
        # Sample std of [10,20,30,40] is sqrt(166.6667) ≈ 12.9099
        assert abs(height.std - np.std([10, 20, 30, 40], ddof=1)) < 1e-9

    def test_ignores_missing_in_count(self):
        frame = _toy_frame()
        frame.loc[0, "weight_kg"] = np.nan
        summaries = summary_statistics(frame)
        weight = next(s for s in summaries if s.column == "weight_kg")
        assert weight.count == 3

    def test_fixture_summary_counts(self):
        cleaned, _ = clean_dataset(load_dataset())
        summaries = summary_statistics(cleaned)
        # Every numeric column has the same complete count after cleaning.
        assert len({s.count for s in summaries}) == 1
        assert summaries[0].count == len(cleaned)


class TestGroupMeans:
    """Per-group means are exact and deterministically ordered."""

    def test_group_means_exact(self):
        result = group_means(_toy_frame())
        assert list(result.index) == ["alpha", "beta"]
        assert result.loc["alpha", "height_cm"] == 15.0
        assert result.loc["beta", "height_cm"] == 35.0
        assert result.loc["alpha", "resting_hr_bpm"] == 95.0

    def test_columns_are_numeric_features(self):
        result = group_means(_toy_frame())
        assert list(result.columns) == ["height_cm", "weight_kg", "resting_hr_bpm"]

    def test_missing_group_column_raises(self):
        frame = _toy_frame().drop(columns=["group"])
        with pytest.raises(KeyError, match="group column"):
            group_means(frame)

    def test_custom_schema(self):
        frame = pd.DataFrame(
            {
                "cohort": ["x", "x", "y"],
                "score": [1.0, 3.0, 10.0],
            }
        )
        schema = DatasetSchema(group_column="cohort", numeric_columns=("score",))
        result = group_means(frame, schema)
        assert result.loc["x", "score"] == 2.0
        assert result.loc["y", "score"] == 10.0
