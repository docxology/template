"""Smoke tests for auto-generated analysis (domain: signal)."""
# spec_hash: b9deb8b6cbc27e0f  grammar_hash: 647b9d2969d0f696
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain signal must not raise."""
    run()  # must not raise
