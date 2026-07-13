#!/usr/bin/env python3
"""Full realize pipeline for a single child project."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.grammar import load_grammar
from src.expand import expand
from src.materialize import materialize
from src.realize import validate_child, run_analysis_stage
from src.project_paths import project_output_dirs

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """CLI entry point."""
    grammar = load_grammar(PROJECT_ROOT)
    spec = expand(grammar)
    dirs = project_output_dirs(PROJECT_ROOT)
    result = materialize(spec, out_root=dirs["children"], template_root=PROJECT_ROOT)
    print(f"Child: {result.name}")
    print(f"Root:  {result.root}")
    print(f"Hash:  {result.tree_hash}")

    validation = validate_child(result.root)
    print(f"Valid: {validation['valid']}")

    analysis = run_analysis_stage(result.root)
    print(f"Analysis: {'OK' if analysis['success'] else 'FAILED'}")
    if not analysis["success"]:
        print(analysis.get("stderr", "")[:300])


if __name__ == "__main__":
    main()
