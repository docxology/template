#!/usr/bin/env python3
"""Regenerate a deterministic sibling of the shipped EDA dataset fixture."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.eda.generate import DEFAULT_N_ROWS, DEFAULT_SEED, generate_measurements  # noqa: E402
from src.project_paths import project_output_dirs  # noqa: E402


def generate_measurements_file(project_root: Path | None = None) -> Path:
    """Write the deterministic generated dataset under ``output/data/``.

    Accepts an output-root override so tests can run against a temporary
    directory (mirroring ``eda_analysis.run_eda``). Returns the written path.
    """
    data_dir = project_output_dirs(project_root)["data"]
    data_dir.mkdir(parents=True, exist_ok=True)
    out = data_dir / "measurements_generated.csv"
    generate_measurements(DEFAULT_N_ROWS, DEFAULT_SEED).to_csv(out, index=False)
    return out


def main() -> None:
    """CLI entry point: print the written path for manifest collection."""
    print(generate_measurements_file())


if __name__ == "__main__":
    main()
