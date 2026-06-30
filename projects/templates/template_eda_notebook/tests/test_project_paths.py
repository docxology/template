"""Tests for project_paths helpers (no mocks; real temp dirs)."""

from __future__ import annotations

import sys
import types
from pathlib import Path

from src.project_paths import project_output_dirs, resolve_project_root


class TestProjectOutputDirs:
    """Output directory map is rooted at the given project root."""

    def test_default_root_under_project(self):
        dirs = project_output_dirs()
        assert dirs["figures"].name == "figures"
        assert dirs["output"].name == "output"
        # All output dirs live under the same output/ parent.
        assert dirs["figures"].parent == dirs["output"]
        assert dirs["data"].parent == dirs["output"]

    def test_explicit_root_override(self, tmp_path):
        dirs = project_output_dirs(tmp_path)
        assert dirs["output"] == tmp_path / "output"
        assert dirs["figures"] == tmp_path / "output" / "figures"
        assert dirs["reports"] == tmp_path / "output" / "reports"
        assert dirs["web"] == tmp_path / "output" / "web"


class TestResolveProjectRoot:
    """resolve_project_root prefers a module-level project_root attribute."""

    def test_falls_back_to_default(self):
        root = resolve_project_root("definitely_not_a_real_module_xyz")
        assert isinstance(root, Path)
        assert (root / "src").is_dir()

    def test_uses_module_project_root_attribute(self, tmp_path):
        name = "_eda_fake_module_for_test"
        module = types.ModuleType(name)
        sentinel = tmp_path / "some" / "where"
        module.project_root = str(sentinel)
        sys.modules[name] = module
        try:
            assert resolve_project_root(name) == sentinel
        finally:
            del sys.modules[name]
