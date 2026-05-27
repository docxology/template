"""Candidate selection, task orchestration, and ML result writers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from infrastructure.autoresearch import BudgetPolicy

from .ml_data import (
    CandidateSpec,
    DatasetSummary,
    MNISTTaskConfig,
    load_mnist_arrays,
    load_mnist_task_config,
    summarize_dataset,
)
from .ml_models import BaselineResult, CandidateResult, evaluate_candidate, evaluate_nearest_centroid


@dataclass(frozen=True)
class MLTaskResult:
    """Complete deterministic MNIST neural-network AutoResearch result."""

    task_config: MNISTTaskConfig
    dataset: DatasetSummary
    baseline: BaselineResult
    candidates: tuple[CandidateResult, ...]
    accepted_candidate_id: str
    candidate_count: int
    evaluated_candidate_count: int
    budget_exhausted: bool
    llm_calls_used: int
    cost_usd_used: float

    @property
    def accepted_candidate(self) -> CandidateResult:
        """Return the accepted candidate result."""
        for candidate in self.candidates:
            if candidate.identifier == self.accepted_candidate_id:
                return candidate
        raise ValueError(f"accepted candidate is missing: {self.accepted_candidate_id}")

    @property
    def best_accuracy(self) -> float:
        """Return the accepted candidate test accuracy."""
        return float(self.accepted_candidate.test_accuracy or 0.0)

    @property
    def accuracy_delta(self) -> float:
        """Return the accepted-candidate improvement over the baseline."""
        return self.best_accuracy - self.baseline.test_accuracy

    @property
    def benchmark_score(self) -> float:
        """Return a compact benchmark score for the bounded loop."""
        metric_score = 1.0 if self.accuracy_delta > 0 else 0.5 if self.accuracy_delta == 0 else 0.0
        budget_score = 1.0 if self.evaluated_candidate_count <= self.task_config.max_candidates else 0.0
        offline_score = 1.0 if self.llm_calls_used == 0 and self.cost_usd_used == 0.0 else 0.0
        # Reward a neural candidate only if it was actually evaluated (has a real
        # test accuracy), not merely present/deferred in the candidate set. A bare
        # presence check let an unevaluated transformer earn a full point.
        neural_score = 1.0 if self.transformer_evaluated else 0.0
        selection_score = 1.0 if self.accepted_candidate.status == "accepted" else 0.0
        return round((metric_score + budget_score + offline_score + neural_score + selection_score) / 5.0, 3)

    @property
    def transformer_evaluated(self) -> bool:
        """Return whether a tiny patch-attention candidate was evaluated."""
        return any(
            candidate.model_type == "tiny_patch_transformer" and candidate.test_accuracy is not None
            for candidate in self.candidates
        )

    @property
    def model_families(self) -> tuple[str, ...]:
        """Return the configured baseline and candidate model families."""
        values = {self.baseline.model_type}
        values.update(candidate.model_type for candidate in self.candidates)
        return tuple(sorted(values))

    def to_dict(self) -> dict[str, object]:
        """Serialize the full task result."""
        return {
            "task_name": self.task_config.name,
            "configuration_source": self.task_config.source_path,
            "task_config": self.task_config.to_dict(),
            "objective": {
                "metric": self.task_config.metric_name,
                "direction": self.task_config.metric_direction,
            },
            "model_families": list(self.model_families),
            "dataset": self.dataset.to_dict(),
            "baseline": self.baseline.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "accepted_candidate": self.accepted_candidate.to_dict(),
            "accepted_candidate_id": self.accepted_candidate_id,
            "candidate_count": self.candidate_count,
            "evaluated_candidate_count": self.evaluated_candidate_count,
            "budget_exhausted": self.budget_exhausted,
            "llm_calls_used": self.llm_calls_used,
            "cost_usd_used": self.cost_usd_used,
            "best_accuracy": round(self.best_accuracy, 6),
            "baseline_accuracy": round(self.baseline.test_accuracy, 6),
            "accuracy_delta": round(self.accuracy_delta, 6),
            "benchmark_score": self.benchmark_score,
            "transformer_evaluated": self.transformer_evaluated,
        }

    def to_summary_dict(self) -> dict[str, object]:
        """Serialize the manuscript-facing summary."""
        return {
            "seed": self.task_config.seed,
            "dataset_name": self.dataset.dataset_name,
            "train_size": self.dataset.train_size,
            "test_size": self.dataset.test_size,
            "candidate_count": self.candidate_count,
            "evaluated_candidate_count": self.evaluated_candidate_count,
            "accepted_candidate_id": self.accepted_candidate_id,
            "accepted_model_type": self.accepted_candidate.model_type,
            "baseline_accuracy": round(self.baseline.test_accuracy, 6),
            "best_accuracy": round(self.best_accuracy, 6),
            "accuracy_delta": round(self.accuracy_delta, 6),
            "budget_exhausted": self.budget_exhausted,
            "benchmark_score": self.benchmark_score,
            "llm_calls_used": self.llm_calls_used,
            "cost_usd_used": self.cost_usd_used,
            "parameter_count": self.accepted_candidate.parameter_count,
            "transformer_evaluated": self.transformer_evaluated,
        }


def run_bounded_ml_task(project_root: Path, budget_policy: BudgetPolicy) -> MLTaskResult:
    """Run the configured deterministic MNIST neural-network task."""
    config = load_mnist_task_config(project_root)
    x_train, y_train, x_test, y_test = load_mnist_arrays(project_root, config)
    dataset = summarize_dataset(project_root, config, x_train, y_train, x_test, y_test)
    baseline = evaluate_nearest_centroid(x_train, y_train, x_test, y_test, identifier=config.baseline_id)
    candidate_limit = min(config.max_candidates, budget_policy.max_iterations)
    evaluated_specs = config.candidates[:candidate_limit]
    deferred_specs = config.candidates[candidate_limit:]
    evaluated = tuple(
        evaluate_candidate(
            spec,
            x_train,
            y_train,
            x_test,
            y_test,
            baseline_accuracy=baseline.test_accuracy,
            robustness_transforms=config.robustness_transforms,
        )
        for spec in evaluated_specs
    )
    accepted = select_accepted_candidate(evaluated)
    candidates = tuple(_with_final_status(result, accepted.identifier) for result in evaluated) + tuple(
        deferred_candidate(spec) for spec in deferred_specs
    )
    return MLTaskResult(
        task_config=config,
        dataset=dataset,
        baseline=baseline,
        candidates=candidates,
        accepted_candidate_id=accepted.identifier,
        candidate_count=len(config.candidates),
        evaluated_candidate_count=len(evaluated_specs),
        budget_exhausted=len(config.candidates) > len(evaluated_specs),
        llm_calls_used=0,
        cost_usd_used=0.0,
    )


def select_accepted_candidate(candidates: tuple[CandidateResult, ...]) -> CandidateResult:
    """Select the best candidate with deterministic tie-breaking."""
    if not candidates:
        raise ValueError("at least one candidate is required")
    return sorted(
        candidates,
        key=lambda candidate: (
            -(candidate.test_accuracy if candidate.test_accuracy is not None else -1.0),
            candidate.parameter_count,
            candidate.identifier,
        ),
    )[0]


def deferred_candidate(spec: CandidateSpec) -> CandidateResult:
    """Create an unevaluated deferred candidate row."""
    return CandidateResult(
        identifier=spec.identifier,
        title=spec.title,
        model_type=spec.model_type,
        status="deferred",
        lifecycle=("proposed", "deferred"),
        test_accuracy=None,
        train_accuracy=None,
        test_loss=None,
        train_loss=None,
        parameter_count=0,
        epochs=0,
        seed=spec.seed,
        accuracy_delta_vs_baseline=None,
        config=spec.to_dict(),
    )


def write_confusion_matrix_csv(path: Path, matrix: tuple[tuple[int, ...], ...]) -> Path:
    """Write a confusion matrix CSV for the accepted candidate."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true\\pred", *range(10)])
        for label, row in enumerate(matrix):
            writer.writerow([label, *row])
    return path


