"""Tests for the shared manuscript audit gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from textbook import content
from textbook.audit import format_audit_table, orphan_part_markdown_paths, run_manuscript_audit
from textbook.config import ChapterRef, load_config


PROJECT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT / "manuscript"


def test_run_manuscript_audit_real_project_passes():
    config = load_config(MANUSCRIPT)
    report = run_manuscript_audit(PROJECT, config)
    assert report.problems == ()
    assert report.total_words > 0
    assert report.total_stubs > 0
    assert len(report.rows) == len(config["units"]) + sum(len(unit.get("chapters", [])) for unit in config["units"])


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


def test_run_manuscript_audit_require_complete_rejects_scaffold(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    chapter = ChapterRef(
        part_id="part_I",
        part_label="I",
        part_title="P",
        directory="part_I",
        file="chapter.md",
        title="Chapter",
        enabled=True,
    )
    chapter.path(manuscript).write_text(content.scaffold_chapter(chapter), encoding="utf-8")
    (manuscript / "labs" / "part_I").mkdir(parents=True)
    (manuscript / "questions" / "part_I").mkdir(parents=True)
    (manuscript / "labs" / "part_I" / "lab_chapter.md").write_text("# Lab\n", encoding="utf-8")
    (manuscript / "questions" / "part_I" / "q_chapter.md").write_text("# Questions\n", encoding="utf-8")
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "chapter.md", "title": "Chapter"}],
            }
        ],
    }

    structural = run_manuscript_audit(tmp_path, config)
    complete = run_manuscript_audit(tmp_path, config, require_complete=True)

    assert structural.problems == ()
    assert structural.total_stubs > 0
    assert any("stub markers remaining" in problem for problem in complete.problems)
    assert any("INCOMPLETE" in row for row in complete.rows)
    assert complete.total_stubs == structural.total_stubs


def test_run_manuscript_audit_require_complete_accepts_filled_section(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    chapter = ChapterRef(
        part_id="part_I",
        part_label="I",
        part_title="P",
        directory="part_I",
        file="chapter.md",
        title="Chapter",
        enabled=True,
    )
    filled = (
        content.scaffold_chapter(chapter)
        .replace("<!-- STUB", "<!-- FILLED")
        .replace("TODO:", "DONE:")
        .replace("TKTK", "Complete")
    )
    chapter.path(manuscript).write_text(filled, encoding="utf-8")
    (manuscript / "labs" / "part_I").mkdir(parents=True)
    (manuscript / "questions" / "part_I").mkdir(parents=True)
    (manuscript / "labs" / "part_I" / "lab_chapter.md").write_text("# Lab\n", encoding="utf-8")
    (manuscript / "questions" / "part_I" / "q_chapter.md").write_text("# Questions\n", encoding="utf-8")
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "chapter.md", "title": "Chapter"}],
            }
        ],
    }

    report = run_manuscript_audit(tmp_path, config, require_complete=True)

    assert report.problems == ()
    assert report.total_stubs == 0
    assert report.rows[0].endswith("OK")


def test_audit_cli_require_complete_reports_counts_and_fails():
    result = subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "audit_textbook_quality.py"), "--require-complete"],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 1
    assert "stub markers remaining" in result.stdout
    assert "INCOMPLETE" in result.stdout
    assert "Totals:" in result.stdout


def test_audit_cli_default_allows_scaffold_and_explains_mode():
    result = subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "audit_textbook_quality.py")],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0
    assert "stub markers remain" in result.stdout
    assert "allowed in default mode" in result.stdout
    assert "--require-complete" in result.stdout


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
