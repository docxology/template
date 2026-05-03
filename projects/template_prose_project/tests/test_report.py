"""Tests for src.report — markdown review report assembly."""

from __future__ import annotations

from pathlib import Path

from infrastructure.prose import analyze_files

from src.pipeline import CheckResult
from src.report import write_review_report


def _sample_report():
    return analyze_files(
        {
            "00_a.md": "# A\n\nThis cites [@k1] and is fine.",
            "01_b.md": "# B\n\nThis paragraph elaborates on the topic.",
        }
    )


def test_basic_report(tmp_path: Path):
    report = _sample_report()
    checks = [
        CheckResult(name="all_good", passed=True, message="ok"),
        CheckResult(name="something_failed", passed=False, message="bad"),
    ]
    out = write_review_report(
        tmp_path / "review.md",
        title="Demo",
        manuscript_report=report,
        checks=checks,
    )
    text = out.read_text(encoding="utf-8")
    assert "# Demo" in text
    assert "all_good" in text
    assert "✅" in text
    assert "❌" in text


def test_per_file_table(tmp_path: Path):
    report = _sample_report()
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_per_file_table=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "Per-file metrics" in text
    assert "00_a.md" in text


def test_outline_section(tmp_path: Path):
    report = _sample_report()
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_outline=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "## Outline" in text


def test_quality_flags_section(tmp_path: Path):
    report = _sample_report()
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_quality_flags=True,
    )
    # We can't guarantee that this prose will trigger flags, but the
    # report should at least not error out and should produce a file.
    assert out.exists()


def test_minimal_report(tmp_path: Path):
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=_sample_report(),
        checks=[],
        include_per_file_table=False,
        include_outline=False,
        include_quality_flags=False,
    )
    text = out.read_text(encoding="utf-8")
    assert "Per-file metrics" not in text
    assert "Outline" not in text


def test_failing_check_renders_warning_emoji(tmp_path: Path):
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=_sample_report(),
        checks=[CheckResult(name="failed", passed=False, message="boom")],
    )
    text = out.read_text(encoding="utf-8")
    assert "## Checks ⚠️" in text


def test_outline_for_file_without_headings(tmp_path: Path):
    """A file with no headings renders the '_(no headings)_' placeholder."""
    # Headings detection requires '#' at start of line; pure body text has none.
    report = analyze_files({"00_no_headings.md": "Just body text.\n\nMore body."})
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_outline=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "_(no headings)_" in text
