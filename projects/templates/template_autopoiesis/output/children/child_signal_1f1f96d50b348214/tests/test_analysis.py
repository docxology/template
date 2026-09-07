"""Smoke tests for auto-generated analysis (domain: signal)."""
# spec_hash: 1f1f96d50b348214  grammar_hash: a1f3e428cf1fb3e3
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain signal must not raise."""
    run()  # must not raise
