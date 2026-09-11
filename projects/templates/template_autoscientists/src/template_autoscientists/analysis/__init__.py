"""Deterministic building blocks behind the coordination loop: the shared
state records, the synthetic objective, noise-band confirmation, and the
offline transcript envelope."""

from .confirmation import Confirmation, confirm_improvement
from .objective import SyntheticObjective
from .state import Champion, ExperimentOutcome, Proposal, SharedState
from .transcript import (
    TRANSCRIPT_SCHEMA,
    replay_transcript,
    transcript_digest,
    validate_transcript,
)

__all__ = [
    "TRANSCRIPT_SCHEMA",
    "Champion",
    "Confirmation",
    "ExperimentOutcome",
    "Proposal",
    "SharedState",
    "SyntheticObjective",
    "confirm_improvement",
    "replay_transcript",
    "transcript_digest",
    "validate_transcript",
]
