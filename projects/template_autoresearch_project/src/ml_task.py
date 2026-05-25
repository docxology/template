"""Configurable deterministic MNIST neural-network task."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal, cast

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
    l2: float

    def to_dict(self) -> dict[str, int | float]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


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
    candidates: tuple[CandidateSpec, ...]
    source_path: str = DEFAULT_CONFIG_PATH

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        return {
            "id": self.identifier,
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

    def to_dict(self) -> dict[str, str | int | float]:
        """Serialize to JSON-safe primitives."""
        return asdict(self)


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

    def to_dict(self) -> dict[str, object]:
        """Serialize to JSON-safe primitives."""
        payload = asdict(self)
        payload["lifecycle"] = list(self.lifecycle)
        payload["confusion_matrix"] = [list(row) for row in self.confusion_matrix]
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

    def to_dict(self) -> dict[str, object]:
        """Serialize the full task result."""
        return {
            "task_name": "tiny MNIST neural-network classification",
            "task_config": self.task_config.to_dict(),
            "objective": {
                "metric": self.task_config.metric_name,
                "direction": self.task_config.metric_direction,
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
            "baseline_accuracy": round(self.baseline.test_accuracy, 6),
            "accuracy_delta": round(self.accuracy_delta, 6),
            "benchmark_score": self.benchmark_score,
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
            "transformer_evaluated": any(
                candidate.model_type == "tiny_patch_transformer" and candidate.test_accuracy is not None
                for candidate in self.candidates
            ),
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
        evaluate_candidate(spec, x_train, y_train, x_test, y_test, baseline_accuracy=baseline.test_accuracy)
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
    candidates = tuple(
        _candidate_from_row(row, defaults)
        for row in _mapping_list(payload.get("candidate_configs"), "candidate_configs")
    )
    baseline = _mapping(payload.get("baseline"), "baseline")
    if not candidates:
        raise ValueError("mnist_task.yaml must declare at least one candidate")
    max_candidates = _positive_int(task.get("max_candidates", len(candidates)), "task.max_candidates")
    return MNISTTaskConfig(
        identifier=str(task.get("id", "mnist_tiny_neural_search") or "mnist_tiny_neural_search"),
        dataset_path=str(task.get("dataset_path", "data/mnist_tiny.npz") or "data/mnist_tiny.npz"),
        provenance_path=str(task.get("provenance_path", "data/mnist_tiny_provenance.json") or ""),
        seed=_nonnegative_int(task.get("seed", 0), "task.seed"),
        metric_name=str(task.get("metric_name", "test_accuracy") or "test_accuracy"),
        metric_direction=str(task.get("metric_direction", "maximize") or "maximize"),
        max_candidates=max_candidates,
        normalization=str(task.get("normalization", "zero_one") or "zero_one"),
        baseline_id=str(baseline.get("id", "nearest_centroid_baseline") or "nearest_centroid_baseline"),
        baseline_type=str(baseline.get("type", "nearest_centroid") or "nearest_centroid"),
        training_defaults=defaults,
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
        dataset_name=str(provenance.get("dataset", "MNIST tiny subset")),
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
    """Train and evaluate one neural-network candidate."""
    train_features = features_for_candidate(spec, x_train)
    test_features = features_for_candidate(spec, x_test)
    if spec.model_type == "mlp":
        train_metrics, test_metrics, parameter_count, y_pred = train_mlp_classifier(
            spec,
            train_features,
            y_train,
            test_features,
            y_test,
        )
    else:
        train_metrics, test_metrics, parameter_count, y_pred = train_softmax_classifier(
            spec,
            train_features,
            y_train,
            test_features,
            y_test,
            extra_parameter_count=_fixed_feature_parameter_count(spec),
        )
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
) -> tuple[dict[str, float], dict[str, float], int, np.ndarray]:
    """Train a deterministic softmax classifier."""
    rng = np.random.default_rng(spec.seed)
    class_count = 10
    weights = rng.normal(0.0, 0.03, size=(x_train.shape[1], class_count))
    bias = np.zeros(class_count)
    for epoch in range(spec.training.epochs):
        for batch_indices in _batch_indices(y_train.size, spec.training.batch_size, rng, epoch):
            xb = x_train[batch_indices]
            yb = y_train[batch_indices]
            probs = softmax(xb @ weights + bias)
            grad_logits = probs
            grad_logits[np.arange(yb.size), yb] -= 1.0
            grad_logits /= yb.size
            grad_w = xb.T @ grad_logits + spec.training.l2 * weights
            grad_b = grad_logits.sum(axis=0)
            weights -= spec.training.learning_rate * grad_w
            bias -= spec.training.learning_rate * grad_b
    train_metrics = _linear_metrics(x_train, y_train, weights, bias, spec.training.l2)
    test_metrics = _linear_metrics(x_test, y_test, weights, bias, spec.training.l2)
    y_pred = np.argmax(x_test @ weights + bias, axis=1)
    parameter_count = int(weights.size + bias.size + extra_parameter_count)
    return train_metrics, test_metrics, parameter_count, y_pred.astype(np.int64)


def train_mlp_classifier(
    spec: CandidateSpec,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> tuple[dict[str, float], dict[str, float], int, np.ndarray]:
    """Train a small deterministic MLP classifier."""
    rng = np.random.default_rng(spec.seed)
    layer_sizes = (x_train.shape[1], *spec.hidden_sizes, 10)
    weights = [
        rng.normal(0.0, math.sqrt(2.0 / layer_sizes[index]), size=(layer_sizes[index], layer_sizes[index + 1]))
        for index in range(len(layer_sizes) - 1)
    ]
    biases = [np.zeros(size) for size in layer_sizes[1:]]
    for epoch in range(spec.training.epochs):
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
            for index, (grad_w, grad_b) in enumerate(zip(grad_weights, grad_biases)):
                weights[index] -= spec.training.learning_rate * grad_w
                biases[index] -= spec.training.learning_rate * grad_b
    train_metrics = _mlp_metrics(x_train, y_train, weights, biases, spec.activation, spec.training.l2)
    test_metrics = _mlp_metrics(x_test, y_test, weights, biases, spec.activation, spec.training.l2)
    y_pred = np.argmax(_mlp_forward(x_test, weights, biases, spec.activation)[0][-1], axis=1)
    parameter_count = int(sum(weight.size for weight in weights) + sum(bias.size for bias in biases))
    return train_metrics, test_metrics, parameter_count, y_pred.astype(np.int64)


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


def _training_config(raw: dict[str, Any]) -> TrainingConfig:
    return TrainingConfig(
        batch_size=_positive_int(raw.get("batch_size", 50), "training.batch_size"),
        epochs=_positive_int(raw.get("epochs", 20), "training.epochs"),
        learning_rate=_nonnegative_float(raw.get("learning_rate", 0.1), "training.learning_rate"),
        l2=_nonnegative_float(raw.get("l2", 0.0), "training.l2"),
    )


def _training_overrides(raw: dict[str, Any]) -> dict[str, int | float]:
    keys = {"batch_size", "epochs", "learning_rate", "l2"}
    overrides: dict[str, int | float] = {}
    for key, value in raw.items():
        if key not in keys:
            raise ValueError(f"unsupported training key: {key}")
        if key in {"batch_size", "epochs"}:
            overrides[key] = _positive_int(value, f"training.{key}")
        else:
            overrides[key] = _nonnegative_float(value, f"training.{key}")
    return overrides


def _replace_training_config(base: TrainingConfig, overrides: dict[str, int | float]) -> TrainingConfig:
    return TrainingConfig(
        batch_size=int(overrides.get("batch_size", base.batch_size)),
        epochs=int(overrides.get("epochs", base.epochs)),
        learning_rate=float(overrides.get("learning_rate", base.learning_rate)),
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


def _nonnegative_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")
    return float(value)
