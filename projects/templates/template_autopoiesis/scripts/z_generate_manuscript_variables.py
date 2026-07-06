#!/usr/bin/env python3
"""Generate manuscript variables JSON and resolve {{TOKEN}} placeholders."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manuscript_variables import generate_variables, save_variables
from src.project_paths import project_output_dirs

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    variables = generate_variables(PROJECT_ROOT)
    dirs = project_output_dirs(PROJECT_ROOT)
    out = dirs["data"] / "manuscript_variables.json"
    save_variables(variables, out)
    print(f"Variables written to {out}")
    print(f"  DOMAIN_COUNT          = {variables['DOMAIN_COUNT']}")
    print(f"  EFFECTIVE_PRODUCT_SIZE = {variables['EFFECTIVE_PRODUCT_SIZE']}")
    print(f"  PRODUCT_SIZE           = {variables['PRODUCT_SIZE']}")
    print(f"  GRAMMAR_HASH           = {variables['GRAMMAR_HASH']}")


if __name__ == "__main__":
    main()
