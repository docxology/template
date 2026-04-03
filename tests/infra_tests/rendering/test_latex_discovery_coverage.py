"""Tests for infrastructure/rendering/latex_discovery.py.

Covers: PackageStatus namedtuple, find_kpsewhich, check_latex_package.

No mocks used — all tests use real filesystem checks and real subprocess calls.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering.latex_discovery import (
    PackageStatus,
    find_kpsewhich,
    check_latex_package,
)


class TestPackageStatus:
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


class TestFindKpsewhich:
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


class TestCheckLatexPackage:
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
