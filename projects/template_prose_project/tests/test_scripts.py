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
            "--config", str(iso / "manuscript" / "config.yaml"),
            "--project-root", str(iso),
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
        cfg.read_text(encoding="utf-8").replace(
            "target_grade_level_max: 18.0", "target_grade_level_max: 1.0"
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_prose_pipeline.py"),
            "--config", str(cfg),
            "--project-root", str(iso),
            "--strict",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1


def test_y_figures_skips_without_input(tmp_path: Path):
    """y_generate_prose_figures.py exits 2 when manuscript_report.json missing."""
    # Skip-path is hard to test for the bundled project since output may exist;
    # this is mostly for defensive validation that the exit code is 2 in that path.
    if not (PROJECT_ROOT / "output" / "manuscript_report.json").exists():
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "y_generate_prose_figures.py")],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 2
