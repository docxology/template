#!/usr/bin/env python3
"""Run the stdlib fixture producer before any platform dependency setup."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "infrastructure/project/acceptance_fixture_preparation.py"),
        run_name="__main__",
    )
