"""Candidate-selection compatibility exports for the MNIST AutoResearch task."""

from __future__ import annotations

from .ml_training import (
    CandidateResult,
    MLTaskResult,
    accepted_error_examples,
    deferred_candidate,
    select_accepted_candidate,
    write_confusion_matrix_csv,
    write_error_examples_json,
    write_training_history_csv,
)

__all__ = [
    "CandidateResult",
    "MLTaskResult",
    "accepted_error_examples",
    "deferred_candidate",
    "select_accepted_candidate",
    "write_confusion_matrix_csv",
    "write_error_examples_json",
    "write_training_history_csv",
]
