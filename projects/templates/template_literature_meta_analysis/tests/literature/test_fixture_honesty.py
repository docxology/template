"""Tests for LIT-FIXTURE-HONESTY-1 manuscript validator."""

from __future__ import annotations

from pathlib import Path

from literature.fixture_honesty import validate_fixture_honesty, validate_negative_control


def test_negative_control_fails() -> None:
    findings = validate_negative_control()
    assert findings
    assert any("empirical" in finding.message.lower() for finding in findings)


def test_clean_tokenized_prose_passes(tmp_path: Path) -> None:
    manuscript = tmp_path / "section.md"
    manuscript.write_text(
        "The {{SEARCH_TERM}} corpus uses a committed synthetic fixture for offline runs.\n",
        encoding="utf-8",
    )
    assert validate_fixture_honesty(tmp_path) == []


def test_empirical_phrasing_fails(tmp_path: Path) -> None:
    manuscript = tmp_path / "bad.md"
    manuscript.write_text("We found strong evidence in the synthetic run.\n", encoding="utf-8")
    findings = validate_fixture_honesty(tmp_path)
    assert len(findings) == 1
    assert findings[0].line_number == 1
