"""Tests for project_paths module."""

from __future__ import annotations


from src.project_paths import project_output_dirs


# ---------------------------------------------------------------------------
# project_output_dirs
# ---------------------------------------------------------------------------


def test_project_output_dirs_returns_dict(tmp_path):
    result = project_output_dirs(tmp_path)
    assert isinstance(result, dict)


def test_project_output_dirs_has_required_keys(tmp_path):
    result = project_output_dirs(tmp_path)
    required = {"output", "figures", "data", "manuscript", "children"}
    assert required.issubset(set(result.keys()))


def test_project_output_dirs_creates_dirs(tmp_path):
    result = project_output_dirs(tmp_path)
    for name, path in result.items():
        assert path.exists(), f"Expected {name} dir to exist at {path}"
        assert path.is_dir()


def test_project_output_dirs_figures_under_output(tmp_path):
    result = project_output_dirs(tmp_path)
    assert result["figures"].parent == result["output"]


def test_project_output_dirs_children_under_output(tmp_path):
    result = project_output_dirs(tmp_path)
    assert result["children"].parent == result["output"]


def test_project_output_dirs_idempotent(tmp_path):
    """Calling twice should not raise and dirs should still exist."""
    project_output_dirs(tmp_path)
    result = project_output_dirs(tmp_path)
    for _, path in result.items():
        assert path.exists()


def test_project_output_dirs_string_root(tmp_path):
    result = project_output_dirs(str(tmp_path))
    assert isinstance(result, dict)
    assert len(result) > 0
