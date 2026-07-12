"""Tests for figure-data preparers (no mocks; no matplotlib needed)."""

from __future__ import annotations

import pandas as pd
import pytest
from src.eda.cleaning import clean_dataset
from src.eda.dataset import load_dataset
from src.eda.figures import (
    CORRELATION_COLOR_LIMITS,
    CorrelationFigureData,
    GroupCountFigureData,
    HistogramFigureData,
    correlation_heatmap_data,
    group_count_data,
    histogram_data,
)


class TestHistogramData:
    """Histogram preparation returns bin counts and edges only."""

    def test_counts_sum_to_non_missing_rows(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = histogram_data(cleaned, "height_cm", bins=8)
        assert isinstance(data, HistogramFigureData)
        assert sum(data.counts) == cleaned["height_cm"].notna().sum()

    def test_edges_length_is_bins_plus_one(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = histogram_data(cleaned, "weight_kg", bins=5)
        assert len(data.edges) == 6
        assert len(data.counts) == 5

    def test_ignores_missing_values(self):
        frame = pd.DataFrame({"height_cm": [1.0, 2.0, None, 4.0]})
        data = histogram_data(frame, "height_cm", bins=3)
        assert sum(data.counts) == 3

    def test_zero_bins_raises(self):
        cleaned, _ = clean_dataset(load_dataset())
        with pytest.raises(ValueError, match="bins must be positive"):
            histogram_data(cleaned, "height_cm", bins=0)

    def test_missing_column_raises(self):
        cleaned, _ = clean_dataset(load_dataset())
        with pytest.raises(KeyError, match="not in frame"):
            histogram_data(cleaned, "nonexistent", bins=4)


class TestCorrelationHeatmapData:
    """Heatmap preparation mirrors the correlation matrix."""

    def test_labels_and_square_values(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = correlation_heatmap_data(cleaned)
        assert isinstance(data, CorrelationFigureData)
        assert data.labels == ["height_cm", "weight_kg", "resting_hr_bpm"]
        assert len(data.values) == 3
        assert all(len(row) == 3 for row in data.values)

    def test_diagonal_is_one(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = correlation_heatmap_data(cleaned)
        for i in range(len(data.labels)):
            assert abs(data.values[i][i] - 1.0) < 1e-12

    def test_color_scale_covers_full_pearson_range(self):
        assert CORRELATION_COLOR_LIMITS == (-1.0, 1.0)


class TestGroupCountData:
    """Group-count preparation returns sorted labels and aligned counts."""

    def test_counts_total_equals_rows(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = group_count_data(cleaned)
        assert isinstance(data, GroupCountFigureData)
        assert sum(data.counts) == len(cleaned)

    def test_labels_sorted(self):
        cleaned, _ = clean_dataset(load_dataset())
        data = group_count_data(cleaned)
        assert data.labels == sorted(data.labels)

    def test_missing_group_column_raises(self):
        frame = pd.DataFrame({"height_cm": [1.0, 2.0]})
        with pytest.raises(KeyError, match="group column"):
            group_count_data(frame)
