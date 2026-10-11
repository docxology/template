#!/usr/bin/env python3
"""Generate manuscript variables JSON and resolve {{TOKEN}} placeholders."""

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

from template_autopoiesis.manuscript.manuscript_variables import generate_variables, save_variables  # noqa: E402 - actual provider selection precedes own imports
from template_autopoiesis.core.project_paths import project_output_dirs  # noqa: E402 - actual provider selection precedes own imports
from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree  # noqa: E402 - actual provider selection precedes own imports


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
