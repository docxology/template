"""Configurable deterministic MNIST neural-network task."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Literal, Sequence, cast

import numpy as np
import yaml

from infrastructure.autoresearch import BudgetPolicy

DEFAULT_CONFIG_PATH = "mnist_task.yaml"
ModelType = Literal["softmax_regression", "mlp", "tiny_patch_transformer"]


@dataclass(frozen=True)
class TrainingConfig:
    """SGD settings for one MNIST candidate."""

    batch_size: int
    epochs: int
    learning_rate: float
    learning_rate_decay: float
    gradient_clip_norm: float
    l2: float

    def to_dict(self) -> dict[str, int | float]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


@dataclass(frozen=True)
class DiagnosticConfig:
    """File-configured statistical diagnostic settings."""

    calibration_bins: int = 10
    bootstrap_resamples: int = 1000
    bootstrap_seed_offset: int = 10_003
    low_margin_threshold: float = 0.15
    high_confidence_threshold: float = 0.8
    coverage_thresholds: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8, 0.9)

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["coverage_thresholds"] = list(self.coverage_thresholds)
        return payload


@dataclass(frozen=True)
class RobustnessTransformSpec:
    """File-configured deterministic robustness transform."""

    identifier: str
    transform_type: str
    dx: int = 0
    dy: int = 0
    factor: float = 1.0

    def to_dict(self) -> dict[str, str | int | float]:
        """Serialize to JSON-safe primitives."""
        return {
            "id": self.identifier,
            "type": self.transform_type,
            "dx": self.dx,
            "dy": self.dy,
            "factor": self.factor,
        }


@dataclass(frozen=True)
class CandidateSpec:
    """One file-configured neural-network candidate."""

    identifier: str
    title: str
    model_type: ModelType
    seed: int
    training: TrainingConfig
    hidden_sizes: tuple[int, ...] = ()
    activation: str = "relu"
    patch_size: int = 7
    d_model: int = 32
    train_attention: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["hidden_sizes"] = list(self.hidden_sizes)
        payload["training"] = self.training.to_dict()
        return payload


@dataclass(frozen=True)
class MNISTTaskConfig:
    """Resolved end-to-end MNIST task configuration."""

    identifier: str
    name: str
    dataset_path: str
    provenance_path: str
    seed: int
    metric_name: str
    metric_direction: str
    max_candidates: int
    normalization: str
    baseline_id: str
    baseline_type: str
    training_defaults: TrainingConfig
    diagnostics: DiagnosticConfig
    robustness_transforms: tuple[RobustnessTransformSpec, ...]
    candidates: tuple[CandidateSpec, ...]
    source_path: str = DEFAULT_CONFIG_PATH

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        return {
            "id": self.identifier,
            "name": self.name,
            "dataset_path": self.dataset_path,
            "provenance_path": self.provenance_path,
            "seed": self.seed,
            "metric_name": self.metric_name,
            "metric_direction": self.metric_direction,
            "max_candidates": self.max_candidates,
            "normalization": self.normalization,
            "baseline": {
                "id": self.baseline_id,
                "type": self.baseline_type,
            },
            "training_defaults": self.training_defaults.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "robustness_transforms": [transform.to_dict() for transform in self.robustness_transforms],
            "candidate_configs": [candidate.to_dict() for candidate in self.candidates],
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class DatasetSummary:
    """Summary statistics for the local MNIST subset."""

    dataset_name: str
    source: str
    seed: int
    train_size: int
    test_size: int
    image_shape: tuple[int, int]
    class_count: int
    train_per_class: dict[str, int]
    test_per_class: dict[str, int]
    provenance_sha256: str

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["image_shape"] = list(self.image_shape)
        return payload


@dataclass(frozen=True)
class BaselineResult:
    """Nearest-centroid baseline result."""

    identifier: str
    model_type: str
    test_accuracy: float
    train_accuracy: float
    parameter_count: int
    test_predictions: tuple[int, ...] = ()
    confusion_matrix: tuple[tuple[int, ...], ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["test_predictions"] = list(self.test_predictions)
        payload["confusion_matrix"] = [list(row) for row in self.confusion_matrix]
        return payload


@dataclass(frozen=True)
class CandidateResult:
    """Evaluation result for one configured candidate."""

    identifier: str
    title: str
    model_type: str
    status: str
    lifecycle: tuple[str, ...]
    test_accuracy: float | None
    train_accuracy: float | None
    test_loss: float | None
    train_loss: float | None
    parameter_count: int
    epochs: int
    seed: int
    accuracy_delta_vs_baseline: float | None
    config: dict[str, object]
    confusion_matrix: tuple[tuple[int, ...], ...] = ()
    training_history: tuple[dict[str, int | float], ...] = ()
    test_predictions: tuple[int, ...] = ()
    test_probabilities: tuple[tuple[float, ...], ...] = ()
    robustness_metrics: tuple[dict[str, str | int | float], ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["lifecycle"] = list(self.lifecycle)
        payload["confusion_matrix"] = [list(row) for row in self.confusion_matrix]
        payload["training_history"] = [dict(row) for row in self.training_history]
        payload["test_predictions"] = list(self.test_predictions)
        payload["test_probabilities"] = [list(row) for row in self.test_probabilities]
        payload["robustness_metrics"] = [dict(row) for row in self.robustness_metrics]
        return payload


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
        neural_score = (
            1.0 if any(candidate.model_type == "tiny_patch_transformer" for candidate in self.candidates) else 0.0
        )
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


def load_mnist_task_config(project_root: Path, config_path: str = DEFAULT_CONFIG_PATH) -> MNISTTaskConfig:
    """Load the file-backed MNIST task configuration."""
    path = project_root / config_path
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("mnist_task.yaml must contain a mapping")
    task = _mapping(payload.get("task"), "task")
    defaults = _training_config(_mapping(payload.get("training_defaults"), "training_defaults"))
    diagnostics = _diagnostic_config(_optional_mapping(payload.get("diagnostics"), "diagnostics"))
    robustness_transforms = _robustness_transform_specs(payload.get("robustness_transforms"))
    candidates = tuple(
        _candidate_from_row(row, defaults)
        for row in _mapping_list(payload.get("candidate_configs"), "candidate_configs")
    )
    baseline = _mapping(payload.get("baseline"), "baseline")
    if not candidates:
        raise ValueError("mnist_task.yaml must declare at least one candidate")
    max_candidates = _positive_int(task.get("max_candidates", len(candidates)), "task.max_candidates")
    return MNISTTaskConfig(
        identifier=str(task.get("id", "mnist_small_neural_search") or "mnist_small_neural_search"),
        name=str(
            task.get("name", "small MNIST neural-network classification") or "small MNIST neural-network classification"
        ),
        dataset_path=str(task.get("dataset_path", "data/mnist_small.npz") or "data/mnist_small.npz"),
        provenance_path=str(task.get("provenance_path", "data/mnist_small_provenance.json") or ""),
        seed=_nonnegative_int(task.get("seed", 0), "task.seed"),
        metric_name=str(task.get("metric_name", "test_accuracy") or "test_accuracy"),
        metric_direction=str(task.get("metric_direction", "maximize") or "maximize"),
        max_candidates=max_candidates,
        normalization=str(task.get("normalization", "zero_one") or "zero_one"),
        baseline_id=str(baseline.get("id", "nearest_centroid_baseline") or "nearest_centroid_baseline"),
        baseline_type=str(baseline.get("type", "nearest_centroid") or "nearest_centroid"),
        training_defaults=defaults,
        diagnostics=diagnostics,
        robustness_transforms=robustness_transforms,
        candidates=candidates,
        source_path=config_path,
    )


def load_mnist_arrays(
    project_root: Path,
    config: MNISTTaskConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load and normalize local MNIST arrays."""
    path = project_root / config.dataset_path
    with np.load(path) as data:
        x_train = np.asarray(data["x_train"], dtype=np.float64)
        y_train = np.asarray(data["y_train"], dtype=np.int64)
        x_test = np.asarray(data["x_test"], dtype=np.float64)
        y_test = np.asarray(data["y_test"], dtype=np.int64)
    if config.normalization == "zero_one":
        x_train = x_train / 255.0
        x_test = x_test / 255.0
    elif config.normalization != "none":
        raise ValueError(f"unsupported normalization: {config.normalization}")
    _validate_mnist_shapes(x_train, y_train, x_test, y_test)
    return x_train, y_train, x_test, y_test


