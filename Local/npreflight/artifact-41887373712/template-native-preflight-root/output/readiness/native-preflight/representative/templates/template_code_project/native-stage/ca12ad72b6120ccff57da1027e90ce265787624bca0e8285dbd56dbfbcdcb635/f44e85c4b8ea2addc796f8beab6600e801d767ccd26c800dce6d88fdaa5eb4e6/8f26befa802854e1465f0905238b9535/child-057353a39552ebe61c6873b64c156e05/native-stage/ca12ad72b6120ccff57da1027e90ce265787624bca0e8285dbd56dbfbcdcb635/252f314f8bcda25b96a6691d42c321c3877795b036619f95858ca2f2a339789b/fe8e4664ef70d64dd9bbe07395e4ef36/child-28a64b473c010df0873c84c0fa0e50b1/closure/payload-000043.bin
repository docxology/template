"""Benchmark harnesses for canonical template projects."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.benchmark.template_harness import (
        BenchmarkCheckResult,
        BenchmarkManifest,
        BenchmarkScore,
    )
    from infrastructure.benchmark.rubrics import RubricScore, RubricSet

__all__ = [
    "BenchmarkCheckResult",
    "BenchmarkManifest",
    "BenchmarkScore",
    "RubricScore",
    "RubricSet",
    "load_benchmark_manifest",
    "run_benchmark_manifest",
    "score_project_against_manifest",
    "score_rubric",
    "scores_to_dict",
    "scores_to_markdown",
    "write_default_manifest",
]


def __getattr__(name: str) -> Any:
    """Load benchmark harness exports lazily."""
    if name in __all__:
        if name in {"RubricScore", "RubricSet", "score_rubric"}:
            module = import_module("infrastructure.benchmark.rubrics")
            return getattr(module, name)
        module = import_module("infrastructure.benchmark.template_harness")
        return getattr(module, name)
    raise AttributeError(name)
