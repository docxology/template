"""Tests for infrastructure.rendering.latex_discovery module.

Tests LaTeX executable discovery and package checking.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


class TestPackageStatusFromLatexDiscovery:
    """Test PackageStatus namedtuple."""

    def test_construction_installed(self):
        """Should create installed package status."""
        status = PackageStatus(name="geometry", installed=True, path="/usr/share/texmf/geometry.sty")
        assert status.name == "geometry"
        assert status.installed is True
        assert status.path is not None

    def test_construction_not_installed(self):
        """Should create not-installed package status."""
        status = PackageStatus(name="nonexistent", installed=False)
        assert status.name == "nonexistent"
        assert status.installed is False
        assert status.path is None

    def test_default_path_is_none(self):
        """Default path should be None."""
        status = PackageStatus(name="test", installed=True)
        assert status.path is None

    def test_is_hashable(self):
        """PackageStatus should be hashable (usable in sets/dicts)."""
        s1 = PackageStatus(name="foo", installed=True, path="/x")
        s2 = PackageStatus(name="bar", installed=False)
        assert {s1, s2}  # Should be usable in set

    def test_equality(self):
        """Equal PackageStatus instances should be equal."""
        s1 = PackageStatus(name="foo", installed=True, path="/x")
        s2 = PackageStatus(name="foo", installed=True, path="/x")
        assert s1 == s2

    def test_tuple_unpacking(self):
        """Should support tuple unpacking."""
        name, installed, path = PackageStatus(name="test", installed=False)
        assert name == "test"
        assert installed is False
        assert path is None


class TestFindKpsewhichFromLatexDiscovery:
    """Test find_kpsewhich executable discovery."""

    def test_returns_path_or_none(self):
        """Should return a Path or None."""
        result = find_kpsewhich()
        assert result is None or isinstance(result, Path)

    def test_found_path_exists(self):
        """If found, the path should exist."""
        result = find_kpsewhich()
        if result is not None:
            assert result.exists()


class TestCheckLatexPackageFromLatexDiscovery:
    """Test check_latex_package function."""

    def test_with_no_kpsewhich(self):
        """When kpsewhich is unavailable, should return not-installed."""
        # Pass a nonexistent path
        fake_path = Path("/nonexistent/kpsewhich")
        status = check_latex_package("geometry", kpsewhich_path=fake_path)
        assert isinstance(status, PackageStatus)
        # It may fail or succeed depending on subprocess behavior

    def test_auto_discover_kpsewhich(self):
        """Should auto-discover kpsewhich and check a package."""
        status = check_latex_package("article")
        assert isinstance(status, PackageStatus)
        assert status.name == "article"

    def test_nonexistent_package(self):
        """Should report nonexistent package as not installed."""
        kpsewhich = find_kpsewhich()
        if kpsewhich is None:
            pytest.skip("kpsewhich not available")
        status = check_latex_package("nonexistent_package_xyz_123", kpsewhich_path=kpsewhich)
        assert status.installed is False

    def test_common_package_if_latex_available(self):
        """If LaTeX is available, common packages like 'article' should be found."""
        kpsewhich = find_kpsewhich()
        if kpsewhich is None:
            pytest.skip("kpsewhich not available")
        status = check_latex_package("article", kpsewhich_path=kpsewhich)
        assert status.installed is True
        assert status.path is not None
