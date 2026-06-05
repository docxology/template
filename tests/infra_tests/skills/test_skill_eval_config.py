"""Tests for the skill eval case-to-skill routing configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "docs/prompts/_skill-eval/scripts"
sys.path.insert(0, str(_SCRIPTS))

from skill_eval.config import EVAL_JSON, EVAL_SKILL_MAP, REPO  # noqa: E402


def test_eval_skill_map_covers_all_eval_ids() -> None:
    payload = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    eval_ids = {int(row["id"]) for row in payload["evals"]}

    assert eval_ids <= set(EVAL_SKILL_MAP)


def test_academic_workflow_eval_cases_are_mapped_to_new_skills() -> None:
    expected = {
        21: "docs/prompts/deep-research/SKILL.md",
        22: "docs/prompts/academic-paper/SKILL.md",
        23: "docs/prompts/academic-paper-reviewer/SKILL.md",
        24: "docs/prompts/academic-pipeline/SKILL.md",
        25: "docs/prompts/SKILL.md",
        26: "docs/prompts/SKILL.md",
    }

    for eval_id, rel_path in expected.items():
        assert EVAL_SKILL_MAP[eval_id] == rel_path
        assert (REPO / rel_path).is_file()


def test_agentic_use_eval_cases_are_mapped_to_agentic_skill() -> None:
    expected = {
        28: "docs/prompts/agentic-use/SKILL.md",
        29: "docs/prompts/agentic-use/SKILL.md",
    }

    for eval_id, rel_path in expected.items():
        assert EVAL_SKILL_MAP[eval_id] == rel_path
        assert (REPO / rel_path).is_file()
