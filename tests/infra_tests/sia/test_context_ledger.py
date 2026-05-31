"""Tests for context ledger."""

from __future__ import annotations

from pathlib import Path

from infrastructure.sia.context_ledger import append_generation, init_context
from infrastructure.sia.models import EvaluationResult, GenerationArtifacts


def test_context_ledger_is_deterministic(tmp_path: Path) -> None:
    path = init_context(tmp_path / "context.md", task_name="mini")
    artifacts = GenerationArtifacts(
        generation=1,
        gen_dir=tmp_path / "gen_1",
        target_agent=tmp_path / "gen_1" / "target_agent.py",
        agent_execution=tmp_path / "gen_1" / "agent_execution.json",
        improvement=None,
        results=tmp_path / "gen_1" / "results.json",
        evaluation=EvaluationResult("accuracy", 0.8, 10),
    )
    append_generation(path, artifacts=artifacts, improvement_excerpt="Tune threshold.")
    text = path.read_text(encoding="utf-8")
    assert "Generation 1" in text
    assert "accuracy" in text
    assert "Tune threshold" in text


def test_context_ledger_appends_once_per_call(tmp_path: Path) -> None:
    path = init_context(tmp_path / "context.md", task_name="mini")
    artifacts = GenerationArtifacts(
        generation=1,
        gen_dir=tmp_path / "gen_1",
        target_agent=tmp_path / "gen_1" / "target_agent.py",
        agent_execution=tmp_path / "gen_1" / "agent_execution.json",
        improvement=None,
        results=tmp_path / "gen_1" / "results.json",
        evaluation=EvaluationResult("accuracy", 0.8, 10),
    )
    append_generation(path, artifacts=artifacts)
    append_generation(path, artifacts=artifacts)
    text = path.read_text(encoding="utf-8")
    assert text.count("## Generation 1") == 2
