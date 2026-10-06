"""Tests for infrastructure.orchestration.stage_logger."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from infrastructure.orchestration.stage_logger import (
    setup_multiproject_log,
    setup_stage_log,
    stage_log_path,
)


def test_stage_log_path_per_project_layout(tmp_path: Path) -> None:
    p = stage_log_path(tmp_path, "template_code_project")
    expected = tmp_path / "projects" / "template_code_project" / "output" / "logs" / "pipeline.log"
    assert p == expected


def test_stage_log_path_central_layout(tmp_path: Path) -> None:
    p = stage_log_path(tmp_path, "tcp", layout="central")
    expected = tmp_path / "output" / "tcp" / "logs" / "pipeline.log"
    assert p == expected


def test_stage_log_path_rejects_unknown_layout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown layout"):
        stage_log_path(tmp_path, "x", layout="bogus")


def test_setup_stage_log_creates_directory_and_banner(tmp_path: Path) -> None:
    fixed_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    log = setup_stage_log(tmp_path, "template_code_project", "Environment Setup", now=fixed_now)
    assert log.exists()
    assert log.parent.is_dir()
    text = log.read_text(encoding="utf-8")
    assert "2024-01-01 12:00:00 UTC" in text
    assert "Starting: Environment Setup" in text


def test_setup_stage_log_appends_not_clobbers(tmp_path: Path) -> None:
    log = setup_stage_log(tmp_path, "template_code_project", "First")
    first_size = log.stat().st_size
    log = setup_stage_log(tmp_path, "template_code_project", "Second")
    assert log.stat().st_size > first_size
    text = log.read_text(encoding="utf-8")
    assert "First" in text
    assert "Second" in text


def test_setup_stage_log_idempotent_directory(tmp_path: Path) -> None:
    setup_stage_log(tmp_path, "template_code_project", "Stage1")
    # Second invocation appends through the same confined directory.
    setup_stage_log(tmp_path, "template_code_project", "Stage2")


def test_setup_multiproject_log_writes_banner(tmp_path: Path) -> None:
    fixed_now = datetime(2024, 6, 15, 9, 30, 0, tzinfo=timezone.utc)
    log = setup_multiproject_log(tmp_path, now=fixed_now)
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "Multi-Project Pipeline Started" in text
    assert "2024-06-15 09:30:00 UTC" in text


def _snapshot(directory: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
        for path in directory.rglob("*")
    }


@pytest.mark.parametrize("component", ["output", "logs", "leaf"])
def test_project_log_refuses_output_links_without_external_writes(tmp_path: Path, component: str) -> None:
    repository = tmp_path / "repo"
    project = repository / "projects/templates/demo"
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "sentinel.log"
    sentinel.write_text("PRIVATE FIXTURE BYTES\n")
    output = project / "output"
    if component == "output":
        project.mkdir(parents=True)
        output.symlink_to(external, target_is_directory=True)
    elif component == "logs":
        output.mkdir(parents=True)
        (output / "logs").symlink_to(external, target_is_directory=True)
    else:
        (output / "logs").mkdir(parents=True)
        (output / "logs/pipeline.log").symlink_to(sentinel)
    before = _snapshot(external)
    with pytest.raises((ValueError, OSError), match="[Ss]ymlink|symbolic links|real directory"):
        setup_stage_log(repository, "templates/demo", "Refused")
    assert _snapshot(external) == before


@pytest.mark.parametrize("layout", ["central", "aggregate"])
def test_root_layout_logs_refuse_linked_output_before_any_external_mkdir(tmp_path: Path, layout: str) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (external / "sentinel").write_bytes(b"preserved\n")
    (repository / "output").symlink_to(external, target_is_directory=True)
    before = _snapshot(external)
    with pytest.raises(ValueError):
        if layout == "aggregate":
            setup_multiproject_log(repository)
        else:
            setup_stage_log(repository, "templates/demo", "Refused", layout="central")
    assert _snapshot(external) == before


def test_project_log_refuses_linked_nominated_root_ancestor(tmp_path: Path) -> None:
    external = tmp_path / "external"
    (external / "repo").mkdir(parents=True)
    (external / "sentinel").write_text("preserved\n")
    linked = tmp_path / "linked"
    linked.symlink_to(external, target_is_directory=True)
    before = _snapshot(external)
    with pytest.raises(ValueError):
        setup_stage_log(linked / "repo", "templates/demo", "Refused")
    assert _snapshot(external) == before


@pytest.mark.parametrize("lifecycle", ["active", "working", "ongoing", "archive", "working/_category"])
def test_approved_private_project_leaf_links_append_in_canonical_project(tmp_path: Path, lifecycle: str) -> None:
    repository = tmp_path / "repo"
    canonical = tmp_path / "private" / lifecycle / "demo"
    (canonical / "src").mkdir(parents=True)
    lexical = repository / "projects" / lifecycle / "demo"
    lexical.parent.mkdir(parents=True)
    lexical.symlink_to(canonical, target_is_directory=True)
    fixed_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    log = setup_stage_log(repository, f"{lifecycle}/demo", "First", now=fixed_now)
    assert log == lexical / "output/logs/pipeline.log"
    first = log.read_bytes()
    assert "Starting: First" in first.decode()
    setup_stage_log(repository, f"{lifecycle}/demo", "Second", now=fixed_now)
    assert log.read_bytes().startswith(first)
    assert "Starting: Second" in log.read_text()
    assert (canonical / "output/logs/pipeline.log").stat().st_mode & 0o777 == 0o600


def test_private_project_link_does_not_allow_links_inside_output(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    canonical = tmp_path / "private/working/demo"
    (canonical / "src").mkdir(parents=True)
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    lexical.symlink_to(canonical, target_is_directory=True)
    external = tmp_path / "external"
    external.mkdir()
    (canonical / "output").symlink_to(external, target_is_directory=True)
    before = _snapshot(external)
    with pytest.raises(ValueError):
        setup_stage_log(repository, "working/demo", "Refused")
    assert _snapshot(external) == before


def test_public_project_leaf_link_is_not_a_private_lifecycle_exception(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    external = tmp_path / "external"
    (external / "src").mkdir(parents=True)
    lexical = repository / "projects/templates/demo"
    lexical.parent.mkdir(parents=True)
    lexical.symlink_to(external, target_is_directory=True)
    before = _snapshot(external)
    with pytest.raises(ValueError):
        setup_stage_log(repository, "templates/demo", "Refused")
    assert _snapshot(external) == before


@pytest.mark.parametrize("log_name", ["../escape.log", "/escape.log", "..", "", "dir\\escape.log", "bad\0.log"])
def test_log_filename_traversal_is_refused_before_writes(tmp_path: Path, log_name: str) -> None:
    with pytest.raises(ValueError, match="log_name"):
        setup_stage_log(tmp_path, "templates/demo", "Refused", log_name=log_name)
    with pytest.raises(ValueError, match="log_name"):
        setup_multiproject_log(tmp_path, log_name=log_name)
    assert list(tmp_path.iterdir()) == []
