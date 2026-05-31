"""Tests for local CodeGraph integration helpers."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.project.codegraph import (
    build_codegraph_files_command,
    build_codegraph_init_command,
    build_scope_check_command,
    extract_paths_from_files_payload,
    unexpected_indexed_project_paths,
)


def test_build_codegraph_init_command_targets_repo_root(tmp_path: Path) -> None:
    command = build_codegraph_init_command(tmp_path)

    assert command.cwd == tmp_path
    assert command.argv == ("codegraph", "init", str(tmp_path), "--index")
    assert "Initialize" in command.description


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_build_codegraph_init_command_resolves_project_symlink(tmp_path: Path) -> None:
    external = tmp_path / "private" / "active" / "encinitas"
    external.mkdir(parents=True)
    symlink = tmp_path / "template" / "projects" / "encinitas"
    symlink.parent.mkdir(parents=True)
    symlink.symlink_to(external, target_is_directory=True)

    command = build_codegraph_init_command(symlink)

    assert command.cwd == external
    assert command.argv == ("codegraph", "init", str(external), "--index")


def test_build_codegraph_files_command_uses_json_output(tmp_path: Path) -> None:
    command = build_codegraph_files_command(tmp_path)

    assert command.cwd == tmp_path
    assert command.argv == ("codegraph", "files", str(tmp_path), "--json")


def test_scope_check_command_pipes_files_query_to_verify_step(tmp_path: Path) -> None:
    command = build_scope_check_command(tmp_path)

    assert command.cwd == tmp_path
    assert "codegraph files" in command.description
    assert "verify" in command.description.lower()


def test_unexpected_indexed_project_paths_flags_private_projects() -> None:
    indexed_paths = [
        "infrastructure/project/codegraph.py",
        "projects/README.md",
        "projects/templates/template_code_project/src/optimizer.py",
        "projects/templates/template_autoresearch_project/tests/test_loop.py",
        "projects/encinitas/src/history.py",
        "projects/biology_textbook/manuscript/01_cells.md",
    ]

    assert unexpected_indexed_project_paths(indexed_paths) == [
        "projects/biology_textbook/manuscript/01_cells.md",
        "projects/encinitas/src/history.py",
    ]


def test_extract_paths_from_files_payload_accepts_common_json_shapes() -> None:
    payload = """
    {
      "files": [
        {"path": "infrastructure/project/codegraph.py"},
        "projects/templates/template_code_project/src/optimizer.py"
      ],
      "nested": {"relativePath": "projects/encinitas/src/history.py"}
    }
    """

    assert extract_paths_from_files_payload(payload) == [
        "infrastructure/project/codegraph.py",
        "projects/encinitas/src/history.py",
        "projects/templates/template_code_project/src/optimizer.py",
    ]
