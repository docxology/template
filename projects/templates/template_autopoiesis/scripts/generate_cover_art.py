#!/usr/bin/env python3
"""Generate cover art for the autopoiesis paper."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.grammar import KNOWN_DOMAINS, load_grammar
from src.cover_art import render_cover
from src.project_paths import project_output_dirs

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """CLI entry point."""
    grammar = load_grammar(PROJECT_ROOT)
    dirs = project_output_dirs(PROJECT_ROOT)
    out = dirs["figures"] / "cover_art.png"
    render_cover(
        domains=KNOWN_DOMAINS,
        seed=grammar.seed,
        out_path=out,
        title="Autopoietic Project Generation",
        subtitle="A combinatoric grammar for deterministic project synthesis",
        grammar_hash=grammar.grammar_hash,
    )
    print(f"Cover art written to {out}")


if __name__ == "__main__":
    main()
