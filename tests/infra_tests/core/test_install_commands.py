"""Tests for infrastructure.core.install_commands module.

Tests build_install_commands using real platform detection (No Mocks Policy).
"""

from __future__ import annotations

import platform


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
        result = build_install_commands("xelatex", system="darwin")
        assert any("brew install" in cmd for cmd in result)
        assert len(result) >= 2

    def test_darwin_no_brew(self):
        """On macOS without brew, should suggest brew install with a hint."""
        import shutil as _shutil

        original_which = _shutil.which
        try:
            _shutil.which = lambda name: None if name == "brew" else original_which(name)
            result = build_install_commands("xelatex", system="darwin")
        finally:
            _shutil.which = original_which
        assert any("brew install" in cmd for cmd in result)

    def test_custom_dependency_name(self):
        """Should use the dependency name in commands."""
        result = build_install_commands("my_custom_tool")
        assert any("my_custom_tool" in cmd for cmd in result)

    def test_always_has_verification_step(self):
        """Last command should always be a verification step."""
        result = build_install_commands("test_tool")
        assert "which test_tool" in result[-1]


class TestBuildInstallCommandsBranchCoverage:
    """Branch-coverage tests using monkeypatch with real callables (no Mock objects).

    Each test patches platform.system and/or shutil.which with real lambda
    functions that return deterministic string values, satisfying the No-Mocks
    Policy while exercising every conditional branch in build_install_commands.
    """

    def test_linux_yum_branch(self, monkeypatch):
        """On Linux where only yum is available, returns a yum install command."""
        import platform as _platform

        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Linux")

        def _which_yum_only(cmd: str) -> str | None:
            return "/usr/bin/yum" if cmd == "yum" else None

        monkeypatch.setattr(_mod.shutil, "which", _which_yum_only)

        result = _mod.build_install_commands("wget")
        assert any("yum install" in cmd for cmd in result)
        assert result[-1] == "which wget  # Verify installation"

    def test_linux_dnf_branch(self, monkeypatch):
        """On Linux where only dnf is available, returns a dnf install command."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Linux")

        def _which_dnf_only(cmd: str) -> str | None:
            return "/usr/bin/dnf" if cmd == "dnf" else None

        monkeypatch.setattr(_mod.shutil, "which", _which_dnf_only)

        result = _mod.build_install_commands("ripgrep")
        assert any("dnf install" in cmd for cmd in result)

    def test_linux_pacman_branch(self, monkeypatch):
        """On Linux where only pacman is available, returns a pacman install command."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Linux")

        def _which_pacman_only(cmd: str) -> str | None:
            return "/usr/bin/pacman" if cmd == "pacman" else None

        monkeypatch.setattr(_mod.shutil, "which", _which_pacman_only)

        result = _mod.build_install_commands("fd")
        assert any("pacman -S" in cmd for cmd in result)

    def test_linux_no_known_package_manager(self, monkeypatch):
        """On Linux with no known package manager, returns a comment placeholder."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Linux")
        monkeypatch.setattr(_mod.shutil, "which", lambda cmd: None)

        result = _mod.build_install_commands("mytool")
        assert any("# Install mytool using your package manager" == cmd for cmd in result)

    def test_darwin_no_brew(self, monkeypatch):
        """On macOS without Homebrew, returns a comment suggesting brew install."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Darwin")
        monkeypatch.setattr(_mod.shutil, "which", lambda cmd: None)

        result = _mod.build_install_commands("pandoc")
        assert any("# Install pandoc using Homebrew: brew install pandoc" == cmd for cmd in result)

    def test_windows_platform_fallback(self, monkeypatch):
        """On Windows (or any non-linux/non-darwin OS), returns a generic comment."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Windows")

        result = _mod.build_install_commands("cmake")
        assert any("# Install cmake using your system's package manager" == cmd for cmd in result)
        assert result[-1] == "which cmake  # Verify installation"

    def test_linux_apt_get_branch_explicit(self, monkeypatch):
        """On Linux where apt-get is available, returns an apt-get install command."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Linux")

        def _which_apt_only(cmd: str) -> str | None:
            return "/usr/bin/apt-get" if cmd == "apt-get" else None

        monkeypatch.setattr(_mod.shutil, "which", _which_apt_only)

        result = _mod.build_install_commands("curl")
        assert any("apt-get" in cmd and "curl" in cmd for cmd in result)
        assert result[-1] == "which curl  # Verify installation"

    def test_darwin_with_brew(self, monkeypatch):
        """On macOS with Homebrew present, returns a brew install command."""
        import platform as _platform
        import infrastructure.core.install_commands as _mod

        monkeypatch.setattr(_platform, "system", lambda: "Darwin")

        def _which_brew(cmd: str) -> str | None:
            return "/usr/local/bin/brew" if cmd == "brew" else None

        monkeypatch.setattr(_mod.shutil, "which", _which_brew)

        result = _mod.build_install_commands("git")
        assert any("brew install git" == cmd for cmd in result)