def write_training_history_csv(path: Path, result: MLTaskResult) -> Path:
    """Write epoch-level train/test metrics for evaluated candidates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "candidate_id",
                "model_type",
                "epoch",
                "learning_rate",
                "train_accuracy",
                "test_accuracy",
                "train_loss",
                "test_loss",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        for candidate in result.candidates:
            for row in candidate.training_history:
                writer.writerow(
                    {
                        "candidate_id": candidate.identifier,
                        "model_type": candidate.model_type,
                        "epoch": row["epoch"],
                        "learning_rate": row["learning_rate"],
                        "train_accuracy": row["train_accuracy"],
                        "test_accuracy": row["test_accuracy"],
                        "train_loss": row["train_loss"],
                        "test_loss": row["test_loss"],
                    }
                )
    return path


def accepted_error_examples(project_root: Path, result: MLTaskResult, *, limit: int = 10) -> list[dict[str, int]]:
    """Return deterministic accepted-candidate test-set error examples."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    predictions = np.asarray(result.accepted_candidate.test_predictions, dtype=np.int64)
    if predictions.size != y_test.size:
        raise ValueError("accepted-candidate predictions do not match test-set size")
    examples: list[dict[str, int]] = []
    for index, (true_label, predicted_label) in enumerate(zip(y_test, predictions, strict=True)):
        if int(true_label) == int(predicted_label):
            continue
        examples.append(
            {
                "test_index": index,
                "true_label": int(true_label),
                "predicted_label": int(predicted_label),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def write_error_examples_json(path: Path, project_root: Path, result: MLTaskResult, *, limit: int = 10) -> Path:
    """Write accepted-candidate error examples for review and figure generation."""
    payload = {
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_dataset": result.task_config.dataset_path,
        "examples": accepted_error_examples(project_root, result, limit=limit),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _with_final_status(result: CandidateResult, accepted_id: str) -> CandidateResult:
    if result.identifier == accepted_id:
        return replace(result, status="accepted", lifecycle=("proposed", "evaluated", "accepted"))
    return replace(result, status="rejected", lifecycle=("proposed", "evaluated", "rejected"))


__all__ = [
    "CandidateResult",
    "MLTaskResult",
    "accepted_error_examples",
    "deferred_candidate",
    "run_bounded_ml_task",
    "select_accepted_candidate",
    "write_confusion_matrix_csv",
    "write_error_examples_json",
    "write_training_history_csv",
]
