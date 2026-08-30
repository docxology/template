"""Tests for AutoResearch multi-phase orchestration engine."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from infrastructure.autoresearch.orchestrator import AutoResearchOrchestrator


def test_autoresearch_orchestrator_execution(tmp_path: Path) -> None:
    # Set up synthetic repo and project
    repo_root = tmp_path
    proj_dir = repo_root / "projects" / "templates" / "test_proj"
    proj_dir.mkdir(parents=True)

    (proj_dir / "src").mkdir()
    (proj_dir / "tests").mkdir()
    (proj_dir / "scripts").mkdir()
    (proj_dir / "manuscript").mkdir()
    (proj_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: 'Test'\n")
    (proj_dir / "autoresearch.yaml").write_text("enabled: true\ntopic: 'Testing'\n")

    # Minimal pipeline.yaml
    pipe_file = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    pipe_file.parent.mkdir(parents=True)
    pipe_file.write_text("stages:\n  - name: Setup\n    script: stage_00_setup.py\n")

    orchestrator = AutoResearchOrchestrator(repo_root, "templates/test_proj")
    result = orchestrator.execute_plan(fail_on_extrinsic=False, write_reports=False)

    assert result.project_name == "templates/test_proj"
    assert len(result.events) > 0
    assert result.phase_reached in ("extrinsic", "completed")
    assert result.candidates_processed == 0
    assert result.candidate_budget == 1
    assert result.reports_written is False
    assert all(datetime.fromisoformat(event.timestamp) for event in result.events)
    payload = result.to_dict()
    assert payload["project_name"] == "templates/test_proj"
    assert payload["candidates_processed"] == 0
    assert payload["candidate_budget"] == 1
    assert "events" in payload
    assert all(event["timestamp"] for event in payload["events"])


def test_autoresearch_report_write_failure_is_fatal(tmp_path: Path) -> None:
    repo_root = tmp_path
    proj_dir = repo_root / "projects" / "templates" / "test_proj"
    proj_dir.mkdir(parents=True)
    for name in ("src", "tests", "scripts", "manuscript"):
        (proj_dir / name).mkdir()
    (proj_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: 'Test'\n")
    (proj_dir / "autoresearch.yaml").write_text("enabled: true\ntopic: 'Testing'\n")
    pipe_file = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    pipe_file.parent.mkdir(parents=True)
    pipe_file.write_text("stages:\n  - name: Setup\n    script: stage_00_setup.py\n")

    output_dir = proj_dir / "output"
    output_dir.mkdir()
    (output_dir / "reports").write_text("a file, not a directory", encoding="utf-8")

    result = AutoResearchOrchestrator(repo_root, "templates/test_proj").execute_plan(
        fail_on_extrinsic=False,
        write_reports=True,
    )

    assert result.success is False
    assert result.phase_reached == "finalization"
    assert result.candidates_processed == 0
    assert result.reports_written is False
    report_event = next(event for event in result.events if event.action == "write_reports")
    assert report_event.status == "error"


def test_autoresearch_cli_orchestrate(tmp_path: Path, capsys) -> None:
    from infrastructure.autoresearch.cli import main

    repo_root = tmp_path
    proj_dir = repo_root / "projects" / "templates" / "test_proj"
    proj_dir.mkdir(parents=True)
    (proj_dir / "src").mkdir()
    (proj_dir / "tests").mkdir()
    (proj_dir / "scripts").mkdir()
    (proj_dir / "manuscript").mkdir()
    (proj_dir / "manuscript" / "config.yaml").write_text("paper:\n  title: 'Test'\n")
    (proj_dir / "autoresearch.yaml").write_text("enabled: true\ntopic: 'Testing'\n")

    pipe_file = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    pipe_file.parent.mkdir(parents=True)
    pipe_file.write_text("stages:\n  - name: Setup\n    script: stage_00_setup.py\n")

    # Run orchestrate command
    rc = main(["orchestrate", "--project", "templates/test_proj", "--repo-root", str(repo_root), "--json"])
    assert rc in (0, 1)
    captured = capsys.readouterr()
    assert "project_name" in captured.out
