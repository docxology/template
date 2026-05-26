"""Model and metric compatibility exports for the MNIST AutoResearch task."""

from __future__ import annotations

from .ml_training import (
    BaselineResult,
    CandidateResult,
    CandidateSpec,
    confusion_matrix,
    cross_entropy,
    evaluate_candidate,
    evaluate_nearest_centroid,
    evaluate_robustness,
    features_for_candidate,
    flatten_images,
    softmax,
    tiny_patch_attention_features,
    train_mlp_classifier,
    train_softmax_classifier,
)

__all__ = [
    "BaselineResult",
    "CandidateResult",
    "CandidateSpec",
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
