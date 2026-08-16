"""Refresh the checked-in notebook-to-source binding receipt."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from src.eda.notebook_binding import build_binding_receipt  # noqa: E402


SOURCE_PATHS = [
    "src/eda/__init__.py",
    "src/eda/cleaning.py",
    "src/eda/correlation.py",
    "src/eda/dataset.py",
    "src/eda/figures.py",
    "src/eda/notebook_binding.py",
    "src/eda/statistics.py",
]


def main() -> int:
    """Write the deterministic binding receipt and print its path."""
    output = PROJECT / "data" / "notebook_binding.json"
    output.write_text(
        json.dumps(
            build_binding_receipt(PROJECT, "notebooks/eda_walkthrough.ipynb", SOURCE_PATHS),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
