"""Pre-push smoke: minimal real checks (< few seconds).

Full infrastructure tests run in CI (``test-infra``). This module only confirms
discovery, bundled config paths, canonical project imports, and one CLI subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_discover_projects_finds_templates() -> None:
    from infrastructure.project.discovery import discover_projects

    projects = discover_projects(_repo_root())
    names = {p.name for p in projects}
    # The permanent public exemplars must always be present under
    # ``projects/``. ``template_search_project`` is an optional add-on
    # exemplar that rotates between ``projects/`` and
    # ``projects/archive/``; do not gate on it here.
    assert "template_autoresearch_project" in names
    assert "template_code_project" in names
    assert "template_prose_project" in names


def test_default_pipeline_yaml_is_present() -> None:
    cfg = _repo_root() / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    text = cfg.read_text(encoding="utf-8")
    assert "stages:" in text


def test_template_project_optimizer_import_path() -> None:
    import optimizer as optimizer_mod

    assert hasattr(optimizer_mod, "gradient_descent")


def test_validation_cli_help_returns_zero() -> None:
    repo = _repo_root()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.validation.cli",
            "--help",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_check_tracked_all_returns_zero_on_clean_repo() -> None:
    repo = _repo_root()
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "check_tracked_all.py")],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
