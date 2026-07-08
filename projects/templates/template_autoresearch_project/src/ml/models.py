"""Model evaluation primitives for the MNIST AutoResearch task."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, cast

import numpy as np

from .data import CandidateSpec, RobustnessTransformSpec
from .training import (
    _mlp_forward,
    confusion_matrix,
    cross_entropy,
    fixed_feature_parameter_count,
    flatten_images,
    probability_rows,
    softmax,
    tiny_patch_attention_features,
    train_mlp_classifier,
    train_softmax_classifier,
)


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
            """Process predict probabilities."""
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
            extra_parameter_count=fixed_feature_parameter_count(spec),
        )

        def predict_probabilities(x_values: np.ndarray) -> np.ndarray:
            """Process predict probabilities."""
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
        test_probabilities=probability_rows(y_probs),
        robustness_metrics=evaluate_robustness(spec, x_test, y_test, predict_probabilities, robustness_transforms),
    )


def features_for_candidate(spec: CandidateSpec, x_values: np.ndarray) -> np.ndarray:
    """Return the model input features for a candidate."""
    if spec.model_type in {"softmax_regression", "mlp"}:
        return flatten_images(x_values)
    if spec.model_type == "tiny_patch_transformer":
        return tiny_patch_attention_features(x_values, spec)
    raise ValueError(f"unsupported model_type: {spec.model_type}")


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


def _nearest_centroid_predict(features: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    distances = ((features[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return cast(np.ndarray, np.argmin(distances, axis=1).astype(np.int64))


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


__all__ = [
    "BaselineResult",
    "CandidateResult",
    "confusion_matrix",
    "cross_entropy",
    "evaluate_candidate",
    "evaluate_nearest_centroid",
    "evaluate_robustness",
    "features_for_candidate",
    "flatten_images",
    "softmax",
    "tiny_patch_attention_features",
    "train_mlp_classifier",
    "train_softmax_classifier",
]
