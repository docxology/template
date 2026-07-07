"""Pytest configuration for template_gold_refinement tests."""

import os
import subprocess
import sys

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the repo root to path so the documented per-project pytest command
# works from a clean environment.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)


@pytest.fixture(scope="session", autouse=True)
def _ensure_analysis_outputs_exist():
    """Run the analysis script once before the suite so registry/dashboard
    outputs exist regardless of test-file collection order.

    ``test_registry_integrity.py`` (and ``test_dashboard.py``'s integrity
    checks) read generated artifacts under ``output/`` — ``figure_registry.json``,
    ``figure_quality_report.json``, ``dashboard.html`` — that are only produced
    by ``scripts/refinement_analysis.py``. Pytest's default alphabetical
    collection order runs ``test_registry_integrity.py`` *before*
    ``test_scripts_smoke.py`` (which is what actually invokes that script), so
    on a clean checkout — or right after the pipeline's "Clean Output
    Directories" stage wipes ``output/`` — those tests fail even though the
    underlying code is correct. Running the script once, session-scoped,
    before any test removes that ordering dependency.
    """
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "refinement_analysis.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=ROOT,
        env={**os.environ, "SOURCE_DATE_EPOCH": "1782345600"},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
