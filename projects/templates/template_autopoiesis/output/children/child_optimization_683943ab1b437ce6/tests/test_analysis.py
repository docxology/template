"""Smoke tests for auto-generated analysis (domain: optimization)."""
# spec_hash: 683943ab1b437ce6  grammar_hash: 484f85e003a8825a
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain optimization must not raise."""
    run()  # must not raise
