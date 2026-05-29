"""Tests for infrastructure.core.agent_memory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.agent_memory import (
    MAX_BULLETS,
    empty_memory_payload,
    load_memory,
    normalize_bullets,
    save_memory,
)


def test_normalize_bullets_strips_dedupes_and_caps() -> None:
    items = [
        "  First preference  ",
        "first preference",
        "Second",
        "",
        "Third",
    ]
    assert normalize_bullets(items) == ["First preference", "Second", "Third"]
    long_list = [f"item-{index}" for index in range(MAX_BULLETS + 5)]
    assert len(normalize_bullets(long_list)) == MAX_BULLETS


def test_empty_memory_payload_has_required_keys() -> None:
    payload = empty_memory_payload()
    assert payload["version"] == 1
    assert payload["learned_user_preferences"] == []
    assert payload["learned_workspace_facts"] == []


def test_load_memory_uses_example_when_live_file_missing(tmp_path: Path) -> None:
    example = tmp_path / ".cursor/hooks/state/continual-learning-memory.example.json"
    example.parent.mkdir(parents=True)
    example.write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": None,
                "learned_user_preferences": ["Prefer uv run"],
                "learned_workspace_facts": [],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_memory(tmp_path)
    assert loaded["learned_user_preferences"] == ["Prefer uv run"]


def test_save_memory_round_trip(tmp_path: Path) -> None:
    payload = empty_memory_payload()
    payload["learned_user_preferences"] = ["Alpha", "alpha", "Beta"]
    payload["learned_workspace_facts"] = ["Fact one"]
    path = save_memory(tmp_path, payload)
    assert path.is_file()
    reloaded = load_memory(tmp_path)
    assert reloaded["learned_user_preferences"] == ["Alpha", "Beta"]
    assert reloaded["learned_workspace_facts"] == ["Fact one"]
    assert reloaded["updated_at"] is not None


def test_load_memory_rejects_invalid_version(tmp_path: Path) -> None:
    memory = tmp_path / ".cursor/hooks/state/continual-learning-memory.json"
    memory.parent.mkdir(parents=True)
    memory.write_text(
        json.dumps(
            {
                "version": 99,
                "updated_at": None,
                "learned_user_preferences": [],
                "learned_workspace_facts": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported memory version"):
        load_memory(tmp_path)
