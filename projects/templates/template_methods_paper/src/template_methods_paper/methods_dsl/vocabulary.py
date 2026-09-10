"""Controlled vocabulary for method steps and execution targets.

Generalizes the intent vocabulary of BPL (Biology Programming Language,
https://gitlab.com/bota-biosciences-public/bpl-code) — whose design principle
#2 states "users write high-level intents (``transfer``, ``add_reagent``,
``incubate``); the compiler lowers them to backend-specific primitives" —
from wet-lab protocols to any controlled procedure: a step names *what*
happens, not *how* a particular backend performs it.
"""

from __future__ import annotations

from enum import Enum


class StepKind(Enum):
    """A controlled-vocabulary intent for one method step.

    Mirrors BPL's protocol-level verbs (``add_reagent``, ``transfer``,
    ``incubate``) but is domain-neutral: ``TRANSFER`` covers moving material,
    data, or control between two resources regardless of domain.
    """

    TRANSFER = "transfer"
    ADD = "add"
    MIX = "mix"
    INCUBATE = "incubate"
    MEASURE = "measure"
    WAIT = "wait"
    COMPUTE = "compute"
    VALIDATE = "validate"
    ANNOTATE = "annotate"


class Target(Enum):
    """Execution backend a method (or step) is compiled for.

    Mirrors BPL's ``@target(human | robot | simulation)`` annotation —
    "human as first-class backend" (design principle #4) means manual steps
    are part of the execution plan, not comments.
    """

    HUMAN = "human"
    AUTOMATED = "automated"
    SIMULATION = "simulation"


# Step kinds that can only run on an AUTOMATED backend (no manual equivalent
# in this DSL's scope) — used by the target compatibility gate.
_AUTOMATED_ONLY: frozenset[StepKind] = frozenset({StepKind.COMPUTE})


def target_accepts(target: Target, kind: StepKind) -> bool:
    """Return whether *target* can execute a step of *kind*.

    ``HUMAN`` and ``SIMULATION`` accept every kind except the automated-only
    set; ``AUTOMATED`` accepts every kind.
    """
    if target == Target.AUTOMATED:
        return True
    return kind not in _AUTOMATED_ONLY
