"""Tests for infrastructure.rendering.pipeline._validate_latex_packages.

Real ValidationReport instances — no mocking.
"""

from __future__ import annotations

from infrastructure.rendering.latex_validation import ValidationReport
from infrastructure.rendering.pipeline import _validate_latex_packages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    *,
    all_required: bool = True,
    missing_req: list[str] | None = None,
    missing_opt: list[str] | None = None,
) -> ValidationReport:
    """Build a real ValidationReport dataclass for testing _validate_latex_packages."""
    return ValidationReport(
        required_packages=[],
        optional_packages=[],
        missing_required=missing_req or [],
        missing_optional=missing_opt or [],
        all_required_available=all_required,
    )


# ---------------------------------------------------------------------------
# _validate_latex_packages  (real ValidationReport instances — no mocking)
# ---------------------------------------------------------------------------


def test_validate_latex_packages_all_available() -> None:
    """Returns 0 when all required packages are available."""
    result = _validate_latex_packages(report=_make_report(all_required=True))

    assert result == 0


def test_validate_latex_packages_missing_required() -> None:
    """Returns 1 when required packages are missing."""
    result = _validate_latex_packages(report=_make_report(all_required=False, missing_req=["multirow", "cleveref"]))

    assert result == 1


def test_validate_latex_packages_optional_missing_still_passes() -> None:
    """Returns 0 even when optional packages are absent."""
    result = _validate_latex_packages(report=_make_report(all_required=True, missing_opt=["minted"]))

    assert result == 0


def test_validate_latex_packages_empty_report() -> None:
    """Returns 0 for an all-clean report with no packages at all."""
    result = _validate_latex_packages(report=_make_report())

    assert result == 0


def test_validate_latex_packages_multiple_missing_required() -> None:
    """Returns 1 with multiple missing required packages."""
    result = _validate_latex_packages(
        report=_make_report(
            all_required=False,
            missing_req=["multirow", "cleveref", "doi", "newunicodechar"],
        )
    )

    assert result == 1


def test_validate_latex_packages_os_error_is_non_fatal() -> None:
    """Returns 0 (proceed anyway) when report=None and validator raises OSError.

    This test calls _validate_latex_packages() with no report so it runs the
    live validate_preamble_packages path.  On systems without kpsewhich the
    OSError handler returns 0 (non-fatal).  On systems with LaTeX installed
    the function also returns 0 (all packages available) or 1 (missing).
    Either way the function must not raise.
    """
    result = _validate_latex_packages()

    assert result in (0, 1)
