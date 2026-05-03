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
    log = setup_stage_log(tmp_path, "template_code_project", "Setup Environment", now=fixed_now)
    assert log.exists()
    assert log.parent.is_dir()
    text = log.read_text(encoding="utf-8")
    assert "2024-01-01 12:00:00 UTC" in text
    assert "Starting: Setup Environment" in text


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
    # Second invocation must not raise; uses parents=True/exist_ok=True.
    setup_stage_log(tmp_path, "template_code_project", "Stage2")


def test_setup_multiproject_log_writes_banner(tmp_path: Path) -> None:
    fixed_now = datetime(2024, 6, 15, 9, 30, 0, tzinfo=timezone.utc)
    log = setup_multiproject_log(tmp_path, now=fixed_now)
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "Multi-Project Pipeline Started" in text
    assert "2024-06-15 09:30:00 UTC" in text
