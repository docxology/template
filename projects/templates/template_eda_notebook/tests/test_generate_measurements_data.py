"""Deterministic dataset-generation tests (no mocks; real frames).

These tests bind the generator's output to the shipped fixture's documented
contract: same schema, same size, same missingness pattern, same group
labels, and the same correlation sign structure. They also cover the thin
``scripts/generate_measurements_data.py`` orchestrator via a temporary
output root.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.eda.generate import DEFAULT_N_ROWS, DEFAULT_SEED, generate_measurements

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _PROJECT_ROOT / "scripts" / "generate_measurements_data.py"
_SHIPPED = _PROJECT_ROOT / "data" / "measurements.csv"

_NUMERIC_COLUMNS = ["height_cm", "weight_kg", "resting_hr_bpm"]


def _load_script_module():
    """Import the script as a module so its generator can be called directly."""
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    spec = importlib.util.spec_from_file_location("generate_measurements_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generated() -> pd.DataFrame:
    return generate_measurements()


@pytest.fixture(scope="module")
def shipped() -> pd.DataFrame:
    return pd.read_csv(_SHIPPED)


class TestGenerateMeasurements:
    def test_deterministic_for_same_seed(self):
        first = generate_measurements(seed=DEFAULT_SEED)
        second = generate_measurements(seed=DEFAULT_SEED)
        pd.testing.assert_frame_equal(first, second)

    def test_different_seed_changes_values(self):
        first = generate_measurements(seed=1)
        second = generate_measurements(seed=2)
        assert not first["height_cm"].equals(second["height_cm"])

    def test_schema_matches_shipped_fixture(self, generated, shipped):
        assert list(generated.columns) == list(shipped.columns)
        assert (generated[_NUMERIC_COLUMNS].dtypes == "float64").all()
        assert (shipped[_NUMERIC_COLUMNS].dtypes == "float64").all()

    def test_row_count_matches_shipped_fixture(self, generated, shipped):
        assert len(generated) == len(shipped) == DEFAULT_N_ROWS

    def test_missingness_matches_shipped_contract(self, generated, shipped):
        assert generated.isna().sum().to_dict() == shipped.isna().sum().to_dict()

    def test_group_labels_match_shipped_fixture(self, generated, shipped):
        assert set(generated["group"].unique()) == set(shipped["group"].unique())
        assert len(generated["group"].dropna()) == DEFAULT_N_ROWS

    def test_correlation_sign_structure_matches_shipped(self, generated, shipped):
        gen = generated[_NUMERIC_COLUMNS].corr()
        ref = shipped[_NUMERIC_COLUMNS].corr()
        assert gen.loc["height_cm", "weight_kg"] > 0.5
        assert ref.loc["height_cm", "weight_kg"] > 0.5
        assert gen.loc["height_cm", "resting_hr_bpm"] < 0
        assert ref.loc["height_cm", "resting_hr_bpm"] < 0
        assert gen.loc["weight_kg", "resting_hr_bpm"] < 0
        assert ref.loc["weight_kg", "resting_hr_bpm"] < 0

    def test_family_statistics_close_to_shipped(self, generated, shipped):
        # Same family, not a byte-exact clone: means and stds stay within a
        # couple of units of the shipped fixture for every numeric column.
        for column in _NUMERIC_COLUMNS:
            assert abs(generated[column].mean() - shipped[column].mean()) < 3.0
            assert abs(generated[column].std() - shipped[column].std()) < 3.0

    def test_empty_frame_keeps_schema(self):
        empty = generate_measurements(n_rows=0)
        assert list(empty.columns) == [
            "subject_id",
            "group",
            "height_cm",
            "weight_kg",
            "resting_hr_bpm",
        ]
        assert len(empty) == 0


class TestGenerateMeasurementsScript:
    def test_writes_generated_csv(self, tmp_path):
        module = _load_script_module()
        out = module.generate_measurements_file(project_root=tmp_path)
        assert out.exists()
        assert out.stat().st_size > 0
        assert out.name == "measurements_generated.csv"

    def test_generated_csv_round_trips_through_loader(self, tmp_path):
        module = _load_script_module()
        out = module.generate_measurements_file(project_root=tmp_path)
        frame = pd.read_csv(out)
        assert list(frame.columns) == ["subject_id", "group", "height_cm", "weight_kg", "resting_hr_bpm"]
        assert len(frame) == DEFAULT_N_ROWS
        assert frame.isna().sum().to_dict() == {
            "subject_id": 0,
            "group": 0,
            "height_cm": 1,
            "weight_kg": 2,
            "resting_hr_bpm": 1,
        }
