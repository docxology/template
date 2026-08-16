"""Smoke tests for auto-generated analysis (domain: graph)."""
# spec_hash: ad8ab1d87fcea0c5  grammar_hash: 0a330435ef3eb0d7
# seed: 42  track: analytical  section_set: standard
from analysis import run


def test_run_smoke() -> None:
    """run() for domain graph must not raise."""
    run()  # must not raise
