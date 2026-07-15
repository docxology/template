#!/usr/bin/env python3
"""Thin orchestrator: write the deterministic synthetic fixture corpus to disk.

All corpus-building logic lives in ``src/literature/fixture_corpus.py``; this script
only handles CLI args and I/O. The committed fixture lets CI and a fresh clone run the
whole pipeline offline with byte-identical outputs.

Usage::

    uv run python scripts/generate_fixture_corpus.py            # -> data/fixtures/<term>_corpus.jsonl
    uv run python scripts/generate_fixture_corpus.py --n 120 --out output/data/corpus.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from literature.fixture_corpus import (
    DEFAULT_N,
    DEFAULT_SEED,
    DEFAULT_TERM,
    build_synthetic_corpus,
)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate a synthetic fixture corpus")
    parser.add_argument("--term", default=DEFAULT_TERM)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    corpus = build_synthetic_corpus(args.term, args.n, args.seed)
    out = args.out or (_PROJECT_ROOT / "data" / "fixtures" / f"{args.term}_corpus.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    corpus.save(out)
    print(f"{len(corpus)} records -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
