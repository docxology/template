"""Deterministic reference implementation of the AutoScientists coordination model.

Standalone methods demonstrating the mechanisms from Gao, Fang & Zitnik,
*AutoScientists: Self-Organizing Agent Teams for Long-Running Scientific
Experimentation* (arXiv:2605.28655): a shared champion/experiment-log state, a
dead-end registry, effect-size ranking, noise-band confirmation, and
stagnation-driven team reorganization.

The coordination loop depends only on the :class:`~.agents.Proposer` protocol.
:class:`~.agents.DeterministicProposer` drives the reproducible exemplar runs;
The explicit live comparison uses identity-checked local Ollama proposals under
matched budgets and retains source, provider, and outcome receipts.
"""

from __future__ import annotations

from .agents import DeterministicProposer, Proposer
from .analysis.confirmation import Confirmation, confirm_improvement
from .search.dead_ends import DeadEnd, DeadEndRegistry
from .analysis.objective import SyntheticObjective
from .search.ranking import axis_effect_sizes, rank_axes
from .search import SearchConfig, SearchResult, run_search
from .search.stagnation import StagnationDetector, reorganize_axes
from .analysis.state import Champion, ExperimentOutcome, Proposal, SharedState
from .analysis.transcript import TRANSCRIPT_SCHEMA, replay_transcript, transcript_digest, validate_transcript


__all__ = [
    "Champion",
    "Confirmation",
    "DeadEnd",
    "DeadEndRegistry",
    "DeterministicProposer",
    "ExperimentOutcome",
    "Proposal",
    "Proposer",
    "SearchConfig",
    "SearchResult",
    "SharedState",
    "StagnationDetector",
    "SyntheticObjective",
    "TRANSCRIPT_SCHEMA",
    "axis_effect_sizes",
    "confirm_improvement",
    "rank_axes",
    "reorganize_axes",
    "run_search",
    "replay_transcript",
    "transcript_digest",
    "validate_transcript",
]
