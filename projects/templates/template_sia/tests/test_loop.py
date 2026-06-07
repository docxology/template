"""Tests for template_sia."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from src.loop import build_run_config, fixtures_dir, run_sia_loop_project
from src.loop_config import load_paper_title, load_sia_settings
from src.reports import compute_variables, write_loop_report, write_manuscript_variables

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Volatile/derived paths that must never be copied into a test sandbox: copying a
# live coverage DB while pytest-cov rewrites it raises a mid-copy FileNotFoundError
# (a real flaky failure that broke the render's Project-Tests stage). Copy source only.
_COPY_IGNORE = shutil.ignore_patterns(
    ".coverage*",
    "coverage_project.json",
    "htmlcov",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "output",
    "*.egg-info",
)


def _copy_project(dst: Path) -> None:
    """Copy the project into a sandbox, excluding volatile/derived artifacts."""
    shutil.copytree(PROJECT_ROOT, dst, ignore=_COPY_IGNORE)


def test_load_sia_settings():
    settings = load_sia_settings(PROJECT_ROOT)
    assert settings.task_name == "mini_classify"
    assert settings.max_generations == 3
    assert settings.live is False


def test_fixtures_dir_exists():
    root = fixtures_dir(PROJECT_ROOT)
    assert root.is_dir()
    for gen in (1, 2, 3):
        assert (root / f"gen_{gen}" / "results.json").is_file()


def test_run_sia_loop_project_fixture_replay(tmp_path: Path):
    """Dry-run loop writes three generations and a summary."""

    project = tmp_path / "proj"
    _copy_project(project)
    for path in project.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
    if (project / "output").exists():
        shutil.rmtree(project / "output")

    result = run_sia_loop_project(project, live=False)
    assert len(result.artifacts) == 3
    summary = json.loads(result.run_summary.read_text(encoding="utf-8"))
    assert summary["live"] is False
    assert len(summary["generations"]) == 3
    assert result.report_path.is_file()
    metrics = [g["evaluation"]["metric_value"] for g in summary["generations"]]
    assert metrics == [0.5, 0.6667, 0.8333]


def test_build_run_config_live_overrides_settings():
    config = build_run_config(PROJECT_ROOT, live=True)
    assert config.live is True
    assert config.fixtures_dir is None


def test_compute_variables_after_run(tmp_path: Path):

    project = tmp_path / "proj"
    _copy_project(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    run_sia_loop_project(project, live=False)
    variables = compute_variables(project)
    assert variables["SIA_TASK_NAME"] == "mini_classify"
    assert variables["SIA_FINAL_METRIC_VALUE"] == "0.8333"
    assert load_paper_title(project) in variables["CONFIG_TITLE"]


def test_write_manuscript_variables(tmp_path: Path):

    project = tmp_path / "proj"
    _copy_project(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    run_sia_loop_project(project, live=False)
    path = write_manuscript_variables(project)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["SIA_GENERATION_COUNT"] == "3"


def test_run_sia_loop_script():
    script = PROJECT_ROOT / "scripts" / "run_sia_loop.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--project-root", str(PROJECT_ROOT)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "sia_loop_report.md" in proc.stdout


def test_z_generate_manuscript_variables_script():
    run_script = PROJECT_ROOT / "scripts" / "run_sia_loop.py"
    subprocess.run(
        [sys.executable, str(run_script), "--project-root", str(PROJECT_ROOT)],
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    gen_script = PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"
    proc = subprocess.run(
        [sys.executable, str(gen_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    assert out.is_file()


def test_write_loop_report_standalone(tmp_path: Path):

    project = tmp_path / "proj"
    _copy_project(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    run_sia_loop_project(project, live=False)
    report = write_loop_report(project)
    text = report.read_text(encoding="utf-8")
    assert "SIA loop report" in text
    assert "0.8333" in text
