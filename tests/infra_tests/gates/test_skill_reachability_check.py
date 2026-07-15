"""Tests for the opt-in skill-reachability gate (scripts/gates/skill_reachability_check.py).

No mocks: each case builds a real synthetic repo under ``tmp_path`` (a real
``docs/AGENTS.md``, the three entrypoint files, a ``SKILL.md`` under a discovery
root, and a ``docs/_generated/skills_index.md``) and exercises the gate's pass
and fail exit paths through its ``main`` entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.gates.skill_reachability_check import main as gate_main  # noqa: E402
from tests._support.projects import write_doc  # noqa: E402

_SKILL_REL = "infrastructure/widget/SKILL.md"
_SKILL_BODY = """---
name: infrastructure-widget
description: A synthetic widget skill for the reachability gate test.
---

# Widget
"""

# A docs/AGENTS.md whose Markdown links resolve (relative to docs/) to each of
# the three discovery entrypoints.
_GOOD_AGENTS = """# docs/ — Documentation Hub

| Audience | Start Here |
| -------- | ---------- |
| AI Agent | [skills index](_generated/skills_index.md), [prompts hub](prompts/SKILL.md), [composition](prompts/COMPOSITION.md) |
"""


def _write_entrypoints(repo_root: Path) -> None:
    """Create the three discovery entrypoint files on disk."""
    write_doc(repo_root / "docs" / "_generated" / "skills_index.md", "# Skill Index\n")
    write_doc(repo_root / "docs" / "prompts" / "SKILL.md", "# Prompts Hub\n")
    write_doc(repo_root / "docs" / "prompts" / "COMPOSITION.md", "# Composition\n")


def _write_skill_and_index(repo_root: Path, *, in_index: bool) -> None:
    """Create one discoverable SKILL.md and the skills index (with/without its row).

    ``docs/prompts/SKILL.md`` is itself discoverable (``docs/prompts`` is a
    discovery root), so a complete index must list both that path and the
    widget skill. ``in_index=False`` omits only the widget row to exercise the
    "discovered but absent" failure.
    """
    write_doc(repo_root / _SKILL_REL, _SKILL_BODY)
    index_body = "# Skill Index\n\n| Skill | Path | Description |\n| --- | --- | --- |\n"
    index_body += "| `prompts` | `docs/prompts/SKILL.md` | Prompts hub. |\n"
    if in_index:
        index_body += f"| `infrastructure-widget` | `{_SKILL_REL}` | A synthetic widget skill. |\n"
    write_doc(repo_root / "docs" / "_generated" / "skills_index.md", index_body)


def _make_good_repo(repo_root: Path) -> None:
    """Build a repo that satisfies both reachability invariants."""
    _write_entrypoints(repo_root)
    write_doc(repo_root / "docs" / "AGENTS.md", _GOOD_AGENTS)
    _write_skill_and_index(repo_root, in_index=True)


def test_gate_passes_for_reachable_repo(tmp_path: Path) -> None:
    """All three links resolve and the discovered skill is in the index → exit 0."""
    _make_good_repo(tmp_path)

    exit_code = gate_main(["--repo-root", str(tmp_path)])

    assert exit_code == 0


def test_gate_fails_when_a_front_door_link_is_missing(tmp_path: Path) -> None:
    """Dropping the COMPOSITION.md link makes the front-door check fail → exit 1."""
    _make_good_repo(tmp_path)
    # Rewrite AGENTS.md without the composition link (file still exists on disk).
    agents = (
        "# docs/ — Documentation Hub\n\n"
        "| AI Agent | [skills index](_generated/skills_index.md), "
        "[prompts hub](prompts/SKILL.md) |\n"
    )
    write_doc(tmp_path / "docs" / "AGENTS.md", agents)

    exit_code = gate_main(["--repo-root", str(tmp_path)])

    assert exit_code == 1


def test_gate_fails_when_link_does_not_resolve(tmp_path: Path, capsys) -> None:
    """A link whose target file is absent does not count as reaching it → exit 1."""
    _make_good_repo(tmp_path)
    # Delete the COMPOSITION.md target so its link no longer resolves.
    (tmp_path / "docs" / "prompts" / "COMPOSITION.md").unlink()

    exit_code = gate_main(["--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "COMPOSITION.md" in captured.out
    assert "skill-reachability gate" in captured.out


def test_gate_fails_when_index_missing_a_discovered_skill(tmp_path: Path, capsys) -> None:
    """A SKILL.md present on disk but absent from the index → exit 1."""
    _write_entrypoints(tmp_path)
    write_doc(tmp_path / "docs" / "AGENTS.md", _GOOD_AGENTS)
    _write_skill_and_index(tmp_path, in_index=False)

    exit_code = gate_main(["--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert _SKILL_REL in captured.out
    assert "skill-reachability gate" in captured.out


def test_gate_rejects_skill_path_mentioned_only_in_prose(tmp_path: Path, capsys) -> None:
    """A prose decoy must not masquerade as a generated index row."""
    _write_entrypoints(tmp_path)
    write_doc(tmp_path / "docs" / "AGENTS.md", _GOOD_AGENTS)
    _write_skill_and_index(tmp_path, in_index=False)
    index = tmp_path / "docs" / "_generated" / "skills_index.md"
    index.write_text(index.read_text(encoding="utf-8") + f"\nMentioned elsewhere: `{_SKILL_REL}`.\n", encoding="utf-8")

    exit_code = gate_main(["--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert _SKILL_REL in captured.out
