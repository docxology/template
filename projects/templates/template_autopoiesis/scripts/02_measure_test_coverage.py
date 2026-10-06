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

from template_autopoiesis.manuscript.manuscript_variables import measure_test_summary  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.core.project_paths import project_output_dirs  # noqa: E402 - actual provider selection precedes own imports


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
