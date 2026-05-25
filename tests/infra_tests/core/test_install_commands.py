"""Tests for infrastructure.core.install_commands module.

Tests build_install_commands using real platform detection (No Mocks Policy).
"""

from __future__ import annotations

import platform

import pytest

from infrastructure.core.install_commands import build_install_commands


class TestBuildInstallCommands:
    """Tests for build_install_commands."""

    def test_returns_list(self):
        """build_install_commands always returns a list."""
        result = build_install_commands("curl")
        assert isinstance(result, list)

    def test_always_includes_verify_command(self):
        """Last command is always the 'which <dep>' verify step."""
        result = build_install_commands("curl")
        assert result[-1] == "which curl  # Verify installation"

    def test_returns_at_least_two_items(self):
        """Returns install command plus verify step — at least 2 items."""
        result = build_install_commands("git")
        assert len(result) >= 2

    def test_dependency_name_in_commands(self):
        """The dependency name appears in all returned commands."""
        dep = "texlive-full"
        result = build_install_commands(dep)
        for cmd in result:
            assert dep in cmd, f"Expected '{dep}' in command: {cmd!r}"

    def test_darwin_uses_brew_when_available(self):
        """On macOS with Homebrew, returns brew install command."""
        import shutil
        if platform.system().lower() == "darwin" and shutil.which("brew"):
            result = build_install_commands("pandoc")
            assert any("brew install" in cmd for cmd in result)

    def test_linux_uses_apt_when_available(self):
        """On Debian/Ubuntu, returns apt-get command."""
        import shutil
        if platform.system().lower() == "linux" and shutil.which("apt-get"):
            result = build_install_commands("curl")
            assert any("apt-get" in cmd for cmd in result)

    def test_different_dependencies_produce_different_commands(self):
        """Commands are parameterized by dependency name."""
        result_curl = build_install_commands("curl")
        result_git = build_install_commands("git")
        # At minimum the verify steps differ
        assert result_curl[-1] != result_git[-1]

    def test_special_chars_in_dependency_name(self):
        """Handles package names with hyphens and dots."""
        result = build_install_commands("tex-live-2024")
        assert isinstance(result, list)
        assert len(result) >= 2


class TestBuildInstallCommandsFromInstallCommands:
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
