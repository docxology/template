#!/usr/bin/env python3
"""Tests for infrastructure/core/analysis_pipeline.py.

Real subprocess execution and tmp_path fixtures only — no mocks. The
runner is invoked end-to-end with on-disk Python scripts.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from infrastructure.core.analysis_pipeline import (
    run_analysis_pipeline,
    run_analysis_script,
)
from infrastructure.core.exceptions import ScriptExecutionError


def _make_project(repo_root: Path, name: str = "p") -> Path:
    """Create a minimal project with src/scripts dirs."""
    project = repo_root / "projects" / name
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    return project


def _write_script(scripts_dir: Path, name: str, body: str) -> Path:
    path = scripts_dir / name
    path.write_text(textwrap.dedent(body))
    return path


def test_run_analysis_pipeline_no_scripts_returns_zero(tmp_path: Path) -> None:
    _make_project(tmp_path)
    assert run_analysis_pipeline([], tmp_path, "p") == 0


def test_run_analysis_script_success(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    marker = tmp_path / "ran.txt"
    script = _write_script(
        project / "scripts",
        "01_ok.py",
        f"""
        from pathlib import Path
        Path({str(marker)!r}).write_text("yes")
        """,
    )

    assert run_analysis_script(script, tmp_path, "p") == 0
    assert marker.read_text() == "yes"


def test_run_analysis_script_resolves_wip_project_env(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "working" / "draft"
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "project_dir.txt"
    script = _write_script(
        project / "scripts",
        "01_env.py",
        f"""
        import os
        from pathlib import Path
        Path({str(marker)!r}).write_text(os.environ["PROJECT_DIR"])
        """,
    )

    assert run_analysis_script(script, tmp_path, "draft") == 0
    assert marker.read_text() == str(project.resolve())


def test_run_analysis_script_nonzero_exit(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    script = _write_script(
        project / "scripts",
        "02_fail.py",
        """
        import sys
        sys.exit(3)
        """,
    )
    assert run_analysis_script(script, tmp_path, "p") == 3


def test_run_analysis_pipeline_collects_results(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    out = tmp_path / "outputs.txt"
    s1 = _write_script(
        project / "scripts",
        "01_a.py",
        f"""
        from pathlib import Path
        Path({str(out)!r}).write_text("first")
        """,
    )
    s2 = _write_script(
        project / "scripts",
        "02_b.py",
        f"""
        from pathlib import Path
        p = Path({str(out)!r})
        p.write_text(p.read_text() + ',second')
        """,
    )

    rc = run_analysis_pipeline([s1, s2], tmp_path, "p")
    assert rc == 0
    assert out.read_text() == "first,second"


def test_run_analysis_pipeline_reports_failure(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    s_ok = _write_script(project / "scripts", "01_ok.py", "print('ok')")
    s_bad = _write_script(
        project / "scripts",
        "02_bad.py",
        "import sys\nsys.exit(2)",
    )
    assert run_analysis_pipeline([s_ok, s_bad], tmp_path, "p") == 1


def test_run_analysis_script_missing_file_returns_python_exit(tmp_path: Path) -> None:
    """A non-existent script reaches the interpreter and returns Python's exit code (not 0)."""
    project = _make_project(tmp_path)
    bogus = project / "scripts" / "does_not_exist.py"
    rc = run_analysis_script(bogus, tmp_path, "p")
    assert rc != 0


def test_script_execution_error_class_attached() -> None:
    """``ScriptExecutionError`` is the documented wrapper used by run_analysis_script."""
    err = ScriptExecutionError("wrapped", context={"script": "x"})
    assert "wrapped" in str(err)
