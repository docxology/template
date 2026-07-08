"""Dataset loading and schema description for the EDA exemplar.

Loads the shipped, deterministic CSV fixture (``data/measurements.csv``) into a
``pandas.DataFrame`` and exposes a small typed schema so downstream cleaning and
statistics code can reason about which columns are numeric without re-sniffing
dtypes everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# The fixture ships next to ``src/`` under the project's ``data/`` directory.
# Resolve relative to this file so the path is correct regardless of the caller's
# working directory (never hard-code an absolute path).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATASET = _PROJECT_ROOT / "data" / "measurements.csv"


@dataclass(frozen=True)
class DatasetSchema:
    """Typed description of the measurements dataset.

    Attributes:
        id_column: Per-row identifier column (not analysed numerically).
        group_column: Categorical grouping column.
        numeric_columns: Tuple of column names treated as numeric features.
    """

    id_column: str = "subject_id"
    group_column: str = "group"
    numeric_columns: tuple[str, ...] = ("height_cm", "weight_kg", "resting_hr_bpm")

    @property
    def all_columns(self) -> tuple[str, ...]:
        """Process all columns."""
        return (self.id_column, self.group_column, *self.numeric_columns)


def default_dataset_path() -> Path:
    """Return the path to the shipped CSV fixture."""
    return _DEFAULT_DATASET


def load_dataset(path: str | Path | None = None) -> pd.DataFrame:
    """Load the measurements dataset from CSV.

    Args:
        path: Optional CSV path. Defaults to the shipped fixture
            (``data/measurements.csv``).

    Returns:
        A DataFrame with the raw columns; numeric columns may contain ``NaN``
        for missing cells (cleaning is a separate, explicit step).

    Raises:
        FileNotFoundError: If the resolved path does not exist.
    """
    csv_path = Path(path) if path is not None else _DEFAULT_DATASET
    if not csv_path.exists():
        raise FileNotFoundError(f"dataset CSV not found: {csv_path}")
    frame = pd.read_csv(csv_path)
    schema = DatasetSchema()
    for column in schema.numeric_columns:
        if column in frame.columns:
            # ``errors='coerce'`` turns blank/garbage cells into NaN rather than
            # masking the problem — the cleaning step decides what to do with them.
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def numeric_columns(frame: pd.DataFrame, schema: DatasetSchema | None = None) -> list[str]:
    """Return the schema's numeric columns that are present in ``frame``.

    Args:
        frame: The dataset.
        schema: Optional schema; defaults to :class:`DatasetSchema`.

    Returns:
        Ordered list of numeric column names present in the frame.
    """
    schema = schema or DatasetSchema()
    return [column for column in schema.numeric_columns if column in frame.columns]
