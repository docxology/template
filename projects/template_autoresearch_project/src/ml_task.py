"""Deterministic tiny ML task for the AutoResearch exemplar."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from infrastructure.autoresearch import BudgetPolicy

DEFAULT_SEED = 20260525
DEFAULT_TRAIN_SIZE = 96
DEFAULT_TEST_SIZE = 64


@dataclass(frozen=True)
class DatasetSummary:
    """Summary statistics for the deterministic classification task."""

    seed: int
    train_size: int
    test_size: int
    feature_count: int
    train_positive_rate: float
    test_positive_rate: float

    def to_dict(self) -> dict[str, int | float]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


@dataclass(frozen=True)
class CandidateSpec:
    """One bounded candidate proposed for the ML loop."""

    identifier: str
    title: str
    feature_map: str
    alpha: float
    complexity: int
    proposal_status: str = "proposed"

    def to_dict(self) -> dict[str, str | float | int]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


@dataclass(frozen=True)
class CandidateResult:
    """Evaluation result for one candidate."""

    identifier: str
    title: str
    feature_map: str
    alpha: float
    complexity: int
    status: str
    lifecycle: tuple[str, ...]
    accuracy: float | None
    accuracy_delta_vs_baseline: float | None

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["lifecycle"] = list(self.lifecycle)
        return payload


@dataclass(frozen=True)
class BaselineResult:
    """Majority-class baseline for the ML task."""

    identifier: str
    accuracy: float
    predicted_label: int

    def to_dict(self) -> dict[str, str | int | float]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


@dataclass(frozen=True)
class MLTaskResult:
    """Complete deterministic ML-loop result."""

    task_name: str
    objective_metric: str
    objective_direction: str
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
        """Return the accepted candidate accuracy."""
        accuracy = self.accepted_candidate.accuracy
        return float(accuracy if accuracy is not None else 0.0)

    @property
    def accuracy_delta(self) -> float:
        """Return accepted-candidate accuracy improvement over baseline."""
        return self.best_accuracy - self.baseline.accuracy

    @property
    def benchmark_score(self) -> float:
        """Return a compact benchmark score for the bounded loop."""
        metric_score = 1.0 if self.accuracy_delta > 0 else 0.5 if self.accuracy_delta == 0 else 0.0
        budget_score = 1.0 if self.evaluated_candidate_count <= self.candidate_count else 0.0
        offline_score = 1.0 if self.llm_calls_used == 0 and self.cost_usd_used == 0.0 else 0.0
        selection_score = 1.0 if self.accepted_candidate.status == "accepted" else 0.0
        return round((metric_score + budget_score + offline_score + selection_score) / 4.0, 3)

    def to_dict(self) -> dict[str, object]:
        """Serialize the full task result."""
        return {
            "task_name": self.task_name,
            "objective": {
                "metric": self.objective_metric,
                "direction": self.objective_direction,
            },
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
            "baseline_accuracy": round(self.baseline.accuracy, 6),
            "accuracy_delta": round(self.accuracy_delta, 6),
            "benchmark_score": self.benchmark_score,
        }

    def to_summary_dict(self) -> dict[str, object]:
        """Serialize the manuscript-facing summary."""
        return {
            "seed": self.dataset.seed,
            "candidate_count": self.candidate_count,
            "evaluated_candidate_count": self.evaluated_candidate_count,
            "accepted_candidate_id": self.accepted_candidate_id,
            "baseline_accuracy": round(self.baseline.accuracy, 6),
            "best_accuracy": round(self.best_accuracy, 6),
            "accuracy_delta": round(self.accuracy_delta, 6),
            "budget_exhausted": self.budget_exhausted,
            "benchmark_score": self.benchmark_score,
            "llm_calls_used": self.llm_calls_used,
            "cost_usd_used": self.cost_usd_used,
        }


def run_bounded_ml_task(
    project_root: Path,
    budget_policy: BudgetPolicy,
    *,
    seed: int = DEFAULT_SEED,
    train_size: int = DEFAULT_TRAIN_SIZE,
    test_size: int = DEFAULT_TEST_SIZE,
) -> MLTaskResult:
    """Run the deterministic bounded ML task."""
    dataset = generate_dataset(seed=seed, train_size=train_size, test_size=test_size)
    x_train, y_train, x_test, y_test = dataset
    summary = summarize_dataset(x_train, y_train, x_test, y_test, seed=seed)
    baseline = evaluate_majority_baseline(y_train, y_test)
    specs = load_candidate_specs(project_root)
    evaluated_specs = specs[: budget_policy.max_iterations]
    deferred_specs = specs[budget_policy.max_iterations :]

    evaluated = [
        evaluate_candidate(spec, x_train, y_train, x_test, y_test, baseline_accuracy=baseline.accuracy)
        for spec in evaluated_specs
    ]
    accepted = select_accepted_candidate(tuple(evaluated))
    candidates = []
    for result in evaluated:
        if result.identifier == accepted.identifier:
            candidates.append(
                CandidateResult(
                    identifier=result.identifier,
                    title=result.title,
                    feature_map=result.feature_map,
                    alpha=result.alpha,
                    complexity=result.complexity,
                    status="accepted",
                    lifecycle=("proposed", "evaluated", "accepted"),
                    accuracy=result.accuracy,
                    accuracy_delta_vs_baseline=result.accuracy_delta_vs_baseline,
                )
            )
        else:
            candidates.append(
                CandidateResult(
                    identifier=result.identifier,
                    title=result.title,
                    feature_map=result.feature_map,
                    alpha=result.alpha,
                    complexity=result.complexity,
                    status="rejected",
                    lifecycle=("proposed", "evaluated", "rejected"),
                    accuracy=result.accuracy,
                    accuracy_delta_vs_baseline=result.accuracy_delta_vs_baseline,
                )
            )
    candidates.extend(deferred_candidate(spec) for spec in deferred_specs)

    return MLTaskResult(
        task_name="fixed-seed nonlinear binary classification",
        objective_metric="heldout_accuracy",
        objective_direction="maximize",
        dataset=summary,
        baseline=baseline,
        candidates=tuple(candidates),
        accepted_candidate_id=accepted.identifier,
        candidate_count=len(specs),
        evaluated_candidate_count=len(evaluated_specs),
        budget_exhausted=len(specs) > len(evaluated_specs),
        llm_calls_used=0,
        cost_usd_used=0.0,
    )


def generate_dataset(
    *,
    seed: int = DEFAULT_SEED,
    train_size: int = DEFAULT_TRAIN_SIZE,
    test_size: int = DEFAULT_TEST_SIZE,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate a fixed-seed nonlinear binary classification dataset."""
    rng = np.random.default_rng(seed)
    total_size = train_size + test_size
    x_values = rng.normal(loc=0.0, scale=1.0, size=(total_size, 2))
    latent = x_values[:, 0] * x_values[:, 1] + 0.18 * rng.normal(size=total_size)
    y_values = np.where(latent >= 0.0, 1, -1).astype(int)
    order = rng.permutation(total_size)
    train_indices = order[:train_size]
    test_indices = order[train_size:]
    return x_values[train_indices], y_values[train_indices], x_values[test_indices], y_values[test_indices]


