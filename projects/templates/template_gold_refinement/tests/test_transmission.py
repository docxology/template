"""Tests for manuscript transmission bookends."""

from __future__ import annotations

from pathlib import Path

import pytest

from transmission import validate_transmission_bookends

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_live_manuscript_is_bookended() -> None:
    receipt = validate_transmission_bookends(PROJECT_ROOT / "manuscript")
    assert receipt["status"] == "pass"
    assert receipt["first_section"]["role"] == "transmission_begin"
    assert receipt["last_section"]["role"] == "transmission_end"


def test_missing_begin_bookend_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "01_section.md").write_text("# Section\n", encoding="utf-8")
    (tmp_path / "99_999_transmission_end.md").write_text("<!-- transmission:end -->\n", encoding="utf-8")
    with pytest.raises(ValueError, match="first manuscript section"):
        validate_transmission_bookends(tmp_path)


def test_missing_end_marker_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "00_000_transmission_begin.md").write_text("<!-- transmission:begin -->\n", encoding="utf-8")
    (tmp_path / "99_999_transmission_end.md").write_text("# End\n", encoding="utf-8")
    with pytest.raises(ValueError, match="end bookend marker"):
        validate_transmission_bookends(tmp_path)
