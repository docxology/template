"""Tests for correlation analysis (no mocks; real frames)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.eda.cleaning import clean_dataset
from src.eda.correlation import correlation_matrix, strongest_pairs
from src.eda.dataset import load_dataset


class TestCorrelationMatrix:
    """Pearson correlation matrix is square with unit diagonal."""

    def test_square_with_unit_diagonal(self):
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        assert matrix.shape == (3, 3)
        for column in matrix.columns:
            assert abs(matrix.loc[column, column] - 1.0) < 1e-12

    def test_symmetric(self):
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        np.testing.assert_allclose(matrix.to_numpy(), matrix.to_numpy().T, atol=1e-12)

    def test_perfect_positive_correlation(self):
        frame = pd.DataFrame(
            {
                "height_cm": [1.0, 2.0, 3.0, 4.0],
                "weight_kg": [2.0, 4.0, 6.0, 8.0],  # exactly 2x height
                "resting_hr_bpm": [4.0, 3.0, 2.0, 1.0],  # perfectly negative
            }
        )
        matrix = correlation_matrix(frame)
        assert abs(matrix.loc["height_cm", "weight_kg"] - 1.0) < 1e-12
        assert abs(matrix.loc["height_cm", "resting_hr_bpm"] + 1.0) < 1e-12

    def test_fixture_height_weight_positive(self):
        # The fixture is designed so weight depends positively on height.
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        assert matrix.loc["height_cm", "weight_kg"] > 0.5


class TestStrongestPairs:
    """Ranking by absolute correlation, sign preserved, each pair once."""

    def test_top_pair_is_strongest(self):
        frame = pd.DataFrame(
            {
                "height_cm": [1.0, 2.0, 3.0, 4.0],
                "weight_kg": [2.0, 4.0, 6.0, 8.0],  # r = +1
                "resting_hr_bpm": [1.0, 1.0, 3.0, 2.0],  # weak
            }
        )
        matrix = correlation_matrix(frame)
        pairs = strongest_pairs(matrix, top_n=1)
        assert len(pairs) == 1
        col_a, col_b, value = pairs[0]
        assert {col_a, col_b} == {"height_cm", "weight_kg"}
        assert abs(value - 1.0) < 1e-12

    def test_negative_sign_preserved(self):
        frame = pd.DataFrame(
            {
                "height_cm": [1.0, 2.0, 3.0, 4.0],
                "weight_kg": [4.0, 3.0, 2.0, 1.0],  # r = -1
                "resting_hr_bpm": [1.0, 2.0, 1.0, 2.0],
            }
        )
        matrix = correlation_matrix(frame)
        pairs = strongest_pairs(matrix, top_n=1)
        _, _, value = pairs[0]
        assert value < 0

    def test_each_unordered_pair_once(self):
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        pairs = strongest_pairs(matrix, top_n=10)
        # 3 columns -> 3 distinct unordered pairs.
        assert len(pairs) == 3
        seen = {frozenset((a, b)) for a, b, _ in pairs}
        assert len(seen) == 3

    def test_top_n_zero_returns_empty(self):
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        assert strongest_pairs(matrix, top_n=0) == []

    def test_negative_top_n_raises(self):
        cleaned, _ = clean_dataset(load_dataset())
        matrix = correlation_matrix(cleaned)
        with pytest.raises(ValueError, match="top_n must be non-negative"):
            strongest_pairs(matrix, top_n=-1)
