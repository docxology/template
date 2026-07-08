#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for candidate in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree
from src.analysis import generate_artifacts
from src.manuscript_variables import generate_variables, save_variables


def main() -> int:
    """CLI entry point."""
    generate_artifacts(PROJECT_ROOT)
    variables = generate_variables(PROJECT_ROOT)
    out_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    save_variables(variables, out_path)
    write_resolved_manuscript_tree(PROJECT_ROOT, variables)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
