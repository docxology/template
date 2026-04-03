"""Tests for infrastructure/core/install_commands.py.

Covers: build_install_commands with real platform detection.

No mocks used — tests use real platform.system() and real shutil.which().
"""

from __future__ import annotations

import platform

import pytest

from infrastructure.core.install_commands import build_install_commands


class TestBuildInstallCommands:
    """Test build_install_commands for various dependencies."""

    def test_returns_list(self):
        """Should return a list of strings."""
        result = build_install_commands("pandoc")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(cmd, str) for cmd in result)

    def test_includes_verification(self):
        """Should include a verification command."""
        result = build_install_commands("pandoc")
        assert any("which pandoc" in cmd or "Verify" in cmd for cmd in result)

    def test_darwin_brew(self):
        """On macOS with brew, should suggest brew install."""
        system = platform.system().lower()
        if system != "darwin":
            pytest.skip("Not on macOS")
        result = build_install_commands("xelatex")
        # Should have at least one install command + verification
        assert len(result) >= 2

    def test_custom_dependency_name(self):
        """Should use the dependency name in commands."""
        result = build_install_commands("my_custom_tool")
        assert any("my_custom_tool" in cmd for cmd in result)

    def test_always_has_verification_step(self):
        """Last command should always be a verification step."""
        result = build_install_commands("test_tool")
        assert "which test_tool" in result[-1]
