"""Tests for registry-backed figures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from src.figures import write_all_figures
from src.loop import run_sia_loop_project

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_figures_are_deterministic_pngs():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    first = write_all_figures(PROJECT_ROOT)
    hashes_first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in first]
    second = write_all_figures(PROJECT_ROOT)
    hashes_second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in second]
    assert hashes_first == hashes_second
    for path in first:
        assert path.is_file()
        assert path.stat().st_size > 0
        assert path.suffix == ".png"
