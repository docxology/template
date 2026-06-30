"""Tests for src.project_paths."""

from __future__ import annotations

from pathlib import Path

from src.project_paths import project_output_dirs, resolve_project_root


def test_project_output_dirs_default_root_has_expected_keys():
    dirs = project_output_dirs()
    assert set(dirs) == {"output", "figures", "data", "reports", "web"}
    assert dirs["figures"] == dirs["output"] / "figures"


def test_project_output_dirs_custom_root(tmp_path):
    dirs = project_output_dirs(tmp_path)
    assert dirs["output"] == tmp_path / "output"
    assert dirs["data"] == tmp_path / "output" / "data"


def test_resolve_project_root_falls_back_to_default_when_module_absent():
    root = resolve_project_root("a_module_name_that_will_never_be_imported")
    assert isinstance(root, Path)
    assert root.name == "template_methods_paper"
