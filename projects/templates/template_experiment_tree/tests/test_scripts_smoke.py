"""Subprocess smoke tests for the thin orchestrators (real execution)."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from template_experiment_tree.store import save_tree
from template_experiment_tree.tree import ExperimentTree

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def script_project(tmp_path: Path) -> Path:
    project = tmp_path / "repo" / "projects" / "templates" / "template_experiment_tree"
    for directory in ("scripts", "src", "manuscript"):
        shutil.copytree(
            PROJECT_ROOT / directory,
            project / directory,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    return project


def run(project: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(project / "scripts" / script), *args],
        capture_output=True,
        text=True,
        cwd=project,
        timeout=120,
    )


def test_init_tree_creates_store(script_project):
    result = run(script_project, "init_tree.py", "--force")
    assert result.returncode == 0, result.stderr
    store = script_project / "output" / "data" / "experiment_tree.json"
    assert store.is_file()
    assert "E001" in store.read_text()


def test_init_tree_refuses_overwrite(script_project):
    initial = run(script_project, "init_tree.py")
    assert initial.returncode == 0, initial.stderr
    result = run(script_project, "init_tree.py")
    assert result.returncode == 1
    assert "already exists" in result.stdout


def test_record_experiment_answer(tmp_path, script_project):
    store = tmp_path / "s.json"
    initial = run(script_project, "init_tree.py")
    assert initial.returncode == 0, initial.stderr
    shutil.copy(script_project / "output" / "data" / "experiment_tree.json", store)
    result = run(
        script_project, "record_experiment.py", "E002", "halving did not help", "dead_end", "--store", str(store)
    )
    assert result.returncode == 0, result.stderr
    assert "dead_end" in store.read_text()


def test_record_experiment_refuses_frozen_node(tmp_path, script_project):
    store = tmp_path / "s.json"
    initial = run(script_project, "init_tree.py")
    assert initial.returncode == 0, initial.stderr
    shutil.copy(script_project / "output" / "data" / "experiment_tree.json", store)
    result = run(script_project, "record_experiment.py", "E003", "back-filled", "win", "--store", str(store))
    assert result.returncode == 1
    assert "REFUSED" in result.stdout


def test_manuscript_variables_strict(tmp_path, script_project):
    result = run(
        script_project,
        "z_generate_manuscript_variables.py",
        "--store",
        str(tmp_path / "missing.json"),
        "--out",
        str(tmp_path / "v.json"),
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout


@pytest.fixture
def hydration_project(tmp_path: Path) -> Path:
    project = tmp_path / "repo" / "projects" / "templates" / "template_experiment_tree"
    (project / "scripts").mkdir(parents=True)
    shutil.copy2(
        PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py",
        project / "scripts" / "z_generate_manuscript_variables.py",
    )
    shutil.copytree(PROJECT_ROOT / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (project / "manuscript").mkdir()
    (project / "manuscript" / "01_results.md").write_text("Answered: {{EXP_ANSWERED}}\n")
    tree = ExperimentTree()
    tree.add_node("E001", "Baseline", "python scripts/run_baseline.py")
    save_tree(tree, project / "output" / "data" / "experiment_tree.json")
    return project


@pytest.mark.parametrize("require_answered", [False, True])
def test_manuscript_variables_hydrates_with_sdk(hydration_project: Path, require_answered: bool) -> None:
    if require_answered:
        tree = ExperimentTree()
        tree.add_node("E001", "Baseline", "python scripts/run_baseline.py")
        tree.record_answer("E001", "converged", "win")
        save_tree(tree, hydration_project / "output" / "data" / "experiment_tree.json")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT.parents[2])
    result = subprocess.run(
        [
            sys.executable,
            str(hydration_project / "scripts" / "z_generate_manuscript_variables.py"),
            *(["--require-answered"] if require_answered else []),
        ],
        cwd=hydration_project,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    variables = json.loads((hydration_project / "output" / "data" / "manuscript_variables.json").read_text())
    assert variables["exp_answered"] == int(require_answered)
    resolved = (hydration_project / "output" / "manuscript" / "01_results.md").read_text()
    assert resolved == f"Answered: {int(require_answered)}\n"
    assert "wrote " in result.stdout


def test_manuscript_variables_fails_without_sdk(hydration_project: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(hydration_project / "scripts" / "z_generate_manuscript_variables.py"),
        ],
        cwd=hydration_project,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError: No module named 'infrastructure'" in result.stderr
    assert "wrote " not in result.stdout
    assert not (hydration_project / "output" / "data" / "manuscript_variables.json").exists()
    assert not (hydration_project / "output" / "manuscript").exists()


def test_report_render(tmp_path, script_project):
    initial = run(script_project, "init_tree.py")
    assert initial.returncode == 0, initial.stderr
    result = run(script_project, "report.py", "--out-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "experiment_record.md").is_file()
    assert (tmp_path / "tree_state.png").is_file()
