"""Deterministic context.md ledger for SIA runs."""

from __future__ import annotations

from pathlib import Path

from .models import EvaluationResult, GenerationArtifacts


def init_context(path: Path, *, task_name: str) -> Path:
    """Create an empty context ledger with a header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            f"# SIA context ledger — {task_name}\n\n",
            encoding="utf-8",
        )
    return path


def append_generation(
    path: Path,
    *,
    artifacts: GenerationArtifacts,
    improvement_excerpt: str = "",
) -> Path:
    """Append a generation summary without LLM calls."""
    lines = [
        f"## Generation {artifacts.generation}\n",
        f"- Target agent: `{artifacts.target_agent.name}`\n",
        f"- Execution log: `{artifacts.agent_execution.name}`\n",
    ]
    if artifacts.evaluation is not None:
        lines.extend(_format_evaluation(artifacts.evaluation))
    if improvement_excerpt.strip():
        lines.append("\n### Improvement rationale\n\n")
        lines.append(improvement_excerpt.strip())
        lines.append("\n")
    lines.append("\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.writelines(lines)
    return path


def _format_evaluation(result: EvaluationResult) -> list[str]:
    return [
        f"- Metric: `{result.metric_name}` = {result.metric_value:.6g}\n",
        f"- Samples: {result.n_samples}\n",
    ]


__all__ = ["append_generation", "init_context"]
