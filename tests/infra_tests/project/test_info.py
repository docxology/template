#!/usr/bin/env python3
"""Tests for infrastructure.project.info."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import FileNotFoundError
from infrastructure.project.info import collect_project_info


def _scaffold_project(tmp_path: Path, name: str = "demo") -> Path:
    root = tmp_path / "projects" / name
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: Demo Title\nauthors:\n  - name: Author\n",
        encoding="utf-8",
    )
    (root / "manuscript" / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_mod.py").write_text("def test_f():\n    assert True\n", encoding="utf-8")
    (root / "output" / "pdf").mkdir(parents=True)
    (root / "output" / "figures").mkdir(parents=True)
    (root / "output" / "pdf" / "demo.pdf").write_bytes(b"%PDF-1.4\n")
    (root / "output" / "figures" / "fig.png").write_bytes(b"\x89PNG\r\n")
    return root


def test_collect_project_info_happy_path(tmp_path: Path) -> None:
    _scaffold_project(tmp_path)
    info = collect_project_info("demo", tmp_path)
    assert info["name"] == "demo"
    assert info["manuscript"]["has_config"] is True
    assert info["manuscript"]["title"] == "Demo Title"
    assert info["source"]["py_files"] == 1
    assert info["tests"]["test_files"] == 1
    assert info["output"]["pdf_count"] == 1
    assert info["output"]["figure_count"] == 1


def test_collect_project_info_missing_project(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        collect_project_info("missing", tmp_path)
