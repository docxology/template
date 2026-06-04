"""Self-improving AI harness utilities (SIA contract)."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AgentExecutionLog",
    "EvaluationResult",
    "GenerationArtifacts",
    "GenerationState",
    "RunConfig",
    "TaskLayout",
    "append_generation",
    "init_context",
    "load_agent_execution",
    "read_results_json",
    "run_evaluation",
    "run_sia_loop",
    "validate_task_dir",
    "write_results_json",
]

_EXPORTS = {
    "AgentExecutionLog": ("infrastructure.sia.models", "AgentExecutionLog"),
    "EvaluationResult": ("infrastructure.sia.models", "EvaluationResult"),
    "GenerationArtifacts": ("infrastructure.sia.models", "GenerationArtifacts"),
    "GenerationState": ("infrastructure.sia.models", "GenerationState"),
    "RunConfig": ("infrastructure.sia.models", "RunConfig"),
    "TaskLayout": ("infrastructure.sia.models", "TaskLayout"),
    "append_generation": ("infrastructure.sia.context_ledger", "append_generation"),
    "init_context": ("infrastructure.sia.context_ledger", "init_context"),
    "load_agent_execution": ("infrastructure.sia.execution_logs", "load_agent_execution"),
    "read_results_json": ("infrastructure.sia.evaluation_runner", "read_results_json"),
    "run_evaluation": ("infrastructure.sia.evaluation_runner", "run_evaluation"),
    "run_sia_loop": ("infrastructure.sia.loop_runner", "run_sia_loop"),
    "validate_task_dir": ("infrastructure.sia.task_layout", "validate_task_dir"),
    "write_results_json": ("infrastructure.sia.evaluation_runner", "write_results_json"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)
