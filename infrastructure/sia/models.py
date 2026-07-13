"""Typed contracts for the SIA self-improvement harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskLayout:
    """Validated SIA task directory layout."""

    task_dir: Path
    public_dir: Path
    private_dir: Path
    reference_dir: Path
    task_md: Path
    evaluate_script: Path | None

    def to_dict(self) -> dict[str, str]:
        """Serialize paths as repo-relative strings."""
        return {
            "task_dir": str(self.task_dir),
            "public_dir": str(self.public_dir),
            "private_dir": str(self.private_dir),
            "reference_dir": str(self.reference_dir),
            "task_md": str(self.task_md),
            "evaluate_script": str(self.evaluate_script) if self.evaluate_script else "",
        }


@dataclass(frozen=True)
class EvaluationResult:
    """Canonical evaluation output written by task evaluate.py scripts."""

    metric_name: str
    metric_value: float
    n_samples: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the canonical results.json shape."""
        payload: dict[str, Any] = dict(self.extra) if self.extra else {}
        payload.update(
            {
                "metric_name": self.metric_name,
                "metric_value": self.metric_value,
                "n_samples": self.n_samples,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EvaluationResult:
        """Parse results.json payload."""
        extra = {
            key: value for key, value in payload.items() if key not in {"metric_name", "metric_value", "n_samples"}
        }
        return cls(
            metric_name=str(payload["metric_name"]),
            metric_value=float(payload["metric_value"]),
            n_samples=int(payload["n_samples"]),
            extra=extra,
        )


@dataclass(frozen=True)
class AgentExecutionLog:
    """Normalized agent execution record."""

    trajectories: tuple[dict[str, Any], ...]
    format: str  # "single" or "multi"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""
        if self.format == "single" and len(self.trajectories) == 1:
            return dict(self.trajectories[0])
        return {"trajectories": list(self.trajectories)}


@dataclass(frozen=True)
class GenerationArtifacts:
    """Artifact paths for one SIA generation."""

    generation: int
    gen_dir: Path
    target_agent: Path
    agent_execution: Path
    improvement: Path | None
    results: Path | None
    evaluation: EvaluationResult | None

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, Any]:
        """Serialize artifact metadata."""
        return {
            "generation": self.generation,
            "gen_dir": _portable_path(self.gen_dir, relative_to),
            "target_agent": _portable_path(self.target_agent, relative_to),
            "agent_execution": _portable_path(self.agent_execution, relative_to),
            "improvement": _portable_path(self.improvement, relative_to) if self.improvement else "",
            "results": _portable_path(self.results, relative_to) if self.results else "",
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
        }


def _portable_path(path: Path, relative_to: Path | None) -> str:
    if relative_to is not None:
        try:
            return path.resolve().relative_to(relative_to.resolve()).as_posix()
        except ValueError:
            pass
    return path.as_posix()


@dataclass
class RunConfig:
    """Configuration for one SIA run."""

    task_dir: Path
    output_dir: Path
    run_id: int = 1
    max_generations: int = 3
    live: bool = False
    fixtures_dir: Path | None = None
    target_timeout_sec: int = 60
    llm_model: str = ""

    def run_root(self) -> Path:
        """Return runs/run_{id}/ under output_dir."""
        return self.output_dir / "runs" / f"run_{self.run_id}"


@dataclass
class GenerationState:
    """Mutable state while advancing the SIA loop."""

    config: RunConfig
    layout: TaskLayout
    current_generation: int = 1
    artifacts: list[GenerationArtifacts] = field(default_factory=list)
    context_path: Path | None = None

    def gen_dir(self, generation: int | None = None) -> Path:
        """Path to gen_{n}/ under the run root."""
        gen = generation if generation is not None else self.current_generation
        return self.config.run_root() / f"gen_{gen}"


__all__ = [
    "AgentExecutionLog",
    "EvaluationResult",
    "GenerationArtifacts",
    "GenerationState",
    "RunConfig",
    "TaskLayout",
]
