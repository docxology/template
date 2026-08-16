"""Smoke tests for auto-generated analysis (domain: dynamics)."""
# spec_hash: 1693c227ea200969  grammar_hash: 16b9eb43de4d5e77
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain dynamics must not raise."""
    run()  # must not raise
