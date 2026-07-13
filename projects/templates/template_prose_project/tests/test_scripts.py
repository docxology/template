"""Tests for the orchestrator scripts (subprocess; no mocks)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent


def _setup_isolated(tmp_path: Path) -> Path:
    iso = tmp_path / "iso"
    iso.mkdir()
    shutil.copytree(PROJECT_ROOT / "manuscript", iso / "manuscript")
    return iso


def test_run_prose_pipeline_offline(tmp_path: Path):
    iso = _setup_isolated(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_prose_pipeline.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (iso / "output" / "manuscript_report.json").exists()
    assert (iso / "output" / "review_report.md").exists()
    summary = json.loads((iso / "output" / "run_summary.json").read_text())
    assert summary["total_words"] > 0


def test_run_prose_pipeline_strict_mode(tmp_path: Path):
    """Strict mode exits non-zero when checks fail."""
    iso = _setup_isolated(tmp_path)
    # Make the grade-level band impossibly tight.
    cfg = iso / "manuscript" / "config.yaml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace("target_grade_level_max: 18.0", "target_grade_level_max: 1.0"),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_prose_pipeline.py"),
            "--config",
            str(cfg),
            "--project-root",
            str(iso),
            "--strict",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_y_figures_skips_without_input(tmp_path: Path):
    """y_generate_prose_figures.py exits 2 when manuscript_report.json missing.

    Uses --project-root to point at the isolated tmp tree so the test never
    depends on (or pollutes) the bundled project's output/ directory.
    """
    iso = tmp_path / "iso"
    iso.mkdir()
    # No manuscript_report.json in iso/output/ — the script should exit 2.
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "y_generate_prose_figures.py"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_z_generate_manuscript_variables(tmp_path: Path):
    """z_generate_manuscript_variables.py runs end-to-end on an isolated manuscript tree.

    Mirrors test_run_prose_pipeline_offline but exercises the final-stage
    z_ script: takes a real manuscript_report.json produced by Phase 1,
    derives substitution variables, and writes both
    output/data/manuscript_variables.json and output/manuscript/*.md
    (token-substituted).
    """
    iso = _setup_isolated(tmp_path)
    # Phase 1 — produce manuscript_report.json so the z_ script has its input.
    p1 = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_prose_pipeline.py"),
            "--config",
            str(iso / "manuscript" / "config.yaml"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert p1.returncode == 0, p1.stderr
    assert (iso / "output" / "manuscript_report.json").exists()

    # Phase 2.z — variable hydration.
    p2 = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"),
            "--project-root",
            str(iso),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert p2.returncode == 0, p2.stderr
    variables_path = iso / "output" / "data" / "manuscript_variables.json"
    assert variables_path.exists()
    payload = json.loads(variables_path.read_text(encoding="utf-8"))
    # The bundled manuscript always produces a non-empty word count.
    assert payload["total_words"] > 0
    # Token-substituted manuscript tree must exist; no literal {{TOKEN}} left.
    substituted_dir = iso / "output" / "manuscript"
    assert substituted_dir.is_dir()
    for md in substituted_dir.glob("*.md"):
        assert "{{" not in md.read_text(encoding="utf-8"), f"unresolved tokens in {md}"
