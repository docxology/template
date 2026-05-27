"""Tests for release pairing validation."""

from __future__ import annotations

from infrastructure.publishing.release_pairing import (
    format_pairing_checklist,
    validate_release_pairing,
)


def _complete_current() -> dict[str, str]:
    return {
        "doi": "10.5281/zenodo.12345",
        "github_release_url": "https://github.com/owner/demo/releases/tag/v1.0.0",
        "pdf_sha256": "a" * 64,
        "zenodo_record_url": "https://zenodo.org/records/12345",
    }


class TestReleasePairing:
    def test_validate_complete_pairing_passes(self) -> None:
        report = validate_release_pairing(_complete_current(), require_doi=True)
        assert report.valid is True
        assert all(check.passed for check in report.checks)

    def test_validate_missing_doi_fails_when_required(self) -> None:
        current = _complete_current()
        current.pop("doi")
        report = validate_release_pairing(current, require_doi=True)
        assert report.valid is False
        assert any(check.name == "doi" and not check.passed for check in report.checks)

    def test_validate_draft_mode_without_doi(self) -> None:
        current = {
            "github_release_url": "",
            "pdf_sha256": "",
        }
        report = validate_release_pairing(current, require_doi=False)
        assert report.valid is False
        assert any(check.name == "doi" and check.passed is False for check in report.checks)

    def test_validate_mismatched_zenodo_url_fails(self) -> None:
        current = _complete_current()
        current["zenodo_record_url"] = "https://zenodo.org/records/99999"
        report = validate_release_pairing(current, require_doi=True)
        assert report.valid is False
        assert any(check.name == "zenodo_record_url" and not check.passed for check in report.checks)

    def test_format_pairing_checklist_renders_markers(self) -> None:
        report = validate_release_pairing(_complete_current(), require_doi=True)
        text = format_pairing_checklist(report)
        assert "✓" in text
        assert "DOI" in text
