#!/usr/bin/env python3
"""Run this project's own test suite and cache real test/coverage numbers.

Writes ``output/data/test_coverage_summary.json`` so
``z_generate_manuscript_variables.py`` can report the manuscript's TEST_COUNT
and COVERAGE_PCT tokens from an actual measurement instead of a hardcoded
literal, and ``output/data/coverage_full.json`` (the raw per-module report) so
``01_generate_manuscript_assets.py::fig_coverage_by_module`` can plot real,
per-module coverage. Runs first in ``manuscript/config.yaml``'s
``analysis.scripts`` allowlist so both downstream consumers see fresh data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manuscript_variables import measure_test_summary
from src.project_paths import project_output_dirs

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """CLI entry point."""
    dirs = project_output_dirs(PROJECT_ROOT)
    full_report = dirs["data"] / "coverage_full.json"
    test_count, coverage_pct = measure_test_summary(PROJECT_ROOT, full_report_out=full_report)
    out = dirs["data"] / "test_coverage_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"test_count": test_count, "coverage_pct": coverage_pct}, indent=2))
    print(f"Test coverage summary written to {out}")
    print(f"  TEST_COUNT    = {test_count}")
    print(f"  COVERAGE_PCT  = {coverage_pct}")
    print(f"Full per-module coverage written to {full_report}")


if __name__ == "__main__":
    main()