def summarize_dataset(
    project_root: Path,
    config: MNISTTaskConfig,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> DatasetSummary:
    """Summarize the local MNIST subset and provenance file."""
    provenance_path = project_root / config.provenance_path
    provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
    if not isinstance(provenance, dict):
        provenance = {}
    return DatasetSummary(
        dataset_name=str(provenance.get("dataset", "MNIST small subset")),
        source=str(provenance.get("source_base_url", "local")),
        seed=config.seed,
        train_size=int(y_train.size),
        test_size=int(y_test.size),
        image_shape=(int(x_train.shape[1]), int(x_train.shape[2])),
        class_count=int(np.unique(y_train).size),
        train_per_class=_class_counts(y_train),
        test_per_class=_class_counts(y_test),
        provenance_sha256=str(provenance.get("npz_sha256", "")),
    )


def evaluate_nearest_centroid(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    *,
    identifier: str,
) -> BaselineResult:
    """Evaluate a nearest-centroid digit baseline."""
    train_flat = flatten_images(x_train)
    test_flat = flatten_images(x_test)
    centroids = np.vstack([train_flat[y_train == label].mean(axis=0) for label in range(10)])
    train_pred = _nearest_centroid_predict(train_flat, centroids)
    test_pred = _nearest_centroid_predict(test_flat, centroids)
    return BaselineResult(
        identifier=identifier,
        model_type="nearest_centroid",
        train_accuracy=round(float(np.mean(train_pred == y_train)), 6),
        test_accuracy=round(float(np.mean(test_pred == y_test)), 6),
        parameter_count=int(centroids.size),
        test_predictions=tuple(int(value) for value in test_pred.tolist()),
        confusion_matrix=confusion_matrix(y_test, test_pred),
    )


def evaluate_candidate(
    spec: CandidateSpec,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    *,
    baseline_accuracy: float,
    robustness_transforms: tuple[RobustnessTransformSpec, ...],
) -> CandidateResult:
    """Train and evaluate one neural-network candidate."""
    train_features = features_for_candidate(spec, x_train)
    test_features = features_for_candidate(spec, x_test)
    if spec.model_type == "mlp":
        (
            train_metrics,
            test_metrics,
            parameter_count,
            y_pred,
            y_probs,
            history,
            mlp_weights,
            mlp_biases,
        ) = train_mlp_classifier(
            spec,
            train_features,
            y_train,
            test_features,
            y_test,
        )

        def predict_probabilities(x_values: np.ndarray) -> np.ndarray:
            features = features_for_candidate(spec, x_values)
            logits = _mlp_forward(features, mlp_weights, mlp_biases, spec.activation)[0][-1]
            return softmax(logits)

    else:
        (
            train_metrics,
            test_metrics,
            parameter_count,
            y_pred,
            y_probs,
            history,
            linear_weights,
            linear_bias,
        ) = train_softmax_classifier(
            spec,
            train_features,
            y_train,
            test_features,
            y_test,
            extra_parameter_count=_fixed_feature_parameter_count(spec),
        )

        def predict_probabilities(x_values: np.ndarray) -> np.ndarray:
            features = features_for_candidate(spec, x_values)
            return softmax(features @ linear_weights + linear_bias)

    test_accuracy = test_metrics["accuracy"]
    return CandidateResult(
        identifier=spec.identifier,
        title=spec.title,
        model_type=spec.model_type,
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        test_accuracy=test_accuracy,
        train_accuracy=train_metrics["accuracy"],
        test_loss=test_metrics["loss"],
        train_loss=train_metrics["loss"],
        parameter_count=parameter_count,
        epochs=spec.training.epochs,
        seed=spec.seed,
        accuracy_delta_vs_baseline=round(test_accuracy - baseline_accuracy, 6),
        config=spec.to_dict(),
        confusion_matrix=confusion_matrix(y_test, y_pred),
        training_history=history,
        test_predictions=tuple(int(value) for value in y_pred.tolist()),
        test_probabilities=_probability_rows(y_probs),
        robustness_metrics=evaluate_robustness(spec, x_test, y_test, predict_probabilities, robustness_transforms),
    )


def features_for_candidate(spec: CandidateSpec, x_values: np.ndarray) -> np.ndarray:
    """Return the model input features for a candidate."""
    if spec.model_type in {"softmax_regression", "mlp"}:
        return flatten_images(x_values)
    if spec.model_type == "tiny_patch_transformer":
        return tiny_patch_attention_features(x_values, spec)
    raise ValueError(f"unsupported model_type: {spec.model_type}")


def train_softmax_classifier(
    spec: CandidateSpec,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    *,
    extra_parameter_count: int = 0,
) -> tuple[
    dict[str, float],
    dict[str, float],
    int,
    np.ndarray,
    np.ndarray,
    tuple[dict[str, int | float], ...],
    np.ndarray,
    np.ndarray,
]:
    """Train a deterministic softmax classifier."""
    rng = np.random.default_rng(spec.seed)
    class_count = 10
    weights = rng.normal(0.0, 0.03, size=(x_train.shape[1], class_count))
    bias = np.zeros(class_count)
    history: list[dict[str, int | float]] = []
    for epoch in range(spec.training.epochs):
        learning_rate = _epoch_learning_rate(spec.training, epoch)
        for batch_indices in _batch_indices(y_train.size, spec.training.batch_size, rng, epoch):
            xb = x_train[batch_indices]
            yb = y_train[batch_indices]
            probs = softmax(xb @ weights + bias)
            grad_logits = probs
            grad_logits[np.arange(yb.size), yb] -= 1.0
            grad_logits /= yb.size
            grad_w = xb.T @ grad_logits + spec.training.l2 * weights
            grad_b = grad_logits.sum(axis=0)
            scale = _gradient_clip_scale((grad_w, grad_b), spec.training.gradient_clip_norm)
            weights -= learning_rate * scale * grad_w
            bias -= learning_rate * scale * grad_b
        history.append(
            _history_row(
                epoch + 1,
                learning_rate,
                _linear_metrics(x_train, y_train, weights, bias, spec.training.l2),
                _linear_metrics(x_test, y_test, weights, bias, spec.training.l2),
            )
        )
    train_metrics = _linear_metrics(x_train, y_train, weights, bias, spec.training.l2)
    test_metrics = _linear_metrics(x_test, y_test, weights, bias, spec.training.l2)
    test_probs = softmax(x_test @ weights + bias)
    y_pred = np.argmax(test_probs, axis=1)
    parameter_count = int(weights.size + bias.size + extra_parameter_count)
    return (
        train_metrics,
        test_metrics,
        parameter_count,
        y_pred.astype(np.int64),
        test_probs,
        tuple(history),
        weights,
        bias,
    )


def train_mlp_classifier(
    spec: CandidateSpec,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> tuple[
    dict[str, float],
    dict[str, float],
    int,
    np.ndarray,
    np.ndarray,
    tuple[dict[str, int | float], ...],
    list[np.ndarray],
    list[np.ndarray],
]:
    """Train a small deterministic MLP classifier."""
    rng = np.random.default_rng(spec.seed)
    layer_sizes = (x_train.shape[1], *spec.hidden_sizes, 10)
    weights = [
        rng.normal(0.0, math.sqrt(2.0 / layer_sizes[index]), size=(layer_sizes[index], layer_sizes[index + 1]))
        for index in range(len(layer_sizes) - 1)
    ]
    biases = [np.zeros(size) for size in layer_sizes[1:]]
    history: list[dict[str, int | float]] = []
    for epoch in range(spec.training.epochs):
        learning_rate = _epoch_learning_rate(spec.training, epoch)
        for batch_indices in _batch_indices(y_train.size, spec.training.batch_size, rng, epoch):
            xb = x_train[batch_indices]
            yb = y_train[batch_indices]
            activations, preactivations = _mlp_forward(xb, weights, biases, spec.activation)
            grad = softmax(activations[-1])
            grad[np.arange(yb.size), yb] -= 1.0
            grad /= yb.size
            grad_weights: list[np.ndarray] = []
            grad_biases: list[np.ndarray] = []
            for layer_index in reversed(range(len(weights))):
                grad_weights.append(activations[layer_index].T @ grad + spec.training.l2 * weights[layer_index])
                grad_biases.append(grad.sum(axis=0))
                if layer_index > 0:
                    grad = grad @ weights[layer_index].T
                    grad *= _activation_grad(preactivations[layer_index - 1], spec.activation)
            grad_weights.reverse()
            grad_biases.reverse()
            scale = _gradient_clip_scale(
                tuple(grad_weights) + tuple(grad_biases),
                spec.training.gradient_clip_norm,
            )
            for index, (grad_w, grad_b) in enumerate(zip(grad_weights, grad_biases)):
                weights[index] -= learning_rate * scale * grad_w
                biases[index] -= learning_rate * scale * grad_b
        history.append(
            _history_row(
                epoch + 1,
                learning_rate,
                _mlp_metrics(x_train, y_train, weights, biases, spec.activation, spec.training.l2),
                _mlp_metrics(x_test, y_test, weights, biases, spec.activation, spec.training.l2),
            )
        )
    train_metrics = _mlp_metrics(x_train, y_train, weights, biases, spec.activation, spec.training.l2)
    test_metrics = _mlp_metrics(x_test, y_test, weights, biases, spec.activation, spec.training.l2)
    test_probs = softmax(_mlp_forward(x_test, weights, biases, spec.activation)[0][-1])
    y_pred = np.argmax(test_probs, axis=1)
    parameter_count = int(sum(weight.size for weight in weights) + sum(bias.size for bias in biases))
    return (
        train_metrics,
        test_metrics,
        parameter_count,
        y_pred.astype(np.int64),
        test_probs,
        tuple(history),
        weights,
        biases,
    )


def tiny_patch_attention_features(x_values: np.ndarray, spec: CandidateSpec) -> np.ndarray:
    """Return fixed tiny patch-attention features for MNIST images."""
    if 28 % spec.patch_size != 0:
        raise ValueError("patch_size must divide 28")
    rng = np.random.default_rng(spec.seed)
    patches_per_side = 28 // spec.patch_size
    patch_dim = spec.patch_size * spec.patch_size
    patches = (
        x_values.reshape(x_values.shape[0], patches_per_side, spec.patch_size, patches_per_side, spec.patch_size)
        .swapaxes(2, 3)
        .reshape(x_values.shape[0], patches_per_side * patches_per_side, patch_dim)
    )
    embed = rng.normal(0.0, 1.0 / math.sqrt(patch_dim), size=(patch_dim, spec.d_model))
    q_proj = rng.normal(0.0, 1.0 / math.sqrt(spec.d_model), size=(spec.d_model, spec.d_model))
    k_proj = rng.normal(0.0, 1.0 / math.sqrt(spec.d_model), size=(spec.d_model, spec.d_model))
    v_proj = rng.normal(0.0, 1.0 / math.sqrt(spec.d_model), size=(spec.d_model, spec.d_model))
    out_proj = rng.normal(0.0, 1.0 / math.sqrt(spec.d_model), size=(spec.d_model, spec.d_model))
    token_positions = np.arange(patches.shape[1], dtype=np.float64)[:, None]
    dims = np.arange(spec.d_model, dtype=np.float64)[None, :]
    pos = np.sin(token_positions / np.power(10000.0, (2 * (dims // 2)) / spec.d_model))
    tokens = patches @ embed + pos
    q_values = tokens @ q_proj
    k_values = tokens @ k_proj
    v_values = tokens @ v_proj
    scores = q_values @ np.swapaxes(k_values, 1, 2) / math.sqrt(spec.d_model)
    attention = softmax(scores)
    attended = attention @ v_values @ out_proj
    return cast(np.ndarray, np.maximum(attended.mean(axis=1), 0.0))


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


def evaluate_robustness(
    spec: CandidateSpec,
    x_test: np.ndarray,
    y_test: np.ndarray,
    predict_probabilities: Callable[[np.ndarray], np.ndarray],
    transforms: tuple[RobustnessTransformSpec, ...],
) -> tuple[dict[str, str | int | float], ...]:
    """Evaluate deterministic no-retrain perturbations for one candidate."""
    rows: list[dict[str, str | int | float]] = []
    for transform in transforms:
        transformed = _apply_robustness_transform(x_test, transform)
        probabilities = predict_probabilities(transformed)
        predictions = np.argmax(probabilities, axis=1)
        rows.append(
            {
                "candidate_id": spec.identifier,
                "model_type": spec.model_type,
                "transform": transform.identifier,
                "transform_type": transform.transform_type,
                "accuracy": round(float(np.mean(predictions == y_test)), 6),
                "sample_count": int(y_test.size),
            }
        )
    return tuple(rows)


def flatten_images(x_values: np.ndarray) -> np.ndarray:
    """Flatten MNIST image arrays."""
    return x_values.reshape(x_values.shape[0], -1)


def softmax(logits: np.ndarray) -> np.ndarray:
    """Stable softmax over the last axis."""
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return cast(np.ndarray, exp / exp.sum(axis=-1, keepdims=True))


def cross_entropy(probs: np.ndarray, labels: np.ndarray) -> float:
    """Return mean cross-entropy loss."""
    clipped = np.clip(probs[np.arange(labels.size), labels], 1e-12, 1.0)
    return float(-np.mean(np.log(clipped)))


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[tuple[int, ...], ...]:
    """Return a 10-by-10 confusion matrix."""
    matrix = np.zeros((10, 10), dtype=int)
    for true_label, pred_label in zip(y_true, y_pred):
        matrix[int(true_label), int(pred_label)] += 1
    return tuple(tuple(int(value) for value in row) for row in matrix)


def _probability_rows(probabilities: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(round(float(value), 10) for value in row) for row in probabilities)


def _apply_robustness_transform(x_values: np.ndarray, transform: RobustnessTransformSpec) -> np.ndarray:
    if transform.transform_type == "identity":
        return x_values
    if transform.transform_type == "contrast":
        return np.clip(x_values * transform.factor, 0.0, 1.0)
    if transform.transform_type == "shift":
        return _shift_images(x_values, dx=transform.dx, dy=transform.dy)
    raise ValueError(f"unsupported robustness transform type: {transform.transform_type}")


def _shift_images(x_values: np.ndarray, *, dx: int, dy: int) -> np.ndarray:
    shifted = np.zeros_like(x_values)
    source_y_start = max(0, -dy)
    source_y_end = x_values.shape[1] - max(0, dy)
    source_x_start = max(0, -dx)
    source_x_end = x_values.shape[2] - max(0, dx)
    dest_y_start = max(0, dy)
    dest_y_end = dest_y_start + max(0, source_y_end - source_y_start)
    dest_x_start = max(0, dx)
    dest_x_end = dest_x_start + max(0, source_x_end - source_x_start)
    if source_y_end > source_y_start and source_x_end > source_x_start:
        shifted[:, dest_y_start:dest_y_end, dest_x_start:dest_x_end] = x_values[
            :,
            source_y_start:source_y_end,
            source_x_start:source_x_end,
        ]
    return shifted


def _candidate_from_row(row: dict[str, Any], defaults: TrainingConfig) -> CandidateSpec:
    model_type = str(row.get("model_type", "") or "")
    if model_type not in {"softmax_regression", "mlp", "tiny_patch_transformer"}:
        raise ValueError(f"unsupported model_type: {model_type}")
    training = defaults
    raw_training = row.get("training")
    if raw_training is not None:
        training = _replace_training_config(
            training,
            _training_overrides(_mapping(raw_training, "candidate.training")),
        )
    return CandidateSpec(
        identifier=str(row.get("id", "") or ""),
        title=str(row.get("title", row.get("id", "")) or ""),
        model_type=cast(ModelType, model_type),
        seed=_nonnegative_int(row.get("seed", 0), "candidate.seed"),
        training=training,
        hidden_sizes=tuple(_positive_int(value, "candidate.hidden_sizes") for value in row.get("hidden_sizes", [])),
        activation=str(row.get("activation", "relu") or "relu"),
        patch_size=_positive_int(row.get("patch_size", 7), "candidate.patch_size"),
        d_model=_positive_int(row.get("d_model", 32), "candidate.d_model"),
        train_attention=bool(row.get("train_attention", False)),
    )


def _diagnostic_config(raw: dict[str, Any]) -> DiagnosticConfig:
    thresholds = raw.get("coverage_thresholds", [0.5, 0.6, 0.7, 0.8, 0.9])
    if not isinstance(thresholds, list):
        raise ValueError("diagnostics.coverage_thresholds must be a list")
    coverage_thresholds = tuple(_probability_float(value, "diagnostics.coverage_thresholds") for value in thresholds)
    if not coverage_thresholds:
        raise ValueError("diagnostics.coverage_thresholds must not be empty")
    return DiagnosticConfig(
        calibration_bins=_positive_int(raw.get("calibration_bins", 10), "diagnostics.calibration_bins"),
        bootstrap_resamples=_positive_int(raw.get("bootstrap_resamples", 1000), "diagnostics.bootstrap_resamples"),
        bootstrap_seed_offset=_nonnegative_int(
            raw.get("bootstrap_seed_offset", 10_003),
            "diagnostics.bootstrap_seed_offset",
        ),
        low_margin_threshold=_probability_float(
            raw.get("low_margin_threshold", 0.15),
            "diagnostics.low_margin_threshold",
        ),
        high_confidence_threshold=_probability_float(
            raw.get("high_confidence_threshold", 0.8),
            "diagnostics.high_confidence_threshold",
        ),
        coverage_thresholds=coverage_thresholds,
    )


def _robustness_transform_specs(raw: object) -> tuple[RobustnessTransformSpec, ...]:
    if raw is None:
        return (
            RobustnessTransformSpec(identifier="identity", transform_type="identity"),
            RobustnessTransformSpec(identifier="shift_right_1", transform_type="shift", dx=1),
            RobustnessTransformSpec(identifier="shift_down_1", transform_type="shift", dy=1),
            RobustnessTransformSpec(identifier="low_contrast_0_85", transform_type="contrast", factor=0.85),
        )
    rows = _mapping_list(raw, "robustness_transforms")
    transforms: list[RobustnessTransformSpec] = []
    for row in rows:
        transform_type = str(row.get("type", "") or "")
        if transform_type not in {"identity", "shift", "contrast"}:
            raise ValueError(f"unsupported robustness transform type: {transform_type}")
        identifier = str(row.get("id", "") or "")
        if not identifier:
            raise ValueError("robustness transform id must not be empty")
        transforms.append(
            RobustnessTransformSpec(
                identifier=identifier,
                transform_type=transform_type,
                dx=_int_value(row.get("dx", 0), "robustness_transform.dx"),
                dy=_int_value(row.get("dy", 0), "robustness_transform.dy"),
                factor=_nonnegative_float(row.get("factor", 1.0), "robustness_transform.factor"),
            )
        )
    if not transforms:
        raise ValueError("robustness_transforms must not be empty")
    return tuple(transforms)


def _training_config(raw: dict[str, Any]) -> TrainingConfig:
    return TrainingConfig(
        batch_size=_positive_int(raw.get("batch_size", 50), "training.batch_size"),
        epochs=_positive_int(raw.get("epochs", 20), "training.epochs"),
        learning_rate=_nonnegative_float(raw.get("learning_rate", 0.1), "training.learning_rate"),
        learning_rate_decay=_decay_float(raw.get("learning_rate_decay", 1.0), "training.learning_rate_decay"),
        gradient_clip_norm=_nonnegative_float(raw.get("gradient_clip_norm", 0.0), "training.gradient_clip_norm"),
        l2=_nonnegative_float(raw.get("l2", 0.0), "training.l2"),
    )


def _training_overrides(raw: dict[str, Any]) -> dict[str, int | float]:
    keys = {"batch_size", "epochs", "learning_rate", "learning_rate_decay", "gradient_clip_norm", "l2"}
    overrides: dict[str, int | float] = {}
    for key, value in raw.items():
        if key not in keys:
            raise ValueError(f"unsupported training key: {key}")
        if key in {"batch_size", "epochs"}:
            overrides[key] = _positive_int(value, f"training.{key}")
        elif key == "learning_rate_decay":
            overrides[key] = _decay_float(value, f"training.{key}")
        else:
            overrides[key] = _nonnegative_float(value, f"training.{key}")
    return overrides


def _replace_training_config(base: TrainingConfig, overrides: dict[str, int | float]) -> TrainingConfig:
    return TrainingConfig(
        batch_size=int(overrides.get("batch_size", base.batch_size)),
        epochs=int(overrides.get("epochs", base.epochs)),
        learning_rate=float(overrides.get("learning_rate", base.learning_rate)),
        learning_rate_decay=float(overrides.get("learning_rate_decay", base.learning_rate_decay)),
        gradient_clip_norm=float(overrides.get("gradient_clip_norm", base.gradient_clip_norm)),
        l2=float(overrides.get("l2", base.l2)),
    )


def _validate_mnist_shapes(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> None:
    if x_train.ndim != 3 or x_test.ndim != 3 or x_train.shape[1:] != (28, 28) or x_test.shape[1:] != (28, 28):
        raise ValueError("MNIST arrays must have shape (n, 28, 28)")
    if y_train.ndim != 1 or y_test.ndim != 1:
        raise ValueError("MNIST label arrays must be one-dimensional")
    if x_train.shape[0] != y_train.size or x_test.shape[0] != y_test.size:
        raise ValueError("MNIST images and labels must have matching lengths")
    if set(np.unique(y_train).tolist()) != set(range(10)) or set(np.unique(y_test).tolist()) != set(range(10)):
        raise ValueError("MNIST train and test labels must contain all 10 classes")


def _nearest_centroid_predict(features: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    distances = ((features[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return cast(np.ndarray, np.argmin(distances, axis=1).astype(np.int64))


def _batch_indices(size: int, batch_size: int, rng: np.random.Generator, epoch: int) -> tuple[np.ndarray, ...]:
    order = rng.permutation(size) if epoch > 0 else np.arange(size)
    return tuple(order[start : start + batch_size] for start in range(0, size, batch_size))


def _linear_metrics(
    features: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    bias: np.ndarray,
    l2: float,
) -> dict[str, float]:
    logits = features @ weights + bias
    probs = softmax(logits)
    accuracy = float(np.mean(np.argmax(probs, axis=1) == labels))
    loss = cross_entropy(probs, labels) + 0.5 * l2 * float(np.sum(weights * weights))
    return {"accuracy": round(accuracy, 6), "loss": round(loss, 6)}


def _history_row(
    epoch: int,
    learning_rate: float,
    train_metrics: dict[str, float],
    test_metrics: dict[str, float],
) -> dict[str, int | float]:
    return {
        "epoch": epoch,
        "learning_rate": round(learning_rate, 8),
        "train_accuracy": train_metrics["accuracy"],
        "test_accuracy": test_metrics["accuracy"],
        "train_loss": train_metrics["loss"],
        "test_loss": test_metrics["loss"],
    }


def _mlp_forward(
    features: np.ndarray,
    weights: list[np.ndarray],
    biases: list[np.ndarray],
    activation: str,
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    activations = [features]
    preactivations: list[np.ndarray] = []
    current = features
    for weight, bias in zip(weights[:-1], biases[:-1]):
        preactivation = current @ weight + bias
        preactivations.append(preactivation)
        current = _activation(preactivation, activation)
        activations.append(current)
    logits = current @ weights[-1] + biases[-1]
    activations.append(logits)
    return activations, preactivations


def _mlp_metrics(
    features: np.ndarray,
    labels: np.ndarray,
    weights: list[np.ndarray],
    biases: list[np.ndarray],
    activation: str,
    l2: float,
) -> dict[str, float]:
    logits = _mlp_forward(features, weights, biases, activation)[0][-1]
    probs = softmax(logits)
    accuracy = float(np.mean(np.argmax(probs, axis=1) == labels))
    loss = cross_entropy(probs, labels) + 0.5 * l2 * float(sum(np.sum(weight * weight) for weight in weights))
    return {"accuracy": round(accuracy, 6), "loss": round(loss, 6)}


def _activation(values: np.ndarray, activation: str) -> np.ndarray:
    if activation == "relu":
        return cast(np.ndarray, np.maximum(values, 0.0))
    if activation == "tanh":
        return cast(np.ndarray, np.tanh(values))
    raise ValueError(f"unsupported activation: {activation}")


def _activation_grad(values: np.ndarray, activation: str) -> np.ndarray:
    if activation == "relu":
        return (values > 0.0).astype(np.float64)
    if activation == "tanh":
        activated = np.tanh(values)
        return cast(np.ndarray, 1.0 - activated * activated)
    raise ValueError(f"unsupported activation: {activation}")


def _fixed_feature_parameter_count(spec: CandidateSpec) -> int:
    if spec.model_type != "tiny_patch_transformer":
        return 0
    patch_dim = spec.patch_size * spec.patch_size
    return int(patch_dim * spec.d_model + 4 * spec.d_model * spec.d_model)


def _with_final_status(result: CandidateResult, accepted_id: str) -> CandidateResult:
    if result.identifier == accepted_id:
        return replace(result, status="accepted", lifecycle=("proposed", "evaluated", "accepted"))
    return replace(result, status="rejected", lifecycle=("proposed", "evaluated", "rejected"))


def _class_counts(labels: np.ndarray) -> dict[str, int]:
    return {str(label): int(np.sum(labels == label)) for label in range(10)}


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _optional_mapping(value: object, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    return _mapping(value, label)


def _mapping_list(value: object, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    rows: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError(f"{label} entries must be mappings")
        rows.append(row)
    return tuple(rows)


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _int_value(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _nonnegative_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")
    return float(value)


def _probability_float(value: object, label: str) -> float:
    value_float = _nonnegative_float(value, label)
    if value_float > 1.0:
        raise ValueError(f"{label} must be between 0 and 1")
    return value_float


def _decay_float(value: object, label: str) -> float:
    value_float = _nonnegative_float(value, label)
    if value_float <= 0.0 or value_float > 1.0:
        raise ValueError(f"{label} must be greater than 0 and at most 1")
    return value_float


def _epoch_learning_rate(training: TrainingConfig, epoch_index: int) -> float:
    return training.learning_rate * (training.learning_rate_decay**epoch_index)


def _gradient_clip_scale(gradients: Sequence[np.ndarray], max_norm: float) -> float:
    if max_norm <= 0.0:
        return 1.0
    norm_sq = sum(float(np.sum(gradient * gradient)) for gradient in gradients)
    if norm_sq <= 0.0:
        return 1.0
    norm = math.sqrt(norm_sq)
    if norm <= max_norm:
        return 1.0
    return max_norm / norm
