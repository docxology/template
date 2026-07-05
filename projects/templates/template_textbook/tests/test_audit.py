"""Tests for the shared manuscript audit gate."""

from __future__ import annotations

from pathlib import Path

from textbook.audit import format_audit_table, orphan_part_markdown_paths, run_manuscript_audit
from textbook.config import load_config


PROJECT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT / "manuscript"


def test_run_manuscript_audit_real_project_passes():
    config = load_config(MANUSCRIPT)
    report = run_manuscript_audit(PROJECT, config)
    assert report.problems == ()
    assert report.total_words > 0
    assert len(report.rows) == len(config["units"]) + sum(
        len(unit.get("chapters", [])) for unit in config["units"]
    )


def test_format_audit_table_includes_totals():
    table = format_audit_table(("  row",), total_words=10, total_stubs=2)
    assert "Chapter audit:" in table
    assert "Totals: 10 words, 2 stub markers remaining" in table


def test_orphan_part_markdown_detects_unregistered_file(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    (part / "first_principles.md").write_text("# ok\n", encoding="utf-8")
    (part / "orphan.md").write_text("# orphan\n", encoding="utf-8")
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "first_principles.md", "title": "FP"}],
            }
        ],
    }
    orphans = orphan_part_markdown_paths(manuscript, config)
    assert orphans == [part / "orphan.md"]


def test_run_manuscript_audit_flags_missing_chapter(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "missing.md", "title": "Missing"}],
            }
        ],
    }
    report = run_manuscript_audit(tmp_path, config, require_present=True)
    assert any("missing chapter file" in problem for problem in report.problems)


def test_run_manuscript_audit_lenient_allows_missing_chapter(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "missing.md", "title": "Missing"}],
            }
        ],
    }
    report = run_manuscript_audit(tmp_path, config, require_present=False)
    assert not any("missing chapter file" in problem for problem in report.problems)


def test_run_manuscript_audit_flags_invalid_unit_intro(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    (part / "unit_intro.md").write_text("no heading\n", encoding="utf-8")
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "intro_file": "unit_intro.md",
                "chapters": [{"file": "a.md", "title": "A"}],
            }
        ],
    }
    report = run_manuscript_audit(tmp_path, config)
    assert any("missing H1 title" in problem for problem in report.problems)
