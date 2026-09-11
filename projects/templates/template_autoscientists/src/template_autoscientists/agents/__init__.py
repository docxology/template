"""Proposer agents and the language-model plug-in seam: the ``Proposer``
protocol and the deterministic rule-based proposer used for reproducible runs."""

from .agents import DeterministicProposer, Proposer

__all__ = [
    "DeterministicProposer",
    "Proposer",
]
