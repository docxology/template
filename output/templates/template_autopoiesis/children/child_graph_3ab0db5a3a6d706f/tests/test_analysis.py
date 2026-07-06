"""Smoke test for auto-generated analysis."""
from analysis import run


def test_run_smoke():
    run()  # must not raise
