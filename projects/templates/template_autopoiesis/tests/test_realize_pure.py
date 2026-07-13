"""Pure unit tests for realize module (no fixture dependencies)."""

from __future__ import annotations

import sys


from src.realize import _gate_python, _project_slug, run_child_stage


# ---------------------------------------------------------------------------
# _gate_python
# ---------------------------------------------------------------------------


def test_gate_python_returns_real_path(tmp_path):
    """_gate_python should return True (sys.executable is not None)."""
    result = _gate_python(tmp_path)
    assert result is True


def test_gate_python_fallback_sys_executable(tmp_path):
    """sys.executable must be non-None for tests to run at all."""
    assert sys.executable is not None
    assert _gate_python(tmp_path) is True


# ---------------------------------------------------------------------------
# _project_slug
# ---------------------------------------------------------------------------


def test_project_slug_format(tmp_path):
    d = tmp_path / "child_dynamics_abc12345"
    d.mkdir()
    assert _project_slug(d) == "child_dynamics_abc12345"


def test_project_slug_no_path_separators(tmp_path):
    d = tmp_path / "myproject"
    d.mkdir()
    slug = _project_slug(d)
    assert "/" not in slug
    assert "\\" not in slug


# ---------------------------------------------------------------------------
# run_child_stage
# ---------------------------------------------------------------------------


def test_run_child_stage_simple(tmp_path):
    script = tmp_path / "simple.py"
    script.write_text("import sys; sys.exit(0)\n")
    proc = run_child_stage(tmp_path, "simple.py")
    assert proc.returncode == 0


def test_run_child_stage_failing(tmp_path):
    script = tmp_path / "fail.py"
    script.write_text("import sys; sys.exit(42)\n")
    proc = run_child_stage(tmp_path, "fail.py")
    assert proc.returncode == 42


def test_run_child_stage_missing_script(tmp_path):
    proc = run_child_stage(tmp_path, "does_not_exist.py")
    assert proc.returncode != 0
