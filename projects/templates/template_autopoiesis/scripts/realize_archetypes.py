#!/usr/bin/env python3
"""Materialize + validate one child per domain (archetypes)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.grammar import KNOWN_DOMAINS, force_domain, load_grammar
from src.expand import expand
from src.materialize import materialize
from src.realize import validate_child, run_analysis_stage
from src.project_paths import project_output_dirs

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """CLI entry point."""
    grammar = load_grammar(PROJECT_ROOT)
    dirs = project_output_dirs(PROJECT_ROOT)
    child_dir = dirs["children"]

    for domain in KNOWN_DOMAINS:
        g = force_domain(grammar, domain)
        spec = expand(g)
        result = materialize(spec, out_root=child_dir, template_root=PROJECT_ROOT, clean=True)
        validation = validate_child(result.root)
        analysis = run_analysis_stage(result.root)
        status = "✓" if validation["valid"] and analysis["success"] else "✗"
        print(f"  {status} {domain}: {result.name}")
        if not validation["valid"]:
            print(f"    Missing: {validation['missing']}")
        if not analysis["success"]:
            print(f"    Analysis error: {analysis.get('stderr', '')[:100]}")


if __name__ == "__main__":
    main()
