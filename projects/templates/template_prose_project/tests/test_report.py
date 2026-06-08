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


def _flagged_prose_report():
    """Manuscript slice engineered to trigger all quality-flag heuristics."""
    long_sentence = " ".join(f"token{i}" for i in range(36))
    body = (
        "The manuscript was examined by reviewers who might perhaps find "
        "that the evidence suggests a possibly incomplete argument. "
        f"{long_sentence}."
    )
    return analyze_files({"01_flagged.md": f"# Flagged\n\n{body}"})


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
    report = _flagged_prose_report()
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_quality_flags=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "## Quality flags" in text
    assert "01_flagged.md" in text
    assert "long sentence" in text
    assert "passive-voice" in text
    assert "hedge word" in text
    assert "perhaps" in text


def test_quality_flags_partial_only_long_sentence(tmp_path: Path):
    """One flag firing renders its bullet; the others are absent.

    A long sentence with no "be + past participle" pair and no hedge words
    triggers only `long_sentence_count`, exercising the false branches of
    `if q.passive_count:` and `if q.hedge_count:` in report.py. This proves
    the bullet list adapts to which flags actually fire.
    """
    long_sentence = " ".join(f"word{i}" for i in range(40))
    report = analyze_files({"01_long.md": f"# Long\n\n{long_sentence}."})
    out = write_review_report(
        tmp_path / "r.md",
        title="X",
        manuscript_report=report,
        checks=[],
        include_quality_flags=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "## Quality flags" in text
    assert "long sentence" in text
    assert "passive-voice" not in text
    assert "hedge word" not in text


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
