"""Deterministic MNIST model training primitives."""

from __future__ import annotations

import math
from typing import Sequence, cast

import numpy as np

from .ml_data import CandidateSpec, TrainingConfig


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


def fixed_feature_parameter_count(spec: CandidateSpec) -> int:
    """Return fixed-feature parameters used by the tiny patch attention transform."""
    if spec.model_type != "tiny_patch_transformer":
        return 0
    patch_dim = spec.patch_size * spec.patch_size
    return int(patch_dim * spec.d_model + 4 * spec.d_model * spec.d_model)


def probability_rows(probabilities: np.ndarray) -> tuple[tuple[float, ...], ...]:
    """Serialize probability arrays as rounded immutable rows."""
    return tuple(tuple(round(float(value), 10) for value in row) for row in probabilities)


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


__all__ = [
    "confusion_matrix",
    "cross_entropy",
    "fixed_feature_parameter_count",
    "flatten_images",
    "probability_rows",
    "softmax",
    "tiny_patch_attention_features",
    "train_mlp_classifier",
    "train_softmax_classifier",
]
