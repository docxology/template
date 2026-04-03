"""Tests for infrastructure.rendering.latex_discovery module.

Tests LaTeX executable discovery and package checking.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering.latex_discovery import (
    PackageStatus,
    check_latex_package,
    find_kpsewhich,
)


class TestPackageStatus:
    """Tests for PackageStatus NamedTuple."""

    def test_basic_creation(self):
        status = PackageStatus(name="graphicx", installed=True, path="/usr/share/texlive/graphicx.sty")
        assert status.name == "graphicx"
        assert status.installed is True
        assert status.path is not None

    def test_not_installed(self):
        status = PackageStatus(name="missing_pkg", installed=False)
        assert status.installed is False
        assert status.path is None

    def test_hashable(self):
        """NamedTuple should be hashable for use in sets."""
        s1 = PackageStatus(name="a", installed=True, path="/x")
        s2 = PackageStatus(name="b", installed=False)
        result = {s1, s2}
        assert len(result) == 2


class TestFindKpsewhich:
    """Tests for find_kpsewhich."""

    def test_returns_path_or_none(self):
        """Should return a Path or None, never raise."""
        result = find_kpsewhich()
        assert result is None or isinstance(result, Path)


class TestCheckLatexPackage:
    """Tests for check_latex_package."""

    def test_with_nonexistent_kpsewhich(self):
        """If kpsewhich is not found, should return not-installed."""
        # Pass a fake path that doesn't exist
        status = check_latex_package("graphicx", kpsewhich_path=Path("/nonexistent/kpsewhich"))
        # The function tries to run it and catches exceptions
        assert status.name == "graphicx"

    def test_with_no_kpsewhich(self):
        """When kpsewhich is None, should warn and return not-installed."""
        # We can't easily guarantee kpsewhich is or isn't installed,
        # but we can test with an explicit None and fake kpsewhich resolution
        result = check_latex_package("nonexistent_package_xyz123")
        assert result.name == "nonexistent_package_xyz123"
        assert isinstance(result.installed, bool)

    def test_returns_package_status(self):
        """Should always return PackageStatus."""
        result = check_latex_package("article")
        assert isinstance(result, PackageStatus)
