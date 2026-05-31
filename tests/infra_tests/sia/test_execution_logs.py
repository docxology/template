"""Tests for agent execution log loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.sia.execution_logs import load_agent_execution


def test_load_single_trajectory(tmp_path: Path) -> None:
    path = tmp_path / "agent_execution.json"
    path.write_text(json.dumps({"returncode": 0, "stdout": "ok"}), encoding="utf-8")
    log = load_agent_execution(path)
    assert log.format == "single"
    assert log.trajectories[0]["returncode"] == 0


def test_load_multi_trajectory(tmp_path: Path) -> None:
    path = tmp_path / "agent_execution.json"
    payload = {"trajectories": [{"q": 1}, {"q": 2}]}
    path.write_text(json.dumps(payload), encoding="utf-8")
    log = load_agent_execution(path)
    assert log.format == "multi"
    assert len(log.trajectories) == 2


def test_load_multi_trajectory_directory(tmp_path: Path) -> None:
    directory = tmp_path / "agent_execution"
    directory.mkdir()
    (directory / "execution_q1.json").write_text(json.dumps({"q": 1}), encoding="utf-8")
    (directory / "execution_q2.json").write_text(json.dumps({"q": 2}), encoding="utf-8")
    log = load_agent_execution(directory)
    assert log.format == "multi"
    assert len(log.trajectories) == 2


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="not found"):
        load_agent_execution(tmp_path / "missing.json")
