"""Tests for executive output organization helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.executive_outputs import (
    ExecutiveOutputOptions,
    organize_executive_summary,
    organize_multi_project_summary,
    run_executive_output_organization,
)


def test_organize_executive_summary_moves_files_and_copies_combined_pdfs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    executive_dir = repo_root / "output" / "executive_summary"
    project_dir = repo_root / "output" / "template_code_project"
    executive_dir.mkdir(parents=True)
    project_dir.mkdir(parents=True)
    (executive_dir / "dashboard.png").write_bytes(b"png")
    (executive_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")
    (project_dir / "template_code_project_combined.pdf").write_bytes(b"%PDF-1.4\n")

    processed = organize_executive_summary(repo_root)

    assert processed == 3
    assert (executive_dir / "png" / "dashboard.png").exists()
    assert (executive_dir / "md" / "summary.md").exists()
    assert (executive_dir / "combined_pdfs" / "template_code_project_combined.pdf").exists()


def test_organize_multi_project_summary_dry_run_does_not_move_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    summary_dir = repo_root / "output" / "multi_project_summary"
    summary_dir.mkdir(parents=True)
    original = summary_dir / "overview.json"
    original.write_text('{"ok": true}\n', encoding="utf-8")

    processed = organize_multi_project_summary(repo_root, dry_run=True)

    assert processed == 0
    assert original.exists()
    assert not (summary_dir / "json" / "overview.json").exists()


def test_run_executive_output_organization_honors_only_flags(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    executive_dir = repo_root / "output" / "executive_summary"
    multi_dir = repo_root / "output" / "multi_project_summary"
    executive_dir.mkdir(parents=True)
    multi_dir.mkdir(parents=True)
    (executive_dir / "one.pdf").write_bytes(b"%PDF-1.4\n")
    (multi_dir / "two.pdf").write_bytes(b"%PDF-1.4\n")

    processed = run_executive_output_organization(
        repo_root,
        ExecutiveOutputOptions(executive_only=True),
    )

    assert processed == 1
    assert (executive_dir / "pdf" / "one.pdf").exists()
    assert (multi_dir / "two.pdf").exists()


def test_missing_output_directories_are_noop(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    assert organize_executive_summary(repo_root) == 0
    assert organize_multi_project_summary(repo_root) == 0
