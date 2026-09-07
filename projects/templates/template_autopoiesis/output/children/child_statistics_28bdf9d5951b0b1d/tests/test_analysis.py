"""Smoke tests for auto-generated analysis (domain: statistics)."""
# spec_hash: 28bdf9d5951b0b1d  grammar_hash: 1142e011a7d4b835
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain statistics must not raise."""
    run()  # must not raise
