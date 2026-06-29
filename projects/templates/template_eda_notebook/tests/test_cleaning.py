"""Tests for cleaning and normalization (no mocks; real frames)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from src.eda.cleaning import CleaningReport, clean_dataset, normalize_numeric
from src.eda.dataset import DatasetSchema, load_dataset


class TestCleanDataset:
    """Dropping incomplete rows is explicit and reported."""

    def test_fixture_drops_missing_rows(self):
        frame = load_dataset()
        cleaned, report = clean_dataset(frame)
        assert isinstance(report, CleaningReport)
        assert report.rows_in == 120
        assert report.dropped == report.rows_in - report.rows_out
        # No NaNs remain in any numeric column.
        for column in ("height_cm", "weight_kg", "resting_hr_bpm"):
            assert cleaned[column].isna().sum() == 0

    def test_index_is_reset(self):
        frame = load_dataset()
        cleaned, _ = clean_dataset(frame)
        assert list(cleaned.index) == list(range(len(cleaned)))

    def test_no_missing_means_no_drop(self):
        frame = pd.DataFrame(
            {
                "subject_id": ["A", "B"],
                "group": ["alpha", "beta"],
                "height_cm": [180.0, 160.0],
                "weight_kg": [80.0, 55.0],
                "resting_hr_bpm": [60.0, 70.0],
            }
        )
        cleaned, report = clean_dataset(frame)
        assert report.dropped == 0
        assert report.rows_in == report.rows_out == 2
        assert len(cleaned) == 2

    def test_all_rows_missing_yields_empty(self):
        frame = pd.DataFrame(
            {
                "subject_id": ["A", "B"],
                "group": ["alpha", "beta"],
                "height_cm": [np.nan, np.nan],
                "weight_kg": [80.0, 55.0],
                "resting_hr_bpm": [60.0, 70.0],
            }
        )
        cleaned, report = clean_dataset(frame)
        assert report.rows_out == 0
        assert cleaned.empty


class TestNormalizeNumeric:
    """Z-score standardization is exact and does not mutate the input."""

    def test_mean_zero_std_one(self):
        frame = load_dataset()
        cleaned, _ = clean_dataset(frame)
        norm = normalize_numeric(cleaned)
        for column in ("height_cm", "weight_kg", "resting_hr_bpm"):
            assert abs(float(norm[column].mean())) < 1e-9
            assert abs(float(norm[column].std(ddof=1)) - 1.0) < 1e-9

    def test_input_not_mutated(self):
        frame = pd.DataFrame(
            {
                "group": ["a", "b", "c"],
                "height_cm": [1.0, 2.0, 3.0],
                "weight_kg": [10.0, 20.0, 30.0],
                "resting_hr_bpm": [5.0, 6.0, 7.0],
            }
        )
        original = frame["height_cm"].tolist()
        _ = normalize_numeric(frame)
        assert frame["height_cm"].tolist() == original

    def test_non_numeric_columns_pass_through(self):
        frame = pd.DataFrame(
            {
                "group": ["a", "b", "c"],
                "height_cm": [1.0, 2.0, 3.0],
                "weight_kg": [10.0, 20.0, 30.0],
                "resting_hr_bpm": [5.0, 6.0, 7.0],
            }
        )
        norm = normalize_numeric(frame)
        assert norm["group"].tolist() == ["a", "b", "c"]

    def test_constant_column_becomes_zeros(self):
        frame = pd.DataFrame(
            {
                "group": ["a", "b", "c"],
                "height_cm": [5.0, 5.0, 5.0],  # zero variance
                "weight_kg": [10.0, 20.0, 30.0],
                "resting_hr_bpm": [5.0, 6.0, 7.0],
            }
        )
        norm = normalize_numeric(frame)
        assert norm["height_cm"].tolist() == [0.0, 0.0, 0.0]

    def test_single_row_std_nan_becomes_zeros(self):
        # A single row has undefined sample std (NaN); guard should zero it.
        frame = pd.DataFrame(
            {
                "group": ["a"],
                "height_cm": [5.0],
                "weight_kg": [10.0],
                "resting_hr_bpm": [5.0],
            }
        )
        norm = normalize_numeric(frame)
        assert norm["height_cm"].tolist() == [0.0]

    def test_custom_schema_subset(self):
        frame = pd.DataFrame({"x": [1.0, 2.0, 3.0], "label": ["p", "q", "r"]})
        schema = DatasetSchema(numeric_columns=("x",))
        norm = normalize_numeric(frame, schema)
        assert abs(float(norm["x"].mean())) < 1e-9
