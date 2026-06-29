"""Tests for the dataset loader and schema.

> **Template Exemplar Note**: This module enforces the Zero-Mock policy and
> targets high coverage on `src/` (≥90% gate in `pyproject.toml`; live
> percentage in `docs/_generated/COUNTS.md`). All tests use the shipped CSV
> fixture or real temp files — never a mock.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.eda.dataset import (
    DatasetSchema,
    default_dataset_path,
    load_dataset,
    numeric_columns,
)


class TestDatasetSchema:
    """Schema is a frozen, predictable description of the dataset."""

    def test_default_columns(self):
        schema = DatasetSchema()
        assert schema.id_column == "subject_id"
        assert schema.group_column == "group"
        assert schema.numeric_columns == ("height_cm", "weight_kg", "resting_hr_bpm")

    def test_all_columns_property(self):
        schema = DatasetSchema()
        assert schema.all_columns == (
            "subject_id",
            "group",
            "height_cm",
            "weight_kg",
            "resting_hr_bpm",
        )


class TestLoadDataset:
    """Loading the shipped fixture yields a typed, NaN-preserving frame."""

    def test_default_fixture_loads(self):
        frame = load_dataset()
        assert isinstance(frame, pd.DataFrame)
        assert list(frame.columns) == [
            "subject_id",
            "group",
            "height_cm",
            "weight_kg",
            "resting_hr_bpm",
        ]
        assert len(frame) == 120

    def test_numeric_columns_are_float(self):
        frame = load_dataset()
        for column in ("height_cm", "weight_kg", "resting_hr_bpm"):
            assert frame[column].dtype == float

    def test_missing_values_preserved_as_nan(self):
        frame = load_dataset()
        # The fixture intentionally ships blank cells; loading must surface them
        # as NaN rather than dropping or imputing.
        assert frame["weight_kg"].isna().sum() >= 1
        assert frame["height_cm"].isna().sum() >= 1

    def test_default_path_points_at_fixture(self):
        path = default_dataset_path()
        assert path.name == "measurements.csv"
        assert path.exists()

    def test_explicit_path_round_trip(self, tmp_path):
        csv = tmp_path / "tiny.csv"
        csv.write_text(
            "subject_id,group,height_cm,weight_kg,resting_hr_bpm\nA,alpha,180,80,60\nB,beta,160,55,70\n",
            encoding="utf-8",
        )
        frame = load_dataset(csv)
        assert len(frame) == 2
        assert frame["height_cm"].tolist() == [180.0, 160.0]

    def test_garbage_numeric_coerced_to_nan(self, tmp_path):
        csv = tmp_path / "messy.csv"
        csv.write_text(
            "subject_id,group,height_cm,weight_kg,resting_hr_bpm\nA,alpha,notanumber,80,60\n",
            encoding="utf-8",
        )
        frame = load_dataset(csv)
        assert np.isnan(frame["height_cm"].iloc[0])

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="dataset CSV not found"):
            load_dataset(tmp_path / "nope.csv")


class TestNumericColumns:
    """numeric_columns reflects only schema columns actually present."""

    def test_all_present(self):
        frame = load_dataset()
        assert numeric_columns(frame) == ["height_cm", "weight_kg", "resting_hr_bpm"]

    def test_subset_present(self):
        frame = pd.DataFrame({"height_cm": [1.0, 2.0], "group": ["a", "b"]})
        assert numeric_columns(frame) == ["height_cm"]

    def test_custom_schema(self):
        frame = pd.DataFrame({"x": [1.0], "y": [2.0]})
        schema = DatasetSchema(numeric_columns=("x", "y"))
        assert numeric_columns(frame, schema) == ["x", "y"]