def summarize_dataset(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    *,
    seed: int,
) -> DatasetSummary:
    """Summarize train/test data without exposing raw samples."""
    return DatasetSummary(
        seed=seed,
        train_size=int(y_train.size),
        test_size=int(y_test.size),
        feature_count=int(x_train.shape[1]),
        train_positive_rate=round(float(np.mean(y_train == 1)), 6),
        test_positive_rate=round(float(np.mean(y_test == 1)), 6),
    )


def evaluate_majority_baseline(y_train: np.ndarray, y_test: np.ndarray) -> BaselineResult:
    """Evaluate a deterministic majority-class baseline."""
    positive_count = int(np.sum(y_train == 1))
    negative_count = int(np.sum(y_train == -1))
    predicted_label = 1 if positive_count >= negative_count else -1
    accuracy = float(np.mean(y_test == predicted_label))
    return BaselineResult(
        identifier="majority_class_baseline",
        accuracy=round(accuracy, 6),
        predicted_label=predicted_label,
    )


def evaluate_candidate(
    spec: CandidateSpec,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    *,
    baseline_accuracy: float,
) -> CandidateResult:
    """Evaluate one ridge classifier candidate."""
    train_features = feature_matrix(x_train, spec.feature_map)
    test_features = feature_matrix(x_test, spec.feature_map)
    penalty = np.eye(train_features.shape[1])
    penalty[0, 0] = 0.0
    lhs = train_features.T @ train_features + spec.alpha * penalty
    rhs = train_features.T @ y_train
    weights = np.linalg.solve(lhs, rhs)
    scores = test_features @ weights
    predictions = np.where(scores >= 0.0, 1, -1)
    accuracy = round(float(np.mean(predictions == y_test)), 6)
    return CandidateResult(
        identifier=spec.identifier,
        title=spec.title,
        feature_map=spec.feature_map,
        alpha=spec.alpha,
        complexity=spec.complexity,
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        accuracy=accuracy,
        accuracy_delta_vs_baseline=round(accuracy - baseline_accuracy, 6),
    )


