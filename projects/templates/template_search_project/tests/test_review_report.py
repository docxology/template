"""Direct-call tests for src.review_report (no mocks; real files).

Uses an isolated project tree with a pre-materialised ``output/review/summary.json``
so ``ensure_review_summary`` short-circuits without spawning the real
``scripts/review`` subprocess (that flow is exercised separately by the
review-orchestrator's own tests).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.review_report import (
    H,
    check_anchors,
    collect_infra_imports,
    ensure_review_summary,
    generate_review_report,
    project_paths,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]


def test_project_paths_resolve_real_layout():
    project_root, template_root, review_dir = project_paths()
    assert project_root.name == "template_search_project"
    assert (project_root / "AGENTS.md").exists()
    assert template_root.name == "template"
    assert review_dir == project_root / "output" / "review"


def test_H_builds_markdown_header():
    assert H("Title") == "# Title"
    assert H("Sub", level=2) == "## Sub"


def test_check_anchors_finds_broken_and_valid():
    # check_anchors does a literal (non-slugified) substring search for the
    # anchor text within a heading line, so the heading must contain the
    # anchor text verbatim to count as defined.
    text = "## section-one\n\nSee [link](#section-one) for details.\nSee [broken](#does-not-exist) too.\n"
    broken = check_anchors(text)
    assert "does-not-exist" in broken
    assert "section-one" not in broken


def test_check_anchors_html_id_anchor_counts_as_defined():
    text = '<a id="my-anchor"></a>\n\nLink to [it](#my-anchor).\n'
    assert check_anchors(text) == []


def _write_fake_src_module(project_root: Path) -> None:
    (project_root / "src").mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "widget.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\nlogger = get_logger(__name__)\n",
        encoding="utf-8",
    )
    (project_root / "src" / "_private.py").write_text(
        "from infrastructure.core.logging.utils import get_logger\n",
        encoding="utf-8",
    )
    (project_root / "src" / "no_infra.py").write_text("x = 1\n", encoding="utf-8")


def test_collect_infra_imports_finds_real_and_skips_underscore(tmp_path: Path):
    _write_fake_src_module(tmp_path)
    result = collect_infra_imports(tmp_path, REPO_ROOT)
    assert "infrastructure.core.logging.utils" in result
    assert result["infrastructure.core.logging.utils"] == {"widget.py"}


def test_collect_infra_imports_ignores_nonexistent_infra_module(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "fake.py").write_text(
        "from infrastructure.totally_made_up_module import thing\n", encoding="utf-8"
    )
    result = collect_infra_imports(tmp_path, REPO_ROOT)
    assert result == {}


def test_ensure_review_summary_reads_existing_summary(tmp_path: Path):
    review_dir = tmp_path / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 3, "passed": 3, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )
    summary, exit_code, notes = ensure_review_summary(tmp_path, review_dir)
    assert exit_code == 0
    assert notes == ""
    assert summary["total"] == 3


def test_ensure_review_summary_missing_review_script(tmp_path: Path):
    review_dir = tmp_path / "output" / "review"
    (tmp_path / "scripts").mkdir(parents=True)
    summary, exit_code, notes = ensure_review_summary(tmp_path, review_dir)
    assert exit_code == 1
    assert "missing" in notes
    assert summary["overall_exit_code"] == 1


def _make_isolated_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "AGENTS.md").write_text(
        "# Agent guide\n\n### Purpose\n\nStuff.\n\n### Layout\n\nMore stuff.\n",
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Project\n\n## Purpose\n\nStuff.\n", encoding="utf-8")
    (project_root / "manuscript").mkdir()
    (project_root / "manuscript" / "references.bib").write_text(
        "@article{a2020,\n  title={T},\n}\n@article{b2021,\n  title={U},\n}\n",
        encoding="utf-8",
    )
    (project_root / "manuscript" / "01_intro.md").write_text("Intro citing [@a2020] and [@b2021].\n", encoding="utf-8")
    (project_root / "manuscript" / "99_references.md").write_text("See bib.\n", encoding="utf-8")
    _write_fake_src_module(project_root)
    (project_root / "tests").mkdir()
    (project_root / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (project_root / "scripts").mkdir()
    (project_root / "scripts" / "review").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    review_dir = project_root / "output" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "summary.json").write_text(
        json.dumps({"total": 2, "passed": 2, "failed": 0, "skipped": 0, "overall_exit_code": 0}),
        encoding="utf-8",
    )
    (review_dir / "stage_bibtex_validation.json").write_text(
        json.dumps({"status": "ok", "success": True}), encoding="utf-8"
    )
    (review_dir / "stage_bibliography_completeness.json").write_text(
        json.dumps({"status": "ok", "success": False}), encoding="utf-8"
    )

    (project_root / "review_config.yaml").write_text(
        "review:\n"
        "  stages:\n"
        "  - name: bibtex_validation\n"
        "    enabled: true\n"
        "  - name: bibliography_completeness\n"
        "    enabled: true\n"
        "  - name: skipped_stage\n"
        "    enabled: false\n",
        encoding="utf-8",
    )
    return project_root


def test_generate_review_report_writes_markdown_and_prints_summary(tmp_path: Path, capsys):
    project_root = _make_isolated_project(tmp_path)
    exit_code = generate_review_report(project_root, REPO_ROOT, project_root / "output" / "review")
    assert exit_code == 0

    out = project_root / "output" / "review" / "REVIEW_REPORT.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "DEEP REVIEW REPORT" in text
    assert "PASS — all enabled stages passed" in text
    assert "a2020" in text and "b2021" in text
    assert "PASS  bibtex_validation" in text
    assert "FAIL  bibliography_completeness" in text
    assert "SKIP (disabled or not materialised)  skipped_stage" in text

    captured = capsys.readouterr()
    assert "REPORT →" in captured.out
    assert "DEEP REVIEW SUMMARY" in captured.out
