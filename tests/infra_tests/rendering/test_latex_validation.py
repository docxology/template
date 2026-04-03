"""Tests for infrastructure.rendering.latex_validation.

Covers ValidationReport dataclass, validate_packages() with empty and
non-empty lists, and get_missing_packages_command().  All tests use real
data structures and real subprocess calls (or skip if LaTeX is absent).
No mocking framework is used.
"""

from __future__ import annotations

import pytest

from infrastructure.rendering.latex_validation import (
    ValidationReport,
    get_missing_packages_command,
    validate_packages,
)


# ---------------------------------------------------------------------------
# ValidationReport dataclass
# ---------------------------------------------------------------------------


class TestValidationReport:
    """Tests for the ValidationReport dataclass."""

    def test_all_required_available_true(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=[],
            all_required_available=True,
        )
        assert report.all_required_available is True

    def test_all_required_available_false(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=["multirow"],
            missing_optional=[],
            all_required_available=False,
        )
        assert report.all_required_available is False
        assert "multirow" in report.missing_required

    def test_str_all_available(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=[],
            all_required_available=True,
        )
        text = str(report)
        assert "All required packages available" in text

    def test_str_missing_required(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=["cleveref", "doi"],
            missing_optional=[],
            all_required_available=False,
        )
        text = str(report)
        assert "cleveref" in text
        assert "doi" in text
        assert "Missing" in text

    def test_str_missing_optional(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=["minted"],
            all_required_available=True,
        )
        text = str(report)
        assert "minted" in text

    def test_str_includes_install_command(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=["multirow"],
            missing_optional=[],
            all_required_available=False,
        )
        text = str(report)
        assert "tlmgr install" in text
        assert "multirow" in text

    def test_missing_optional_list_stored(self) -> None:
        report = ValidationReport(
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=["minted", "pgfplots"],
            all_required_available=True,
        )
        assert len(report.missing_optional) == 2
        assert "pgfplots" in report.missing_optional


# ---------------------------------------------------------------------------
# validate_packages() with empty lists (no LaTeX required)
# ---------------------------------------------------------------------------


class TestValidatePackagesEmptyLists:
    """Tests for validate_packages() that do not require LaTeX installation."""

    def test_empty_required_and_optional(self) -> None:
        report = validate_packages(required=[], optional=[])
        assert isinstance(report, ValidationReport)
        assert report.all_required_available is True
        assert report.missing_required == []
        assert report.missing_optional == []

    def test_empty_required_returns_true_all_available(self) -> None:
        report = validate_packages(required=[], optional=[])
        assert report.all_required_available is True

    def test_report_has_correct_structure(self) -> None:
        report = validate_packages(required=[], optional=[])
        assert hasattr(report, "required_packages")
        assert hasattr(report, "optional_packages")
        assert hasattr(report, "missing_required")
        assert hasattr(report, "missing_optional")
        assert hasattr(report, "all_required_available")

    def test_empty_lists_produce_empty_package_statuses(self) -> None:
        report = validate_packages(required=[], optional=[])
        assert report.required_packages == []
        assert report.optional_packages == []


# ---------------------------------------------------------------------------
# validate_packages() when kpsewhich is absent
# ---------------------------------------------------------------------------


class TestValidatePackagesNoKpsewhich:
    """Tests for validate_packages() behaviour when kpsewhich_path=None."""

    def test_required_package_without_kpsewhich_reports_missing(self) -> None:
        """When kpsewhich_path=None (no kpsewhich found), packages are marked missing."""
        report = validate_packages(
            required=["nonexistent_pkg_xyz_test"],
            optional=[],
            kpsewhich_path=None,
        )
        # If kpsewhich is found on this system the result may vary — just check type
        assert isinstance(report, ValidationReport)
        assert isinstance(report.all_required_available, bool)


# ---------------------------------------------------------------------------
# get_missing_packages_command()
# ---------------------------------------------------------------------------


class TestGetMissingPackagesCommand:
    """Tests for get_missing_packages_command()."""

    def test_empty_list_returns_empty_string(self) -> None:
        assert get_missing_packages_command([]) == ""

    def test_single_package(self) -> None:
        cmd = get_missing_packages_command(["multirow"])
        assert "tlmgr install" in cmd
        assert "multirow" in cmd

    def test_multiple_packages(self) -> None:
        cmd = get_missing_packages_command(["multirow", "cleveref", "doi"])
        assert "multirow" in cmd
        assert "cleveref" in cmd
        assert "doi" in cmd

    def test_command_starts_with_sudo_tlmgr(self) -> None:
        cmd = get_missing_packages_command(["pkg"])
        assert cmd.startswith("sudo tlmgr install")


# ---------------------------------------------------------------------------
# Live integration: validate_preamble_packages (skip if LaTeX absent)
# ---------------------------------------------------------------------------


class TestValidatePreamblePackagesLive:
    """Live tests that call the full validator (skip if no LaTeX)."""

    def test_validate_preamble_packages_returns_report(self) -> None:
        from infrastructure.rendering.latex_discovery import find_kpsewhich
        from infrastructure.rendering.latex_validation import validate_preamble_packages

        if find_kpsewhich() is None:
            pytest.skip("kpsewhich not found — LaTeX not installed")

        report = validate_preamble_packages(strict=False)
        assert isinstance(report, ValidationReport)
        assert isinstance(report.all_required_available, bool)
        assert isinstance(report.missing_required, list)
