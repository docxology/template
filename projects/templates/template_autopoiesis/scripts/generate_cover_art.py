#!/usr/bin/env python3
"""Generate cover art for the autopoiesis paper."""

from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BOOTSTRAP = importlib.util.spec_from_file_location(
    "autopoiesis_script_bootstrap", PROJECT_ROOT / "scripts/_bootstrap.py"
)
if _BOOTSTRAP is None or _BOOTSTRAP.loader is None:
    raise ImportError("actual project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP)
_BOOTSTRAP.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_ROOT)

from template_autopoiesis.core.grammar import KNOWN_DOMAINS, load_grammar  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.figures.cover_art import render_cover  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.core.project_paths import project_output_dirs  # noqa: E402 - actual provider selection precedes own imports


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
