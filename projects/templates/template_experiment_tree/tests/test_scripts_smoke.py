"""Subprocess smoke tests for the thin orchestrators (real execution)."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(PROJECT_ROOT / "scripts" / script), *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=120,
    )


def test_init_tree_creates_store(tmp_path):
    result = run("init_tree.py", "--force")
    assert result.returncode == 0, result.stderr
    store = PROJECT_ROOT / "output" / "data" / "experiment_tree.json"
    assert store.is_file()
    assert "E001" in store.read_text()


def test_init_tree_refuses_overwrite():
    result = run("init_tree.py")
    assert result.returncode == 1
    assert "already exists" in result.stdout


def test_record_experiment_answer(tmp_path):
    store = tmp_path / "s.json"
    run("init_tree.py", "--force")
    import shutil

    shutil.copy(PROJECT_ROOT / "output" / "data" / "experiment_tree.json", store)
    result = run("record_experiment.py", "E002", "halving did not help", "dead_end", "--store", str(store))
    assert result.returncode == 0, result.stderr
    assert "dead_end" in store.read_text()


def test_record_experiment_refuses_frozen_node(tmp_path):
    store = tmp_path / "s.json"
    run("init_tree.py", "--force")
    import shutil

    shutil.copy(PROJECT_ROOT / "output" / "data" / "experiment_tree.json", store)
    result = run("record_experiment.py", "E003", "back-filled", "win", "--store", str(store))
    assert result.returncode == 1
    assert "REFUSED" in result.stdout


def test_manuscript_variables_strict(tmp_path):
    result = run(
        "z_generate_manuscript_variables.py",
        "--store",
        str(tmp_path / "missing.json"),
        "--out",
        str(tmp_path / "v.json"),
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout


def test_report_render(tmp_path):
    result = run("report.py", "--out-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "experiment_record.md").is_file()
    assert (tmp_path / "tree_state.png").is_file()
    sys.path.insert(0, str(PROJECT_ROOT / "src"))  # keep import surface explicit
