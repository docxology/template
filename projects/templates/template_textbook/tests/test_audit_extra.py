"""Additional negative-control tests for the shared manuscript audit gate.

These exercise branch coverage that the structural happy-path does not reach:
orphan part markdown flagged via ``run_manuscript_audit``, a part_* glob entry
that is not a directory, and missing configured reference appendices.
"""

from __future__ import annotations

from pathlib import Path

from textbook.audit import run_manuscript_audit


PROJECT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT / "manuscript"

_CONFIG_WITH_PROJECT = {
    "book": {"title": "t"},
    "units": [
        {
            "id": "part_I",
            "title": "P",
            "directory": "part_I",
            "chapters": [{"file": "a.md", "title": "A"}],
        }
    ],
}


def _write_contract_satisfying_chapter(path: Path) -> None:
    """Write a scaffolded chapter (structurally valid, stub markers allowed)."""
    from textbook import content
    from textbook.config import ChapterRef

    chapter = ChapterRef(
        part_id="part_I",
        part_label="I",
        part_title="P",
        directory="part_I",
        file=path.name,
        title="A",
        enabled=True,
    )
    path.write_text(content.scaffold_chapter(chapter), encoding="utf-8")


def test_run_manuscript_audit_flags_orphan_part_markdown(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    _write_contract_satisfying_chapter(part / "a.md")
    (part / "orphan.md").write_text("# orphan\n", encoding="utf-8")
    report = run_manuscript_audit(tmp_path, _CONFIG_WITH_PROJECT)
    assert any("orphan markdown under part directory" in p for p in report.problems)


def test_run_manuscript_audit_skips_non_directory_part_glob(tmp_path):
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    (manuscript / "labs" / "part_I").mkdir(parents=True)
    (manuscript / "questions" / "part_I").mkdir(parents=True)
    _write_contract_satisfying_chapter(part / "a.md")
    (manuscript / "labs" / "part_I" / "lab_a.md").write_text("# Lab\n", encoding="utf-8")
    (manuscript / "questions" / "part_I" / "q_a.md").write_text("# Q\n", encoding="utf-8")
    # A file named like a part_* directory must be ignored (not treated as a dir).
    (manuscript / "part_0").write_text("not a directory\n", encoding="utf-8")
    report = run_manuscript_audit(tmp_path, _CONFIG_WITH_PROJECT)
    assert report.problems == ()


def test_run_manuscript_audit_flags_missing_reference_appendix(tmp_path):
    from textbook.audit import run_manuscript_audit

    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    appendices = manuscript / "appendices"
    appendices.mkdir(parents=True)
    _write_contract_satisfying_chapter(part / "a.md")
    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "a.md", "title": "A"}],
            }
        ],
        "appendices": {
            "reference": [{"file": "appendix_missing.md", "title": "Missing"}],
        },
    }
    report = run_manuscript_audit(tmp_path, config, require_present=True)
    assert any("missing configured reference file" in p for p in report.problems)


def test_run_manuscript_audit_reports_missing_companion_stubs_when_complete(tmp_path):
    """With require_complete, an incomplete lab/question is reported."""
    manuscript = tmp_path / "manuscript"
    part = manuscript / "part_I"
    part.mkdir(parents=True)
    labs = manuscript / "labs" / "part_I"
    questions = manuscript / "questions" / "part_I"
    labs.mkdir(parents=True)
    questions.mkdir(parents=True)
    _write_contract_satisfying_chapter(part / "a.md")
    (labs / "lab_a.md").write_text("# Lab with no stub\n", encoding="utf-8")
    (questions / "q_a.md").write_text("# Q with <!-- STUB --> marker\n", encoding="utf-8")

    config = {
        "book": {"title": "t"},
        "units": [
            {
                "id": "part_I",
                "title": "P",
                "directory": "part_I",
                "chapters": [{"file": "a.md", "title": "A"}],
            }
        ],
    }

    solved = run_manuscript_audit(tmp_path, config, require_complete=False)
    assert not any("stub markers remaining" in p for p in solved.problems)

    complete = run_manuscript_audit(tmp_path, config, require_complete=True)
    assert any("stub markers remaining" in p for p in complete.problems)
