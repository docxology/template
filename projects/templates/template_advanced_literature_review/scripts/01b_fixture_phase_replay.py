#!/usr/bin/env python3
"""Replay the committed corpus through the phase-provenance contract."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project()

from multi_phase.search import MultiPhaseSearchRunner


def main() -> None:
    """Generate deterministic phase artifacts from the bundled corpus."""
    config_path = PROJECT_ROOT / "manuscript" / "config.yaml"
    corpus_path = PROJECT_ROOT / "output" / "data" / "corpus.jsonl"
    if not corpus_path.is_file():
        raise FileNotFoundError(f"fixture corpus not found: {corpus_path}")
    runner = MultiPhaseSearchRunner(config_path, output_dir=PROJECT_ROOT / "output" / "data")
    runner.replay_fixture(corpus_path)
    print(PROJECT_ROOT / "output" / "data" / "phase_metadata.json")


if __name__ == "__main__":
    main()
