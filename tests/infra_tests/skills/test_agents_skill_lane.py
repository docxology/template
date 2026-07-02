#!/usr/bin/env python3
"""Validation gate for the per-exemplar ``.agents/skills`` lane.

Every public exemplar ships a Hermes/agentskills.io skill at
``projects/templates/<name>/.agents/skills/<name>/SKILL.md``. That lane is
intentionally excluded from ``infrastructure.skills`` discovery (the Cursor/editor
manifest is a separate lane — see CLAUDE.md), so nothing else parses these files.
A YAML-quoting typo in one of them shipped once and no gate caught it; this test
is that gate. No mocks — it reads the real committed files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.skills.discovery import split_yaml_frontmatter


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _agents_skill_files() -> list[Path]:
    root = _repo_root()
    return sorted((root / "projects" / "templates").glob("*/.agents/skills/*/SKILL.md"))


def test_every_public_exemplar_ships_an_agents_skill() -> None:
    files = _agents_skill_files()
    exemplars = sorted((_repo_root() / "projects" / "templates").glob("*/"))
    # One .agents skill per public exemplar (15 as of this writing); never fewer.
    assert len(files) >= 15
    assert len(files) == len([d for d in exemplars if (d / ".agents").is_dir()])


@pytest.mark.parametrize("skill_path", _agents_skill_files(), ids=lambda p: p.parent.name)
def test_agents_skill_frontmatter_parses_and_is_complete(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")
    fm, body = split_yaml_frontmatter(text)
    # A YAML-quoting error makes split_yaml_frontmatter return None → caught here.
    assert fm is not None, f"{skill_path}: frontmatter failed to parse as YAML"
    for key in ("name", "description"):
        assert key in fm, f"{skill_path}: missing required frontmatter key '{key}'"
        assert isinstance(fm[key], str) and fm[key].strip(), f"{skill_path}: '{key}' must be a non-empty string"
    assert body.strip(), f"{skill_path}: skill body is empty"
