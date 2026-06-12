"""Deterministic reference implementation of the AutoScientists coordination model.

Standalone methods demonstrating the mechanisms from Gao, Fang & Zitnik,
*AutoScientists: Self-Organizing Agent Teams for Long-Running Scientific
Experimentation* (arXiv:2605.28655): a shared champion/experiment-log state, a
dead-end registry, effect-size ranking, noise-band confirmation, and
stagnation-driven team reorganization.

The coordination loop depends only on the :class:`~.agents.Proposer` protocol.
:class:`~.agents.DeterministicProposer` drives the reproducible exemplar runs;
:class:`~.agents.HermesProposer` swaps in a live Hermes agent (served by Ollama)
for the opt-in agentic demo.
"""

from __future__ import annotations

from .agents import DeterministicProposer, Proposer
from .confirmation import Confirmation, confirm_improvement
from .dead_ends import DeadEnd, DeadEndRegistry
from .objective import SyntheticObjective
from .ranking import axis_effect_sizes, rank_axes
from .search import SearchConfig, SearchResult, run_search
from .stagnation import StagnationDetector, reorganize_axes
from .state import Champion, ExperimentOutcome, Proposal, SharedState


def __getattr__(name: str):  # pragma: no cover - lazy script-layer export
    if name == "HermesProposer":
        from hermes_proposer import HermesProposer

        return HermesProposer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Champion",
    "Confirmation",
    "DeadEnd",
    "DeadEndRegistry",
    "DeterministicProposer",
    "ExperimentOutcome",
    "HermesProposer",
    "Proposal",
    "Proposer",
    "SearchConfig",
    "SearchResult",
    "SharedState",
    "StagnationDetector",
    "SyntheticObjective",
    "axis_effect_sizes",
    "confirm_improvement",
    "rank_axes",
    "reorganize_axes",
    "run_search",
]
