"""Data and configuration loading for the MNIST AutoResearch task."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import yaml

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


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "CandidateSpec",
    "DatasetSummary",
    "DiagnosticConfig",
    "MNISTTaskConfig",
    "ModelType",
    "RobustnessTransformSpec",
    "TrainingConfig",
    "load_mnist_arrays",
    "load_mnist_task_config",
    "summarize_dataset",
]
