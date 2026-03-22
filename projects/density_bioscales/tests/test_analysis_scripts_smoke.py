"""Smoke tests: analysis scripts run without error (real subprocess, no mocks)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def test_analysis_scripts_exit_zero() -> None:
    env = {**os.environ, "MPLBACKEND": "Agg"}
    for script in (
        "01_generate_density_tables.py",
        "02_plot_density_overview.py",
        "03_plot_preset_envelopes.py",
    ):
        completed = subprocess.run(
            [sys.executable, str(PROJECT / "scripts" / script)],
            cwd=str(PROJECT),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, (
            script,
            completed.stderr,
            completed.stdout,
        )