def select_accepted_candidate(candidates: tuple[CandidateResult, ...]) -> CandidateResult:
    """Select the best candidate with deterministic simplicity tie-breaking."""
    if not candidates:
        raise ValueError("at least one candidate is required")
    return sorted(
        candidates,
        key=lambda candidate: (
            -(candidate.accuracy if candidate.accuracy is not None else -1.0),
            candidate.complexity,
            candidate.alpha,
            candidate.identifier,
        ),
    )[0]


def deferred_candidate(spec: CandidateSpec) -> CandidateResult:
    """Create an unevaluated deferred candidate row."""
    return CandidateResult(
        identifier=spec.identifier,
        title=spec.title,
        feature_map=spec.feature_map,
        alpha=spec.alpha,
        complexity=spec.complexity,
        status="deferred",
        lifecycle=("proposed", "deferred"),
        accuracy=None,
        accuracy_delta_vs_baseline=None,
    )


def feature_matrix(x_values: np.ndarray, feature_map: str) -> np.ndarray:
    """Return the candidate feature matrix."""
    ones = np.ones((x_values.shape[0], 1))
    if feature_map == "linear":
        return np.column_stack((ones, x_values[:, 0], x_values[:, 1]))
    if feature_map == "quadratic":
        return np.column_stack(
            (
                ones,
                x_values[:, 0],
                x_values[:, 1],
                x_values[:, 0] * x_values[:, 1],
                x_values[:, 0] ** 2,
                x_values[:, 1] ** 2,
            )
        )
    raise ValueError(f"unsupported feature_map: {feature_map}")


def load_candidate_specs(project_root: Path) -> tuple[CandidateSpec, ...]:
    """Load ML candidate specs from ``seed_ideas.yaml``."""
    payload = yaml.safe_load((project_root / "seed_ideas.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("seed_ideas.yaml must contain a mapping")
    specs: list[CandidateSpec] = []
    for idea in _mapping_list(payload.get("ideas")):
        if idea.get("id") != "idea-ml-loop":
            continue
        for row in _mapping_list(idea.get("candidates")):
            params = row.get("parameters", {})
            if not isinstance(params, dict):
                raise ValueError("ML candidate parameters must be mappings")
            specs.append(_candidate_spec_from_row(row, params))
    if not specs:
        raise ValueError("seed_ideas.yaml must declare idea-ml-loop candidates")
    return tuple(specs)


def _candidate_spec_from_row(row: dict[str, Any], params: dict[str, Any]) -> CandidateSpec:
    identifier = str(row.get("id", "") or "").strip()
    title = str(row.get("title", identifier) or identifier).strip()
    feature_map = str(params.get("feature_map", "") or "").strip()
    if feature_map not in {"linear", "quadratic"}:
        raise ValueError(f"unsupported ML candidate feature_map: {feature_map}")
    alpha = float(params.get("alpha", 1.0))
    if alpha < 0:
        raise ValueError("ML candidate alpha must be non-negative")
    complexity = int(params.get("complexity", 1))
    if complexity < 1:
        raise ValueError("ML candidate complexity must be positive")
    return CandidateSpec(
        identifier=identifier,
        title=title,
        feature_map=feature_map,
        alpha=alpha,
        complexity=complexity,
        proposal_status=str(row.get("status", "proposed") or "proposed"),
    )


def _mapping_list(value: object) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("expected a list")
    rows: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("expected list entries to be mappings")
        rows.append(row)
    return tuple(rows)
