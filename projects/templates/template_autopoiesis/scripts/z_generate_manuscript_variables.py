#!/usr/bin/env python3
"""Generate manuscript variables JSON and resolve {{TOKEN}} placeholders."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parents[4]))  # repo root (for `infrastructure`)

from src.manuscript_variables import generate_variables, save_variables
from src.project_paths import project_output_dirs
from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree

PROJECT_ROOT = Path(__file__).parent.parent


def _load_test_coverage_summary(data_dir: Path) -> tuple[int | str | None, str | None]:
    """Read the real numbers written by 02_measure_test_coverage.py, if present."""
    summary_path = data_dir / "test_coverage_summary.json"
    if not summary_path.is_file():
        return None, None
    summary = json.loads(summary_path.read_text())
    return summary.get("test_count"), summary.get("coverage_pct")


def main():
    """CLI entry point."""
    dirs = project_output_dirs(PROJECT_ROOT)
    test_count, coverage_pct = _load_test_coverage_summary(dirs["data"])
    variables = generate_variables(PROJECT_ROOT, test_count=test_count, coverage_pct=coverage_pct)
    out = dirs["data"] / "manuscript_variables.json"
    save_variables(variables, out)
    write_resolved_manuscript_tree(PROJECT_ROOT, {k: str(v) for k, v in variables.items()})
    print(f"Variables written to {out}")
    print(f"  DOMAIN_COUNT          = {variables['DOMAIN_COUNT']}")
    print(f"  EFFECTIVE_PRODUCT_SIZE = {variables['EFFECTIVE_PRODUCT_SIZE']}")
    print(f"  PRODUCT_SIZE           = {variables['PRODUCT_SIZE']}")
    print(f"  GRAMMAR_HASH           = {variables['GRAMMAR_HASH']}")


if __name__ == "__main__":
    main()
